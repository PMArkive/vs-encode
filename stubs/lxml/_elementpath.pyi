from _typeshed import Incomplete
from collections.abc import Generator

xpath_tokenizer_re: Incomplete

def xpath_tokenizer(pattern, namespaces: Incomplete | None = ...) -> Generator[Incomplete, None, None]: ...
def prepare_child(next, token): ...
def prepare_star(next, token): ...
def prepare_self(next, token): ...
def prepare_descendant(next, token): ...
def prepare_parent(next, token): ...
def prepare_predicate(next, token): ...

ops: Incomplete

def iterfind(elem, path, namespaces: Incomplete | None = ...): ...
def find(elem, path, namespaces: Incomplete | None = ...): ...
def findall(elem, path, namespaces: Incomplete | None = ...): ...
def findtext(elem, path, default: Incomplete | None = ..., namespaces: Incomplete | None = ...): ...
