from __future__ import annotations

from typing import Any

from vardautomation import X264, X265
from vskernels import get_prop

from .helpers import get_encoder_cores, get_lookahead, get_sar, get_range_x264, get_range_x265

__all__ = ['X264Custom', 'X265Custom']


class X264Custom(X264):
    """
    Custom x265 runner that adds new useful keys.

    You set them by putting {key:type} in the settings file.
    `s` is used for strings, `d` is used for integers.

    For example:
        --threads {thread:d} --colormatrix {matrix:s}

    The type is also given in the individdual explanation.

    :key thread:            Automatically determine amount of threads for x264 to use. (d)
    :key range:             Automatically determine the clip's color range from the clip's frameprops. (s)
    :key matrix:            Automatically determine the clip's color matrix from the clip's frameprops. (s)
    :key transfer:          Automatically determine the clip's gamma transfer from the clip's frameprops. (s)
    :key primaries:         Automatically determine the clip's color primaries from the clip's frameprops. (s)
    :key sarden:            Automatically determine the clip's sar denominator from the clip's frameprops. (d)
    :key sarnum:            Automatically determine the clip's sar numerator from the clip's frameprops. (d)
    :key lookahead:         Automatically determine the lookahead based on the framerate of the video. (d)
                            Values above 120 are not recommended.
    """

    def set_variable(self) -> Any:
        """Set a custom variable."""
        sar = get_sar(self.clip)

        return super().set_variable() | {
            'thread': get_encoder_cores(),
            'range': get_range_x264(self.clip),
            'sarden': sar[0],
            'sarnum': sar[1],
            'lookahead': get_lookahead(self.clip),
        }


class X265Custom(X265):
    """
    Custom x265 runner that adds new useful keys.

    You set them by putting {key:type} in the settings file.
    `s` is used for strings, `d` is used for integers.

    For example:
        --numa-pools {thread:d} --colormatrix {matrix:d}

    The type is also given in the individual explanation.

    :key thread:            Automatically determine amount of threads for x265 to use. (d)
    :key range:             Automatically determine the clip's color range from the clip's frameprops. (s)
    :key matrix:            Automatically determine the clip's color matrix from the clip's frameprops. (d)
    :key transfer:          Automatically determine the clip's gamma transfer from the clip's frameprops. (d)
    :key primaries:         Automatically determine the clip's color primaries from the clip's frameprops. (d)
    :key chromaloc:         Automatically determine the clip's chroma location from the clip's frameprops. (d)
    :key sarden:            Automatically determine the clip's sar denominator from the clip's frameprops. (d)
    :key sarnum:            Automatically determine the clip's sar numerator from the clip's frameprops. (d)
    :key lookahead:         Automatically determine the lookahead based on the framerate of the video. (d)
                            Values above 120 are not recommended. x265's spec limits lookahead to 250.
    :key crops:             Automatically determine the clip's display-window from the clip's frameprops. (s)
                            This will enable cropping in realtime and automatically add "--overscan crop" too.
                            Expected to be a string following this pattern: "<left>,<top>,<right>,<bottom>".
                            Custom frameprop is "_crops". Only use for anamorphic resolutions. Experimental.
    """

    def set_variable(self) -> Any:
        """Set a custom variable."""
        sar = get_sar(self.clip)

        return super().set_variable() | {
            'thread': get_encoder_cores(),
            'range': get_range_x265(self.clip),
            'chromaloc': get_prop(self.clip, '_ChromaLocation', int),
            'sarden': sar[0],
            'sarnum': sar[1],
            'lookahead': get_lookahead(self.clip),
            'crops': f"{get_prop(self.clip, '_crops', str)} --overscan crop"
        }
