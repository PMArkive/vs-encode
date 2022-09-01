from __future__ import annotations

from enum import Enum


class SetupStep(str, Enum):
    """Enum representing all the individual steps in the automation process."""

    VIDEO = 'video'
    LOSSLESS = 'lossless'
    AUDIO = 'audio'
    CHAPTERS = 'chapters'
    MUXING = 'muxing'
