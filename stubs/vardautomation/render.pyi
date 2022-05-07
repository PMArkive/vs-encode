import vapoursynth as vs
from enum import IntEnum
from rich.progress import ProgressColumn, Task
from rich.text import Text
from typing import BinaryIO, List, Optional, TextIO, overload

class FPSColumn(ProgressColumn):
    def render(self, task: Task) -> Text: ...


@overload
def clip_async_render(clip: vs.VideoNode, outfile: Optional[BinaryIO] = ..., timecodes: None = ..., progress: Optional[str] = ..., callback: Union[RenderCallback, List[RenderCallback], None] = ...) -> None: ...
@overload
def clip_async_render(clip: vs.VideoNode, outfile: Optional[BinaryIO] = ..., timecodes: TextIO = ..., progress: Optional[str] = ..., callback: Union[RenderCallback, List[RenderCallback], None] = ...) -> List[float]: ...

class WaveFormat(IntEnum):
    PCM: int
    IEEE_FLOAT: int
    EXTENSIBLE: int

class WaveHeader(IntEnum):
    WAVE: int
    WAVE64: int
    AUTO: int

def audio_async_render(audio: vs.AudioNode, outfile: BinaryIO, header: WaveHeader = ..., progress: Optional[str] = ...) -> None: ...

class SceneChangeMode(IntEnum):
    WWXD: int
    SCXVID: int
    MV: int
