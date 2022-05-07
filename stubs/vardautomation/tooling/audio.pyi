import abc
import vapoursynth as vs
from ..config import FileInfo
from ..types import AnyPath, DuplicateFrame, Trim
from ..vpathlib import VPath
from .base import BasicTool
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from enum import Enum, IntEnum
from typing import Any, Dict, List, NoReturn, Optional, Sequence, Union

class AudioExtracter(BasicTool):
    file: FileInfo
    track_in: Sequence[int]
    track_out: Sequence[int]
    def __init__(self, binary: AnyPath, settings: Union[AnyPath, List[str], Dict[str, Any]], file: FileInfo) -> None: ...

class _AutoSetTrack(AudioExtracter, ABC, metaclass=abc.ABCMeta):
    track_in: Incomplete
    track_out: Incomplete
    def __init__(self, binary: AnyPath, settings: List[str], file: FileInfo, track_in: Union[int, Sequence[int]] = ..., track_out: Union[int, Sequence[int]] = ...) -> None: ...
    def run(self) -> None: ...
    def set_variable(self) -> Dict[str, Any]: ...

class _FFmpegSetTrack(_AutoSetTrack, ABC): ...

class MKVAudioExtracter(_AutoSetTrack):
    def __init__(self, file: FileInfo, *, track_in: Union[int, Sequence[int]] = ..., track_out: Union[int, Sequence[int]] = ..., mkvextract_args: Optional[List[str]] = ...) -> None: ...

class Eac3toAudioExtracter(_AutoSetTrack):
    def __init__(self, file: FileInfo, *, track_in: Union[int, Sequence[int]] = ..., track_out: Union[int, Sequence[int]] = ..., eac3to_args: Optional[List[str]] = ...) -> None: ...

class FFmpegAudioExtracter(_FFmpegSetTrack):
    def __init__(self, file: FileInfo, *, track_in: Union[int, Sequence[int]] = ..., track_out: Union[int, Sequence[int]] = ...) -> None: ...

class AudioEncoder(BasicTool):
    file: FileInfo
    track: int
    xml_tag: Optional[AnyPath]
    def __init__(self, binary: AnyPath, settings: Union[AnyPath, List[str], Dict[str, Any]], file: FileInfo, *, track: int = ..., xml_tag: Optional[AnyPath] = ...) -> None: ...
    def run(self) -> None: ...
    def set_variable(self) -> Dict[str, Any]: ...

class PassthroughAudioEncoder(AudioEncoder):
    def __init__(self, file: FileInfo, *, track: int = ...) -> None: ...
    def run(self) -> None: ...

class BitrateMode(Enum):
    ABR: Incomplete
    CBR: Incomplete
    VBR: Incomplete
    CVBR: Incomplete
    TVBR: Incomplete
    HARD_CBR: Incomplete

class QAACEncoder(AudioEncoder):
    def __init__(self, file: FileInfo, *, track: int = ..., mode: QAAC_BITRATE_MODE = ..., bitrate: int = ..., xml_tag: Optional[AnyPath] = ..., qaac_args: Optional[List[str]] = ...) -> None: ...

class OpusEncoder(AudioEncoder):
    def __init__(self, file: FileInfo, *, track: int = ..., mode: OPUS_BITRATE_MODE = ..., bitrate: int = ..., xml_tag: Optional[AnyPath] = ..., use_ffmpeg: bool = ..., opus_args: Optional[List[str]] = ...) -> None: ...

class FDKAACEncoder(AudioEncoder):
    def __init__(self, file: FileInfo, *, track: int = ..., mode: FDK_BITRATE_MODE = ..., bitrate: int = ..., cutoff: int = ..., xml_tag: Optional[AnyPath] = ..., use_ffmpeg: bool = ..., fdk_args: Optional[List[str]] = ...) -> None: ...

class FlacCompressionLevel(IntEnum):
    ZERO: int
    ONE: int
    TWO: int
    THREE: int
    FOUR: int
    FIVE: int
    SIX: int
    SEVEN: int
    EIGHT: int
    NINE: int
    TEN: int
    ELEVEN: int
    TWELVE: int
    FAST: int
    BEST: int
    VARDOU: int

class FlacEncoder(AudioEncoder):
    def __init__(self, file: FileInfo, *, track: int = ..., xml_tag: Optional[AnyPath] = ..., level: FlacCompressionLevel = ..., use_ffmpeg: bool = ..., flac_args: Optional[List[str]] = ...) -> None: ...

class AudioCutter(ABC, metaclass=abc.ABCMeta):
    file: FileInfo
    track: int
    kwargs: Dict[str, Any]
    def __init__(self, file: FileInfo, *, track: int, **kwargs: Any) -> None: ...
    @abstractmethod
    def run(self) -> None: ...
    @classmethod
    @abstractmethod
    def generate_silence(cls, s: float, output: AnyPath, num_ch: int = ..., sample_rate: int = ..., bitdepth: int = ...) -> Union[None, NoReturn]: ...

class ScipyCutter(AudioCutter):
    def __init__(self, file: FileInfo, *, track: int, **kwargs: Any) -> None: ...
    def run(self) -> None: ...
    @classmethod
    def scipytrim(cls, src: AnyPath, output: AnyPath, trims: Union[Union[Trim, DuplicateFrame], List[Trim], List[Union[Trim, DuplicateFrame]]], ref_clip: vs.VideoNode, *, combine: bool = ...) -> None: ...
    @classmethod
    def generate_silence(cls, s: float, output: AnyPath, num_ch: int = ..., sample_rate: int = ..., bitdepth: int = ...) -> None: ...

class EztrimCutter(AudioCutter):
    def run(self) -> None: ...
    @classmethod
    def ezpztrim(cls, src: AnyPath, output: AnyPath, trims: Union[Union[Trim, DuplicateFrame], List[Trim], List[Union[Trim, DuplicateFrame]]], ref_clip: vs.VideoNode, *, combine: bool = ..., cleanup: bool = ...) -> None: ...
    @classmethod
    def generate_silence(cls, s: float, output: AnyPath, num_ch: int = ..., sample_rate: int = ..., bitdepth: int = ...) -> None: ...
    @classmethod
    def combine(cls, files: List[VPath], output: AnyPath) -> None: ...

class SoxCutter(AudioCutter):
    def run(self) -> None: ...
    @classmethod
    def soxtrim(cls, src: AnyPath, output: AnyPath, trims: Union[Union[Trim, DuplicateFrame], List[Trim], List[Union[Trim, DuplicateFrame]]], ref_clip: vs.VideoNode, *, combine: bool = ..., cleanup: bool = ...) -> None: ...
    @classmethod
    def generate_silence(cls, s: float, output: AnyPath, num_ch: int = ..., sample_rate: int = ..., bitdepth: int = ...) -> None: ...

class PassthroughCutter(AudioCutter):
    def run(self) -> None: ...
    @classmethod
    def generate_silence(cls, s: float, output: AnyPath, num_ch: int = ..., sample_rate: int = ..., bitdepth: int = ...) -> NoReturn: ...
