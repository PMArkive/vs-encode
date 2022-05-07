import loguru
from ..types import T as T
from .core import LogLevel as LogLevel
from typing import Any, Callable, NoReturn

def close_and_reverse_tags(colour_tags: str) -> str: ...
def loguru_format(record: loguru.Record) -> str: ...
def sys_exit(_: BaseException) -> NoReturn: ...

class _log_func_wrapper:
    name: str
    no: int
    colour: str
    colour_close: str
    def __call__(self, *args: Any, **kwargs: Any) -> T: ...

def add_log_attribute(log_level: LogLevel) -> Callable[[Callable[..., T]], _log_func_wrapper[T]]: ...
