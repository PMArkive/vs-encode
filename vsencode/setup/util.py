from __future__ import annotations

import warnings
from functools import partial
from typing import TYPE_CHECKING, Any, Protocol, Sequence, cast, overload

import vapoursynth as vs
from pymediainfo import MediaInfo
from vskernels import (
    MISSING, Bicubic, Kernel, Matrix, MatrixT, Primaries, PrimariesT, Transfer, TransferT, UndefinedMatrixError,
    get_kernel, get_prop
)
from vsparsedvd import DGIndexNV  # type: ignore
from vsutil import depth, get_depth, is_image

from ..util import FilePath, MPath
from .helpers import _check_index_exists
from .types import CHROMA_LOCATION, COLOR_RANGE, IndexFile, IndexingType, IndexType, Range

core = vs.core


class IndexClipFunction(Protocol):
    @overload
    def __call__(
        self,
        *, ref: vs.VideoNode | None = None,
        film_thr: float = 99.0, force_lsmas: bool = False,
        tail_lines: int = 4, kernel: Kernel | str = Bicubic(b=0, c=1/2),
        **index_args: Any
    ) -> IndexClipFunction:
        ...

    @overload
    def __call__(
        self,
        path: FilePath, /, ref: vs.VideoNode | None = None,
        film_thr: float = 99.0, force_lsmas: bool = False,
        tail_lines: int = 4, kernel: Kernel | str = Bicubic(b=0, c=1/2),
        **index_args: Any
    ) -> vs.VideoNode:
        ...

    def __call__(  # type: ignore
        self,
        path: FilePath = ..., /, ref: vs.VideoNode | None = None,
        film_thr: float = 99.0, force_lsmas: bool = False,
        tail_lines: int = 4, kernel: Kernel | str = Bicubic(b=0, c=1/2),
        **index_args: Any
    ) -> vs.VideoNode | IndexClipFunction:
        ...


def _index_clip(
    path: FilePath = MISSING, /, ref: vs.VideoNode | None = None,  # type: ignore
    film_thr: float = 99.0, force_lsmas: bool = False,
    tail_lines: int = 4, kernel: Kernel | str = Bicubic(b=0, c=1/2),
    debug: bool = False, **index_args: Any
) -> vs.VideoNode | IndexClipFunction:
    """
    Index and load video clips for use in VapourSynth automatically.

    Taken from lvsfunc.

    .. note::
        | For this function to work properly, you NEED to have DGIndex(NV) in your PATH!
        | DGIndexNV will be faster, but it only works with an NVidia GPU.

    This function will try to index the given video file using DGIndex(NV).
    If it can't, it will fall back on L-SMASH. L-SMASH can also be forced using ``force_lsmas``.
    It also automatically determines if an image has been imported.

    This function will automatically check whether your clip is mostly FILM.
    If FILM is above ``film_thr`` and the order is above 0,
    it will automatically set ``fieldop=1`` and ``_FieldBased=0``.
    This can be disabled by passing ``fieldop=0`` to the function yourself.

    You can pass a ref clip to further adjust the clip.
    This affects the dimensions, framerates, matrix/transfer/primaries,
    and in the case of an image, the length of the clip.

    Alias for this function is ``lvsfunc.src``.

    Dependencies:

    * `dgdecode <https://www.rationalqm.us/dgmpgdec/dgmpgdec.html>`_
    * `dgdecodenv <https://www.rationalqm.us/dgdecnv/binaries/>`_
    * `L-SMASH-Works <https://github.com/AkarinVS/L-SMASH-Works>`_
    * `vs-imwri <https://github.com/vapoursynth/vs-imwri>`_

    Thanks `RivenSkaye <https://github.com/RivenSkaye>`_!

    :param file:            File to index and load in.
    :param ref:             Use another clip as reference for the clip's format,
                            resolution, framerate, and matrix/transfer/primaries (Default: None).
    :param film_thr:        FILM percentage the dgi must exceed for ``fieldop=1`` to be set automatically.
                            If set above 100.0, it's silently lowered to 100.0 (Default: 99.0).
    :param force_lsmas:     Force files to be imported with L-SMASH (Default: False).
    :param kernel:          py:class:`vskernels.Kernel` object used for converting the `clip` to match `ref`.
                            This can also be the string name of the kernel
                            (Default: py:class:`vskernels.Bicubic(b=0, c=1/2)`).
    :param tail_lines:      Lines to check on the tail of the dgi file.
                            Increase this value if FILM and ORDER do exist in your dgi file
                            but it's having trouble finding them.
                            Set to 2 for a very minor speed-up, as that's usually enough to find them (Default: 4).
    :param kwargs:          Optional arguments passed to the indexing filter.

    :return:                VapourSynth clip representing the input file.

    :raises ValueError:     Something other than a path is passed to ``path``.
    """
    if path == MISSING:
        return partial(  # type: ignore
            index_clip, ref=ref, film_thr=film_thr, force_lsmas=force_lsmas,
            tail_lines=tail_lines, kernel=kernel, **index_args
        )

    MPath.check_file_exists(path)
    path = MPath(path).to_str()

    clip = None
    film_thr = float(min(100, film_thr))

    if path.startswith('file:///'):
        path = path[8::]

    file_type = _check_index_exists(path)
    file_idx_type = isinstance(file_type, IndexFile) and file_type.type or None

    debug_prop = ''
    props = dict[str, Any]()

    if force_lsmas or file_idx_type is IndexingType.LWI:
        clip = core.lsmas.LWLibavSource(path, **index_args)
        debug_prop = 'lsmas'
    elif file_type is IndexType.IMAGE:
        clip = core.imwri.Read(path, **index_args)
        debug_prop = 'imwri'
    elif file_idx_type is IndexingType.DGI:
        try:
            indexer = DGIndexNV()

            idx_path = indexer.index([path], False, False)[0]

            idx_info = indexer.get_info(idx_path, 0).footer

            props |= dict(
                dgi_fieldop=0,
                dgi_order=idx_info.order,
                dgi_film=idx_info.film
            )

            indexer_kwargs = dict[str, Any]()
            if idx_info.film >= film_thr:
                indexer_kwargs |= dict(fieldop=1)
                props |= dict(dgi_fieldop=1, _FieldBased=0)

            clip = indexer.vps_indexer(idx_path, **indexer_kwargs)
            debug_prop = 'DGIndexNV'
        except Exception as e:
            warnings.warn(
                f"index_clip: 'Unable to index using DGIndexNV! Falling back to lsmas...'\n\t{e}"
            )

    if clip is None:
        return _index_clip(path, ref, film_thr, True, tail_lines, kernel, debug, **index_args)

    if debug and debug_prop:
        clip = clip.std.SetFrameProps(idx_used=debug_prop)

    if ref:
        return match_clip(clip, ref, length=is_image(path), kernel=kernel)
    return clip


if TYPE_CHECKING:
    index_clip: IndexClipFunction = ...  # type: ignore
else:
    index_clip = _index_clip


def init_clip(clip: vs.VideoNode,
              mediainfo: MediaInfo | None = None,
              matrix: MatrixT | None = None,
              transfer: TransferT | None = None,
              primaries: PrimariesT | None = None,
              chroma_loc: CHROMA_LOCATION | None = vs.CHROMA_LEFT,
              color_range: COLOR_RANGE | None = None) -> vs.VideoNode:
    """
    Initialize a clip by setting properties automatically where possible.

    This function will its best to use any data it can to determine the right props.
    It does this by first checking the clip's frameprops, and if those don't contain any info,
    checking the MediaInfo object to see if they're defined in there.

    If all else fails, it will fall back on a default value listed below.

    :param clip:            Input clip.
    :param mediainfo:       MediaInfo object of the input clip.
    :param matrix:          Matrix coefficients. Default: Guess from resolution.
    :param transfer:        Transfer characteristics. Default: Guess from matrix
    :param primaries:       Color primaries. Default: Guess from matrix.
    :param chroma_loc:      Chroma location. Defaults to CHROMA_LEFT.
    :param color_range:     Color range. Defaults to RANGE_LIMITED.
    """
    matrix = matrix or _get_matrix(clip, mediainfo)

    # Doing this in advance for future checks
    clip = clip.std.SetFrameProps(_Matrix=matrix)

    transfer = transfer or _get_transfer(clip, mediainfo)
    primaries = primaries or _get_primaries(clip, mediainfo)
    color_range = color_range or _get_range(mediainfo)

    return depth(
        clip.std.SetFrameProps(
            _Transfer=int(transfer), _Primaries=int(primaries),
            _ChromaLocation=chroma_loc, _ColorRange=color_range
        ),
        get_depth(clip)
    )


def _get_matrix(clip: vs.VideoNode, mediainfo: MediaInfo | None = None) -> Matrix:
    matrix = None

    try:
        return Matrix.from_video(clip, strict=True)
    except UndefinedMatrixError:
        if mediainfo is not None:
            try:
                matrix = get_from_mediainfo(mediainfo, key="matrix_coefficients")
            except KeyError:
                ...

        return matrix or Matrix.from_res(clip)


def _get_transfer(clip: vs.VideoNode, mediainfo: MediaInfo | None = None) -> Transfer:
    matrix = Matrix(get_prop(clip.get_frame(0), "_Matrix", int))
    transfer = get_prop(clip.get_frame(0), "_Transfer", int)

    if transfer == 2:
        if mediainfo is not None:
            try:
                transfer = get_from_mediainfo(mediainfo, key="transfer_characteristics")
            except KeyError:
                transfer = Transfer.from_matrix(matrix)
        else:
            transfer = Transfer.from_matrix(matrix)

    return Transfer(transfer)


def _get_primaries(clip: vs.VideoNode, mediainfo: MediaInfo | None = None) -> Primaries:
    matrix = get_prop(clip.get_frame(0), "_Matrix", int)
    primaries = get_prop(clip.get_frame(0), "_Primaries", int)

    if primaries == 2:
        if mediainfo is not None:
            try:
                primaries = get_from_mediainfo(mediainfo, key="color_primaries")
            except KeyError:
                primaries = Primaries(matrix)
        else:
            primaries = Primaries(matrix)

    return Primaries(primaries)


def _get_range(mediainfo: MediaInfo | None = None) -> Any:
    if mediainfo is not None:
        try:
            range = get_from_mediainfo(mediainfo, key="color_primaries")
        except KeyError:
            range = "Limited"
    else:
        range = "Limited"

    match range.lower():
        case "limited": return vs.RANGE_LIMITED
        case "full": return vs.RANGE_FULL


def get_from_mediainfo(mediainfo: MediaInfo | str, track_type: str = "Video", key: str = "") -> Any:
    """
    Try to retrieve information from a mediainfo object.

    If the key can not be found, this will return a KeyError.

    :param mediainfo:       MediaInfo object.
    :param track_type:      Track type to find the key for. Defaults to "Video".
    :param key:             Key to check for.
    """
    if not key:
        raise ValueError("get_from_mediainfo: 'You must request _a_ key!'")

    mediainfo = cast(MediaInfo, mediainfo)

    for track in mediainfo.tracks:
        if track.track_type == track_type:
            data = track.to_data()
            return data[key]


def normalize_ranges(clip: vs.VideoNode, ranges: Range | list[Range]) -> Sequence[Range]:
    r"""
        Normalize :py:func:`lvsfunc.types.Range`\(s) to a list of inclusive positive integer ranges.

        Taken from lvsfunc.

        :param clip:        Reference clip used for length.
        :param ranges:      Single :py:class:`lvsfunc.types.Range`,
                            or a list of :py:class:`lvsfunc.types.Range`\(s).

        :return:            List of inclusive positive ranges.
        """
    ranges = ranges if isinstance(ranges, list) else [ranges]

    out = []
    for r in ranges:
        if isinstance(r, tuple):
            start, end = r

            if start is None:
                start = 0

            if end is None:
                end = clip.num_frames - 1
        elif r is None:
            start = clip.num_frames - 1
            end = clip.num_frames - 1
        else:
            start = r
            end = r

        if start < 0:
            start = clip.num_frames - 1 + start

        if end < 0:
            end = clip.num_frames - 1 + end

        out.append((start, end))

    return out


def match_clip(clip: vs.VideoNode, ref: vs.VideoNode,
               dimensions: bool = True, vformat: bool = True,
               matrices: bool = True, length: bool = False,
               kernel: Kernel | str = Bicubic(b=0, c=1/2)) -> vs.VideoNode:
    """
    Try matching the given clip's format with the reference clip's.

    :param clip:        Clip to process.
    :param ref:         Reference clip.
    :param dimensions:  Match video dimensions (Default: True).
    :param vformat:     Match video formats (Default: True).
    :param matrices:    Match matrix/transfer/primaries (Default: True).
    :param length:      Match clip length (Default: False).
    :param kernel:      py:class:`vskernels.Kernel` object used for the format conversion.
                        This can also be the string name of the kernel
                        (Default: py:class:`vskernels.Bicubic(b=0, c=1/2)`).

    :return:            Clip that matches the ref clip in format.
    """
    kernel = get_kernel(kernel)()

    clip = clip * ref.num_frames if length else clip
    clip = kernel.scale(clip, ref.width, ref.height) if dimensions else clip

    if vformat:
        assert ref.format
        clip = kernel.resample(clip, format=ref.format, matrix=Matrix.from_video(ref))

    if matrices:
        ref_frame = ref.get_frame(0)

        clip = clip.std.SetFrameProps(
            _Matrix=get_prop(ref_frame, '_Matrix', int),
            _Transfer=get_prop(ref_frame, '_Transfer', int),
            _Primaries=get_prop(ref_frame, '_Primaries', int)
        )

    return clip.std.AssumeFPS(fpsnum=ref.fps.numerator, fpsden=ref.fps.denominator)
