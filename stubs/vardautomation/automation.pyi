import vapoursynth as vs
from .config import FileInfo
from .tooling import AudioCutter, AudioEncoder, AudioExtracter, LosslessEncoder, MatroskaFile, Qpfile, VideoEncoder
from .types import AnyPath
from .vpathlib import CleanupSet, VPath
from _typeshed import Incomplete
from enum import Enum
from typing import Callable, List, Optional, Sequence, Tuple, TypedDict
from typing_extensions import NotRequired
from vardefunc.types import Range

class RunnerConfig:
    class Order(Enum):
        VIDEO: Incomplete
        AUDIO: Incomplete
    v_encoder: VideoEncoder
    v_lossless_encoder: Optional[LosslessEncoder]
    a_extracters: Union[AudioExtracter, Sequence[AudioExtracter], None]
    a_cutters: Union[AudioCutter, Sequence[AudioCutter], None]
    a_encoders: Union[AudioEncoder, Sequence[AudioEncoder], None]
    mkv: Union[MatroskaFile, None]
    order: Order
    clear_outputs: bool
    def __init__(self, v_encoder, v_lossless_encoder, a_extracters, a_cutters, a_encoders, mkv, order, clear_outputs) -> None: ...

class _QpFileParams(TypedDict):
    qpfile_clip: NotRequired[vs.VideoNode]
    qpfile_func: NotRequired[Callable[[vs.VideoNode, AnyPath], Qpfile]]

class SelfRunner:
    clip: Union[vs.VideoNode, Sequence[vs.VideoNode]]
    file: FileInfo
    config: RunnerConfig
    work_files: CleanupSet
    def __init__(self, clip: Union[vs.VideoNode, Sequence[vs.VideoNode]], file: FileInfo, config: RunnerConfig) -> None: ...
    def run(self, *, show_logo: bool = ...) -> None: ...
    def inject_qpfile_params(self, qpfile_clip: vs.VideoNode, qpfile_func: Callable[[vs.VideoNode, AnyPath], Qpfile] = ...) -> None: ...
    def rename_final_file(self, name: AnyPath) -> None: ...
    def upload_ftp(self, ftp_name: str, destination: AnyPath, rclone_args: Optional[List[str]] = ...) -> None: ...

class Patch:
    encoder: VideoEncoder
    clip: vs.VideoNode
    file: FileInfo
    ranges: List[Tuple[int, int]]
    debug: bool
    workdir: VPath
    output_filename: VPath
    def __init__(self, encoder: VideoEncoder, clip: vs.VideoNode, file: FileInfo, ranges: Union[Range, List[Range]], output_filename: Optional[str] = ..., *, debug: bool = ...) -> None: ...
    def run(self) -> None: ...
    def do_cleanup(self) -> None: ...
