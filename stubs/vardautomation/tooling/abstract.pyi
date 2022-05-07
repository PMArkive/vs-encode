import abc
from ..types import AnyPath
from ..vpathlib import VPath
from abc import ABC, abstractmethod
from typing import Any, Dict, List, NoReturn

class Tool(ABC, metaclass=abc.ABCMeta):
    binary: VPath
    params: List[str]
    def __init__(self, binary: AnyPath, settings: Union[AnyPath, List[str], Dict[str, Any]]) -> None: ...
    @abstractmethod
    def run(self) -> Union[None, NoReturn]: ...
    @abstractmethod
    def set_variable(self) -> Dict[str, Any]: ...
