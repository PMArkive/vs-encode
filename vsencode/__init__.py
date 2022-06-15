"""
    vs-encode, an extensive wrapper around vardautomation
    to help make it easier to digest for newer video encoders.

    If you spot any issues, please don't hesitate to send in a Pull Request
    or reach out to me on Discord (LightArrowsEXE#0476)!

    For further support, drop by the `IEW Discord server <https://discord.gg/qxTxVJGtst>`_.
"""

# flake8: noqa

from vardautomation import VPath
from vardautomation.language import *

from . import (encoder, exceptions, generate, helpers, presets, templates,
               types, util)
from .encoder import *
from .exceptions import *
from .generate import *
from .helpers import FileInfo
from .presets import *
from .templates import *
from .types import *
from .util import *

# Aliases
load_video = FileInfo
src = FileInfo
source = FileInfo
