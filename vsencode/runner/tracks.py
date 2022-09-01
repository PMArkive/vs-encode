from __future__ import annotations
from dataclasses import dataclass

from ..util import FilePath


@dataclass
class BaseTrack:
    """Base Class all tracks inherit from."""

    path: FilePath
    name: str = ''


class VideoTrack(BaseTrack):
    """Class representing a video track."""


class AudioTrack(BaseTrack):
    """Class representing an audio track."""


class ChapterTrack(BaseTrack):
    """Class representing a chapter track."""


class SubtitleTrack(BaseTrack):
    """Class representing a subtitle track."""
