"""
Useful utility functions for encoders.
"""
import math
import multiprocessing as mp
import os
from functools import cache
from pathlib import Path
from typing import Iterable, List

import vapoursynth as vs
from appdirs import AppDirs
from vardautomation import get_vs_core as _get_vs_core

__all__: List[str] = [
    'get_shader'
]


@cache
def get_shader(filename: str = '.shaders/FSRCNNX_x2_56-16-4-1.glsl') -> str:
    """
    Obtain a shader file for libplacebo-based filtering.

    By default this function will look for the shader file in a subdirectory called ".shaders".
    If it can't find it, it will look for the file in the mpv user directory.

    :param filename:    Shader filename.
    :param file_dir:    Custom directory where the file is expected to be.
                        If it can't be found in there, this function will try to obtain
                        the shader from the mpv directory.
                        Default: '.shaders'
    """
    in_cwd = Path(os.path.join(os.getcwd(), filename))
    mpv_dir = Path(AppDirs().user_data_dir).parents[0] / f"Roaming/mpv/shaders/{filename}"

    if in_cwd.is_file():
        return str(in_cwd)
    elif mpv_dir.is_file():
        return str(mpv_dir)
    else:
        raise FileNotFoundError(f"get_shader: '{filename} could not be found!'")


@cache
def get_vs_core(threads: Iterable[int | None] = None,
                max_cache_size: int | None = None,
                reserve_core: bool = True) -> vs.Core:
    """
    Gets the VapourSynth singleton core for you through vardautomation with additional parameters.
    """
    if not threads:
        threads_for_vs = math.ceil(mp.cpu_count() * 0.6)
        threads = range(0, (threads_for_vs - 2) if reserve_core else range(0, threads_for_vs))

    return _get_vs_core(threads, max_cache_size)
