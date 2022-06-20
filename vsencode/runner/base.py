from enum import Enum
from typing import Dict, List

import vapoursynth as vs
from lvsfunc import check_variable
from vardautomation import JAPANESE, FileInfo2, Lang, logger

from ..exceptions import AlreadyInChainError, NotEnoughValuesError
from ..generate import IniSetup

__all__ = ['BaseRunner', 'SetupStep']


class SetupStep(str, Enum):
    VIDEO = 'video'
    LOSSLESS = 'lossless'
    AUDIO = 'audio'
    CHAPTERS = 'chapters'
    MUXING = 'muxing'


class BaseRunner:
    # init vars
    file: FileInfo2
    clip: vs.VideoNode

    # Languages for video, audio and chapter tracks
    v_lang: Lang
    a_lang: List[Lang]
    c_lang: Lang

    # Keeping track of the steps done...
    setup_steps: Dict[SetupStep, bool] = {
        SetupStep.VIDEO: False,
        SetupStep.LOSSLESS: False,
        SetupStep.AUDIO: False,
        SetupStep.CHAPTERS: False,
        SetupStep.MUXING: False
    }

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
        if self.setup_steps[step] and not verify:
            raise AlreadyInChainError(step.value)
