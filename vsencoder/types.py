"""
Generic types.
"""
from enum import IntEnum
from typing import List, Literal

__all__: List[str] = [
    'EncodersEnum'
]


# TODO: Replace with proper enums
VIDEO_ENCODER = Literal['x264', 'x265', 'nvencclossless', 'ffv1']
AUDIO_ENCODER = Literal['passthrough', 'qaac', 'opus', 'fdkaac', 'flac']


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
