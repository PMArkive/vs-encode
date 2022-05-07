from typing import Any, Dict

from vardautomation.utils import Properties
from vardautomation.video import X264, X265

from .helpers import get_encoder_cores, x264_get_matrix_str


class X264Custom(X264):
    """
    Custom x265 runner that adds new useful keys.
    You set them by putting {key:type} in the settings file.
    `s` is used for strings, `d` is used for integers.

    For example:
        --threads {thread:d}

    The type is also given in the individdual explanation.

    :key thread:        Automatically determine amount of threads for x265 to run. (d)
    :key matrix:        Automatically set the clip's color matrix from the clip's frameprops. (s)
    :key transfer:      Automatically set the clip's gamma transfer from the clip's frameprops. (s)
    :key primaries:     Automatically set the clip's color primaries from the clip's frameprops. (s)
    """
    props_obj = Properties()

    def set_variable(self) -> Any:
        return super().set_variable() | dict(
            thread=get_encoder_cores(),
            matrix=x264_get_matrix_str(self.props_obj.get_prop(self.clip.get_frame(0), '_Matrix', int)),
            primaries=x264_get_matrix_str(self.props_obj.get_prop(self.clip.get_frame(0), '_Primaries', int)),
            transfer=x264_get_matrix_str(self.props_obj.get_prop(self.clip.get_frame(0), '_Transfer', int)))


class X265Custom(X265):
    """
    Custom x265 runner that adds new useful keys.
    You set them by putting {key:type} in the settings file.
    `s` is used for strings, `d` is used for integers.

    For example:
        --numa-pools {thread:d}

    The type is also given in the individdual explanation.

    :key thread:        Automatically determine amount of threads for x265 to run. (d)
    :key matrix:        Automatically set the clip's color matrix from the clip's frameprops. (d)
    :key transfer:      Automatically set the clip's gamma transfer from the clip's frameprops. (d)
    :key primaries:     Automatically set the clip's color primaries from the clip's frameprops. (d)
    """
    props_obj = Properties()

    def set_variable(self) -> Any:
        return super().set_variable() | dict(
            thread=get_encoder_cores(),
            matrix=self.props_obj.get_prop(self.clip.get_frame(0), '_Matrix', int),
            primaries=self.props_obj.get_prop(self.clip.get_frame(0), '_Primaries', int),
            transfer=self.props_obj.get_prop(self.clip.get_frame(0), '_Transfer', int))