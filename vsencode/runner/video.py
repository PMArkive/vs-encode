from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Callable, Dict, Tuple, cast

import vapoursynth as vs
from vardautomation import LosslessEncoder, VideoLanEncoder, VPath, logger

from ..exceptions import NoLosslessVideoEncoderError, NoVideoEncoderError
from ..generate import VEncSettingsGenerator
from ..helpers import verify_file_exists
from ..types import LOSSLESS_VIDEO_ENCODER, VIDEO_CODEC
from ..video import finalize_clip, get_lossless_video_encoder, get_video_encoder, validate_qp_clip
from .base import BaseRunner, SetupStep

if TYPE_CHECKING:
    from ..encoder import EncodeRunner
else:
    EncodeRunner = Any

__all__ = ['VideoRunner']


class VideoRunner(BaseRunner):
    """Generate VideoRunner object."""

    # Generic Muxer vars
    v_encoder: VideoLanEncoder
    l_encoder: LosslessEncoder | None = None

    # Video-related vars
    qp_clip: vs.VideoNode | None = None
    post_lossless: Callable[[VPath], vs.VideoNode] | None = None

    def video(
        self, encoder: VIDEO_CODEC = 'x265', settings: str | bool | None = None,
        /, zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
        *, qp_clip: vs.VideoNode | bool | None = None, prefetch: int | None = None,
        **enc_overrides: Any
    ) -> EncodeRunner:
        """
        Set up the relevant settings for the video.

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
                                    This should not be set higher than your keyint in the encoding settings.
                                    Default is input clip's framerate * 10.
        :param enc_overrides:       Overrides for the encoder settings.
        """
        self.check_in_chain(SetupStep.VIDEO)
        logger.success("Checking video related settings...")

        if not any(encoder.lower() == x for x in ['x264', 'x265', 'h265', 'h264']):
            raise NoVideoEncoderError("Invalid video encoder given!")

        if zones:
            # TODO: Add normalisation
            zones = dict(sorted(zones.items()))

        if settings is None:
            if verify_file_exists(f"_settings/{encoder}_settings"):
                settings = f"_settings/{encoder}_settings"
            else:
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

        if prefetch is None:
            with open(str(settings)) as f:
                fr = f.read()
                if "{keyint:d}" in fr:
                    prefetch = round(self.clip.fps) * 10
                elif "--keyint" in fr:  # I feel that there's a better way to do this, I'm just dumb
                    match = re.search(r"--keyint \d+", fr)
                    prefetch = int(re.sub(r"[^\d+]", '', match.group(0))) if match else 0

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

        return cast(EncodeRunner, self)

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
        self.check_in_chain(SetupStep.LOSSLESS)
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

        return cast(EncodeRunner, self)
