from __future__ import annotations

import subprocess as sp

import vapoursynth as vs
from vsutil import is_image

from ..util import FilePath, MPath
from .types import IndexFile, IndexingType, IndexType

core = vs.core


def _check_has_nvidia() -> bool:
    """Check if the user has an Nvidia GPU."""
    try:
        sp.check_output('nvidia-smi')
        return True
    except sp.CalledProcessError:
        return False


def _check_index_exists(path: FilePath) -> IndexFile | IndexType:
    """Check whether a lwi or dgi exists. Returns an IndexExists Enum."""
    path = MPath(path)

    for itype in IndexingType:
        if path.suffix == itype.value:
            return IndexFile(itype, path.exists())

    for itype in IndexingType:
        if path.with_suffix(f'{path.suffix}{itype.value}').exists():
            return IndexFile(itype, True)

    if is_image(path):
        return IndexType.IMAGE

    return IndexType.NONE
