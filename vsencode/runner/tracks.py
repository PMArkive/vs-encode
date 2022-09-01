from ..types import FilePath
from ..setup.source import Source
import vapoursynth as vs


class BaseTrack:
    """Base Class all tracks inherit from."""

    path: FilePath
    name: str

    def __init__(self, file: FilePath, name: str = ""):
        self.file = file
        self.name = name


class VideoTrack(BaseTrack):
    """Class representing a video track."""


class AudioTrack(BaseTrack):
    """Class representing an audio track."""


class ChapterTrack(BaseTrack):
    """Class representing a chapter track."""


class SubtitleTrack(BaseTrack):
    """Class representing a subtitle track."""
