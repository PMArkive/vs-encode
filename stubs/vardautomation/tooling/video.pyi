import vapoursynth as vs
from ..config import FileInfo
from ..types import AnyPath, UpdateFunc
from ..vpathlib import VPath
from .abstract import Tool
from .misc import Qpfile
from _typeshed import Incomplete
from abc import ABC
from typing import Any, Callable, Dict, List, NoReturn, Optional, Sequence, Tuple, overload

def progress_update_func(value: int, endvalue: int) -> None: ...

class VideoEncoder(Tool):
    file: FileInfo
    clip: vs.VideoNode
    y4m: bool
    progress_update: Optional[UpdateFunc]
    prefetch: int
    backlog: int
    @overload
    def run_enc(self, clip: vs.VideoNode, file: FileInfo) -> None: ...
    @overload
    def run_enc(self, clip: vs.VideoNode, file: None) -> None: ...
    def run(self) -> NoReturn: ...
    def set_variable(self) -> Dict[str, Any]: ...

class LosslessEncoder(VideoEncoder):
    suffix_name: str
    def set_variable(self) -> Dict[str, Any]: ...

class NVEncCLossless(LosslessEncoder):
    suffix_name: str
    progress_update: Incomplete
    def __init__(self, *, hevc: bool = ...) -> None: ...

class FFV1(LosslessEncoder):
    suffix_name: str
    progress_update: Incomplete
    def __init__(self, *, threads: int = ...) -> None: ...

class SupportQpfile(VideoEncoder, ABC):
    @overload
    def run_enc(self, clip: vs.VideoNode, file: FileInfo) -> None: ...
    @overload
    def run_enc(self, clip: vs.VideoNode, file: None) -> None: ...
    @overload
    def run_enc(self, clip: vs.VideoNode, file: FileInfo, *, qpfile_clip: vs.VideoNode, qpfile_func: Callable[[vs.VideoNode, AnyPath], Qpfile] = ...) -> None: ...
    @overload
    def run_enc(self, clip: vs.VideoNode, file: None, *, qpfile_clip: None = ..., qpfile_func: Callable[[vs.VideoNode, AnyPath], Qpfile] = ...) -> None: ...

class SupportResume(SupportQpfile, ABC):
    resumable: bool
    @overload
    def run_enc(self, clip: vs.VideoNode, file: FileInfo) -> None: ...
    @overload
    def run_enc(self, clip: vs.VideoNode, file: None) -> None: ...
    @overload
    def run_enc(self, clip: vs.VideoNode, file: FileInfo, *, qpfile_clip: vs.VideoNode, qpfile_func: Callable[[vs.VideoNode, AnyPath], Qpfile] = ...) -> None: ...
    @overload
    def run_enc(self, clip: vs.VideoNode, file: None, *, qpfile_clip: None = ..., qpfile_func: Callable[[vs.VideoNode, AnyPath], Qpfile] = ...) -> None: ...

class SupportManualVFR(SupportResume, ABC):
    tcfile: VPath
    @overload
    def run_enc(self, clip: vs.VideoNode, file: FileInfo) -> None: ...
    @overload
    def run_enc(self, clip: vs.VideoNode, file: None) -> None: ...
    @overload
    def run_enc(self, clip: Sequence[vs.VideoNode], file: FileInfo) -> None: ...
    @overload
    def run_enc(self, clip: vs.VideoNode, file: FileInfo, *, qpfile_clip: vs.VideoNode, qpfile_func: Callable[[vs.VideoNode, AnyPath], Qpfile] = ...) -> None: ...
    @overload
    def run_enc(self, clip: vs.VideoNode, file: None, *, qpfile_clip: None = ..., qpfile_func: Callable[[vs.VideoNode, AnyPath], Qpfile] = ...) -> None: ...
    @overload
    def run_enc(self, clip: Sequence[vs.VideoNode], file: FileInfo, *, qpfile_clip: vs.VideoNode, qpfile_func: Callable[[vs.VideoNode, AnyPath], Qpfile] = ...) -> None: ...

class VideoLanEncoder(SupportManualVFR, SupportResume, SupportQpfile, VideoEncoder, ABC):
    resumable: bool
    progress_update: Incomplete
    def __init__(self, settings: Union[AnyPath, List[str], Dict[str, Any]], zones: Optional[Dict[Tuple[int, int], Dict[str, Any]]] = ..., override_params: Optional[Dict[str, Any]] = ..., progress_update: Optional[UpdateFunc] = ...) -> None: ...
    @property
    def params_asdict(self) -> Dict[str, Any]: ...
    def set_variable(self) -> Dict[str, Any]: ...

class X265(VideoLanEncoder):
    resumable: bool
    def set_variable(self) -> Dict[str, Any]: ...

class X264(VideoLanEncoder):
    resumable: bool
    def set_variable(self) -> Dict[str, Any]: ...
