from _typeshed import Incomplete

basestring = str
unicode = str

class ElementMaker:
    def __init__(self, typemap: Incomplete | None = ..., namespace: Incomplete | None = ..., nsmap: Incomplete | None = ..., makeelement: Incomplete | None = ...) -> None: ...
    def __call__(self, tag, *children, **attrib): ...
    def __getattr__(self, tag): ...

E: Incomplete
