import os
import shutil
from copy import deepcopy
from fractions import Fraction
from typing import Any, Dict, List, Sequence, Tuple

import vapoursynth as vs
from vardautomation import (Chapter, FileInfo, Lang, Patch, SelfRunner, VPath,
                            logger)

from .helpers import finalize_clip, get_channel_layout_str, resolve_ap_trims
from .setup import IniSetup

__all__: List[str] = [
    'Encoder'
]


class Encoder:
    """
    Encoding chain builder.
    """
    import vardautomation as va

    # init vars
    file: FileInfo
    clip: vs.VideoNode
    clean_up: bool

    # Language for every stream
    v_language: Lang
    a_language: Lang
    c_language: Lang

    # Generic Muxer vars
    v_encoder: va.VideoEncoder
    v_lossless_encoder: va.LosslessEncoder | None = None
    a_tracks: va.AudioTrack | List[va.AudioTrack] = []
    a_extracters: va.AudioExtracter | Sequence[va.AudioExtracter] | None = None
    a_cutters: va.AudioCutter | Sequence[va.AudioCutter] | None = None
    a_encoders: va.AudioEncoder | Sequence[va.AudioEncoder] | None = None
    muxer: va.MatroskaFile

    # Video-related vars
    enc_lossless: bool = False
    clean_up: bool = True
    qp_clip: vs.VideoNode | None = None

    # Audio-related vars
    external_audio: bool = True
    audio_files: List[str] = []

    # Chapters-related vars
    chapters: va.ChapterStream | None = None

    def __init__(self,
                 file: FileInfo,
                 clip: vs.VideoNode,
                 languages: Lang | List[Lang] | None = None,
                 **setup_args: Any
                 ) -> None:
        """
        :param file:            FileInfo object.
        :param clip:            VideoNode to use for the output.
                                This should be the filtered clip, or in other words,
                                the clip you want to encode as usual.
        :param languages:       Languages for every track.
                                If given a list, you can set individual languages per track.
                                The first will always be the language of the video track.
                                It's best to set this to your source's region.
                                The second one is used for all Audio streams.
                                The third one will be used for chapters.
                                If None, assumes Japanese for all streams.
        :param setup_args:      Kwargs for the ini file setup.
        """
        self.file = file
        self.clip = clip

        # TODO: Support multiple languages for different tracks.
        if languages is not None:
            self.v_language = languages[0]
            self.a_language = languages[1]
            self.c_language = languages[2]
        else:
            self.v_language = self.va.JAPANESE
            self.a_language = self.va.JAPANESE
            self.c_language = self.va.JAPANESE

        IniSetup(**setup_args)

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

    def video(self,
              encoder: str = 'x265',
              settings: str = '.settings/settings.txt',
              sanitize_output: bool = True,
              use_qp: bool = True,
              qp_clip: vs.VideoNode | None = None,
              prefetch: int | None = None,
              resumable: bool = True,
              zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
              enc_overrides: Dict[str, Any] = {}
              ) -> "Encoder":
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
        self.clip = finalize_clip(self.clip) if sanitize_output else self.clip

        if zones:
            zones = dict(sorted(zones.items(), key=lambda item: item[1]))

        # TODO: Use proper intenums, match case?
        enc = encoder.lower()

        if enc == 'x264':
            self.v_encoder = self.va.X264(settings, zones=zones, **enc_overrides)
        elif enc == 'x265':
            self.v_encoder = self.va.X265(settings, zones=zones, **enc_overrides)
        elif enc == 'nvencclossless':
            self.v_lossless_encoder = self.va.NVEncCLossless(**enc_overrides)
        elif enc == 'ffv1':
            self.v_lossless_encoder = self.va.FFV1(**enc_overrides)
        else:
            raise ValueError(f"Encoder.video: '\"{encoder}\" is not a valid video encoder! "
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
    def audio(self,
              encoder: str = 'qaac',
              all_tracks: bool = False,
              use_ap: bool = True,
              xml_file: str | None = None,
              fps: Fraction | float | None = None,
              custom_trims: List[int | None] | List[List[int | None]] | None = None,
              external_audio_file: str | None = None,
              external_audio_clip: vs.VideoNode | None = None,
              cut_overrides: Dict[str, Any] = {},
              enc_overrides: Dict[str, Any] = {}
              ) -> "Encoder":
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
        if use_ap:
            try:
                from bvsfunc.util import AudioProcessor as ap
            except ModuleNotFoundError:
                raise ModuleNotFoundError("Encoder.audio: missing dependency 'bvsfunc'")

        try:
            from pymediainfo import MediaInfo
        except ModuleNotFoundError:
            raise ModuleNotFoundError("Encoder.audio: missing dependency 'pymediainfo'")

        else:
            self.a_extracters = [
                self.va.BasicTool('eac3to', [self.file.path.to_str(), '2:',
                                             self.file.a_src.format(1).to_str(), '-log=NUL'])
            ]

        ea_clip = external_audio_clip  # Just making it shorter for convenience

        if not custom_trims:
            trims = self.file.trims_or_dfs if not ea_clip else ea_clip.trims_or_dfs
        else:
            trims = custom_trims

        if isinstance(fps, int) or isinstance(fps, float):
            fps = Fraction(fps, 1)

        file_copy = deepcopy(self.file)

        if not use_ap:
            file_copy.trims_or_dfs = trims

        media_info = MediaInfo.parse(self.file.path)

        track_channels: List[int] = []
        original_codecs: List[str] = []

        for track in media_info.tracks:
            if track.track_type == 'Audio':
                track_channels += [track.channel_s]
                original_codecs += [track.format]
                if not all_tracks:
                    break

        enc = encoder.lower()

        if enc in ('qaac', 'flac') and use_ap:
            is_aac = enc == 'qaac'

            self.audio_files = ap.video_source(
                in_file=external_audio_file or self.file.path.to_str(),
                out_file=self.file.a_src_cut,
                trim_list=resolve_ap_trims(trims),
                trims_framerate=fps or self.file.clip.fps if not ea_clip else ea_clip.clip.fps,
                frames_total=self.file.clip.num_frames if not ea_clip else ea_clip.clip.num_frames,
                flac=not is_aac, aac=is_aac, silent=False, **enc_overrides
            )

            audio_codec_str: str = 'AAC' if is_aac else 'FLAC'

            for i, (track, channels) in enumerate(zip(self.audio_files, track_channels)):
                self.a_tracks += [
                    self.va.AudioTrack(
                        VPath(track), f'{audio_codec_str} {get_channel_layout_str(channels)}',
                        self.a_language, xml_file if is_aac else None)
                ]
                if not all_tracks:
                    break
        elif enc == 'passthrough':
            self.a_cutters = [self.va.PassthroughCutter(file_copy, track=1, **cut_overrides)]
            self.a_encoders = [self.va.PassthroughAudioEncoder(file_copy, track=1, **enc_overrides)]
            self.a_tracks = [
                self.va.AudioTrack(
                    self.file.a_enc_cut.set_track(1),
                    f"{original_codecs[0]} {get_channel_layout_str(track_channels[0])}",
                    self.a_language, 0)
            ]
        elif enc == 'qaac':
            self.a_cutters = [self.va.SoxCutter(file_copy, track=1, **cut_overrides)]
            self.a_encoders = [self.va.QAACEncoder(file_copy, track=1, xml_tag=self.xml_tags, **enc_overrides)]
            self.a_tracks = [
                self.va.AudioTrack(
                    self.file.a_enc_cut.set_track(1),
                    f"{enc.upper()} {get_channel_layout_str(track_channels[0])}",
                    self.a_language, 0, '--tags', f'0:{xml_file.to_str()}')
            ]
        elif enc == 'flac':
            self.a_cutters = [self.va.SoxCutter(file_copy, track=1, **cut_overrides)]
            self.a_encoders = [self.va.FlacEncoder(file_copy, track=1, **enc_overrides)]
            self.a_tracks = [
                self.va.AudioTrack(
                    self.file.a_enc_cut.set_track(1),
                    f"{enc.upper()} {get_channel_layout_str(track_channels[0])}",
                    self.a_language, 0)
            ]
        elif enc == 'opus':
            self.a_cutters = [self.va.SoxCutter(file_copy, track=1, **cut_overrides)]
            self.a_encoders = [self.va.OpusEncoder(file_copy, track=1, **enc_overrides)]
            self.a_tracks = [
                self.va.AudioTrack(
                    self.file.a_enc_cut.set_track(1),
                    f"{enc.upper()} {get_channel_layout_str(track_channels[0])}",
                    self.a_language, 0)
            ]
        elif enc == 'fdkaac':
            self.a_cutters = [self.va.SoxCutter(file_copy, track=1, **cut_overrides)]
            self.a_encoders = [self.va.FDKAACEncoder(file_copy, track=1, **enc_overrides)]
            self.a_tracks = [
                self.va.AudioTrack(
                    self.file.a_enc_cut.set_track(1),
                    f"{enc.upper()} {get_channel_layout_str(track_channels[0])}",
                    self.a_language, 0)
            ]
        else:
            raise ValueError(f"Encoder.video: '\"{encoder}\" is not a valid audio encoder! "
                             "Please see the docstring for valid encoders!'")

        del file_copy

        return self

    def chapters(self,
                 chapter_list: List[Chapter] | None = None,
                 chapter_offset: int | None = None,
                 chapter_names: Sequence[str] | None = None
                 ) -> "Encoder":
        """
        Basic chapter-related setup for the output chapters.

        :param chapter_list:        A list of all chapters.
        :param chapter_offset:      Frame offset for all chapters.
        :param chapter_names:       Names for every chapter.
        """
        assert self.file.chapter
        assert self.file.trims_or_dfs

        chapxml = self.va.MatroskaXMLChapters(self.file.chapter)
        chapxml.create(chapter_list, self.file.clip.fps)
        chapxml.shift_times(chapter_offset, self.file.clip.fps)  # type: ignore
        chapxml.set_names(chapter_names)

        self.chapters = self.va.ChaptersTrack(chapxml.chapter_file, self.c_language)

        return self

    def mux(self, encoder_credit: str = '') -> "Encoder":
        """
        Basic muxing-related setup for the final muxer.
        This will always output an mkv file.

        :param encoder_credit:      Name of the person encoding the video.
                                    For example: `encoder_name=LightArrowsEXE@Kaleido`.
                                    This will be included in the video stream metadata.
        """
        if encoder_credit:
            encoder_credit = f"Original encode by {encoder_credit}"

        self.muxer = self.va.MatroskaFile(
            self.file.name_file_final,
            [
                self.va.VideoTrack(self.file.name_clip_output, encoder_credit, self.v_language),
                self.a_tracks, self.chapters
            ], '--ui-language', 'en'
        )

        return self

    def run(self, clean_up: bool = True, order: str = 'video') -> None:
        """
        Final runner method. This should be used AFTER setting up all the other details.

        :param clean_up:        Clean up files after the encoding is done. Default: True.
        :param order:           Order to encode the video and audio in.
                                Setting it to "video" will first encode the video, and vice versa.
                                This does not affect anything if AudioProcessor is used.
        """
        config = self.va.RunnerConfig(
            v_encoder=self.v_encoder,
            v_lossless_encoder=self.v_lossless_encoder,
            a_extracters=self.a_extracters,
            a_cutters=self.a_cutters,
            a_encoders=self.a_encoders,
            mkv=self.muxer,
            order=self.va.Order.VIDEO
        )

        runner = self.va.SelfRunner(self.clip, self.file, config)

        if self.qp_clip and not self.v_lossless_encoder:
            runner.inject_qpfile_params(qpfile_clip=self.qp_clip)

        runner.run()

        if clean_up:
            self.perform_cleanup(runner)

    def patch(self,
              ranges: int | Tuple[int, int] | List[int | Tuple[int, int]] = [],
              external_file: os.PathLike[str] | str | None = None,
              output_filename: str | None = None,
              clean_up: bool = True
              ) -> None:
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
