from __future__ import annotations

from typing import Any

from vardautomation import X264, X265
from vstools import get_prop

from .helpers import get_encoder_cores, get_lookahead, get_sar, get_range, get_color_range

__all__ = ['X264Custom', 'X265Custom']


class X264Custom(X264):
    """
    Custom x265 runner that adds new useful keys.

    You set them by putting {key:type} in the settings file.
    `s` is used for strings, `d` is used for integers.

    For example:
        --threads {thread:d} --colormatrix {matrix:s}

    The type is also given in the individdual explanation.

    :key lookahead:         Automatically determine the lookahead based on the framerate of the video. (d)
                            Values above 120 are not recommended.
    :key matrix:            Automatically determine the clip's color matrix from the clip's frameprops. (s)
    :key primaries:         Automatically determine the clip's color primaries from the clip's frameprops. (s)
    :key range:             Automatically determine the clip's color range from the clip's frameprops. (d)
    :key sarden:            Automatically determine the clip's sar denominator from the clip's frameprops. (d)
    :key sarnum:            Automatically determine the clip's sar numerator from the clip's frameprops. (d)
    :key thread:            Automatically determine amount of threads for x264 to use. (d)
    :key transfer:          Automatically determine the clip's gamma transfer from the clip's frameprops. (s)
    """

    def set_variable(self) -> Any:
        """Set a custom variable."""
        sar = get_sar(self.clip)

        return super().set_variable() | {
            'lookahead': get_lookahead(self.clip),
            'range': get_range(self.clip),
            'sarden': sar[0],
            'sarnum': sar[1],
            'thread': get_encoder_cores(),
        }


class X265Custom(X265):
    """
    Custom x265 runner that adds new useful keys.

    You set them by putting {key:type} in the settings file.
    `s` is used for strings, `d` is used for integers.

    For example:
        --numa-pools {thread:d} --colormatrix {matrix:d}

    The type is also given in the individual explanation.

    :key chromaloc:         Automatically determine the clip's chroma location from the clip's frameprops. (d)
    :key crops:             Automatically determine the clip's display-window from the clip's frameprops. (s)
                            This will enable cropping in realtime and automatically add "--overscan crop" too.
                            Expected to be a string following this pattern: "<left>,<top>,<right>,<bottom>".
                            Custom frameprop is "_crops". Only use for anamorphic resolutions. Experimental.
    :key lookahead:         Automatically determine the lookahead based on the framerate of the video. (d)
                            Values above 120 are not recommended. x265's spec limits lookahead to 250.
    :key matrix:            Automatically determine the clip's color matrix from the clip's frameprops. (d)
    :key primaries:         Automatically determine the clip's color primaries from the clip's frameprops. (d)
    :key range:             Automatically determine the clip's color range from the clip's frameprops. (d)
    :key sarden:            Automatically determine the clip's sar denominator from the clip's frameprops. (d)
    :key sarnum:            Automatically determine the clip's sar numerator from the clip's frameprops. (d)
    :key thread:            Automatically determine amount of threads for x265 to use. (d)
    :key transfer:          Automatically determine the clip's gamma transfer from the clip's frameprops. (d)
    """

    def set_variable(self) -> Any:
        """Set a custom variable."""
        sar = get_sar(self.clip)
        min_luma, max_luma = get_color_range(self.clip, self.params)

        return super().set_variable() | {
            'chromaloc': get_prop(self.clip, '_ChromaLocation', int),
            'crops': f"{get_prop(self.clip, '_crops', str, default='0,0,0,0')} --overscan crop",  # type:ignore
            'lookahead': get_lookahead(self.clip),
            'range': get_range(self.clip),
            'sarden': sar[0],
            'sarnum': sar[1],
            'thread': get_encoder_cores(),
            'min_luma': min_luma,
            'max_luma': max_luma,
        }
