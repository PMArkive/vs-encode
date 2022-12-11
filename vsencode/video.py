from __future__ import annotations

from typing import Any, Dict, Tuple

from vardautomation import FFV1, LosslessEncoder, NVEncCLossless, VideoLanEncoder
from vstools import finalize_clip, vs

from .codecs import X264Custom, X265Custom
from .exceptions import FrameLengthMismatch, NoVideoEncoderError
from .helpers import get_encoder_cores, verify_file_exists
from .types import LOSSLESS_VIDEO_ENCODER, VIDEO_CODEC


def get_video_encoder(
    v_encoder: VIDEO_CODEC, settings: str | bool | None = None, **kwargs: Any
) -> VideoLanEncoder:
    """Retrieve the video encoder to use."""
    if settings is True or not settings:
        raise NotImplementedError
        #  VEncSettingsSetup(v_encoder)
        ...

    settings = str(settings)

    if not verify_file_exists(settings):
        raise FileNotFoundError(f"Settings file not found at {settings}!")

    match v_encoder.lower():
        case 'x264' | 'h264': return X264Custom(settings, **kwargs)
        case 'x265' | 'h265': return X265Custom(settings, **kwargs)
        case _: raise NoVideoEncoderError


def get_lossless_video_encoder(
    l_encoder: str | LosslessEncoder | LOSSLESS_VIDEO_ENCODER, **kwargs: Any
) -> LosslessEncoder:
    """Retrieve the lossless video encoder to use."""
    threads = kwargs.pop("threads", get_encoder_cores())

    if isinstance(l_encoder, LosslessEncoder):
        return l_encoder
    else:
        l_encoder = l_encoder.lower()
        match l_encoder:
            case 'nvencclossless' | 'nvenc': return NVEncCLossless(**kwargs)
            case 'ffv1': return FFV1(threads=threads, **kwargs)
            case _: raise ValueError("Invalid lossless video encoder!")


def validate_qp_clip(clip: vs.VideoNode, qp_clip: vs.VideoNode) -> vs.VideoNode:
    """Validate whether the qp clip matches the base clip."""
    len_a, len_b = len(clip), len(qp_clip)

    if len_a != len_b:
        raise FrameLengthMismatch(len_a, len_b)
    return qp_clip


def normalize_zones(
    clip: vs.VideoNode, ranges: Dict[Tuple[int | None, int | None], Dict[str, Any]]
) -> Dict[Tuple[int, int], Dict[str, Any]]:
    """Normalize zones, much like `lvsfunc.normalize_ranges`."""
    ...
