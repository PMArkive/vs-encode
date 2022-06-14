from __future__ import annotations

from typing import List

common_idx_ext: List[str] = ['lwi', 'ffindex']

# These codecs get re-encoded/errored out by all the extracters, making a simple passthrough impossible.
reenc_codecs: List[str] = ['AC-3', 'EAC-3']


class FrameLengthMismatch(ValueError):
    """Raised when the amount of frames between two clips don't match."""
    def __init__(self, len_a: int, len_b: int,
                 message: str = "The two given clips don't have the same length ({len_a} vs. {len_b})."):
        super().__init__(message.format(len_a=len_a, len_b=len_b))


class EncoderTypeError(ValueError):
    def __init__(self, message: str = "Expected an encoder type, but got nothing!"):
        super().__init__(message)


class NoVideoEncoderError(EncoderTypeError):
    def __init__(self, message: str = "No video encoder given!"):
        super().__init__(message)


class NoLosslessVideoEncoderError(EncoderTypeError):
    def __init__(self, message: str = "No lossless video encoder given!"):
        super().__init__(message)


class NoAudioEncoderError(EncoderTypeError):
    def __init__(self, message: str = "No audio encoder given!"):
        super().__init__(message)


class NoChaptersError(ValueError):
    def __init__(self, message: str = "No chapters given!"):
        super().__init__(message)


class NotEnoughValuesError(ValueError):
    def __init__(self, message: str = "Not enough values given!"):
        super().__init__(message)


class AlreadyInChainError(ValueError):
    def __init__(self, method: str, message: str = "You may only have one {method} in your chain!"):
        super().__init__(message.format(method=method))


class NotInChainError(ValueError):
    def __init__(self, method: str, message: str = "The {method} method is required in your chain!"):
        super().__init__(message.format(method=method))


class MissingDependenciesError(FileNotFoundError):
    def __init__(self, dependency: str, message: str = "Can't find dependency {dependency}!"):
        super().__init__(message.format(dependency=dependency))
