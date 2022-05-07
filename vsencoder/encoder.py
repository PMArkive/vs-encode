import copy
import os
import shutil
from fractions import Fraction
from typing import Any, Dict, Iterable, List, Literal, Sequence, Tuple

import vapoursynth as vs
from lvsfunc import check_variable, get_prop
from vardautomation import (FFV1, JAPANESE, X264, X265, AudioCutter,
                            AudioEncoder, AudioExtracter, AudioTrack, Chapter,
                            ChaptersTrack, Eac3toAudioExtracter, FileInfo,
                            Lang, LosslessEncoder, MatroskaFile,
                            NVEncCLossless, Patch, RunnerConfig, SelfRunner,
                            VideoLanEncoder, VideoTrack, VPath, logger)
from vardautomation.utils import Properties
from vsutil import get_depth

from .exceptions import (AlreadyInChainError, FrameLengthMismatch,
                         NoAudioEncoderError, NoChaptersError,
                         NoLosslessVideoEncoderError, NotEnoughValuesError,
                         NoVideoEncoderError)
from .helpers import (chain, get_channel_layout_str, get_encoder_cores,
                      resolve_ap_trims, x264_get_matrix_str)
from .audio import *
from .setup import IniSetup, VEncSettingsSetup, XmlGenerator
from .types import (AUDIO_ENCODER, LOSSLESS_VIDEO_ENCODER, VIDEO_ENCODER,
                    AudioTrim)
from .video import (finalize_clip, get_lossless_video_encoder,
                    get_video_encoder, validate_qp_clip)

__all__: List[str] = [
    'EncodeRunner'
]


class EncodeRunner:
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
    """
    # init vars
    file: FileInfo
    clip: vs.VideoNode

    # Whether we're encoding/muxing...
    video_setup: bool = False
    lossless_setup: bool = False
    audio_setup: bool = False
    chapters_setup: bool = False
    muxing_setup: bool = False

    # Generic Muxer vars
    a_tracks: List[AudioTrack] = []
    a_extracters: AudioExtracter | Sequence[AudioExtracter] | None = []
    a_cutters: AudioCutter | Sequence[AudioCutter] | None = []
    a_encoders: AudioEncoder | Sequence[AudioEncoder] | None = []
    c_tracks: List[ChaptersTrack] = []
    muxer: MatroskaFile

    # Video-related vars
    enc_lossless: bool = False
    qp_clip: vs.VideoNode | None = None

    # Audio-related vars
    external_audio: bool = True
    audio_files: List[str] = []

    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        logger.success(f"Initializing vardautomation environent for {file.name}...")

        check_variable(clip, "EncodeRunner")

        self.file = file
        self.clip = clip

        self.file.name_file_final = IniSetup().parse_name()

    @chain
    def video(self, encoder: VIDEO_ENCODER | VideoLanEncoder | bool = 'x265', settings: str | bool | None = None,
              /, zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
              *, qp_clip: vs.VideoNode | bool | None = None, prefetch: int | None = None,
              **enc_overrides: Any) -> None:
        """
        Basic video-related setup for the output video.

        :param encoder:                 What encoder to use when encoding the video.
                                        Valid options are: x264, x265, a custom VideoLanEncoder object,
                                        or False to not encode a video at all.
        :param settings:                Path to settings file.
                                        If None, will autogenerate a settings file with sane defaults.
                                        If False, will use default x264/x265 settings.
        :param zones:                   Zones for x264/x265. Expected in the following format:
                                        {(100, 200): {'crf': 13}, (500, 600): {'crf': 12}}.
                                        Zones will be sorted prior to getting passed to the encoder.
        :param qp_clip:                 Optional qp clip for the qp file creation.
                                        This allows for more consistent lossless trimming,
                                        and will also make your timer's life way easier.
                                        If None, uses base cut clip. If False, disables qp_clip injection.
        :param prefetch:                Prefetch. Set a low value to limit the number of frames rendered at once.
        :param enc_overrides:           Overrides for the encoder settings.
        """
        if self.video_setup:
            raise AlreadyInChainError('video')

        logger.success("Checking video related settings...")

        if zones:
            zones = dict(sorted(zones.items(), key=lambda item: item[1]))  # type:ignore[return-value, arg-type]

        if settings is None:
            # TODO: Automatically generate a settings file
            logger.warning("video: 'No settings file given. Will automatically generate one for you. "
                           "To disable this behaviour, set `settings=False`.")

        self.clip = finalize_clip(self.clip)

        if isinstance(encoder, (str, VideoLanEncoder)):
            self.v_encoder = get_video_encoder(encoder, settings, zones=zones, **enc_overrides)
        else:
            raise NoVideoEncoderError

        if isinstance(qp_clip, vs.VideoNode):
            self.qp_clip = validate_qp_clip(self.clip, qp_clip)
        elif qp_clip is None:
            self.qp_clip = validate_qp_clip(self.clip, self.file.clip_cut)

        self.v_encoder.prefetch = prefetch or 0
        self.v_encoder.resumable = True

        logger.info(f"Encoding video using {encoder}.")
        logger.info(f"Zones: {zones}")

        if isinstance(qp_clip, vs.VideoNode):
            logger.info("qp_clip set using the given qp clip.")
        elif qp_clip is not False:
            logger.info("qp_clip set using the original clip cut as qp clip.")

        self.video_setup = True

    @chain
    def lossless(self, encoder: LOSSLESS_VIDEO_ENCODER | LosslessEncoder = 'ffv1',
                 **enc_overrides: Any) -> None:
        if self.lossless_setup:
            raise AlreadyInChainError('lossless')

        logger.success("Checking lossless intermediary related settings...")

        if isinstance(encoder, (str, LosslessEncoder)):
            self.l_encoder = get_lossless_video_encoder(encoder, **enc_overrides)
        else:
            raise NoLosslessVideoEncoderError

        logger.info(f"Creating an intermediary lossless encode using {encoder}.")

        self.lossless_setup = True


    # TODO: Add `all_tracks` support to internal vardoto extracters/encoders/trimmers.
    @chain
    def audio(self, encoder: AUDIO_ENCODER = 'qaac',
              /, xml_file: str | None = None, all_tracks: bool = False, use_ap: bool = True,
              *, fps: Fraction | float | None = None,
              custom_trims: AudioTrim | None = None,
              external_audio_file: str | None = None, external_audio_clip: vs.VideoNode | None = None,
              cut_overrides: Dict[str, Any] = {}, enc_overrides: Dict[str, Any] = {}) -> None:
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
        if self.audio_setup:
            raise AlreadyInChainError('audio')

        logger.success("Checking audio related settings...")

        if use_ap:
            try:
                from bvsfunc.util import AudioProcessor as ap
            except ModuleNotFoundError:
                raise ModuleNotFoundError("audio: missing dependency 'bvsfunc'. "
                                          "Please install it at https://github.com/begna112/bvsfunc.")
        else:
            self.a_extracters = [Eac3toAudioExtracter(self.file)]

        try:
            from pymediainfo import MediaInfo
        except ModuleNotFoundError:
            raise ModuleNotFoundError("audio: missing dependency 'pymediainfo'")

        ea_clip = external_audio_clip
        ea_file = external_audio_file

        trims = custom_trims or self.file.trims_or_dfs

        self.file.a_src_cut = VPath(self.file.name)
        file_copy = copy.copy(self.file)

        if isinstance(fps, int) or isinstance(fps, float):
            fps = Fraction(f'{fps}/1')

        if ea_file:
            file_copy = set_eafile_properties(self.file, file_copy, ea_file, trims, use_ap=use_ap)

        # OLD CODE
        # Just making it shorter for my own convenience
        ea_clip = external_audio_clip
        ea_file = external_audio_file

        if not custom_trims:
            trims = self.file.trims_or_dfs if not ea_clip else ea_clip.trims_or_dfs
        else:
            trims = custom_trims

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

            for i, (track, channels) in enumerate(zip(self.audio_files, track_channels), 1):
                # TODO: Find a better way to optionally pass an xml file
                if xml_file is not None:
                    self.a_tracks += [
                        self.AudioTrack(
                            VPath(track).format(i), f'{audio_codec_str.upper()} {get_channel_layout_str(channels)}',
                            self.a_lang, i, '--tags', f'0:{str(xml_file)}')
                    ]
                else:
                    self.a_tracks += [
                        self.AudioTrack(
                            VPath(track).format(i), f'{audio_codec_str.upper()} {get_channel_layout_str(channels)}',
                            self.a_lang, i)
                    ]

                if not all_tracks:
                    break
        else:
            match enc:
                case 'passthrough':
                    logger.info(f"Audio codec: {original_codecs[0]}")
                    self.a_cutters = [self.PassthroughCutter(file_copy, track=-1, **cut_overrides)]
                    self.a_encoders = None
                    self.a_extracters = self.Eac3toAudioExtracter(file_copy, track_in=-1, track_out=-1)
                    self.a_tracks += [
                        self.AudioTrack(
                            self.file.a_src_cut.format(1),
                            f"{original_codecs[0].upper()} {get_channel_layout_str(track_channels[0])}",
                            self.a_lang, 0)
                    ]
                case 'qaac':
                    logger.info("Audio codec: aac (QAAC)")
                    self.a_cutters = [self.SoxCutter(file_copy, track=1, **cut_overrides)]
                    self.a_encoders = [self.QAACEncoder(file_copy, track=1, xml_tag=self.xml_tags, **enc_overrides)]
                    self.a_tracks += [
                        self.AudioTrack(
                            self.file.a_enc_cut.format(1).set_track(1),
                            f"AAC {get_channel_layout_str(track_channels[0])}",
                            self.a_lang, 0, '--tags', f'0:{str(xml_file)}')
                    ]
                case 'flac':
                    logger.info("Audio codec: flac (FLAC)")
                    self.a_cutters = [self.SoxCutter(file_copy, track=1, **cut_overrides)]
                    self.a_encoders = [self.FlacEncoder(file_copy, track=1, **enc_overrides)]
                    self.a_tracks += [
                        self.AudioTrack(
                            self.file.a_enc_cut.format(1).set_track(1),
                            f"{enc.upper()} {get_channel_layout_str(track_channels[0])}",
                            self.a_lang, 0)
                    ]
                case 'opus':
                    logger.info("Audio codec: opus (libopus)")
                    self.a_cutters = [self.SoxCutter(file_copy, track=1, **cut_overrides)]
                    self.a_encoders = [self.OpusEncoder(file_copy, track=1, **enc_overrides)]
                    self.a_tracks += [
                        self.AudioTrack(
                            self.file.a_enc_cut.format(1).set_track(1),
                            f"{enc.upper()} {get_channel_layout_str(track_channels[0])}",
                            self.a_lang, 0)
                    ]
                case 'fdkaac':
                    logger.info("Audio codec: aac (FDKAAC)")
                    self.a_cutters = [self.SoxCutter(file_copy, track=1, **cut_overrides)]
                    self.a_encoders = [self.FDKAACEncoder(file_copy, track=1, **enc_overrides)]
                    self.a_tracks += [
                        self.AudioTrack(
                            self.file.a_enc_cut.format(1).set_track(1),
                            f"AAC {get_channel_layout_str(track_channels[0])}",
                            self.a_lang, 0)
                    ]
                case _: raise ValueError(f"Encoder.audio: '\"{encoder}\" is not a valid audio encoder! "
                                         "Please see the docstring for valid encoders!'")

        del file_copy

        self.audio_setup = True


    @chain
    def chapters(self, chapter_list: List[Chapter] | None = None, chapter_offset: int | None = None,
                 chapter_names: Sequence[str] | None = None) -> None:
        """
        Basic chapter-related setup for the output chapters.

        :param chapter_list:        A list of all chapters.
        :param chapter_offset:      Frame offset for all chapters.
        :param chapter_names:       Names for every chapter.
        """
        if self.chapters_setup:
            raise AlreadyInChainError('chapters')

        logger.success("Checking chapter related settings...")

        assert self.file.chapter
        assert self.file.trims_or_dfs

        chapxml = MatroskaXMLChapters(self.file.chapter)
        chapxml.create(chapter_list, self.file.clip.fps)
        chapxml.shift_times(chapter_offset, self.file.clip.fps)  # type: ignore
        chapxml.set_names(chapter_names)

        self.c_tracks += [ChaptersTrack(chapxml.chapter_file, self.c_lang)]

        self.chapters_setup = True


    @chain
    def mux(self, lang: Lang | List[Lang] = JAPANESE, encoder_credit: str = '') -> None:
        """
        Basic muxing-related setup for the final muxer.
        This will always output an mkv file.

        :param encoder_credit:      Name of the person encoding the video.
                                    For example: `encoder_name=LightArrowsEXE@Kaleido`.
                                    This will be included in the video track metadata.
        :param lang:                Languages for every track.
                                    If given a list, you can set individual languages per track.
                                    The first will always be the language of the video track.
                                    It's best to set this to your source's region.
                                    The second one is used for all Audio tracks.
                                    The third one will be used for chapters.
                                    If None, assumes Japanese for all tracks.
        """
        if self.muxing_setup:
            raise AlreadyInChainError('mux')

        logger.success("Checking muxing related settings...")

        if encoder_credit:
            encoder_credit = f"Original encode by {encoder_credit}"

        # TODO: Support multiple languages for different tracks.
        if isinstance(lang, Lang):
            self.v_lang, self.a_lang, self.c_lan = lang, lang, lang
        elif len(lang) >= 3:
            self.v_lang, self.a_lang, self.c_lan = lang[0], lang[1], lang[2]
        else:
            raise NotEnoughValuesError(f"You must give a list of at least three (3) languages! Not {len(lang)}!'")

        # Adding all the tracks
        # TODO: Union[Union[PathLike[str], str], Track, Iterable[Union[Union[PathLike[str], str], Track]], None]
        all_tracks: List[self.AnyPath | self.Track | Iterable[self.AnyPath | self.Track] | None] = [
            VideoTrack(self.file.name_clip_output.to_str(), encoder_credit, self.v_lang)
        ]

        for track in self.a_tracks:
            all_tracks += [track]

        for track in self.c_tracks:
            all_tracks += [track]

        self.muxer = MatroskaFile(self.file.name_file_final, all_tracks, '--ui-language', 'en')

        self.muxing_setup = True


    def run(self, clean_up: bool = True, /, order: str = 'video') -> None:
        """
        Final runner method. This should be used AFTER setting up all the other details.

        :param clean_up:        Clean up files after the encoding is done. Default: True.
        :param order:           Order to encode the video and audio in.
                                Setting it to "video" will first encode the video, and vice versa.
                                This does not affect anything if AudioProcessor is used.
        """
        logger.success("Checking runner related settings...")

        config = RunnerConfig(
            v_encoder=self.v_encoder,
            v_lossless_encoder=self.l_encoder,
            a_extracters=self.a_extracters,
            a_cutters=self.a_cutters,
            a_encoders=self.a_encoders,
            mkv=self.muxer,
            order=RunnerConfig.Order.VIDEO if order.lower() == 'video' else RunnerConfig.Order.AUDIO
        )

        runner = SelfRunner(self.clip, self.file, config)

        # TODO: Test if this works with a lossless encoder
        if self.qp_clip:
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

        runner = Patch(
            encoder=self.v_encoder,
            clip=self.clip,
            file=self.file,
            ranges=ranges,  # type:ignore[arg-type]
            output_filename=output_filename
        )

        runner.run()

        if clean_up:
            self.perform_cleanup(runner)

    def perform_cleanup(self, runner_object: SelfRunner | Patch) -> None:
        """
        Helper function that performs clean-up after running the encode.
        """
        match runner_object:
            case SelfRunner:
                runner_object.work_files.remove(self.file.name_clip_output)
                if self.chapters_setup:
                    runner_object.work_files.remove(self.file.chapter)
                runner_object.work_files.clear()
            case Patch:
                runner_object.do_cleanup()
            case _: raise ValueError("Invalid runner object passed!")

        for track in self.audio_files:
            try:
                os.remove(track)
            except FileNotFoundError:
                logger.warning(f"File \"{track}\" not found! Can't clean it up, so skipping.")

        logger.info("Cleaning up leftover files done!")
