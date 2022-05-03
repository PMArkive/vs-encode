import os
import shutil
from copy import copy
from fractions import Fraction
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import vapoursynth as vs
from vardautomation import (X264, X265, Chapter, FileInfo, Lang, Patch,
                            SelfRunner, VPath, logger)
from vardautomation.utils import Properties

from .helpers import (finalize_clip, get_channel_layout_str, get_encoder_cores,
                      resolve_ap_trims)
from .setup import IniSetup, VEncSettingsSetup, XmlGenerator
from .types import AUDIO_ENCODER, VIDEO_ENCODER

__all__: List[str] = [
    'Encoder'
]


class Encoder:
    """
    Video encoding chain builder.
    There are multiple steps to video encoding and processing, and each is added as an individual step in this class.
    These can be chained in any order, except for `run` which should be run at the end.

    The following steps are included as methods:

        * video
        * audio
        * chapter
        * mux
        * run

    You can chain them together like so:
        ``Encoder(file_obj, filtered_clip).video('x264').audio().mux().run()``

    For arguments, see the individual methods.

    The only REQUIRED steps are `video` and `run`.

    :param file:            FileInfo object.
    :param clip:            VideoNode to use for the output.
                            This should be the filtered clip, or in other words,
                            the clip you want to encode as usual.
    :param languages:       Languages for every track.
                            If given a list, you can set individual languages per track.
                            The first will always be the language of the video track.
                            It's best to set this to your source's region.
                            The second one is used for all Audio tracks.
                            The third one will be used for chapters.
                            If None, assumes Japanese for all tracks.
    :param setup_args:      Kwargs for the ini file setup.
    """
    import vardautomation as va

    # init vars
    file: FileInfo
    clip: vs.VideoNode
    clean_up: bool

    # Language for every track
    v_lang: Lang
    a_lang: Lang
    c_lang: Lang

    # Generic Muxer vars
    v_encoder: va.VideoEncoder
    v_lossless_encoder: va.LosslessEncoder | None = None
    a_tracks: List[va.AudioTrack] = []
    a_extracters: va.AudioExtracter | Sequence[va.AudioExtracter] | None = None
    a_cutters: va.AudioCutter | Sequence[va.AudioCutter] | None = None
    a_encoders: va.AudioEncoder | Sequence[va.AudioEncoder] | None = None
    c_tracks: List[va.ChaptersTrack] = []
    muxer: va.MatroskaFile

    # Video-related vars
    enc_lossless: bool = False
    clean_up: bool = True
    qp_clip: vs.VideoNode | None = None

    # Audio-related vars
    external_audio: bool = True
    audio_files: List[str] = []

    def __init__(self, file: FileInfo, clip: vs.VideoNode, /, lang: Lang | List[Lang] = JAPANESE,
                 **setup_args: Any) -> None:
        logger.success("Initializing vardautomation...\n")
        self.file = file
        self.clip = clip

        # TODO: Support multiple languages for different tracks.
        if isinstance(lang, self.va.Lang):
            self.v_lang = lang
            self.a_lang = lang
            self.c_lang = lang
        elif len(lang) < 3:
            raise ValueError("Encoder: 'You must pass at least three (3) languages! "
                                f"Not {len(lang)}!'")
        elif len(lang) >= 3:
            self.v_lang = lang[0]
            self.a_lang = lang[1]
            self.c_lang = lang[2]

        init = IniSetup(**setup_args)

        self.file.name_file_final = init.parse_name()

    def perform_cleanup(self, runner_object: SelfRunner | Patch) -> None:
        """
        Helper function that performs clean-up after running the encode.
        """
        runner_object.work_files.remove(self.file.name_clip_output)
        runner_object.work_files.remove(self.file.chapter)
        runner_object.work_files.clear()

        for track in self.audio_files:
            try:
                os.remove(track)
            except FileNotFoundError:
                logger.warning(f"File \"{track}\" not found! Can't clean it up, so skipping.")

        logger.info("Cleaning up leftover files done!")

    def video(self, encoder: VIDEO_ENCODER = 'x265', settings: str | bool | None = None,
              zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
              /, *, sanitize_output: bool = True, use_qp: bool = True, qp_clip: vs.VideoNode | None = None,
              prefetch: int | None = None, resumable: bool = True, **enc_overrides: Any) -> "Encoder":
        """
        Basic video-related setup for the output video.

        :param encoder:                 What encoder to use when encoding the video.
                                        Valid options are: x264, x265, nvencclossless, ffv1.
        :param settings:                Path to settings file. Defaults to ".settings/settings.txt".
        :param sanitize_output:         Whether to sanitize the clip for outputting.
                                        This means setting the bitdepth to 10 and clamping it to TV range.
                                        If False, will assume you've handled this in your script yourself.
        :param use_qp:                  Use a qp clip to help the encoder with finding scene changes.
        :param qp_clip:                 Optional qp clip for the qpfile creation. Useful for DVD encodes.
        :param prefetch:                Prefetch. Set a low value to limit the number of frames rendered at once.
        :param resumable:               Enable resumable encoding. This makes it so encodes can continue
                                        even in the event it has stopped midway.
        :param zones:                   Zones for x264/x265. Expected in the following format:
                                        {(100, 200): {'crf': 13}, (500, 600): {'crf': 12}}.
                                        Zones will be sorted prior to getting passed to the encoder.
        :param enc_overrides:           Overrides for the encoder settings.
        """
        logger.success("Checking video related settings...")

        self.clip = finalize_clip(self.clip) if sanitize_output else self.clip

        if zones:
            zones = dict(sorted(zones.items(), key=lambda item: item[1]))

        if settings is None:
            # TODO: Automatically generate a settings file
            logger.warning("video: 'No settings file given. Will automatically generate one for you. "
                           "To disable this behaviour, pass `settings=False`.")

        # TODO: Use proper intenums, match case?
        enc = encoder.lower()

        match enc:
            case 'x264': self.v_encoder = X264Custom(settings, zones=zones, **enc_overrides)
            case 'x265': self.v_encoder = X265Custom(settings, zones=zones, **enc_overrides)
            case 'nvencclossless': self.v_lossless_encoder = self.va.NVEncCLossless(**enc_overrides)
            case 'ffv1': self.v_lossless_encoder = self.va.FFV1(**enc_overrides)
            case _:  raise ValueError(f"Encoder.video: '\"{encoder}\" is not a valid video encoder! "
                                    "Please see the docstring for valid encoders!'")

        logger.info(f"Encoding video using {enc}.")

        if not self.v_lossless_encoder:
            logger.info(f"Zones: {zones}")

            # Set settings that only work for x264/x265
            self.v_encoder.prefetch = prefetch or 0
            self.v_encoder.resumable = resumable

        if use_qp:
            self.qp_clip = qp_clip or self.file.clip_cut

        return self

    # TODO: Add `all_tracks` support to internal vardoto extracters/encoders/trimmers.
    def audio(self, encoder: AUDIO_ENCODER = 'qaac', xml_file: str | None = None,
              /, all_tracks: bool = False, use_ap: bool = True,
              *, fps: Fraction | float | None = None,
              custom_trims: List[int | None] | List[List[int | None]] | None = None,
              external_audio_file: str | None = None, external_audio_clip: vs.VideoNode | None = None,
              cut_overrides: Dict[str, Any] = {}, enc_overrides: Dict[str, Any] = {}) -> "Encoder":
        """
        Basic audio-related setup for the output audio.

        Audio files are always trimmed using either AudioProcessor or Sox.

        :param encoder:                 What encoder/setup to use when encoding the audio.
                                        Valid options are: passthrough, qaac, opus, fdkaac, flac.
        :param all_tracks:              Whether to mux in all the audio tracks or just the first track.
                                        This currently only works with AudioProcessor.
                                        If False, muxes in the first track.
                                        It will ALWAYS grab just the first track when ``use_ap=False``.
        :param use_ap:                  Whether to use bvsfunc's AudioProcessor to process audio.
                                        If False, uses internal vardautomation encoders.
        :param xml_file:                External XML file with audio encoding specifications.
                                        Only used for AAC encodes.
        :param fps:                     Fraction of the framerate for AudioProcessor's handling.
                                        If None, grabs the fps from the input clip.
                                        If int/float, automatically sets it to `fps/1`.
        :param custom_trims             Custom trims for audio trimming.
                                        If None, uses file.trims_or_dfs.
        :param cut_overrides:           Overrides for SoxCutter's cutting.
        :param enc_overrides:           Overrides for the encoder settings.
        """
        logger.success("Checking audio related settings...")

        if use_ap:
            try:
                from bvsfunc.util import AudioProcessor as ap
            except ModuleNotFoundError:
                raise ModuleNotFoundError("Encoder.audio: missing dependency 'bvsfunc'")
        else:
            self.a_extracters = [self.va.Eac3toAudioExtracter(self.file)]

        try:
            from pymediainfo import MediaInfo
        except ModuleNotFoundError:
            raise ModuleNotFoundError("Encoder.audio: missing dependency 'pymediainfo'")

        # Just making it shorter for my own convenience
        ea_clip = external_audio_clip
        ea_file = external_audio_file

        if not custom_trims:
            trims = self.file.trims_or_dfs if not ea_clip else ea_clip.trims_or_dfs
        else:
            trims = custom_trims

        if isinstance(fps, int) or isinstance(fps, float):
            fps = Fraction(fps, 1)  # TODO: Automagically shift decimal point if applicable (23.976 -> 23976)

        self.file.a_src_cut = VPath(self.file.name)

        file_copy = copy(self.file)

        if ea_file is not None:
            file_copy.path = VPath(ea_file)
            file_copy.path_without_ext = VPath(os.path.splitext(ea_file)[0])
            file_copy.work_filename = file_copy.path.stem
            file_copy.a_src_cut = VPath(self.file.name)

        if not use_ap:
            file_copy.trims_or_dfs = trims

        track_channels: List[int] = []
        original_codecs: List[str] = []

        if ea_file is not None:
            ea_media_info = MediaInfo.parse(ea_file)
            for track in ea_media_info.tracks:
                if track.track_type == 'Audio':
                    track_channels += [track.channel_s]
                    original_codecs += [track.format]
                    if not all_tracks:
                        break
        else:
            for track in self.file.media_info.tracks:
                if track.track_type == 'Audio':
                    track_channels += [track.channel_s]
                    original_codecs += [track.format]
                    if not all_tracks:
                        break

        enc = encoder.lower()

        # These codecs get re-encoded/errored out by all the extracters, making a simple passthrough impossible.
        reenc_codecs: List[str] = [
            'AC-3', 'EAC-3'
        ]

        if enc == 'passthrough' and any(codec in original_codecs for codec in reenc_codecs):
            logger.warning("Unsupported audio codecs found in source file! "
                           "Will be automatically set to encode using FLAC instead.\n"
                           f"The following codecs are unsupported: {reenc_codecs}")
            enc = 'flac'

        if enc in ('qaac', 'flac') and use_ap:
            is_aac = enc == 'qaac'
            audio_codec_str: str = 'AAC' if is_aac else 'FLAC'

            if is_aac:
                logger.info("Audio codec: aac (QAAC through AudioProcessor)")
            else:
                logger.info("Audio codec: flac (FLAC through AudioProcessor)")

            if any([ea_clip, ea_file]):
                ea_file = ea_file or ea_clip.path.to_str()

            self.audio_files = ap.video_source(
                in_file=ea_file or self.file.path.to_str(),
                out_file=self.file.a_src_cut,
                trim_list=resolve_ap_trims(trims, self.clip if not ea_clip else ea_clip),
                trims_framerate=fps or self.file.clip.fps if not ea_clip else ea_clip.clip.fps,
                frames_total=self.file.clip.num_frames if not ea_clip else ea_clip.clip.num_frames,
                flac=not is_aac, aac=is_aac, silent=False, **enc_overrides
            )

            for i, (track, channels) in enumerate(zip(self.audio_files, track_channels), 2):
                # TODO: Find a better way to optionally pass an xml file
                if xml_file is not None:
                    self.a_tracks += [
                        self.va.AudioTrack(
                            VPath(track), f'{audio_codec_str.upper()} {get_channel_layout_str(channels)}',
                            self.a_lang, i, '--tags', f'0:{xml_file.to_str()}')
                    ]
                else:
                    self.a_tracks += [
                        self.va.AudioTrack(
                            VPath(track), f'{audio_codec_str.upper()} {get_channel_layout_str(channels)}',
                            self.a_lang, i)
                    ]

                if not all_tracks:
                    break
        else:
            match enc:
                case 'passthrough':
                    logger.info(f"Audio codec: {original_codecs[0]}")
                    self.a_cutters = [self.va.PassthroughCutter(file_copy, track=-1, **cut_overrides)]
                    self.a_encoders = None
                    self.a_extracters = self.va.Eac3toAudioExtracter(file_copy, track_in=-1, track_out=-1)
                    self.a_tracks += [
                        self.va.AudioTrack(
                            self.file.a_src_cut,
                            f"{original_codecs[0].upper()} {get_channel_layout_str(track_channels[0])}",
                            self.a_lang, 0)
                    ]
                case 'qaac':
                    logger.info("Audio codec: aac (QAAC)")
                    self.a_cutters = [self.va.SoxCutter(file_copy, track=1, **cut_overrides)]
                    self.a_encoders = [self.va.QAACEncoder(file_copy, track=1, xml_tag=self.xml_tags, **enc_overrides)]
                    self.a_tracks += [
                        self.va.AudioTrack(
                            self.file.a_enc_cut.set_track(1),
                            f"AAC {get_channel_layout_str(track_channels[0])}",
                            self.a_lang, 0, '--tags', f'0:{xml_file.to_str()}')
                    ]
                case 'flac':
                    logger.info("Audio codec: flac (FLAC)")
                    self.a_cutters = [self.va.SoxCutter(file_copy, track=1, **cut_overrides)]
                    self.a_encoders = [self.va.FlacEncoder(file_copy, track=1, **enc_overrides)]
                    self.a_tracks += [
                        self.va.AudioTrack(
                            self.file.a_enc_cut.set_track(1),
                            f"{enc.upper()} {get_channel_layout_str(track_channels[0])}",
                            self.a_lang, 0)
                    ]
                case 'opus':
                    logger.info("Audio codec: opus (libopus)")
                    self.a_cutters = [self.va.SoxCutter(file_copy, track=1, **cut_overrides)]
                    self.a_encoders = [self.va.OpusEncoder(file_copy, track=1, **enc_overrides)]
                    self.a_tracks += [
                        self.va.AudioTrack(
                            self.file.a_enc_cut.set_track(1),
                            f"{enc.upper()} {get_channel_layout_str(track_channels[0])}",
                            self.a_lang, 0)
                    ]
                case 'fdkaac':
                    logger.info("Audio codec: aac (FDKAAC)")
                    self.a_cutters = [self.va.SoxCutter(file_copy, track=1, **cut_overrides)]
                    self.a_encoders = [self.va.FDKAACEncoder(file_copy, track=1, **enc_overrides)]
                    self.a_tracks += [
                        self.va.AudioTrack(
                            self.file.a_enc_cut.set_track(1),
                            f"AAC {get_channel_layout_str(track_channels[0])}",
                            self.a_lang, 0)
                    ]
                case _: raise ValueError(f"Encoder.video: '\"{encoder}\" is not a valid audio encoder! "
                                        "Please see the docstring for valid encoders!'")

        del file_copy

        return self

    def chapters(self, chapter_list: List[Chapter] | None = None, chapter_offset: int | None = None,
                 chapter_names: Sequence[str] | None = None) -> "Encoder":
        """
        Basic chapter-related setup for the output chapters.

        :param chapter_list:        A list of all chapters.
        :param chapter_offset:      Frame offset for all chapters.
        :param chapter_names:       Names for every chapter.
        """
        logger.success("Checking chapter related settings...")

        assert self.file.chapter
        assert self.file.trims_or_dfs

        chapxml = self.va.MatroskaXMLChapters(self.file.chapter)
        chapxml.create(chapter_list, self.file.clip.fps)
        chapxml.shift_times(chapter_offset, self.file.clip.fps)  # type: ignore
        chapxml.set_names(chapter_names)

        self.c_tracks += [self.va.ChaptersTrack(chapxml.chapter_file, self.c_lang)]

        return self

    def mux(self, encoder_credit: str = '') -> "Encoder":
        """
        Basic muxing-related setup for the final muxer.
        This will always output an mkv file.

        :param encoder_credit:      Name of the person encoding the video.
                                    For example: `encoder_name=LightArrowsEXE@Kaleido`.
                                    This will be included in the video track metadata.
        """
        logger.success("Checking muxing related settings...")

        if encoder_credit:
            encoder_credit = f"Original encode by {encoder_credit}"

        # Adding all the tracks
        all_tracks: List[self.va.AnyPath | self.va.Track | Iterable[self.va.AnyPath | self.va.Track] | None] = [
            self.va.VideoTrack(self.file.name_clip_output.to_str(), encoder_credit, self.v_lang)
        ]

        for track in self.a_tracks:
            all_tracks += [track]

        for track in self.c_tracks:
            all_tracks += [track]

        self.muxer = self.va.MatroskaFile(self.file.name_file_final, all_tracks, '--ui-language', 'en')

        return self

    def run(self, clean_up: bool = True, /, order: str = 'video') -> None:
        """
        Final runner method. This should be used AFTER setting up all the other details.

        :param clean_up:        Clean up files after the encoding is done. Default: True.
        :param order:           Order to encode the video and audio in.
                                Setting it to "video" will first encode the video, and vice versa.
                                This does not affect anything if AudioProcessor is used.
        """
        logger.success("Checking runner related settings...")

        order_type = self.va.RunnerConfig.Order
        encode_order = order_type.VIDEO if order.lower() == 'video' else order_type.AUDIO

        config = self.va.RunnerConfig(
            v_encoder=self.v_encoder,
            v_lossless_encoder=self.v_lossless_encoder,
            a_extracters=self.a_extracters,
            a_cutters=self.a_cutters,
            a_encoders=self.a_encoders,
            mkv=self.muxer,
            order=encode_order
        )

        runner = self.va.SelfRunner(self.clip, self.file, config)

        if self.qp_clip and not self.v_lossless_encoder:
            runner.inject_qpfile_params(qpfile_clip=self.qp_clip)

        try:  # TODO: Figure out why this throws an error.
            runner.run()
        except Exception:
            if self.file.name_file_final.exists():
                logger.warning("\nError during muxing, but file was muxed properly! Continuing...")
            else:
                logger.error("\nError during muxing! No file was written. Exiting...")

        if clean_up:
            self.perform_cleanup(runner)

    def patch(self, ranges: int | Tuple[int, int] | List[int | Tuple[int, int]] = [], clean_up: bool = True,
              /, *, external_file: os.PathLike[str] | str | None = None, output_filename: str | None = None) -> None:
        """
        Patching method. This can be used to patch your videos after encoding.
        Note that you should make sure you did the same setup you did when originally running the encode!

        :ranges:            Frame ranges that require patching. Expects as a list of tuples or integers (can be mixed).
                            Examples: [(0, 100), (400, 600)]; [50, (100, 200), 500].
        :external_file:     File to patch into. This is intended for videos like NCs with only one or two changes
                            so you don't need to encode the entire thing multiple times.
                            It will copy the given file and rename it to ``FileInfo.name_file_final``.
                            If None, performs regular patching on the original encode.
        :param clean_up:    Clean up files after the patching is done. Default: True.
        """
        logger.success("Checking patching related settings...")

        if external_file:
            if os.path.exists(external_file):
                logger.info(f"Copying {external_file} to {self.file.name_file_final}")
                shutil.copy(external_file, self.file.name_file_final)
            else:
                logger.warning(f"{self.file.name_file_final} already exists; please ensure it's the correct file!")

        runner = self.va.Patch(
            encoder=self.v_encoder,
            clip=self.clip,
            file=self.file,
            ranges=ranges,  # type:ignore[arg-type]
            output_filename=output_filename
        )

        runner.run()

        if clean_up:
            self.perform_cleanup(runner)


class X264Custom(X264):
    """
    Custom x265 runner that adds new useful keys.
    You set them by putting {key:type} in the settings file.
    `s` is used for strings, `d` is used for integers.

    For example:
        --threads {thread:d}

    The type is also given in the individdual explanation.

    :key thread:        Automatically determine amount of threads for x265 to run. (d)
    :key matrix:        Automatically set the clip's color matrix from the clip's frameprops. (d)
    :key transfer:      Automatically set the clip's gamma transfer from the clip's frameprops. (d)
    :key primaries:     Automatically set the clip's color primaries from the clip's frameprops. (d)
    """
    props_obj = Properties()

    def set_variable(self) -> Dict[str, Any]:
        return super().set_variable() | dict(
            thread=get_encoder_cores(),
            matrix=self.props_obj.get_prop(self.clip.get_frame(0), '_Matrix', int),
            primaries=self.props_obj.get_prop(self.clip.get_frame(0), '_Primaries', int),
            transfer=self.props_obj.get_prop(self.clip.get_frame(0), '_Transfer', int))


class X265Custom(X265):
    """
    Custom x265 runner that adds new useful keys.
    You set them by putting {key:type} in the settings file.
    `s` is used for strings, `d` is used for integers.

    For example:
        --numa-pools {thread:d}

    The type is also given in the individdual explanation.

    :key thread:        Automatically determine amount of threads for x265 to run. (d)
    :key matrix:        Automatically set the clip's color matrix from the clip's frameprops. (d)
    :key transfer:      Automatically set the clip's gamma transfer from the clip's frameprops. (d)
    :key primaries:     Automatically set the clip's color primaries from the clip's frameprops. (d)
    """
    props_obj = Properties()

    def set_variable(self) -> Dict[str, Any]:
        return super().set_variable() | dict(
            thread=get_encoder_cores(),
            matrix=self.props_obj.get_prop(self.clip.get_frame(0), '_Matrix', int),
            primaries=self.props_obj.get_prop(self.clip.get_frame(0), '_Primaries', int),
            transfer=self.props_obj.get_prop(self.clip.get_frame(0), '_Transfer', int))
