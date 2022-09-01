from __future__ import annotations
from copy import deepcopy

import json
from typing import Any

from ..util import FilePath, MPath


class Config:
    """Config generator and injector."""

    """Video settings."""
    source_directory: str
    reserve_core: bool

    def __init__(self, name: FilePath = "config") -> None:
        """
        Create a Json file (if one doesn't exist yet), import it, and add all the settings as attributes.

        :param name:        Name for the file.
        """
        self.path = (MPath().cwd() / name).with_suffix('.json')

        if not MPath(self.path).exists():
            default_settings = {
                "Video": {
                    "source_directory": "BDMV",
                    "reserve_core": True,
                },
            }

            with open(self.path, "w") as f:
                json.dump(default_settings, f, indent=6)

        self.settings = json.load(open(self.path))

        for key in self.settings:
            if isinstance(self.settings[key], dict):
                for k in self.settings[key]:
                    setattr(self, k, self.settings[key][k])
            else:
                setattr(self, key, self.settings[key])

    def get_settings(self) -> dict[str, Any]:
        return deepcopy(self.settings)
