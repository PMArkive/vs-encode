from __future__ import annotations

import os
import shutil
from typing import List

from vardautomation import MatroskaFile, RunnerConfig, SelfRunner, Track, VideoTrack, VPath, logger, patch
from vardefunc.types import Range

from .helpers import verify_file_exists
from .runner import AudioRunner, ChaptersRunner, SetupStep, VideoRunner
from .util import get_timecodes_path

__all__ = ['EncodeRunner']

common_idx_ext = ['lwi', 'ffindex']


class EncodeRunner(AudioRunner, VideoRunner, ChaptersRunner):
    """
    Build the encoding automation chain.

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

    muxer: MatroskaFile

    def mux(self, encoder_credit: str = '', timecodes: str | bool | None = None) -> EncodeRunner:
        """
        Set up the relevant settings for the muxer.

        This will always output an mkv file.

        :param encoder_credit:      Name of the person encoding the video.
                                    For example: `encoder_name=LightArrowsEXE@Kaleido`.
                                    This will be included in the video track metadata.
        :param timecodes:           Optional timecodes file. Used for VFR encodes.
        """
        self.check_in_chain(SetupStep.MUXING)
        logger.success("Checking muxing related settings...")

        self.check_in_chain(SetupStep.VIDEO, True)

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
        Set up the relevant settings for the runner and run the automation.

        This should be used AFTER setting up all the other details.

        :param clean_up:        Clean up files after the encoding is done. Default: True.
        :param order:           Order to encode the video and audio in.
                                Setting it to "video" will first encode the video, and vice versa.
                                This does not affect anything if AudioProcessor is used.
        :param deep_clean:      Clean all common related project files. Default: False.
        """
        logger.success("Preparing to run encode...")

        self.check_in_chain(SetupStep.VIDEO, True)

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
        self, /, ranges: Range | List[Range], clean_up: bool = True,
        *, external_file: os.PathLike[str] | str | None = None, output_filename: str | None = None
    ) -> None:
        """
        Set up the relevant settings for patching.

        This can be used to patch your videos after encoding.
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

        self.check_in_chain(SetupStep.VIDEO, True)

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
