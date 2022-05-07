import vapoursynth as vs
from .language import Lang
from .types import AnyPath, DuplicateFrame, Trim, VPSIdx
from .vpathlib import VPath
from _typeshed import Incomplete
from enum import IntEnum
from fractions import Fraction
from pymediainfo import MediaInfo
from typing import Callable, Dict, List, NamedTuple, Optional, Sequence, Type, Union

class PresetType(IntEnum):
    NO_PRESET: int
    VIDEO: int
    AUDIO: int
    CHAPTER: int

class Preset:
    idx: Optional[Callable[[str], vs.VideoNode]]
    a_src: Optional[VPath]
    a_src_cut: Optional[VPath]
    a_enc_cut: Optional[VPath]
    chapter: Optional[VPath]
    preset_type: PresetType
    def __init__(self, idx, a_src, a_src_cut, a_enc_cut, chapter, preset_type) -> None: ...

NoPreset: Incomplete
PresetGeneric: Incomplete
PresetBD: Incomplete
PresetBDWAV64: Incomplete
PresetWEB: Incomplete
PresetAAC: Incomplete
PresetOpus: Incomplete
PresetEAC3: Incomplete
PresetFLAC: Incomplete
PresetChapOGM: Incomplete
PresetChapXML: Incomplete

class FileInfo:
    path: VPath
    path_without_ext: VPath
    work_filename: str
    idx: Optional[VPSIdx]
    preset: List[Preset]
    name: str
    workdir: VPath
    a_src: Optional[VPath]
    a_src_cut: Optional[VPath]
    a_enc_cut: Optional[VPath]
    clip: vs.VideoNode
    clip_cut: vs.VideoNode
    name_clip_output: VPath
    name_file_final: VPath
    def __init__(self, path: AnyPath, trims_or_dfs: Union[List[Union[Trim, DuplicateFrame]], Trim, None] = ..., *, idx: Optional[VPSIdx] = ..., preset: Union[Preset, Sequence[Preset]] = ..., workdir: AnyPath = ...): ...
    def __post_init__(self) -> None: ...
    def set_name_clip_output_ext(self, extension: str) -> None: ...
    @property
    def chapter(self) -> Optional[VPath]: ...
    @chapter.setter
    def chapter(self, chap: Optional[VPath]) -> None: ...
    @property
    def trims_or_dfs(self) -> Union[List[Union[Trim, DuplicateFrame]], Trim, None]: ...
    @trims_or_dfs.setter
    def trims_or_dfs(self, x: Union[List[Union[Trim, DuplicateFrame]], Trim, None]) -> None: ...
    @property
    def media_info(self) -> MediaInfo: ...
    @property
    def num_prop(self) -> bool: ...
    @num_prop.setter
    def num_prop(self, x: bool) -> None: ...

class FileInfo2(FileInfo):
    audios: List[vs.AudioNode]
    audios_cut: List[vs.AudioNode]
    def __post_init__(self) -> None: ...
    @property
    def trims_or_dfs(self) -> Union[List[Union[Trim, DuplicateFrame]], Trim, None]: ...
    clip_cut: Incomplete
    @trims_or_dfs.setter
    def trims_or_dfs(self, x: Union[List[Union[Trim, DuplicateFrame]], Trim, None]) -> None: ...
    @property
    def audio(self) -> vs.AudioNode: ...
    @property
    def audio_cut(self) -> vs.AudioNode: ...
    def write_a_src(self, index: int, offset: int = ...) -> None: ...
    def write_a_src_cut(self, index: int, offset: int = ...) -> None: ...

class _File(NamedTuple):
    file: VPath
    chapter: Optional[VPath]

class BlurayShow:
    def __init__(self, episodes: Dict[VPath, List[VPath]], global_trims: Union[List[Union[Trim, DuplicateFrame]], Trim, None] = ..., *, idx: Optional[VPSIdx] = ..., preset: Union[Preset, Sequence[Preset]] = ..., lang: Lang = ..., fps: Fraction = ...) -> None: ...
    def register_ncops(self, *path: VPath) -> None: ...
    def register_nceds(self, *path: VPath) -> None: ...
    def ncops(self, file_info_t: Type[_FileInfoType]) -> List[_FileInfoType]: ...
    def ncop(self, num: int, file_info_t: Type[_FileInfoType], *, start_from: int = ...) -> _FileInfoType: ...
    def nceds(self, file_info_t: Type[_FileInfoType]) -> List[_FileInfoType]: ...
    def nced(self, num: int, file_info_t: Type[_FileInfoType], *, start_from: int = ...) -> _FileInfoType: ...
    def episodes(self, file_info_t: Type[_FileInfoType]) -> List[_FileInfoType]: ...
    def episode(self, num: int, file_info_t: Type[_FileInfoType], *, start_from: int = ...) -> _FileInfoType: ...
