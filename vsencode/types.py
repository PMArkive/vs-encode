import os
from pathlib import Path
from typing import Callable, Protocol, TypeVar

from vapoursynth import VideoNode

__all__: list[str] = ["_Flavour", "FilePath", "F"]


# Function Type
F = TypeVar("F", bound=Callable)  # type:ignore[type-arg]


class _Flavour(Protocol):
    """Flavour for MPath"""

    sep: str
    altsep: str


# PathLikes basically
FilePath = os.PathLike[str] | Path | str

# source.Source typing
Trim = tuple[int | None, int | None]
Range = int | None | Trim
