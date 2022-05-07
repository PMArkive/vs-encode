import asyncio
import vapoursynth as vs
from ..render import SceneChangeMode as SCM
from ..types import AnyPath
from ..vpathlib import VPath
from typing import Iterable, List, NamedTuple, Optional, Union

class Qpfile(NamedTuple):
    path: VPath
    frames: Optional[List[int]]

def make_qpfile(clip: vs.VideoNode, path: Optional[AnyPath] = ..., overwrite: bool = ..., mode: Union[int, SCM] = ...) -> Qpfile: ...

class KeyframesFile(NamedTuple):
    path: VPath
    frames: List[int]

def get_keyframes(path: AnyPath) -> KeyframesFile: ...
def get_vs_core(threads: Optional[Iterable[int]] = ..., max_cache_size: Optional[int] = ...) -> vs.Core: ...

class SubProcessAsync:
    sem: asyncio.Semaphore
    def __init__(self, cmds: List[str], *, nb_cpus: Optional[int] = ...) -> None: ...
