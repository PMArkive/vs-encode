"""
Helper functions used by `__main__`.
"""
import math
import multiprocessing as mp
import os
from functools import partial
from pathlib import Path
from typing import Any, List

from lvsfunc.util import get_prop
from vapoursynth import VideoNode
from vardautomation import VPath
import vardefunc
from .types import FilePath

__all__: List[str] = [
    'resolve_ap_trims',
    'get_channel_layout_str',
    'get_encoder_cores',
]


def get_encoder_cores() -> int:
    """Returns the amount of cores to auto-relocate to the encoder"""
    return math.ceil(mp.cpu_count() * 0.4)


def verify_file_exists(path: FilePath) -> FileNotFoundError | None:
    if not VPath(path).exists():
        raise FileNotFoundError(f"Could not find {path}!")


def x264_get_matrix_str(matrix: int) -> str:
    """Very basic matrix getter"""
    match matrix:
        case 1: return 'bt709'
        case 2: return 'undef'
        case 5: return 'bt470m'
        case 6: return 'smpte170m'
        case 7: return 'smpte240m'
        case _: raise ValueError("x264_get_matrix_str: 'Invalid matrix passed!'")
