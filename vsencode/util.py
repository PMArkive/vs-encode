"""Useful utility functions for encoders."""
from __future__ import annotations

import ctypes
import math
import multiprocessing as mp
import os
import sys
from functools import cache
from pathlib import Path
from typing import Iterable

import vapoursynth as vs
from vardautomation import VPath
from vardautomation import get_vs_core as _get_vs_core

from .generate import IniSetup

__all__ = ['get_shader', 'get_timecodes_path', 'get_vs_core']


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

    if sys.platform == "win32":
        buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.shell32.SHGetFolderPathW(None, 28, None, 0, buf)

        if any([ord(c) > 255 for c in buf]):
            buf2 = ctypes.create_unicode_buffer(1024)
            if ctypes.windll.kernel32.GetShortPathNameW(buf.value, buf2, 1024):
                buf = buf2

        user_data_dir = os.path.normpath(buf.value)
    elif sys.platform == 'darwin':
        user_data_dir = os.path.expanduser('~/Library/Application Support/')
    else:
        user_data_dir = os.getenv('XDG_DATA_HOME', os.path.expanduser("~/.local/share"))

    mpv_dir = Path(user_data_dir).parents[0] / f"Roaming/mpv/shaders/{filename}"

    if in_cwd.is_file():
        return str(in_cwd)
    elif mpv_dir.is_file():
        return str(mpv_dir)
    else:
        raise FileNotFoundError(f"get_shader: '{filename} could not be found!'")


@cache
def get_vs_core(
    threads: int | Iterable[int] | None = None, max_cache_size: int | None = None, reserve_core: bool = True
) -> vs.Core:
    """Get the VapourSynth singleton core for you through vardautomation with additional parameters."""
    if isinstance(threads, int):
        threads = range(0, threads)
    elif not threads:
        threads_for_vs = math.ceil(mp.cpu_count() * 0.6)
        threads = range(0, threads_for_vs - 2 if reserve_core else 0)

    return _get_vs_core(threads, max_cache_size)


@cache
def get_timecodes_path(create_dir: bool = True) -> VPath:
    """Generate path for your timecodes file, based off the caller's filename."""
    file_name = IniSetup().get_show_name()
    tc_path = VPath(f".assets/{file_name[-1]}/{file_name[0]}_{file_name[-1]}_timecodes.txt")

    if create_dir and not tc_path.parent.exists():
        os.makedirs(tc_path.parent, exist_ok=True)

    return tc_path
