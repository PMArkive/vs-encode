from ..config import FileInfo
from ..types import AnyPath
from .abstract import Tool
from typing import Any, Dict, List, Optional

class BasicTool(Tool):
    file: Optional[FileInfo]
    def __init__(self, binary: AnyPath, settings: Union[AnyPath, List[str], Dict[str, Any]], file: Optional[FileInfo] = ...) -> None: ...
    def run(self) -> None: ...
    def set_variable(self) -> Dict[str, Any]: ...
