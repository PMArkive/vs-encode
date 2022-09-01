"""Types specific to setup"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from typing import Callable, Literal

import vapoursynth as vs

core = vs.core

VSIdxFunction = Callable[[str], vs.VideoNode]


class IndexingType(str, Enum):
    DGI = '.dgi'
    LWI = '.lwi'


@dataclass
class IndexFile:
    type: IndexingType
    exists: bool


class IndexType(IntEnum):
    IMAGE = auto()
    NONE = auto()


COLOR_RANGE = Literal[0, 1] | vs.ColorRange
CHROMA_LOCATION = Literal[0, 1, 2, 3, 4, 5] | vs.ChromaLocation

# source.Source typing
Trim = tuple[int | None, int | None]
Range = int | None | Trim
