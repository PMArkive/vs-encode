"""Helper functions used by `__main__`."""
from __future__ import annotations

import math
import multiprocessing as mp
from typing import Any, Sequence

from lvsfunc.misc import source
from vardautomation import AnyPath, DuplicateFrame, FileInfo2, Preset, PresetBD, PresetBDWAV64, Trim, VPath, VPSIdx
from vardautomation.exception import VSColourRangeError
from vstools import get_depth, get_prop, vs

from .types import FilePath, PresetBackup

__all__ = [
    'FileInfo',
    'get_encoder_cores',
    'get_lookahead',
    'get_sar',
    'verify_file_exists',
    'get_range',
]


def get_encoder_cores() -> int:
    """Return the amount of cores to auto-relocate to the encoder."""
    return math.ceil(mp.cpu_count() * 0.4)


def get_lookahead(clip: vs.VideoNode, ceil: int = 72) -> int:
    """
    Return framerate numerator * 10 or ceil, whichever is lower.

    x265 limits the lookahead you can pass to 250 max.
    It's not recommended to go above 120.
    """
    return min([clip.fps.numerator * 5, ceil])


def get_sar(clip: vs.VideoNode) -> tuple[int, int]:
    """Return the SAR from the clip."""
    return get_prop(clip, "_SARDen", int), get_prop(clip, "_SARNum", int)


def get_range(clip: vs.VideoNode) -> int:
    """Return the color range from the clip."""
    # TODO: Double-check ranges for x264 match those of x265. See `get_color_range` also. Convert to enum instead?
    return int(not bool(get_prop(clip, "_ColorRange", int)))


def verify_file_exists(path: FilePath) -> bool:
    """Verify that a given file exists."""
    return VPath(path).exists()


def FileInfo(path: AnyPath, trims: list[Trim | DuplicateFrame] | Trim | None = None,
             idx: VPSIdx | None = source, preset: Preset | Sequence[Preset] | None = PresetBackup,
             *, workdir: AnyPath = VPath().cwd()) -> FileInfo2:
    """
    Generate FileInfo using vardautomation's built-in FileInfo2 generator.

    Exposed through vs-encode for convenience with a couple of extra changes.

    :param path:            Path to your source file.
    :param trims_or_dfs:    Adjust the clip length by trimming or duplicating frames. Python slicing. Defaults to None.
    :param idx:             Indexer used to index the video track. Defaults to :py:data:`lvsfunc.misc.source`.
    :param preset:          Preset used to fill idx, a_src, a_src_cut, a_enc_cut and chapter attributes.
                            Defaults to :py:data:`.PresetBackup`, a custom Preset.
    :param workdir:         Work directory. Defaults to the current directorie where the script is launched.

    :returns:               A FileInfo object containing all the information
                            pertaining to your video and optionally audio.
    """
    if preset is not None:
        preset = [preset] if not isinstance(preset, Sequence) else list(preset)
    else:
        preset = [PresetBD]

    if len(preset) == 1:
        preset.append(PresetBDWAV64)

    if trims is None:
        trims = [(None, None)]

    return FileInfo2(path, trims_or_dfs=trims, idx=idx, preset=preset, workdir=workdir)


def get_color_range(clip: vs.VideoNode, params: list[str]) -> tuple[int, int]:
    """
    Get the luma colour range specified in the params.
    Fallback to the clip properties.

    Taken from Vardautomation, updated to support a {range:d} input.

    :param params:              Settings of the encoder.
    :param clip:                Source
    :return:                    A tuple of min_luma and max_luma value
    """
    bits = get_depth(clip)

    def _get_props(clip: vs.VideoNode) -> dict[str, Any]:
        with clip.get_frame(0) as frame:
            return frame.props.copy()

    if '--range' in params:
        rng_param: int | str = params[params.index('--range') + 1]

        rng_map = ['limited', 'full']

        # TODO: Rewrite to use enums
        if rng_param == '{range:d}':
            rng_param = int(get_range(clip))  # type:ignore

            try:
                rng_param = rng_map[rng_param]
            except IndexError:
                raise VSColourRangeError(f"Unknown color range ({rng_param})!")

        if isinstance(rng_param, str) and len(rng_param) == 1:
            rng_param = int(rng_param)

        if rng_param in ('limited', 0):
            min_luma = 16 << (bits - 8)
            max_luma = 235 << (bits - 8)
        elif rng_param in ('full', 1):
            min_luma = 0
            max_luma = (1 << bits) - 1
        else:
            raise VSColourRangeError(f'Wrong range in parameters ({rng_param})!')
    elif '_ColorRange' in (props := _get_props(clip)):
        color_rng = props['_ColorRange']
        if color_rng == 1:
            min_luma = 16 << (bits - 8)
            max_luma = 235 << (bits - 8)
        elif color_rng == 0:
            min_luma = 0
            max_luma = (1 << bits) - 1
        else:
            raise VSColourRangeError(f'Wrong "_ColorRange" prop in the clip!')
    else:
        raise VSColourRangeError(f'Cannot guess the color range!')

    return min_luma, max_luma
