from __future__ import annotations

import os
from functools import wraps
from mimetypes import guess_type
from pathlib import Path, PosixPath, WindowsPath
from typing import Any, Callable, Concatenate

from pymediainfo import MediaInfo

from .types import P, R

__all__ = [
    'MPath', 'FilePath'
]

MPathMeta = WindowsPath if os.name == 'nt' else PosixPath


class MPathBase(MPathMeta):  # type: ignore
    @staticmethod
    def is_existing_file(func: Callable[Concatenate[MPath, P], R]) -> Callable[Concatenate[MPath, P], R]:
        """Decorator to check whether the MPath points to a file."""
        assert func

        @wraps(func)
        def check(self: Any, *args: P.args, **kwargs: P.kwargs) -> R:
            MPath.check_file_exists(self.to_str())

            return func(self, *args, **kwargs)

        return check

    @staticmethod
    def check_file_exists(file: FilePath) -> None:
        if not MPath(file).is_file():
            raise FileNotFoundError(f"{file} could not be found!")


class MPath(MPathBase):
    """
    Modified pathlib.Path.

    Most ideas here are taken from vardautomation.VPath.
    """

    def to_str(self) -> str:
        """Return Path as string."""
        return str(self)

    @MPathBase.is_existing_file
    def get_mime(self) -> tuple[str | None, str | None]:
        """Return the guessed MIME type (media type) of the file."""
        return guess_type(self.to_str())

    @MPathBase.is_existing_file
    def get_mediainfo(self) -> str | MediaInfo:
        """Return the media of the file."""
        return MediaInfo.parse(self.to_str())


# PathLikes basically
FilePath = os.PathLike[str] | MPath | Path | str
