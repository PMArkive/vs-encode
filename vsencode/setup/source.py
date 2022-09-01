import os
import sys
from pprint import pformat
from typing import Sequence, cast, Any
import inspect

import vapoursynth as vs
from pymediainfo import MediaInfo
from vskernels import Matrix

from ..helpers import check_file_exists
from ..types import FilePath, Range, Trim
from ..util import MPath
from .types import VSIdxFunction
from .util import index_clip, init_clip, normalize_ranges

core = vs.core


class Source:
    """Source object containing all the information about the given file."""

    """Path to the video file"""

    def __init__(self, path: FilePath,
                 trims: list[Trim] | Trim = [(None, None)],
                 indexer: VSIdxFunction = index_clip,
                 workdir: FilePath = MPath().cwd()) -> None:
        """
        Source object for the file you want to encode.

        Make absolutely sure you call this when using ``vsencode``!

        :param path:        Path to the source file.
        :param trims:       Ranges or a list of ranges to trim a clip on.
                            Ranges will be normalized prior to being used.
                            See `this <https://lvsfunc.encode.moe/en/latest/submodules/util.html#lvsfunc.util.replace_ranges>`_
                            for more information.
                            Exclusive, like Python slicing.
        :param indexer:     Indexer used. Defaults to ``index_clip``.
                            To pass custom arguments, wrap the indexer call in a Partial.

                            For example:
                                from functools import partial
                                from lvsfunc.misc import source

                                Source("PATH", indexer=partial(source, force_lsmas=True))

                            Indexer MUST be a callable that expects a string and outputs a VideoNode.
        :param workdir:     Work directory of the project. Defaults to the directory the script is called in.
        """
        self.workdir = MPath(workdir).resolve()

        # Basic info concerning the file itself
        path = MPath(path).to_str()

        if path.startswith('file:///'):
            path = path[8::]

        check_file_exists(path)

        self.path = MPath(path)
        self.path_without_ext = self.path.with_suffix('')
        self.work_filename = self.path.stem
        self.name = MPath(sys.argv[0]).stem

        # Additional info
        self.script = inspect.stack()[1].filename
        self.mediainfo = MediaInfo.parse(path)

        # Handling the clip
        self.idx = indexer

        self.trims = trims

        self.clip = self.idx(self.path.to_str())
        self.clip = init_clip(self.clip)
        self.clip_cut = self.__trim_clip(self.clip)

        # Output names
        self.name_clip_output = self.workdir / MPath(f"{self.name}_encode")
        self.name_file_final = MPath(f"Premux/{self.name} (Premux).mkv")

    def __str__(self) -> str:
        """Pretty up the output when printed."""
        self.get_video_format()
        self.get_video_props()

        dic = dict(self.__dict__)

        return "vsencode Source object\n\n" + pformat(dic, width=200, sort_dicts=True)

    def __trim_clip(self, clip: vs.VideoNode) -> vs.VideoNode:
        """Trim the clip."""
        for trim in normalize_ranges(clip, cast(Range, self.trims)):
            clip = clip[trim[0]:trim[1]]  # type:ignore[index]

        return clip

    def get_video_format(self) -> dict[str, Any]:
        """Get the video format as a dict."""
        format = self.clip.get_frame(0).format

        self.clip_format = dict(
            id=format.id, name=format.name, color_family=format.color_family, sample_type=format.sample_type,
            bits_per_sample=format.bits_per_sample, bytes_per_sample=format.bytes_per_sample,
            subsampling_w=format.subsampling_w, subsampling_h=format.subsampling_h, num_planes=format.num_planes
        )

        return self.clip_format

    def get_video_props(self) -> dict[str, Any]:
        """Get the video props as a dict."""
        self.clip_props = dict(self.clip.get_frame(0).props)
        return self.clip_props

    def print(self) -> None:
        """Object print convenience function."""
        print(self)

    # Aliases
    info = print
