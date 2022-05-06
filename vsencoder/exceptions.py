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
