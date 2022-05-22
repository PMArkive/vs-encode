"""
Helper functions used by `__main__`.
"""
from __future__ import annotations

import math
import multiprocessing as mp
from typing import List, Sequence

from lvsfunc.misc import source
from vardautomation import AnyPath, DuplicateFrame
from vardautomation import FileInfo2
from vardautomation import Preset, Trim, VPath, VPSIdx

from .types import FilePath, PresetBackup

__all__: List[str] = [
    'FileInfo',
    'get_encoder_cores',
    'verify_file_exists'
]


def get_encoder_cores() -> int:
    """Returns the amount of cores to auto-relocate to the encoder"""
    return math.ceil(mp.cpu_count() * 0.4)


def verify_file_exists(path: FilePath) -> bool:
    return VPath(path).exists()


def FileInfo(path: AnyPath, trims: List[Trim | DuplicateFrame] | Trim | None = None,
             /, idx: VPSIdx | None = source, preset: Preset | Sequence[Preset] | None = PresetBackup,
             *, workdir: AnyPath = VPath().cwd()) -> FileInfo2:
    """
    FileInfo generator using vardautomation's built-in FileInfo2 generator,
    exposed through vs-encode for convenience with a couple of extra changes.

    :param path:            Path to your source file.
    :param trims_or_dfs:    Adjust the clip length by trimming or duplicating frames. Python slicing. Defaults to None.
    :param idx:             Indexer used to index the video track. Defaults to :py:data:`lvsfunc.misc.source`.
    :param preset:          Preset used to fill idx, a_src, a_src_cut, a_enc_cut and chapter attributes.
                            Defaults to :py:data:`.PresetBackup`, a custom Preset.
    :param workdir:         Work directory. Defaults to the current directorie where the script is launched.

    :returns:               A FileInfo object containing all the information
                            pertaining to your video and optionally audio.
    """
    from vardautomation import FileInfo2, PresetBDWAV64

    if preset is not None:
        list_of_presets = [preset]
        if len(list_of_presets) == 1:
            preset = [preset, PresetBDWAV64]

    return FileInfo2(path, trims_or_dfs=trims, idx=idx, preset=preset, workdir=workdir)
