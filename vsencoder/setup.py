"""
Basic classes and functions for setting up the Encoder.

These are run automatically when necessary,
but are recommended to run prior to running Encoder.
"""
import os
import sys
from configparser import ConfigParser
from glob import glob
from pathlib import Path
from typing import Any, Dict, List

__all__: List[str] = [
    'IniSetup'
]


caller_name = sys.argv[0]


class IniSetup:
    """
    Class that handles all the basic filename settings of the project,
    including parsing and generating ini files.
    """
    def __init__(self, custom_name: str | None = None,
                 custom_args: Dict[str, Any] = {},
                 showname_args: Dict[str, Any] = {},
                 custom_output_name: str | None = None) -> None:
        """
        Obtain the settings from the config.ini file (or custom name) if it exists, else create ini file.

        :param custom_name:     Custom name for ini file
        :param custom_args:     Settings to override
        """
        config = ConfigParser()
        config_name = custom_name or 'config.ini'

        if not os.path.exists(config_name):
            config['SETTINGS'] = {
                'bdmv_dir': "BDMV",
                'reserve_core': False,
                'show_name': self.get_show_name(caller_name, **showname_args)[0],
                'output_dir': "Premux",
                'output_name': custom_output_name or "$$_@@ (Premux)"
            }

            with open(config_name, 'w') as config_file:
                config.write(config_file)

        config.read(config_name)
        settings = config['SETTINGS']

        if custom_args:
            for k, v in custom_args:
                settings[k] = v

        for key in settings:
            setattr(self, key, settings[key])

    def get_show_name(self, file_name: str = caller_name, key: str = '_', parents: int | None = None) -> List[str]:
        """
        Finds the show's name from the file name. Also returns the episode number.

        :param file_name:       Name of the file
        :param key:             Key for splitting the file name. Defaults to `_`
        :param parents:         How many of the parents should be spliced together for the regular file name.
                                See this as total number of _'s in file_name - 1.
                                Default: Auto-calculate.

        :returns:               List of strings with the show name and episode number.
        """
        _parents = parents or file_name.count(key)

        file_name = os.path.basename(file_name).split(key)
        file_name[-1] = os.path.splitext(file_name[-1])[0]

        if _parents > 1:
            try:  # Check if final split is the episode number
                int(file_name[-1])
            except ValueError as e:
                raise ValueError("get_show_name: 'Please make sure your file name is structured like so: "
                                 f"\"showname{key}ep\" current: {os.path.splitext(caller_name)[0]}. "
                                 "This function expects you to follow this pattern to properly parse "
                                 "all the information it needs!\n", e)

            file_name[0] = ''.join(f'{sn}{key}' for sn in file_name[:-_parents])

        return file_name

    def parse_name(self, key_name: str = '$$', key_ep: str = '@@', key_version: str = '&&') -> Path:
        """
        Converts a string to a proper path based on what's in the config file and __file__ name.

        :param key_name:        Key that indicates where in the filename the show's name should be injected.
        :param key_ep:          Key that indicates where in the filename the episode should be injected.
        :param key_version:     Key that indicates where in the filename the encode version should be injected.

        :returns:               Path object with the output name and directory.
        """
        file_name = self.get_show_name()

        output_name = str(self.output_name).replace(key_name, file_name[0]).replace(key_ep, file_name[-1])

        if key_version in output_name:
            version: int = len(glob(f"{self.output_dir}/*{file_name[-1]}*.*", recursive=False)) + 1
            output_name = output_name.replace(key_version, f"v{version}")

        return Path(self.output_dir + '/' + os.path.basename(output_name) + '.mkv')


def init_project(project_name: str = None) -> None:
    """
    Creates basic files used in conjunction with the rest of this package.
    """
    IniSetup()
    # TODO: Create basic encoding settings files
    # TODO: Create XML for AAC encoding
