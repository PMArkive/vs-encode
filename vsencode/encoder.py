from __future__ import annotations

import copy
import os
import shutil
from fractions import Fraction
from typing import Any, Dict, Iterable, List, Literal, Sequence, Tuple, Union

import vapoursynth as vs
from lvsfunc import check_variable, get_prop
from vardautomation import (FFV1, JAPANESE, X264, X265, AnyPath, AudioCutter,
                            AudioEncoder, AudioExtracter, AudioTrack, Chapter,
                            ChaptersTrack, Eac3toAudioExtracter, FDKAACEncoder,
                            FileInfo2, FlacEncoder, Lang, LosslessEncoder,
                            MatroskaFile, MatroskaXMLChapters, MediaTrack,
                            NVEncCLossless, OpusEncoder)
from vardautomation import PassthroughCutter as PassCutter
from vardautomation import (Patch, PresetBD, QAACEncoder, RunnerConfig,
                            SelfRunner, Track, VideoLanEncoder, VideoTrack,
                            VPath, logger)
from vardautomation.utils import Properties
from vsutil import get_depth

from .audio import (check_aac_encoders_installed, check_ffmpeg_installed,
                    check_qaac_installed, get_track_info,
                    iterate_ap_audio_files, iterate_cutter, iterate_encoder,
                    iterate_extractors, iterate_tracks, run_ap,
                    set_eafile_properties, set_missing_tracks)
from .exceptions import (AlreadyInChainError, FrameLengthMismatch,
                         MissingDependenciesError, NoAudioEncoderError,
                         NoChaptersError, NoLosslessVideoEncoderError,
                         NotEnoughValuesError, NoVideoEncoderError,
                         common_idx_ext, reenc_codecs)
from .generate import IniSetup, VEncSettingsSetup, XmlGenerator
from .helpers import get_encoder_cores, verify_file_exists
from .types import (AUDIO_CODEC, BUILTIN_AUDIO_CUTTERS, BUILTIN_AUDIO_ENCODERS,
                    BUILTIN_AUDIO_EXTRACTORS, LOSSLESS_VIDEO_ENCODER,
                    VIDEO_CODEC, AudioTrim, PresetBackup)
from .util import get_timecodes_path
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
        * lossless
        * audio
        * chapter
        * mux
        * run
        * patch

    You can chain them together like so:
        ``Encoder(file_obj, filtered_clip).video('x264').audio().mux().run()``

    For arguments, see the individual methods.

    The only REQUIRED steps are `video` and `run`.

    :param file:            FileInfo2 object.
    :param clip:            VideoNode to use for the output.
                            This should be the filtered clip, or in other words,
                            the clip you want to encode as usual.
    :param lang:            Languages for every track.
                            If given a list, you can set individual languages per track.
                            The first will always be the language of the video track.
                            It's best to set this to your source's region.
                            The second one is used for all Audio tracks.
                            The third one will be used for chapters.
                            If None, assumes Japanese for all tracks.
    """
    # init vars
    file: FileInfo2
    clip: vs.VideoNode

    # Whether we're encoding/muxing...
    video_setup: bool = False
    lossless_setup: bool = False
    audio_setup: bool = False
    chapters_setup: bool = False
    muxing_setup: bool = False

    # Generic Muxer vars
    v_encoder: VideoLanEncoder
    l_encoder: LosslessEncoder | None = None
    a_extracters: BUILTIN_AUDIO_EXTRACTORS | List[BUILTIN_AUDIO_EXTRACTORS] = []
    a_cutters: BUILTIN_AUDIO_CUTTERS | List[BUILTIN_AUDIO_CUTTERS] = []
    a_encoders: BUILTIN_AUDIO_ENCODERS | List[BUILTIN_AUDIO_ENCODERS] = []
    a_tracks: List[AudioTrack] = []
    c_tracks: List[ChaptersTrack] = []
    muxer: MatroskaFile

    # Video-related vars
    qp_clip: vs.VideoNode | None = None
    post_lossless: Callable[[VPath], vs.VideoNode] | None = None

    # Audio-related vars
    audio_files: List[str] = []


    def __init__(self, file: FileInfo2, clip: vs.VideoNode,
                 lang: Lang | List[Lang] = JAPANESE) -> None:
        logger.success(f"Initializing vardautomation environent for {file.name}...")

        check_variable(clip, "EncodeRunner")

        self.file = file
        self.clip = clip

        # TODO: Support multiple languages for different tracks.
        if isinstance(lang, Lang):
            self.v_lang, self.a_lang, self.c_lang = lang, lang, lang
        elif len(lang) >= 3:
            self.v_lang, self.a_lang, self.c_lang = lang[0], lang[1], lang[2]
        else:
            raise NotEnoughValuesError(f"You must give a list of at least three (3) languages! Not {len(lang)}!'")

        self.file.name_file_final = IniSetup().parse_name()


    def video(self, encoder: VIDEO_CODEC | VideoLanEncoder | bool = 'x265', settings: str | bool | None = None,
              /, zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
              *, qp_clip: vs.VideoNode | bool | None = None, prefetch: int | None = None,
              **enc_overrides: Any) -> "EncodeRunner":
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

        if self.file.name_clip_output.exists():
            self.v_encoder.resumable = True

        logger.info(f"Encoding video using {encoder}.")
        logger.info(f"Zones: {zones}")

        if isinstance(qp_clip, vs.VideoNode):
            logger.info("qp_clip set using the given qp clip.")
        elif qp_clip is not False:
            logger.info("qp_clip set using the original clip cut as qp clip.")

        self.video_setup = True
        return self


    def lossless(self, encoder: LOSSLESS_VIDEO_ENCODER | LosslessEncoder = 'ffv1',
                 /, post_filterchain: Callable[[VPath], vs.VideoNode] | None = None,
                 **enc_overrides: Any) -> "EncodeRunner":
        """
        Create a lossless intermediary file.

        You can also set a filterchain function to be run after the lossless encode is done here.
        Note that this MUST accept a (V)Path for its first param and only outputs a single VideoNode!

        For example:

            .. code-block:: py

                def filter_lossless(path: VPath) -> vs.VideoNode:
                    clip = lvf.source(path)
                    return core.sub.TextFile(clip, "PATH/TO/SUBTITLE.ass")

        This can be useful for cases where you may need to make
        very slight adjustments to the clip after encoding,
        but you don't want to run through the entire filterchain again.
        For example, you could use this to create an encode with and without hardsubs.

        :param encoder:                 What encoder to use for the lossless encode.
                                        Valid options are ffv1 and nvenc/nvencclossless.
        :param post_filterchain:        Filterchain to perform on the lossless video
                                        before being passed to the regular encoder.
        :param enc_overrides:           Overrides for the encoder settings.
        """
        if self.lossless_setup:
            raise AlreadyInChainError('lossless')

        logger.success("Checking lossless intermediary related settings...")

        if isinstance(encoder, (str, LosslessEncoder)):
            self.l_encoder = get_lossless_video_encoder(encoder, **enc_overrides)
        else:
            raise NoLosslessVideoEncoderError

        if callable(post_filterchain):
            self.post_lossless = post_filterchain
        elif post_filterchain is not None:
            logger.error(f"You must pass a callable function to `post_filterchain`! Not a {type(post_filterchian)}! "
                         "If you are passing a function, remove the ()'s and try again.")

        logger.info(f"Creating an intermediary lossless encode using {encoder}.")

        self.lossless_setup = True
        return self


    def audio(self, encoder: AUDIO_CODEC = 'aac',
              /, xml_file: str | List[str] | None = None, all_tracks: bool = False, use_ap: bool = True,
              *, fps: Fraction | float | None = None, custom_trims: AudioTrim | None = None,
              external_audio_file: str | None = None, external_audio_clip: vs.VideoNode | None = None,
              extract_overrides: Dict[str, Any] = {},
              encoder_overrides: Dict[str, Any] = {},
              track_overrides: Dict[str, Any] = {}) -> "EncodeRunner":
        """
        Basic audio-related setup for the output audio.

        Audio files are always trimmed using either AudioProcessor or Sox.

        :param encoder:                 What encoder/setup to use when encoding the audio.
                                        Valid options are: passthrough, aac, opus, fdkaac, flac.
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
        :param extract_overrides:       Overrides for Eac3toAudioExtracter's cutting.
        :param encoder_overrides:       Overrides for the encoder settings.
        :param track_overrides:         Overrides for the audio track settings.
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

        enc = encoder.lower()

        if enc == 'aac':
            check_aac_encoders_installed()

        track_count: int = 1

        ea_file = external_audio_file
        trims = custom_trims or self.file.trims_or_dfs

        self.file = set_missing_tracks(self.file, use_ap=use_ap)
        file_copy = copy.copy(self.file)

        if isinstance(fps, int) or isinstance(fps, float):
            fps = Fraction(f'{fps}/1')

        if ea_file:
            file_copy = set_eafile_properties(file_copy, ea_file,
                                              external_audio_clip=external_audio_clip,
                                              trims=trims, use_ap=use_ap)

        if all_tracks and ea_file is None:
            for track in file_copy.media_info.tracks:
                if track.track_type == 'Audio':
                    track_count += 1
            track_count = track_count - 1   # To compensate for the extra track counted

        track_channels, original_codecs = get_track_info(self.file)

        if enc == 'passthrough' and any(c in original_codecs for c in reenc_codecs):
            logger.warning("Unsupported audio codecs found in source file! "
                           "Will be automatically set to encode using FLAC instead.\n"
                           f"The following codecs are unsupported: {reenc_codecs}")
            enc = 'flac'

        if enc in ('aac', 'flac') and use_ap:
            is_aac = enc == 'aac'

            if is_aac:
                logger.info("Audio codec: AAC (QAAC through AudioProcessor)")
            else:
                logger.info("Audio codec: FLAC (FLAC through AudioProcessor)")

            self.audio_files = run_ap(file_copy, is_aac, trims, fps, **encoder_overrides)
            self.a_tracks = iterate_ap_audio_files(self.audio_files, track_channels,
                                                   all_tracks=all_tracks, codec='AAC' if is_aac else 'FLAC',
                                                   xml_file=xml_file, lang=self.a_lang)
        else:
            if hasattr(self.file, "audios"):
                self.file.write_a_src_cut(1)
            else:
                self.a_extracters = iterate_extractors(file_copy, tracks=track_count, **extract_overrides)

            self.a_tracks = iterate_tracks(file_copy, tracks=track_count)

            # Purely so we can get >120 chars
            sets = encoder_overrides

            match enc:
                case 'passthrough': pass
                case 'aac': self.a_encoders = iterate_encoder(file_copy, QAACEncoder, tracks=track_count, **sets)
                case 'flac': self.a_encoders = iterate_encoder(file_copy, FlacEncoder, tracks=track_count, **sets)
                case 'opus': self.a_encoders = iterate_encoder(file_copy, OpusEncoder, tracks=track_count, **sets)
                case 'fdkaac': self.a_encoders = iterate_encoder(file_copy, FDKAACEncoder, tracks=track_count, **sets)
                case _: raise ValueError(f"'\"{encoder}\" is not a valid audio encoder! "
                                         "Please see the docstring for valid encoders.'")

        del file_copy

        self.audio_setup = True
        return self


    def chapters(self, chapter_list: List[Chapter],
                 chapter_offset: int | None = None,
                 chapter_names: Sequence[str] | None = None) -> "EncodeRunner":
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

        if chapter_offset:
            chapxml.shift_times(chapter_offset, self.file.clip.fps)

        if chapter_names:
            chapxml.set_names(chapter_names)

        self.c_tracks += [ChaptersTrack(chapxml.chapter_file, self.c_lang)]

        self.chapters_setup = True
        return self


    def mux(self, encoder_credit: str = '', timecodes: str | bool | None = None) -> "EncodeRunner":
        """
        Basic muxing-related setup for the final muxer.
        This will always output an mkv file.

        :param encoder_credit:      Name of the person encoding the video.
                                    For example: `encoder_name=LightArrowsEXE@Kaleido`.
                                    This will be included in the video track metadata.
        :param timecodes:           Optional timecodes file. Used for VFR encodes.
        """
        if self.muxing_setup:
            raise AlreadyInChainError('mux')

        logger.success("Checking muxing related settings...")

        if encoder_credit:
            encoder_credit = f"Original encode by {encoder_credit}"

        # Adding all the tracks
        all_tracks: List[MediaTrack] = [
            VideoTrack(self.file.name_clip_output, encoder_credit, self.v_lang)
        ]

        for track in self.a_tracks:
            all_tracks += [track]

        for track in self.c_tracks:  # type:ignore[assignment]
            all_tracks += [track]

        self.muxer = MatroskaFile(self.file.name_file_final, all_tracks, '--ui-language', 'en')

        if isinstance(timecodes, str):
            self.muxer.add_timestamps(timecodes)
        elif timecodes is None:
            tc_path = get_timecodes_path()
            if tc_path.exists():
                self.muxer.add_timestamps(get_timecodes_path())

        self.muxing_setup = True
        return self


    def run(self, clean_up: bool = True, /, order: str = 'video', *, deep_clean: bool = False) -> None:
        """
        Final runner method. This should be used AFTER setting up all the other details.

        :param clean_up:        Clean up files after the encoding is done. Default: True.
        :param order:           Order to encode the video and audio in.
                                Setting it to "video" will first encode the video, and vice versa.
                                This does not affect anything if AudioProcessor is used.
        :param deep_clean:      Clean all common related project files. Default: False.
        """
        logger.success("Checking runner related settings...")

        config = RunnerConfig(
            v_encoder=self.v_encoder,
            v_lossless_encoder=self.l_encoder,
            a_extracters=self.a_extracters,
            a_cutters=self.a_cutters,
            a_encoders=self.a_encoders,
            mkv=self.muxer,
            order=RunnerConfig.Order.VIDEO if order.lower() == 'video' else RunnerConfig.Order.AUDIO,
            clear_outputs=clean_up
        )

        runner = SelfRunner(self.clip, self.file, config)

        if self.qp_clip:
            runner.inject_qpfile_params(qpfile_clip=self.qp_clip)

        if self.post_lossless is not None:
            runner.plp_function = self.post_lossless

        try:  # TODO: Fix this somehow: https://github.com/Ichunjo/vardautomation/issues/106
            runner.run()
        except Exception:
            clean_up = False
            logger.warning("Some kind of error occured during the run! Disabling post clean-up...")

        if not self.file.name_file_final.exists():
            raise FileNotFoundError(f"Could not find {self.file.name_file_final}! Aborting...")

        if clean_up:
            self._perform_cleanup(runner, deep_clean=deep_clean)


    def patch(self, ranges: int | Tuple[int, int] | List[int | Tuple[int, int]] = [], clean_up: bool = True,
              /, *, external_file: os.PathLike[str] | str | None = None, output_filename: str | None = None,
              deep_clean: bool = False) -> None:
        """
        Patching method. This can be used to patch your videos after encoding.
        Note that you should make sure you did the same setup you did when originally running the encode!

        :ranges:                    Frame ranges that require patching. Expects as a list of tuples or integers (can be mixed).
                                    Examples: [(0, 100), (400, 600)]; [50, (100, 200), 500].
        :param clean_up:            Clean up files after the patching is done. Default: True.
        :param external_file:       File to patch into. This is intended for videos like NCs with only one or two changes
                                    so you don't need to encode the entire thing multiple times.
                                    It will copy the given file and rename it to ``FileInfo2.name_file_final``.
                                    If None, performs regular patching on the original encode.
        :param output_filename:     Custom output filename.
        :param deep_clean:          Clean all common related project files. Default: False.
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
            ranges=ranges,
            output_filename=output_filename
        )

        runner.run()

        if not verify_file_exists(self.file.name_file_final):
            raise FileNotFoundError(f"Could not find {self.file.name_file_final}! Aborting...")

        if clean_up:
            self._perform_cleanup(runner, deep_clean=deep_clean)


    def _perform_cleanup(self, runner_object: SelfRunner | Patch, /, *, deep_clean: bool = False) -> None:
        """
        Helper function that performs clean-up after running the encode.
        """
        logger.success("Trying to clean up project files...")

        error: bool = False

        try:
            runner_object.do_cleanup()
        except AttributeError:
            runner_object.work_files.remove(self.file.name_clip_output)

            if self.chapters_setup:
                runner_object.work_files.remove(self.file.chapter)

            runner_object.work_files.clear()
        except Exception:
            error = True

        try:
            os.remove(self.file.name)
        except FileNotFoundError:
            pass

        if self.audio_files:
            for track in self.audio_files:
                try:
                    os.remove(track)
                except FileNotFoundError:
                    error = True

        if deep_clean:
            logger.success("Deep cleaning enabled. Trying to clean common non-essential project files...")

            for ext in common_idx_ext:
                try:
                    os.remove(self.file.path_without_ext / VPath(ext))
                except FileNotFoundError:
                    pass

            if self.lossless_setup:
                try:
                    os.remove(self.file.name_clip_output.append_stem('_lossless').to_str())
                except FileNotFoundError:
                    pass

            try:
                if not os.path.isdir(os.path.join(self.file.workdir, ".done")):
                    os.mkdir(os.path.join(self.file.workdir, ".done"))

                script_error: int = 0

                try:
                    shutil.move(str(self.file.name) + ".py", "done/" + str(self.file.name) + ".py")
                except FileNotFoundError:
                    script_error += 1

                try:
                    shutil.move(str(self.file.name) + ".vpy", "done/" + str(self.file.name) + ".vpy")
                except FileNotFoundError:
                    script_error += 1

                if script_error > 1:
                    error = True
            except OSError:
                error = True

        logger.success("Cleaning up done!")

        if error:
            logger.warning("There were errors found while cleaning. "
                           "Some files may not have been cleaned properly!")
