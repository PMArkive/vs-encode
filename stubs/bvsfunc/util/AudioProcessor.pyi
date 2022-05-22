from typing import *
from _typeshed import Incomplete
from fractions import Fraction

FRAMERATE_MAP: Incomplete

def video_source(in_file: str, trim_list: Union[List[Optional[int]], List[List[Optional[int]]]] = ..., out_file: Optional[str] = ..., out_dir: Optional[str] = ..., trims_framerate: Optional[Fraction] = ..., frames_total: Optional[int] = ..., flac: bool = ..., aac: bool = ..., wav: bool = ..., overwrite: bool = ..., silent: bool = ...) -> List[str]: ...
