from __future__ import annotations

from typing import Any, Callable, ParamSpec, TypeVar

__all__ = [
    'F',
    'P', 'R'
]


# Function Type
F = TypeVar('F', bound=Callable[..., Any])
P = ParamSpec('P')
R = TypeVar('R')
