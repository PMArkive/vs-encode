"""
Generic types.
"""
from enum import IntEnum
import os
from pathlib import Path
from vardautomation import VPath
from typing import List, Literal, Union

__all__: List[str] = [
    'EncodersEnum'
]


# TODO: Replace with proper enums
VIDEO_ENCODER = Literal['x264', 'x265']
LOSSLESS_VIDEO_ENCODER = Literal['nvencclossless', 'ffv1']
AUDIO_ENCODER = Literal['passthrough', 'qaac', 'opus', 'fdkaac', 'flac']


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
