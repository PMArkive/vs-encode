"""
    vs-encode, an extensive module to help run encodes straight from your script.

    If you spot any issues, please don't hesitate to send in a Pull Request
    or reach out to me on Discord (LightArrowsEXE#0476)!

    For further support, drop by the `IEW Discord server <https://discord.gg/qxTxVJGtst>`_.
"""

# flake8: noqa

from vardautomation import FileInfo

from .setup import *
from .encoder import *
from .runner import *
from .helpers import *
from .types import *
from .util import *

# Remove some keys to avoid confusion
keys = ["source"]

for key in keys:
    if key in globals():
        del globals()[key]
