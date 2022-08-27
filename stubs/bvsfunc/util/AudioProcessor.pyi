from fractions import Fraction
from typing import List, Tuple, Union


def video_source(
    in_file: str,
    trim_list: List[List[int | None | Tuple[int | None, int | None]]] | None = None,
    out_file: str | None = None,
    out_dir: str | None = None,
    trims_framerate: Fraction | None = None,
    frames_total: int | None = None,
    flac: bool = True,
    aac: bool = True,
    wav: bool = False,
    overwrite: bool = False,
    silent: bool = True
) -> List[str]: ...
