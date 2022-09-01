"""Types specific to setup"""
from enum import IntEnum, auto
from typing import Callable, Literal

import vapoursynth as vs

core = vs.core

VSIdxFunction = Callable[[str], vs.VideoNode]


class IndexExists(IntEnum):
    """Check if certain files exist for :py:func:`lvsfunc.misc.source`."""

    PATH_IS_DGI = auto()
    PATH_IS_IMG = auto()
    LWI_EXISTS = auto()
    DGI_EXISTS = auto()
    NONE = auto()


COLOR_RANGE = Literal[0, 1] | vs.ColorRange
CHROMA_LOCATION = Literal[0, 1, 2, 3, 4, 5] | vs.ChromaLocation
