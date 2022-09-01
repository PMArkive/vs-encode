from typing import Any, cast
from pathlib import Path
from functools import wraps
import os

from .types import F


def inputs_are_existing_files(func: F) -> F:
    """
    Decorator to check whether the given FilePath arguments point to existing files.

    This is not safe lol. Only use if you expect every argument to be a path and not a regular string.
    """
    assert func

    @wraps(func)
    def check(*args: Any, **kwargs: Any) -> Any:
        arglist = list(args)

        for f in arglist:
            check_file_exists(f)

        for f in list(kwargs):
            check_file_exists(f)

        return func(*arglist, **kwargs)

    return cast(F, check)


def mpath_is_existing_file(func: F) -> F:
    """Decorator to check whether the MPath points to a file."""
    assert func

    @wraps(func)
    def check(self: Any, *args: Any, **kwargs: Any) -> Any:
        check_file_exists(self.to_str())

        return func(self, *args, **kwargs)

    return cast(F, check)


def check_file_exists(file: os.PathLike[str] | Path | str) -> None:
    if not Path(file).is_file():
        raise FileNotFoundError(f"{file} could not be found!")
