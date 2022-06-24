from __future__ import annotations

from typing import Any

from vardautomation import X264, X265

from .helpers import get_encoder_cores

__all__ = ['X264Custom', 'X265Custom']


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

    def set_variable(self) -> Any:
        """Set a custom variable."""
        return super().set_variable() | dict(thread=get_encoder_cores())


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

    def set_variable(self) -> Any:
        """Set a custom variable."""
        return super().set_variable() | dict(thread=get_encoder_cores())
