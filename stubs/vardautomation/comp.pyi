import vapoursynth as vs
from .types import AnyPath
from _typeshed import Incomplete
from enum import Enum
from typing import Dict, Iterable, List, NamedTuple, Optional

class Writer(Enum):
    FFMPEG: Incomplete
    IMWRI: Incomplete
    OPENCV: Incomplete
    PILLOW: Incomplete
    PYQT: Incomplete
    PYTHON: Incomplete

class PictureType(bytes, Enum):
    I: bytes
    P: bytes
    B: bytes

class SlowPicsConf(NamedTuple):
    collection_name: str
    public: bool
    optimise: bool
    nsfw: bool
    remove_after: Optional[int]

class Comparison:
    clips: Incomplete
    path: Incomplete
    path_diff: Incomplete
    max_num: Incomplete
    frames: Incomplete
    def __init__(self, clips: Dict[str, vs.VideoNode], path: AnyPath = ..., num: int = ..., frames: Optional[Iterable[int]] = ..., picture_type: Optional[Union[PictureType, List[PictureType]]] = ...) -> None: ...
    def extract(self, writer: Writer = ..., compression: int = ..., force_bt709: bool = ...) -> None: ...
    def magick_compare(self) -> None: ...
    def upload_to_slowpics(self, config: SlowPicsConf) -> None: ...

def make_comps(clips: Dict[str, vs.VideoNode], path: AnyPath = ..., num: int = ..., frames: Optional[Iterable[int]] = ..., *, picture_types: Optional[Union[PictureType, List[PictureType]]] = ..., force_bt709: bool = ..., writer: Writer = ..., compression: int = ..., magick_compare: bool = ..., slowpics_conf: Optional[SlowPicsConf] = ...) -> None: ...
