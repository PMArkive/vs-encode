"""
Generic types.
"""
from __future__ import annotations

import os
from enum import IntEnum
from pathlib import Path
from typing import List, Literal, Tuple, Type, Union

from vardautomation import (DuplicateFrame, Eac3toAudioExtracter, EztrimCutter,
                            FDKAACEncoder, FFmpegAudioExtracter, FlacEncoder,
                            MKVAudioExtracter, OpusEncoder, PassthroughCutter,
                            Preset, PresetType, QAACEncoder,
                            SoxCutter, VPath)
from vardautomation.tooling import ScipyCutter

__all__: List[str] = [
    'AUDIO_CODEC', 'BUILTIN_AUDIO_ENCODERS', 'EncodersEnum',
    'FilePath', 'LOSSLESS_VIDEO_ENCODER', 'VIDEO_CODEC'
]


# Valid filename values. Any of these MUST be in the filename for the right info to be parsed!
# These should be extensive enough, but should it be missing something, please send in an Issue.
valid_file_values: List[str] = [
    'ncop', 'nced',
    'op', 'ed',
    'mv', 'ins',
    'ova', 'ona', 'movie',
    'menu', 'pv', 'cm', 'iv', 'cv',
    'sp', 'preview',
    'trailer', 'teaser', 'dc',
    'digest', 'web', 'recap',
    'alt', 'vol',
    'genga', 'sb', 'ka', 'sakuga',
]


# TODO: Replace with proper enums
VIDEO_CODEC = Literal["x264", "h264", "x265", 'h265']
LOSSLESS_VIDEO_ENCODER = Literal['nvencclossless', 'ffv1']
AUDIO_CODEC = Literal['passthrough', 'aac', 'opus', 'fdkaac', 'flac']
LOSSY_ENCODERS_GENERATOR = Literal['x264', 'x265', 'both']

BUILTIN_AUDIO_CUTTERS = Union[Type[ScipyCutter], Type[SoxCutter], Type[EztrimCutter], Type[PassthroughCutter]]
BUILTIN_AUDIO_ENCODERS = Union[Type[OpusEncoder], Type[FDKAACEncoder], Type[FlacEncoder], Type[QAACEncoder]]
BUILTIN_AUDIO_EXTRACTORS = Union[Type[MKVAudioExtracter], Type[Eac3toAudioExtracter], Type[FFmpegAudioExtracter]]


PresetBackup = Preset(
    idx=None,
    a_src=VPath('{work_filename:s}_track_{track_number:s}.temp'),
    a_src_cut=VPath('{work_filename:s}_cut_track_{track_number:s}.temp'),
    a_enc_cut=VPath('{work_filename:s}_cut_enc_track_{track_number:s}.temp'),
    chapter=None,
    preset_type=PresetType.AUDIO
)


FilePath = Union[str, os.PathLike, Path, VPath]


class EncodersEnum(IntEnum):
    """Encoders supported by Vardautomation. Currently broken (oops)."""
    # Video encoders
    # X264 = ('Video', 0)
    # X265 = ('Video', 1)
    # NVENCCLOSSLESS = ('Video', 2)
    # FFV1 = ('Video', 3)

    # # Audio encoders
    # PASSTHROUGH = ('Audio', 0)
    # QAAC = ('Audio', 1)
    # OPUS = ('Audio', 2)
    # FDKAAC = ('Audio', 3)
    # FLAC = ('Audio', 4)
    ...
