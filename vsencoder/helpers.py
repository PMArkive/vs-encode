"""
Helper functions used by `__main__`.
"""
from typing import Any, List

import Vapoursynth as vs
from lvsfunc.types import Range

__all__: List[str] = [
    'finalize_clip',
    'resolve_ap_trims',
    'get_channel_layout_str'
]


def finalize_clip(clip: vs.VideoNode, bits: int = 10, tv_range: bool = True) -> vs.VideoNode:
    """
    Finalizing clip for output.
    """
    from vardefunc.util import finalise_clip

    return finalise_clip(clip, bits=bits, clamp_tv_range=tv_range)


def resolve_ap_trims(trims: Range | List[Range], clip: vs.VideoNode | None = None) -> List[List[Any]]:
    """Convert list[tuple] into list[list]. begna pls"""
    from lvsfunc.util import normalize_ranges

    return list(normalize_ranges(clip, trims))


# TODO: Make this a proper function that accurately gets the channel layout.
#       Improving this function should be a priority!!!
def get_channel_layout_str(channels: int) -> str:
    """Very basic channel layout picker for AudioTracks"""
    if channels == 2:
        return '2.0'
    elif channels == 5:
        return '5.1'
    elif channels == 1:
        return '1.0'
    elif channels == 7:
        return '7.1'
    else:
        raise ValueError("get_channel_layout_str: 'Current channel count unsupported!'")
