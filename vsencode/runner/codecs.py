from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum, auto


@dataclass
class BaseEncoder:
    name: str
    fallback: BaseEncoder | None = None
    can_lossless: bool = False


class StandaloneEncoder(BaseEncoder):
    ...


class FFMPEGEncoder(BaseEncoder):
    ...


class VideoCodec(BaseEncoder, Enum):  # TODO: FIX DynamicClassAttribute
    """Enum representing a video codec."""

    # lossy codecs
    H264 = AVC = StandaloneEncoder('x264', FFMPEGEncoder('libx264'))
    """Encoder: x264 (fallback: ffmpeg) ——— https://en.wikipedia.org/wiki/H.264/MPEG-4_AVC """

    H265 = HEVC = StandaloneEncoder('x265', FFMPEGEncoder('libx265'))
    """Encoder: x265 (fallback: ffmpeg) ——— https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding """

    AV1 = StandaloneEncoder('aomenc', StandaloneEncoder('av1an', FFMPEGEncoder('av1')))
    """Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/AOMedia_Video_1 """

    VP8 = FFMPEGEncoder('vp8')
    """Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/VP8 """

    VP9 = FFMPEGEncoder('vp9')
    """Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/VP9 """

    MPEG1 = FFMPEGEncoder('mpeg1')
    """Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/MPEG-1 """

    MPEG2 = FFMPEGEncoder('mpeg2')
    """Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/H.262/MPEG-2_Part_2 """

    QUICKTIME = FFMPEGEncoder('quicktime')
    """Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/Apple_Video """

    WMV = FFMPEGEncoder('wmv')
    """Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/Windows_Media_Video """

    # lossless codecs
    FFV1 = FFMPEGEncoder('ffv1', can_lossless=True)
    """Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/FFV1 """

    PRORES = FFMPEGEncoder('prores', can_lossless=True)
    """(™)  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/ProRes_422 """

    LAGARITH = FFMPEGEncoder('lagarith', can_lossless=True)
    """Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/Lagarith """

    UTVIDEO = FFMPEGEncoder('utvideo', can_lossless=True)
    """Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/Ut_Video_Codec_Suite """


class AudioCodec(BaseEncoder, Enum):
    """Enum representing an audio codec."""

    AAC = StandaloneEncoder('qaac', FFMPEGEncoder('libfdk_aac'))
    """Encoder: iTunes qaac (fallback: ffmpeg) ——— https://en.wikipedia.org/wiki/Advanced_Audio_Coding """

    FLAC = StandaloneEncoder('flac', FFMPEGEncoder('flac'))
    """Encoder: libflac (fallback: ffmpeg) ——— https://en.wikipedia.org/wiki/FLAC """

    OPUS = StandaloneEncoder('opus', FFMPEGEncoder('libopus'))
    """Encoder: libopus (fallback ffmpeg) ——— https://en.wikipedia.org/wiki/Opus_(codec) """

    PCM = LPCM = FFMPEGEncoder('pcm')
    """Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/Linear_pulse-code_modulation """


class SubtitleCodec(IntEnum):
    """Enum representing a subtitle codec."""

    ASS = auto()
    SSA = auto()
    SRT = auto()
    VOBSUB = auto()
    PGS = auto()
