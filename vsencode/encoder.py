from __future__ import annotations

from .util import FilePath, MPath


class BaseEncoder:
    file: MPath

    def __init__(self, file: FilePath) -> None:
        self.file = MPath(file)
