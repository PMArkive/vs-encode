from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from .types import P, R
from .util import MPath


def inputs_are_existing_files(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to check whether the given FilePath arguments point to existing files.

    This is not safe lol. Only use if you expect every argument to be a path and not a regular string.
    """
    assert func

    @wraps(func)
    def check(*args: P.args, **kwargs: P.kwargs) -> Any:
        for f in args:
            MPath.check_file_exists(f)

        for f in list(kwargs):
            MPath.check_file_exists(f)

        return func(*args, **kwargs)

    return check
