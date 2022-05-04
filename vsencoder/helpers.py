"""
Helper functions used by `__main__`.
"""
import math
import multiprocessing as mp
from typing import Any, List

import vapoursynth as vs
from lvsfunc.types import Range
from lvsfunc.util import get_prop

__all__: List[str] = [
    'finalize_clip',
    'resolve_ap_trims',
    'get_channel_layout_str',
    'get_encoder_cores'
]


def finalize_clip(clip: vs.VideoNode, bits: int = 10, tv_range: bool | None = None) -> vs.VideoNode:
    """
    Finalizing clip for output.
    """
    from vardefunc.util import finalise_clip

    if tv_range is None:
        tv_range = get_prop(clip.get_frame(0), '_ColorRange', int) == 1

    return finalise_clip(clip, bits=bits, clamp_tv_range=tv_range)


def resolve_ap_trims(trims: Range | List[Range], clip: vs.VideoNode) -> List[List[Range]]:
    """Convert list[tuple] into list[list]. begna pls"""
    from lvsfunc.util import normalize_ranges

    nranges = list(normalize_ranges(clip, trims))
    return [list(trim) for trim in nranges]


# TODO: Make this a proper function that accurately gets the channel layout.
#       Improving this function should be a priority!!!
def get_channel_layout_str(channels: int) -> str:
    """Very basic channel layout picker for AudioTracks"""
    match channels:
        case 2: return '2.0'
        case 5: return '5.1'
        case 1: return '1.0'
        case 7: return '7.1'
        case _: raise ValueError("get_channel_layout_str: 'Current channel count unsupported!'")


def get_encoder_cores() -> int:
    """Returns the amount of cores to auto-relocate to the encoder"""
    return math.ceil(mp.cpu_count() * 0.4)


def x264_get_matrix_str(matrix: str) -> str:
    match matrix:
        case 1: return 'bt709'
        case 2: return 'undef'
        case 5: return 'bt470m'
        case 6: return 'smpte170m'
        case 7: return 'smpte240m'
        case _: raise ValueError("x264_get_matrix_str: 'Invalid matrix passed!'")
