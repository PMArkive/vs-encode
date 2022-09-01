from mimetypes import guess_type
from pathlib import Path

from pymediainfo import MediaInfo

from .helpers import mpath_is_existing_file
from .types import _Flavour

__all__ = ["MPath"]


class MPath(Path):
    """
    Modified pathlib.Path.

    Most ideas here are taken from vardautomation.VPath.
    """
    _flavour: _Flavour = type(Path())._flavour  # type: ignore[attr-defined]

    def to_str(self) -> str:
        """Return Path as string."""
        return str(self)

    @mpath_is_existing_file
    def get_mime(self) -> tuple[str | None, str | None]:
        """Return the guessed MIME type (media type) of the file."""
        return guess_type(self.to_str())

    @mpath_is_existing_file
    def get_mediainfo(self) -> str | MediaInfo:
        return MediaInfo.parse(self.to_str())
