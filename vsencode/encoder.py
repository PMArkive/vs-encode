from __future__ import annotations

import os
import shutil
from copy import copy as shallow_copy
from fractions import Fraction
from typing import Any, Callable, Dict, List, Sequence, Tuple, Type

import vapoursynth as vs
from lvsfunc import check_variable
from vardautomation import (
    JAPANESE, AudioCutter, AudioEncoder, AudioExtracter, AudioTrack, Chapter, ChaptersTrack, DuplicateFrame,
    FDKAACEncoder, FileInfo2, FlacEncoder, Lang, LosslessEncoder, MatroskaFile, MatroskaXMLChapters, OpusEncoder,
    PassthroughAudioEncoder, QAACEncoder, RunnerConfig, SelfRunner, Track, Trim, VideoLanEncoder, VideoTrack, VPath,
    logger, patch
)
from vardefunc.types import Range

from .audio import (
    check_aac_encoders_installed, get_track_info, iterate_ap_audio_files, iterate_cutter, iterate_encoder,
    iterate_extractors, iterate_tracks, run_ap, set_eafile_properties, set_missing_tracks
)
from .exceptions import AlreadyInChainError, NoLosslessVideoEncoderError, NotEnoughValuesError, NoVideoEncoderError
from .generate import IniSetup, VEncSettingsGenerator
from .helpers import verify_file_exists
from .types import AUDIO_CODEC, LOSSLESS_VIDEO_ENCODER, VIDEO_CODEC
from .util import get_timecodes_path
from .video import finalize_clip, get_lossless_video_encoder, get_video_encoder, validate_qp_clip

__all__ = ['EncodeRunner']

common_idx_ext: List[str] = ['lwi', 'ffindex']

# These codecs get re-encoded/errored out by all the extracters, making a simple passthrough impossible.
reenc_codecs: List[str] = ['AC-3', 'EAC-3']


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

    The only REQUIRED steps are `video` and `run`/`patch`.

    :param file:        FileInfo2 object.
    :param clip:        VideoNode to use for the output.
                        This should be the filtered clip, or in other words,
                        the clip you want to encode as usual.
    :param lang:        Languages for every track.
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
    a_extracters: AudioExtracter | List[AudioExtracter] | None = None
    a_cutters: AudioCutter | List[AudioCutter] | None = None
    a_encoders: AudioEncoder | List[AudioEncoder] | None = None
    a_tracks: List[AudioTrack] = []
    c_tracks: List[ChaptersTrack] = []
    muxer: MatroskaFile

    # Video-related vars
    qp_clip: vs.VideoNode | None = None
    post_lossless: Callable[[VPath], vs.VideoNode] | None = None

    # Audio-related vars
    audio_files: List[str] = []

    def __init__(self, file: FileInfo2, clip: vs.VideoNode, lang: Lang | List[Lang] = JAPANESE) -> None:
        logger.success(f"Initializing vardautomation environent for {file.name}...")

        check_variable(clip, 'EncodeRunner')

        self.file = file
        self.clip = clip

        if isinstance(lang, Lang):
            self.v_lang, self.a_lang, self.c_lang = lang, [lang], lang
        elif len(lang) == 2:
            self.v_lang, self.a_lang, self.c_lang = lang[0], lang[1:], lang[0]
        elif len(lang) >= 3:
            self.v_lang, self.a_lang, self.c_lang = lang[0], lang[1:-1], lang[-1]
        else:
            raise NotEnoughValuesError(f"You must give a list of at least three (3) languages! Not {len(lang)}!'")

        self.file.name_file_final = IniSetup().parse_name()

    def video(
        self, encoder: VIDEO_CODEC = 'x265', settings: str | bool | None = None,
        /, zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
        *, qp_clip: vs.VideoNode | bool | None = None, prefetch: int | None = None,
        **enc_overrides: Any
    ) -> EncodeRunner:
        """
        Basic video-related setup for the output video.

        :param encoder:             What encoder to use when encoding the video.
                                    Valid options are: x264, x265, a custom VideoLanEncoder object,
                                    or False to not encode a video at all.
        :param settings:            Path to settings file.
                                    If None, will autogenerate a settings file with sane defaults.
                                    If False, will use default x264/x265 settings.
        :param zones:               Zones for x264/x265. Expected in the following format:
                                    {(100, 200): {'crf': 13}, (500, 600): {'crf': 12}}.
                                    Zones will be sorted prior to getting passed to the encoder.
        :param qp_clip:             Optional qp clip for the qp file creation.
                                    This allows for more consistent lossless trimming,
                                    and will also make your timer's life way easier.
                                    If None, uses base cut clip. If False, disables qp_clip injection.
        :param prefetch:            Prefetch. Set a low value to limit the number of frames rendered at once.
        :param enc_overrides:       Overrides for the encoder settings.
        """
        check_in_chain('video', self.video_setup)
        logger.success("Checking video related settings...")

        if not any(encoder.lower() == x for x in ['x264', 'x265', 'h265', 'h264']):
            raise NoVideoEncoderError("Invalid video encoder given!")

        if zones:
            # TODO: Add normalisation
            zones = dict(sorted(zones.items()))

        if settings is None:
            logger.warning(
                "video: No settings file found. We will automatically generate one for you using sane defaults. "
                f"To disable this behaviour and use default {encoder} settings, set `settings=False`."
            )

            match encoder:
                case 'x264' | 'h264': VEncSettingsGenerator(encoder)
                case 'x265' | 'h265': VEncSettingsGenerator(encoder)

        self.clip = finalize_clip(self.clip)

        if isinstance(encoder, (str, VideoLanEncoder)):
            self.v_encoder = get_video_encoder(encoder, settings, zones=zones, **enc_overrides)
        else:
            raise NoVideoEncoderError

        self.v_encoder.prefetch = prefetch or 0
        self.v_encoder.resumable = True

        logger.info(f"Encoding video using {encoder}.")
        logger.info(f"Zones: {zones}")

        if isinstance(qp_clip, vs.VideoNode):
            self.qp_clip = validate_qp_clip(self.clip, qp_clip)
            logger.info("qp_clip set using the given qp clip.")
        elif qp_clip is None:
            self.qp_clip = validate_qp_clip(self.clip, self.file.clip_cut)
            logger.info("qp_clip set using the original clip cut as qp clip.")

        self.video_setup = True

        return self

    def lossless(
        self, encoder: LOSSLESS_VIDEO_ENCODER | LosslessEncoder = 'ffv1',
        /, post_filterchain: Callable[[VPath], vs.VideoNode] | None = None,
        **enc_overrides: Any
    ) -> EncodeRunner:
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
        check_in_chain('lossless', self.lossless_setup)
        logger.success("Checking lossless intermediary related settings...")

        if isinstance(encoder, (str, LosslessEncoder)):
            self.l_encoder = get_lossless_video_encoder(encoder, **enc_overrides)
        else:
            raise NoLosslessVideoEncoderError

        if callable(post_filterchain):
            self.post_lossless = post_filterchain
            logger.info("Post-lossless function found! Will apply during the encode...")
        elif post_filterchain is not None:
            logger.error(
                f"You must pass a callable function to `post_filterchain`! Not a {type(post_filterchain)}! "
                "If you are passing a function, remove the ()'s and try again."
            )

        logger.info(f"Creating an intermediary lossless encode using {encoder}.")

        self.lossless_setup = True

        return self

    def audio(
        self, encoder: AUDIO_CODEC = 'aac',
        /, xml_file: str | None = None, all_tracks: bool = False, use_ap: bool = True,
        *, fps: Fraction | float | None = None, reorder: List[int] | None = None,
        custom_trims: List[Trim | DuplicateFrame] | Trim | None = None,
        external_audio_file: str | None = None,
        external_audio_clip: vs.VideoNode | None = None,
        cutter_overrides: Dict[str, Any] = {},
        extract_overrides: Dict[str, Any] = {},
        encoder_overrides: Dict[str, Any] = {},
    ) -> EncodeRunner:
        """
        Basic audio-related setup for the output audio.

        Audio files are always trimmed using either AudioProcessor or Sox.

        :param encoder:                 What encoder/setup to use when encoding the audio.
                                        Valid options are: passthrough, aac, opus, fdkaac, flac.
        :param all_tracks:              Whether to mux in all the audio tracks or just the first track.
                                        If False, muxes in the first track.
        :param use_ap:                  Whether to use bvsfunc's AudioProcessor to process audio.
                                        If False, uses internal vardautomation encoders.
        :param xml_file:                External XML file with audio encoding specifications.
                                        Only used for AAC encodes.
        :param fps:                     Fraction of the framerate for AudioProcessor's handling.
                                        If None, grabs the fps from the input clip.
                                        If int/float, automatically sets it to `fps/1`.
        :param reorder:                 Reorder tracks. For example, if you know you have 3 audio tracks
                                        ordered like [JP, EN, "Commentary"], you can pass [1, 0, 2]
                                        to reorder them to [EN, JP, Commentary].
                                        This should also be used to remove specific tracks.
        :param custom_trims             Custom trims for audio trimming. If None, uses file.trims_or_dfs.
                                        The custom trims are relative to your ``trims_or_dfs``,
                                        so if you're trimming, get the trims from your filterchain.
        :param cutter_overrides:        Overrides for SoxCutter's cutting.
        :param extract_overrides:       Overrides for Eac3toAudioExtracter's extracting.
        :param encoder_overrides:       Overrides for the encoder settings.
        :param track_overrides:         Overrides for the audio track settings.
        """
        check_in_chain('audio', self.audio_setup)
        logger.success("Checking audio related settings...")

        enc = encoder.lower()

        if enc == 'aac':
            check_aac_encoders_installed()
        elif enc == 'passthrough':
            use_ap = False

        track_count: int = 0

        audio_langs = self.a_lang.copy()

        if len(audio_langs) < len(self.file.audios):
            audio_langs += [audio_langs[-1]] * (len(self.file.audios) - len(audio_langs))

        ea_file = external_audio_file

        trims = custom_trims or self.file.trims_or_dfs or []
        trims_ap = [
            (trim, trim) if isinstance(trim, int) else trim
            for trim in trims if trim and not isinstance(trim, DuplicateFrame)
        ]

        self.file = set_missing_tracks(self.file, use_ap=use_ap)
        file_copy = shallow_copy(self.file)

        if isinstance(fps, int) or isinstance(fps, float):
            fps = Fraction(f'{fps}/1')

        if ea_file:
            file_copy = set_eafile_properties(file_copy, ea_file, external_audio_clip, trims, use_ap)

        try:
            track_count = len(file_copy.audios)
        except AttributeError:
            for media_track in file_copy.media_info.tracks:
                if media_track.track_type == 'Audio':
                    track_count += 1

        track_channels, original_codecs = get_track_info(ea_file or file_copy, all_tracks)

        if enc == 'passthrough' and any(c in original_codecs for c in reenc_codecs):
            logger.warning(
                "Unsupported audio codecs found in source file! "
                "Will be automatically set to encode using FLAC instead.\n"
                f"The following codecs are unsupported: {reenc_codecs}"
            )
            enc = 'flac'

        if enc in ('aac', 'flac') and use_ap:
            is_aac = enc == 'aac'

            if is_aac:
                logger.info("Audio codec: AAC (QAAC through AudioProcessor)")
            else:
                logger.info("Audio codec: FLAC (FLAC through AudioProcessor)")

            self.audio_files = run_ap(file_copy, is_aac, trims_ap, fps, **encoder_overrides)  # type: ignore
            self.a_tracks = iterate_ap_audio_files(
                self.audio_files, track_channels, all_tracks,
                'AAC' if is_aac else 'FLAC', xml_file, self.a_lang
            )
        else:
            if hasattr(self.file, "audios"):
                for i, _ in enumerate(file_copy.audios):
                    if not file_copy.a_src_cut or not file_copy.a_enc_cut:
                        continue

                    if not VPath(file_copy.a_src_cut.to_str().format(track_number=i)).exists():
                        file_copy.write_a_src_cut(index=i)

                    self.a_tracks += [
                        AudioTrack(file_copy.a_enc_cut.format(track_number=i), original_codecs[i], audio_langs[i], i)
                    ]

                    if not all_tracks:
                        break
            else:
                self.a_extracters = iterate_extractors(file_copy, tracks=track_count, **extract_overrides)
                self.a_cutters = iterate_cutter(file_copy, tracks=track_count, **cutter_overrides)
                self.a_tracks = iterate_tracks(file_copy, track_count, None, original_codecs)

            aencoder: Type[AudioEncoder]

            match enc:
                case 'passthrough': aencoder = PassthroughAudioEncoder
                case 'aac' | 'qaac': aencoder = QAACEncoder
                case 'flac': aencoder = FlacEncoder
                case 'opus': aencoder = OpusEncoder
                case 'fdkaac': aencoder = FDKAACEncoder
                case _: raise ValueError(
                    f"'\"{encoder}\" is not a valid audio encoder! Please see the docstring for valid encoders.'"
                )

            self.a_encoders = iterate_encoder(file_copy, aencoder, tracks=track_count, **encoder_overrides)

        del file_copy

        lang_tracks: List[AudioTrack] = []

        for track, lang in zip(self.a_tracks, self.a_lang):
            track.lang = lang
            lang_tracks += [track]

        logger.info(f"Setting audio tracks' languages...\nOld: {self.a_tracks}\nNew: {lang_tracks}")
        self.a_tracks = lang_tracks

        if all_tracks and reorder:
            logger.info("Reordering tracks...")
            if len(reorder) > len(self.a_tracks):
                reorder = reorder[:len(self.a_tracks)]

            old_a_tracks = self.a_tracks
            self.a_tracks = [self.a_tracks[i] for i in reorder]

            def _format_tracks(tracks: List[AudioTrack]) -> List[str]:
                return [
                    '{i}: {n} ({l})'.format(i=i, n=tr.name, l=tr.lang.iso639) for i, tr in enumerate(tracks)
                ]

            logger.warning(
                f"Old order: {_format_tracks(old_a_tracks)}\n"
                f"New order: {_format_tracks(self.a_tracks)}"
            )

        self.audio_setup = True

        return self

    def chapters(
        self, chapter_list: List[Chapter], chapter_offset: int | None = None, chapter_names: Sequence[str] | None = None
    ) -> EncodeRunner:
        """
        Basic chapter-related setup for the output chapters.

        :param chapter_list:        A list of all chapters.
        :param chapter_offset:      Frame offset for all chapters.
        :param chapter_names:       Names for every chapter.
        """
        check_in_chain('chapters', self.chapters_setup)
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

    def mux(self, encoder_credit: str = '', timecodes: str | bool | None = None) -> EncodeRunner:
        """
        Basic muxing-related setup for the final muxer.
        This will always output an mkv file.

        :param encoder_credit:      Name of the person encoding the video.
                                    For example: `encoder_name=LightArrowsEXE@Kaleido`.
                                    This will be included in the video track metadata.
        :param timecodes:           Optional timecodes file. Used for VFR encodes.
        """
        check_in_chain('mux', self.muxing_setup)
        logger.success("Checking muxing related settings...")

        check_in_chain('video', self.video_setup, verify=True)

        if encoder_credit:
            encoder_credit = f"Original encode by {encoder_credit}"
            logger.info(f"Credit set in video metadata: \"{encoder_credit}\"...")

        # Adding all the tracks
        all_tracks: List[Track] = [
            VideoTrack(self.file.name_clip_output, encoder_credit, self.v_lang), *self.a_tracks, *self.c_tracks
        ]

        self.muxer = MatroskaFile(self.file.name_file_final.absolute(), all_tracks, '--ui-language', 'en')

        if isinstance(timecodes, str):
            self.muxer.add_timestamps(timecodes)
            logger.info(f"Muxing in timecode file at {timecodes}...")
        elif timecodes is None:
            tc_path = get_timecodes_path()
            if tc_path.exists():
                self.muxer.add_timestamps(get_timecodes_path())
                logger.info(f"Found timecode file at {tc_path}! Muxing in...")

        self.muxing_setup = True

        return self

    def run(self, /, clean_up: bool = True, order: str = 'video', *, deep_clean: bool = False) -> None:
        """
        Final runner method. This should be used AFTER setting up all the other details.

        :param clean_up:        Clean up files after the encoding is done. Default: True.
        :param order:           Order to encode the video and audio in.
                                Setting it to "video" will first encode the video, and vice versa.
                                This does not affect anything if AudioProcessor is used.
        :param deep_clean:      Clean all common related project files. Default: False.
        """
        logger.success("Preparing to run encode...")

        check_in_chain('video', self.video_setup, verify=True)

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

        # TODO: Fix this somehow: https://github.com/Ichunjo/vardautomation/issues/106
        try:
            runner.run()
        except Exception:
            clean_up = False
            logger.warning("Some kind of error occured during the run! Disabling post clean-up...")

        if not self.file.name_file_final.exists():
            raise FileNotFoundError(f"Could not find {self.file.name_file_final}! Aborting...")

        if clean_up:
            self._perform_cleanup(runner, deep_clean=deep_clean)

    def patch(
        self, ranges: Range | List[Range], clean_up: bool = True,
        /, *, external_file: os.PathLike[str] | str | None = None, output_filename: str | None = None
    ) -> None:
        """
        Patching method. This can be used to patch your videos after encoding.
        Note that you should make sure you did the same setup you did when originally running the encode!

        :ranges:                    Frame ranges that require patching.
                                    Expects as a list of tuplesor integers (can be mixed).
                                    Examples: [(0, 100), (400, 600)]; [50, (100, 200), 500].
        :param clean_up:            Clean up files after the patching is done. Default: True.
        :param external_file:       File to patch into. This is intended for videos like NCs with very few changes
                                    so you don't need to encode the entire thing multiple times.
                                    It will copy the given file and rename it to ``FileInfo2.name_file_final``.
                                    If None, performs regular patching on the original encode.
        :param output_filename:     Custom output filename.
        :param deep_clean:          Clean all common related project files. Default: False.
        """
        logger.success("Checking patching related settings...")

        check_in_chain('video', self.video_setup, verify=True)

        if external_file:
            if os.path.exists(external_file):
                logger.info(f"Copying {external_file} to {self.file.name_file_final}")
                shutil.copy(external_file, self.file.name_file_final)
            else:
                logger.warning(f"{self.file.name_file_final} already exists; please ensure it's the correct file!")

        patch(self.v_encoder, self.clip, self.file, ranges, output_filename, clean_up)

        if not verify_file_exists(self.file.name_file_final):
            raise FileNotFoundError(f"Could not find {self.file.name_file_final}! Aborting...")

    def _perform_cleanup(self, runner_object: SelfRunner, /, *, deep_clean: bool = False) -> None:
        """
        Helper function that performs clean-up after running the encode.
        """
        logger.success("Trying to clean up project files...")

        error: bool = False

        try:
            runner_object.work_files.remove(self.file.name_clip_output)

            if self.chapters_setup and self.file.chapter:
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
            logger.warning("There were errors found while cleaning. Some files may not have been cleaned properly!")


def check_in_chain(name: str, var: bool, verify: bool = False) -> None:
    if var and verify is False:
        raise AlreadyInChainError(name)
