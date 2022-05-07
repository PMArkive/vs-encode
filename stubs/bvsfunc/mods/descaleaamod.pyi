import vapoursynth as vs
from _typeshed import Incomplete
from fractions import Fraction
from functools import partial as partial
from typing import Optional, Union

core: Incomplete

def DescaleAAMod(src: vs.VideoNode, w: Optional[int] = ..., h: int = ..., thr: int = ..., kernel: str = ..., b: Union[float, Fraction] = ..., c: Union[float, Fraction] = ..., taps: int = ..., expand: int = ..., inflate: int = ..., showmask: bool = ...) -> vs.VideoNode: ...
