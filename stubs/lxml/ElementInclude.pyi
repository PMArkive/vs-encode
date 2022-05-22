from _typeshed import Incomplete
from lxml import etree as etree

XINCLUDE: str
XINCLUDE_INCLUDE: Incomplete
XINCLUDE_FALLBACK: Incomplete
XINCLUDE_ITER_TAG: Incomplete
DEFAULT_MAX_INCLUSION_DEPTH: int

class FatalIncludeError(etree.LxmlSyntaxError): ...
class LimitedRecursiveIncludeError(FatalIncludeError): ...

def default_loader(href, parse, encoding: Incomplete | None = ...): ...
def include(elem, loader: Incomplete | None = ..., base_url: Incomplete | None = ..., max_depth=...) -> None: ...
