from abc import ABC, ABCMeta
from typing import Any

class SingletonMeta(ABCMeta):
    def __call__(cls, *args: Any, **kwargs: Any) -> Any: ...

class Singleton(ABC, metaclass=SingletonMeta): ...
