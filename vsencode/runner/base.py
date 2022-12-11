from enum import Enum
from typing import List

from vardautomation import JAPANESE, FileInfo2, Lang, logger
from vstools import check_variable, vs

from ..exceptions import AlreadyInChainError, NotEnoughValuesError
from ..generate import IniSetup

__all__ = ['BaseRunner', 'SetupStep']


class SetupStep(str, Enum):
    """Enum representing all the individual steps in the automation process."""

    VIDEO = 'video'
    LOSSLESS = 'lossless'
    AUDIO = 'audio'
    CHAPTERS = 'chapters'
    MUXING = 'muxing'


class BaseRunner:
    """Set up the relevant settings for the vardautomation base."""

    # init vars
    file: FileInfo2
    clip: vs.VideoNode

    # Languages for video, audio and chapter tracks
    v_lang: Lang
    a_lang: List[Lang]
    c_lang: Lang

    # Keeping track of the steps done...
    setup_steps = dict[SetupStep, bool]({
        SetupStep.VIDEO: False,
        SetupStep.LOSSLESS: False,
        SetupStep.AUDIO: False,
        SetupStep.CHAPTERS: False,
        SetupStep.MUXING: False
    })

    def __init__(self, file: FileInfo2, clip: vs.VideoNode, lang: Lang | List[Lang] = JAPANESE) -> None:
        logger.success(f"Initializing vardautomation environent for {file.name}...")

        check_variable(clip, 'EncodeRunner')

        self.file = file
        self.clip = clip

        if isinstance(lang, Lang):
            self.v_lang, self.a_lang, self.c_lang = lang, [lang], lang
        elif len(lang) == 2:
            self.v_lang, self.a_lang, self.c_lang = lang[0], lang[1:], lang[0]
        elif len(lang) >= 3:
            self.v_lang, self.a_lang, self.c_lang = lang[0], lang[1:-1], lang[-1]
        else:
            raise NotEnoughValuesError(f"You must give a list of at least three (3) languages! Not {len(lang)}!'")

        self.file.name_file_final = IniSetup().parse_name()

    def check_in_chain(self, step: SetupStep, verify: bool = False) -> None:
        """Check whether step has already been run in the current chain."""
        if self.setup_steps[step] and not verify:
            raise AlreadyInChainError(step.value)
