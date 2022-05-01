"""
Generic types.
"""
from enum import IntEnum
from typing import List

__all__: List[str] = [
    'EncodersEnum'
]


class EncodersEnum(IntEnum):
    """Encoders supported by Vardautomation"""
    # Video encoders
    X264 = ('Video', 0)
    X265 = ('Video', 1)
    NVENCCLOSSLESS = ('Video', 2)
    FFV1 = ('Video', 3)

    # Audio encoders
    PASSTHROUGH = ('Audio', 0)
    QAAC = ('Audio', 1)
    OPUS = ('Audio', 2)
    FDKAAC = ('Audio', 3)
    FLAC = ('Audio', 4)
