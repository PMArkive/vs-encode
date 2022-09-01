import os
from pathlib import Path


class BaseEncoder:
    file: Path

    def __init__(self, file: os.PathLike[str]) -> None:
        self.file = Path(file)
