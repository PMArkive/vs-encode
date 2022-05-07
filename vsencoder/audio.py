import os
from typing import Any, List, Sequence

from vardautomation import (AudioCutter, AudioEncoder, AudioExtracter,
                            AudioTrack, Eac3toAudioExtracter, FileInfo, VPath)
from .types import AudioTrim

from .helpers import get_channel_layout_str


def set_audio_tracks(self, cutter: AudioCutter | Sequence[AudioCutter] | None = None,
                     encoder: AudioEncoder | Sequence[AudioEncoder] | None = None,
                     extracter: AudioExtracter | Sequence[AudioExtracter] | None = None,
                     track: int = 1, **cut_overrides: Any) -> None:
    if cutter is not None:
        self.a_cutters += [cutter(file_copy, track=-1, **cut_overrides)]

    if encoder is not None:
        self.a_encoders += [encoder(file_copy, track=-1, **cut_overrides)]

    if extracter is not None:
        self.a_extracters += [Eac3toAudioExtracter(file_copy, track_in=-1, track_out=-1)]

    if track is not None:
        self.a_tracks += [
            AudioTrack(
                self.file.a_src_cut.format(1),
                f"{original_codecs[0].upper()} {get_channel_layout_str(track_channels[0])}",
                self.a_lang, 0)
        ]


def set_eafile_properties(file: FileInfo, file_copy: FileInfo,
                          external_audio_file: str,
                          trims: AudioTrim | None = None,
                          use_ap: bool = True) -> FileInfo:
    file_copy.path = VPath(external_audio_file)
    file_copy.path_without_ext = VPath(os.path.splitext(external_audio_file)[0])
    file_copy.work_filename = file_copy.path.stem

    if use_ap:
        file_copy.trims_or_dfs = trims  # type:ignore[assignment]

    return file_copy


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
