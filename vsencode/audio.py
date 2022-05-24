from __future__ import annotations

import os
import shutil
from fractions import Fraction
from typing import Any, List, Tuple

import vapoursynth as vs
from bvsfunc.util import AudioProcessor as ap
from lvsfunc.types import Range
from vardautomation import (JAPANESE, AudioTrack, Eac3toAudioExtracter,
                            FDKAACEncoder, FileInfo2, Lang, Preset,
                            QAACEncoder, SoxCutter, VPath, logger)

from .exceptions import MissingDependenciesError
from .types import (BUILTIN_AUDIO_CUTTERS, BUILTIN_AUDIO_ENCODERS,
                    BUILTIN_AUDIO_EXTRACTORS, AudioTrim, PresetBackup)

try:
    from pymediainfo import MediaInfo
except ModuleNotFoundError:
    raise ModuleNotFoundError("audio: missing dependency 'pymediainfo'")


def resolve_ap_trims(trims: Range | List[Range] | None, clip: vs.VideoNode) -> List[List[Range]]:
    """Convert list[tuple] into list[list]. begna pls"""
    from lvsfunc.util import normalize_ranges

    if trims is None:
        return [[0, clip.num_frames-1]]

    nranges = list(normalize_ranges(clip, trims))
    return [list(trim) for trim in nranges]


def set_eafile_properties(file_obj: FileInfo2,
                          external_audio_file: str,
                          external_audio_clip: vs.VideoNode | None = None,
                          trims: AudioTrim | None = None,
                          use_ap: bool = True) -> FileInfo2:
    file_obj.path = VPath(external_audio_file)
    file_obj.path_without_ext = VPath(os.path.splitext(external_audio_file)[0])
    file_obj.work_filename = file_obj.path.stem

    if external_audio_clip:
        file_obj.clip = external_audio_clip

    if use_ap:
        file_obj.trims_or_dfs = trims  # type:ignore

    return file_obj


def get_track_info(obj: FileInfo2 | str, all_tracks: bool = False) -> Tuple[List[int] | List[str]]:
    track_channels: List[int] = []
    original_codecs: List[str] = []
    media_info: MediaInfo

    if isinstance(obj, str):
        media_info = MediaInfo.parse(obj)  # type:ignore[assignment]
    elif isinstance(obj, FileInfo2):
        media_info = obj.media_info
    else:
        raise ValueError("Obj is not a FileInfo2 object or a path!")

    for track in media_info.tracks:
        if track.track_type == 'Audio':
            track_channels += [track.channel_s]
            original_codecs += [track.format]
            if not all_tracks:
                break

    return (track_channels, original_codecs)


def run_ap(file_obj: FileInfo2, is_aac: bool = True, trims: AudioTrim | None = None,
           fps: Fraction | None = None, **enc_overrides: Any) -> List[str]:
    return ap.video_source(
        in_file=file_obj.path.to_str(),
        out_file=str(file_obj.a_src_cut),
        trim_list=resolve_ap_trims(trims, file_obj.clip),  # type:ignore[arg-type]
        trims_framerate=fps or file_obj.clip.fps,
        frames_total=file_obj.clip.num_frames,
        flac=not is_aac, aac=is_aac, silent=False, **enc_overrides
    )


def check_qaac_installed() -> bool:
    return shutil.which('qaac') is not None


def check_ffmpeg_installed() -> bool:
    return shutil.which('ffmpeg') is not None


def check_aac_encoders_installed() -> None:
    try:
        qaac_ins = check_qaac_installed()
    except MissingDependenciesError:
        logger.warning("qaac not installed!")

    try:
        ffmpeg_ins = check_ffmpeg_installed()
    except MissingDependenciesError:
        logger.warning("ffmpeg not installed!")

    if not any([qaac_ins, ffmpeg_ins]):
        raise MissingDependenciesError("", message="Neither qaac nor ffmpeg are installed!")


def iterate_ap_audio_files(audio_files: List[str], track_channels: List[int],
                           all_tracks: bool = False, codec: str = 'AAC',
                           xml_file: str | None = None,
                           lang: Lang = JAPANESE) -> List[AudioTrack]:
    a_tracks: List[AudioTrack] = []

    xml_arg: Tuple[str, str] = ()
    # TODO: Multi-track support
    if isinstance(xml_file, str):
        xml_arg = ('--tags', f'0:{str(xml_file)}')

    for i, (track, channels) in enumerate(zip(audio_files, track_channels), 1):
        a_tracks += [AudioTrack(VPath(track).format(track_number=i),
                                f'{codec.upper()} {get_channel_layout_str(channels)}',
                                lang, i, *xml_arg)]

        if not all_tracks:
            break

    return a_tracks


no_track_warning: str = "There must be at least one audio track in your file!"


def iterate_cutter(file_obj: FileInfo2, cutter: BUILTIN_AUDIO_CUTTERS = SoxCutter,
                   tracks: int = 1, out_path: VPath | None = None,
                   **overrides: Any) -> List[BUILTIN_AUDIO_CUTTERS]:
    if tracks < 1:
        raise ValueError(no_track_warning)

    if file_obj.a_src_cut is None and out_path:
        if r"{track_number:s}" not in str(file_obj.a_src_cut):
            og_path = os.path.splitext(out_path)
            out_path = VPath(og_path[0] + r"_track_{track_number:s}" + og_path[1])
        file_obj.a_src_cut = out_path

    cutters: List[BUILTIN_AUDIO_CUTTERS] = []

    for i in range(tracks):
        cutters += [cutter(file_obj, track=i, **overrides)]  # type:ignore[list-item]

    return cutters


def iterate_encoder(file_obj: FileInfo2, encoder: BUILTIN_AUDIO_ENCODERS = QAACEncoder,
                    tracks: int = 1, out_path: VPath | None = None,
                    xml_file: str | List[str] | List[None] | None = None,
                    **overrides: Any) -> List[BUILTIN_AUDIO_ENCODERS]:
    if tracks < 1:
        raise ValueError(no_track_warning)

    if file_obj.a_enc_cut is None and out_path:
        if r"track_number:s" not in str(file_obj.a_enc_cut):
            og_path = os.path.splitext(out_path)
            out_path = VPath(og_path[0] + r"_track_\{track_number:s\}" + og_path[1])
        file_obj.a_enc_cut = out_path

    if xml_file is None:
        xml_file: List[str] | List[None] = []  # type:ignore[no-redef]
        for i in range(tracks):
            xml_file += [None]  # type:ignore
    elif isinstance(xml_file, str):
        xml_file_og = xml_file
        xml_file: List[str] = []  # type:ignore[no-redef]
        for i in range(tracks):
            xml_file += [xml_file_og]  # type:ignore[operator]

    if encoder in (QAACEncoder, FDKAACEncoder):
        overrides |= dict(xml_file=xml_file)

    encoders: List[BUILTIN_AUDIO_ENCODERS] = []

    for i in range(tracks):
        encoders += [encoder(file_obj, track=i, **overrides)]  # type:ignore[list-item]

    return encoders


def iterate_extractors(file_obj: FileInfo2, extractor: BUILTIN_AUDIO_EXTRACTORS = Eac3toAudioExtracter,
                       tracks: int = 1, out_path: VPath | None = None,
                       **overrides: Any) -> List[BUILTIN_AUDIO_EXTRACTORS] | None:
    if tracks < 1:
        raise ValueError(no_track_warning)

        try:
            file_obj.write_a_src_cut(1)
        except NameError:
            logger.warning("`Audios` attribute found! Extracting audio with `write_a_src_cut`...")
            return None

    if file_obj.a_src_cut is None and out_path:
        if r"{track_number:s}" not in str(file_obj.a_src_cut):
            og_path = os.path.splitext(out_path)
            out_path = VPath(og_path[0] + r"_track_{track_number:s}" + og_path[1])
        file_obj.a_src_cut = out_path

    extractors: List[BUILTIN_AUDIO_EXTRACTORS] = []

    for i in range(tracks):
        extractors += [extractor(file_obj, track_in=i, track_out=i, **overrides)]  # type:ignore[list-item]

    return extractors


def iterate_tracks(file_obj: FileInfo2, tracks: int = 1, out_path: VPath | None = None,
                   codecs: str | List[str] | None = None, lang: Lang = JAPANESE) -> List[AudioTrack]:
    if tracks < 1:
        raise ValueError(no_track_warning)

    if file_obj.a_enc_cut is None and out_path:
        if r"{track_number:s}" not in str(file_obj.a_enc_cut):
            og_path = os.path.splitext(out_path)
            out_path = VPath(og_path[0] + r"_track_{track_number:s}" + og_path[1])
        file_obj.a_enc_cut = out_path

    if codecs is None:
        codecs: List[str] = []  # type:ignore[no-redef]
        for i in range(tracks):
            codecs += [None]  # type:ignore
    if isinstance(codecs, str):
        og_codec = codecs
        codecs: List[str] = []  # type:ignore[no-redef]
        for i in range(tracks):
            codecs += [og_codec]  # type:ignore[operator]

    audio_tracks: List[AudioTrack] = []

    for i in range(tracks):
        audio_tracks += [AudioTrack(
            file_obj.a_enc_cut.format(track_number=i),
            codecs[i],
            lang,
            i
        )]

    return audio_tracks


def set_missing_tracks(file_obj: FileInfo2, preset: Preset = PresetBackup,
                       use_ap: bool = True) -> FileInfo2:
    try:
        assert isinstance(file_obj.a_src, VPath)
    except AssertionError:
        file_obj.a_src = preset.a_src

    if use_ap:
        file_obj.a_src_cut = file_obj.name
    else:
        try:
            assert isinstance(file_obj.a_src_cut, VPath)
        except AssertionError:
            file_obj.a_src_cut = preset.a_src_cut

    try:
        assert isinstance(file_obj.a_enc_cut, VPath)
    except AssertionError:
        file_obj.a_enc_cut = preset.a_enc_cut

    return file_obj


# TODO: Make this a proper function that accurately gets the channel layout.
#       Improving this function should be a priority!!!
def get_channel_layout_str(channels: int) -> str:
    """Very basic channel layout picker for AudioTracks"""
    match channels:
        case 2: return '2.0'
        case 5: return '5.1'
        case 1: return '1.0'
        case 7: return '7.1'
        case _: raise ValueError("get_channel_layout_str: 'Current channel count unsupported!'")
