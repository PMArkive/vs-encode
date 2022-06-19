from __future__ import annotations

from typing import Any, Dict, Tuple

import vapoursynth as vs
from lvsfunc.util import get_prop
from vardautomation import FFV1, LosslessEncoder, NVEncCLossless, VideoLanEncoder
from vsutil import get_depth

from .codecs import X264Custom, X265Custom
from .exceptions import FrameLengthMismatch, NoVideoEncoderError
from .helpers import get_encoder_cores, verify_file_exists
from .types import LOSSLESS_VIDEO_ENCODER, VIDEO_CODEC


def finalize_clip(clip: vs.VideoNode, bits: int = 10, tv_range: bool = True) -> vs.VideoNode:
    try:
        from vardefunc.util import finalise_clip
    except ModuleNotFoundError:
        raise ModuleNotFoundError("Missing dependency 'vardefunc'")

    if get_prop(clip.get_frame(0), '_ColorRange', int) == 0:
        tv_range = False

    if get_depth(clip) == 8:
        bits = 8

    return finalise_clip(clip, bits, tv_range)


def get_video_encoder(v_encoder: str | VideoLanEncoder | VIDEO_CODEC,
                      settings: str | bool | None = None,
                      **encoder_settings: Any) -> VideoLanEncoder:
    if not settings:
        settings = None
    elif isinstance(settings, str):
        if not verify_file_exists(settings):
            raise FileNotFoundError(f"Settings file not found at {settings}!")
    else:
        #  VEncSettingsSetup(v_encoder)
        ...

    if isinstance(v_encoder, VideoLanEncoder):
        return v_encoder
    else:
        v_encoder = v_encoder.lower()
        match v_encoder:
            case 'x264' | 'h264': return X264Custom(settings, **encoder_settings)
            case 'x265' | 'h265': return X265Custom(settings, **encoder_settings)
            case _: raise NoVideoEncoderError


def get_lossless_video_encoder(l_encoder: str | LosslessEncoder | LOSSLESS_VIDEO_ENCODER,
                               **encoder_settings: Any) -> LosslessEncoder:
    threads = encoder_settings.pop("threads", get_encoder_cores())

    if isinstance(l_encoder, LosslessEncoder):
        return l_encoder
    else:
        l_encoder = l_encoder.lower()
        match l_encoder:
            case 'nvencclossless' | 'nvenc': return NVEncCLossless(**encoder_settings)
            case 'ffv1': return FFV1(threads=threads)
            case _: raise ValueError("Invalid lossless video encoder!")


def validate_qp_clip(clip: vs.VideoNode, qp_clip: vs.VideoNode) -> vs.VideoNode:
    len_a, len_b = len(clip), len(qp_clip)

    if len_a != len_b:
        raise FrameLengthMismatch(len_a, len_b)
    return qp_clip


def normalize_zones(
    clip: vs.VideoNode, ranges: Dict[Tuple[int | None, int | None], Dict[str, Any]]
) -> Dict[Tuple[int, int], Dict[str, Any]]:
    """
    Normalizes zones, much like `lvsfunc.normalize_ranges`.
    """
    ...
