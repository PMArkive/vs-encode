"""Common encoding presets."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import vapoursynth as vs
from vardautomation import FileInfo2
from vardefunc.types import Range

from .encoder import EncodeRunner
from .types import AUDIO_CODEC, VIDEO_CODEC

__all__ = ['encode', 'x264_aac_preset', 'x264_flac_preset', 'x265_aac_preset', 'x265_flac_preset']


def encode(
    file: FileInfo2, clip: vs.VideoNode, patch: bool = False,
    video_enc: VIDEO_CODEC = 'x264', audio_enc: AUDIO_CODEC = 'qaac',
    zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
    patch_ranges: Range | List[Range] = [],
    encoder_credit: str = '', clean_up: bool = True,
    video_args: Dict[str, Any] = {},
    audio_args: Dict[str, Any] = {},
    run_args: Dict[str, Any] = {},
    patch_args: Dict[str, Any] = {},
) -> None:
    """
    Encode function to steer the presets with.

    This is meant to be used for simple encodes where you don't need to mess with the finer details too much.
    Presets have been made using this function as a base as well.

    This will also automatically use a qp clip, set it to resumable, sanitize the input clip,
    encode the video using x264, the audio with QAAC through AudioProcessor,
    and output an mkv with all tracks set to Japanese.

    You can forcibly change anything to suit your needs by passing specific kwargs (through a dictionary).
    However, if you're doing that, you should honestly just be chaining the methods yourself.

    See the Encoder class for further information.

    :param file:                FileInfo2 object.
    :param clip:                Input VideoNode.
    :param patch:               Patching mode. If False, runs a regular encoder.
    :param video_enc:           Encoder to use for the video. See `Encoder.video` for more info.
    :param audio_enc:           Encoder to use for the audio. See `Encoder.audio` for more info.
    :param zones:               Zones for x264/x265. Expected in the following format:
                                {(100, 200): {'crf': 13}, (500, 600): {'crf': 12}}.
                                Zones will be sorted prior to getting passed to the encoder.
                                This is only used when `patch=False`.
    :param patch_ranges:        Frame ranges that require patching.
                                Expects as a list of tuples or integers (can be mixed).
                                Examples: [(0, 100), (400, 600)]; [50, (100, 200), 500].
                                This is only used when `patch=True`.
    :param encoder_credit:      Name of the person encoding the video. Will be included in the video metadata.
    :param clean_up:            Cleans up the encoding files after encoding.

    :param x_args:              Different arguments to be passed to the relevant methods.
                                Although if you're using this, you should really just
                                be calling the methods directly yourself.
    """
    runner = EncodeRunner(file, clip)
    runner.video(video_enc, None, zones, **video_args)
    runner.audio(audio_enc, **audio_args)
    runner.mux(encoder_credit)

    if patch:
        runner.patch(patch_ranges, clean_up, **patch_args)
    else:
        runner.run(clean_up, **run_args)


def x264_aac_preset(
    file: FileInfo2, clip: vs.VideoNode, patch: bool = False,
    zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
    patch_ranges: Range | List[Range] = [],
    encoder_credit: str = '', clean_up: bool = True
) -> None:
    """
    Encode runner using x264 for video and AudioProcessor (QAAC) to AAC for audio.

    See the `encoder` function for more information.
    """
    encode(file, clip, patch, 'x264', 'qaac', zones, patch_ranges, encoder_credit, clean_up)


def x264_flac_preset(
    file: FileInfo2, clip: vs.VideoNode, patch: bool = False,
    zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
    patch_ranges: Range | List[Range] = [],
    encoder_credit: str = '', clean_up: bool = True
) -> None:
    """
    Encode runner using x264 for video and AudioProcessor (FLAC) to FLAC for audio.

    See the `encoder` function for more information.
    """
    encode(file, clip, patch, 'x264', 'flac', zones, patch_ranges, encoder_credit, clean_up)


def x265_aac_preset(
    file: FileInfo2, clip: vs.VideoNode, patch: bool = False,
    zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
    patch_ranges: Range | List[Range] = [],
    encoder_credit: str = '', clean_up: bool = True
) -> None:
    """
    Encode runner using x265 for video and AudioProcessor (QAAC) to AAC for audio.

    See the `encoder` function for more information.
    """
    encode(file, clip, patch, 'x265', 'qaac', zones, patch_ranges, encoder_credit, clean_up)


def x265_flac_preset(
    file: FileInfo2, clip: vs.VideoNode, patch: bool = False,
    zones: Dict[Tuple[int, int], Dict[str, Any]] | None = None,
    patch_ranges: Range | List[Range] = [],
    encoder_credit: str = '', clean_up: bool = True
) -> None:
    """
    Encode runner using x265 for video and AudioProcessor (FLAC) to FLAC for audio.

    See the `encoder` function for more information.
    """
    encode(file, clip, patch, 'x265', 'flac', zones, patch_ranges, encoder_credit, clean_up)
