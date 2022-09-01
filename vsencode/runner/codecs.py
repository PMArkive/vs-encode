from enum import IntEnum, auto


class VideoCodec(IntEnum):
    """Enum representing a video codec."""

    # lossy codecs
    H264 = auto()  # Encoder: x264 (fallback: ffmpeg) ——— https://en.wikipedia.org/wiki/H.264/MPEG-4_AVC
    AVC = auto()  # See above
    H265 = auto()  # Encoder: x265 (fallback: ffmpeg) ——— https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding
    HEVC = auto()  # See above
    AV1 = auto()  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/AOMedia_Video_1
    VP8 = auto()  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/VP8
    VP9 = auto()  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/VP9
    MPEG1 = auto()  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/MPEG-1
    MPEG2 = auto()  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/H.262/MPEG-2_Part_2
    QUICKTIME = auto()  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/Apple_Video
    WMV = auto()  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/Windows_Media_Video

    # lossless codecs
    FFV1 = auto()  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/FFV1
    PRORES = auto()  # (™)  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/ProRes_422
    LAGARITH = auto()  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/Lagarith
    UTVIDEO = auto()  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/Ut_Video_Codec_Suite


class AudioCodec(IntEnum):
    """Enum representing an audio codec."""

    AAC = auto()  # Encoder: iTunes qaac (fallback: ffmpeg) ——— https://en.wikipedia.org/wiki/Advanced_Audio_Coding
    FLAC = auto()  # Encoder: libflac (fallback: ffmpeg) ——— https://en.wikipedia.org/wiki/FLAC
    OPUS = auto()  # Encoder: libopus (fallback ffmpeg) ——— https://en.wikipedia.org/wiki/Opus_(codec)
    PCM = auto()  # Encoder: ffmpeg ——— https://en.wikipedia.org/wiki/Linear_pulse-code_modulation
    LPCM = auto()  # See above


class SubtitleCodec(IntEnum):
    """Enum representing a subtitle codec."""

    ASS = auto()
    SSA = auto()
    SRT = auto()
    VOBSUB = auto()
    PGS = auto()
