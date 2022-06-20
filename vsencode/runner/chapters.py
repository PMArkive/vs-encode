from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Sequence, cast

from vardautomation import Chapter, ChaptersTrack, MatroskaXMLChapters, logger

from .base import BaseRunner, SetupStep

if TYPE_CHECKING:
    from ..encoder import EncodeRunner
else:
    EncodeRunner = Any

__all__ = ['ChaptersRunner']


class ChaptersRunner(BaseRunner):
    c_tracks: List[ChaptersTrack] = []

    def chapters(
        self, chapter_list: List[Chapter], chapter_offset: int | None = None, chapter_names: Sequence[str] | None = None
    ) -> EncodeRunner:
        """
        Basic chapter-related setup for the output chapters.

        :param chapter_list:        A list of all chapters.
        :param chapter_offset:      Frame offset for all chapters.
        :param chapter_names:       Names for every chapter.
        """
        self.check_in_chain(SetupStep.CHAPTERS)
        logger.success("Checking chapter related settings...")

        assert self.file.chapter
        assert self.file.trims_or_dfs

        chapxml = MatroskaXMLChapters(self.file.chapter)
        chapxml.create(chapter_list, self.file.clip.fps)

        if chapter_offset:
            chapxml.shift_times(chapter_offset, self.file.clip.fps)

        if chapter_names:
            chapxml.set_names(chapter_names)

        self.c_tracks += [ChaptersTrack(chapxml.chapter_file, self.c_lang)]

        self.chapters_setup = True

        return cast(EncodeRunner, self)
