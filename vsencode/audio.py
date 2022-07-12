from __future__ import annotations

import os
import shutil
from fractions import Fraction
from typing import Any, List, Sequence, Tuple, Type

import vapoursynth as vs
from lvsfunc import normalize_ranges
from lvsfunc.types import Range
from pymediainfo import MediaInfo
from vardautomation import (
    JAPANESE, AudioCutter, AudioEncoder, AudioExtracter, AudioTrack, DuplicateFrame, Eac3toAudioExtracter,
    FDKAACEncoder, FileInfo2, Lang, Preset, QAACEncoder, SoxCutter, Trim, VPath, logger
)

from .exceptions import MissingDependenciesError
from .types import PresetBackup


def resolve_ap_trims(trims: Range | List[Range] | None, clip: vs.VideoNode) -> List[List[Range]]:
    """Convert list[tuple] into list[list] (begna pls)."""
    if trims is None:
        return [[0, clip.num_frames-1]]

    return [list(trim) for trim in normalize_ranges(clip, trims)]


def set_eafile_properties(
    file_obj: FileInfo2, external_audio_file: str, external_audio_clip: vs.VideoNode | None = None,
    trims: List[Trim | DuplicateFrame] | Trim | None = None, use_ap: bool = True
) -> FileInfo2:
    """Set the external audio file properties."""
    file_obj.path = VPath(external_audio_file)
    file_obj.a_src = VPath(external_audio_file)
    file_obj.path_without_ext = VPath(os.path.splitext(external_audio_file)[0])
    file_obj.work_filename = file_obj.path.stem

    if external_audio_clip:
        file_obj.clip = external_audio_clip

    if use_ap:
        file_obj.trims_or_dfs = trims

    return file_obj


def get_track_info(obj: FileInfo2 | str, all_tracks: bool = False) -> Tuple[List[int], List[str]]:
    """Try to retrieve the channels and original codecs of an audio track."""
    track_channels = list[int]()
    original_codecs = list[str]()
    media_info: MediaInfo

    if isinstance(obj, str):
        parsed = MediaInfo.parse(obj)
        media_info = MediaInfo(parsed) if isinstance(parsed, str) else parsed
    elif isinstance(obj, FileInfo2):
        media_info = obj.media_info
    else:
        raise ValueError("Obj is not a FileInfo2 object or a path!")

    path_name = obj.path if isinstance(obj, FileInfo2) else obj

    logger.info("Checking track info...")
    for i, track in enumerate(media_info.tracks, start=1):
        if track.track_type == 'Audio':
            track_channels += [track.channel_s]
            original_codecs += [track.format]

            logger.warning(f"{path_name} track {i}: {track.format} (Channels: {track.channel_s})")

            if not all_tracks:
                break

    return track_channels, original_codecs


def run_ap(
    file_obj: FileInfo2, is_aac: bool = True,
    trims: Range | List[Range] | None = None,
    fps: Fraction | None = None, **enc_overrides: Any
) -> List[str]:
    """Run bvsfunc.AudioProcessor."""
    # TODO Annoy begna for this: https://github.com/begna112/bvsfunc/issues/16
    try:
        from bvsfunc.util.AudioProcessor import video_source
    except ImportError:
        raise ModuleNotFoundError("audio.run_ap: missing dependency 'bvsfunc'!")

    if 'silent' not in enc_overrides:
        enc_overrides |= {'silent': False}

    return video_source(
        in_file=file_obj.path.to_str(),
        out_file=str(file_obj.a_src_cut),
        trim_list=resolve_ap_trims(trims, file_obj.clip),
        trims_framerate=fps or file_obj.clip.fps,
        frames_total=file_obj.clip.num_frames,
        flac=not is_aac, aac=is_aac, **enc_overrides
    )


def check_qaac_installed() -> bool:
    """Check if qaac is installed."""
    b32 = shutil.which('qaac') is not None
    b64 = shutil.which('qaac64') is not None

    return b32 or b64


def check_ffmpeg_installed() -> bool:
    """Check if ffmpeg is installed."""
    return shutil.which('ffmpeg') is not None


def check_aac_encoders_installed() -> None:
    """Check if all aac encoders are installed."""
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


def iterate_ap_audio_files(
    audio_files: List[str], track_channels: List[int],
    all_tracks: bool = False, codec: str = 'AAC',
    xml_file: str | List[str] | None = None, lang: List[Lang] = [JAPANESE]
) -> List[AudioTrack]:
    """Iterate over every ap audio file and assign relevant information to each."""
    if xml_file:
        if isinstance(xml_file, str):
            xml_file = [xml_file]

        xml_args = [('--tags', f'0:{str(xml)}') for xml in xml_file]
    else:
        xml_args = None

    if xml_args and (diff := len(audio_files) - len(xml_args)):
        xml_args.extend(xml_args[-1:] * diff)

    if not track_channels:
        track_channels = [2] * len(audio_files)

    if len(lang) < len(track_channels):
        lang_old = lang.copy()
        lang.extend([lang[-1]] * (len(track_channels) - len(lang)))
        logger.warning(
            "Less languages passed than channels available! Extending the final entry.\n"
            f"Old langs: {lang_old}\n"
            f"New langs: {lang}"
        )

    a_tracks = list[AudioTrack]()

    # TODO: Fix mypy complaining about arg_type. Can't pass anything to tid because that breaks shit
    # https://discord.com/channels/856381934052704266/856406641872207903/993925364281786399
    # The code still seems to work fine, though.
    zipped = zip(audio_files, track_channels, xml_args, lang)  # type:ignore[arg-type]
    for i, (track, channels, xml_arg, tlang) in enumerate(zipped, start=1):
        a_tracks += [
            AudioTrack(
                VPath(track).format(track_number=i),
                f'{codec.upper()} {get_channel_layout_str(channels)}', tlang, xml_arg  # type:ignore[arg-type]
            )
        ]

        logger.warning(f"{audio_files[i-1]}: Added audio track ({track}, {channels})")
        if not all_tracks:
            break

    return a_tracks


no_track_warning: str = "There must be at least one audio track in your file!"


def iterate_cutter(
    file_obj: FileInfo2, cutter: Type[AudioCutter] = SoxCutter,
    tracks: int = 1, out_path: VPath | None = None,
    **overrides: Any
) -> List[AudioCutter]:
    """Iterate over every audio track with the assigned audio cutter."""
    if tracks < 1:
        raise ValueError(no_track_warning)

    if file_obj.a_src_cut is None and out_path:
        if r"{track_number:s}" not in str(file_obj.a_src_cut):
            og_path = os.path.splitext(out_path)
            out_path = VPath(og_path[0] + r"_track_{track_number:s}" + og_path[1])
        file_obj.a_src_cut = out_path

    return [cutter(file_obj, track=i, **overrides) for i in range(tracks)]


def iterate_encoder(
    file_obj: FileInfo2, encoder: Type[AudioEncoder] = QAACEncoder,
    tracks: int = 1, out_path: VPath | None = None,
    xml_file: str | Sequence[str | None] | None = None,
    **overrides: Any
) -> List[AudioEncoder]:
    """Iterate over every audio track with the assigned audio encoder."""
    if tracks < 1:
        raise ValueError(no_track_warning)

    if file_obj.a_enc_cut is None and out_path:
        if r"track_number:s" not in str(file_obj.a_enc_cut):
            og_path = os.path.splitext(out_path)
            out_path = VPath(og_path[0] + r"_track_\{track_number:s\}" + og_path[1])
        file_obj.a_enc_cut = out_path

    if not isinstance(xml_file, Sequence):
        xml_file = [xml_file] * tracks

    if encoder in (QAACEncoder, FDKAACEncoder):
        overrides |= {'xml_tag': xml_file}

    return [encoder(file=file_obj, track=i, **overrides) for i in range(tracks)]  # type: ignore


def iterate_extractors(
    file_obj: FileInfo2, extractor: Type[AudioExtracter] = Eac3toAudioExtracter,
    tracks: int = 1, out_path: VPath | None = None, **overrides: Any
) -> List[AudioExtracter]:
    """Iterate over every audio track with the assigned audio extractor."""
    if tracks < 1:
        raise ValueError(no_track_warning)

    if file_obj.a_src_cut is None and out_path:
        if r"{track_number:s}" not in str(file_obj.a_src_cut):
            og_path = os.path.splitext(out_path)
            out_path = VPath(og_path[0] + r"_track_{track_number:s}" + og_path[1])
        file_obj.a_src_cut = out_path

    return [extractor(file=file_obj, track_in=i, track_out=i, **overrides) for i in range(tracks)]  # type: ignore


def iterate_tracks(
    file_obj: FileInfo2, tracks: int = 1, out_path: VPath | None = None,
    codecs: str | Sequence[str | None] | None = None, lang: Lang = JAPANESE
) -> List[AudioTrack]:
    """Iterate over every audio track and set the proper properties."""
    if tracks < 1:
        raise ValueError(no_track_warning)

    if file_obj.a_enc_cut is None and out_path:
        if r"{track_number:s}" not in str(file_obj.a_enc_cut):
            og_path = os.path.splitext(out_path)
            out_path = VPath(og_path[0] + r"_track_{track_number:s}" + og_path[1])
        file_obj.a_enc_cut = out_path

    assert file_obj.a_enc_cut

    if not isinstance(codecs, Sequence):
        codecs = [codecs] * tracks

    assert len(codecs) == tracks, 'You need to specify codecs for all tracks!'

    return [
        AudioTrack(file_obj.a_enc_cut.format(track_number=i), codec, lang) for i, codec in enumerate(codecs)
    ]


def set_missing_tracks(file_obj: FileInfo2, preset: Preset = PresetBackup, use_ap: bool = True) -> FileInfo2:
    """Set missing tracks in the given FileInfo object."""
    try:
        assert isinstance(file_obj.a_src, VPath)
    except AssertionError:
        logger.info(f"Set missing track a_src_cut (\"{file_obj.a_src}\" -> \"{file_obj.a_src}\")...")
        file_obj.a_src = preset.a_src

    if use_ap:
        try:
            assert file_obj.a_src_cut == file_obj.name
        except AssertionError:
            logger.info(f"Set missing track a_src_cut (\"{file_obj.a_src_cut}\" -> \"{file_obj.name}\")...")
            file_obj.a_src_cut = VPath(file_obj.name)
    else:
        try:
            assert isinstance(file_obj.a_src_cut, VPath)
        except AssertionError:
            logger.info(f"Set missing track a_src_cut (\"{file_obj.a_src_cut}\" -> \"{preset.a_src_cut}\")...")
            file_obj.a_src_cut = preset.a_src_cut

    try:
        assert isinstance(file_obj.a_enc_cut, VPath)
    except AssertionError:
        logger.info(f"Set missing track a_enc_cut (\"{file_obj.a_enc_cut}\" -> \"{preset.a_enc_cut}\")...")
        file_obj.a_enc_cut = preset.a_enc_cut

    return file_obj


# TODO: Make this a proper function that accurately gets the channel layout.
#       Improving this function should be a priority!!!
def get_channel_layout_str(channels: int) -> str:
    """Return a very basic channel layout picker for audio tracks."""
    match channels:
        case 2: return '2.0'
        case 5: return '5.1'
        case 1: return '1.0'
        case 7: return '7.1'
        case _: raise ValueError("get_channel_layout_str: 'Current channel count unsupported!'")
