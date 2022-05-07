from _typeshed import Incomplete
from langcodes import Language
from typing import Optional

class Lang:
    name: str
    ietf: str
    iso639: str
    def __init__(self, language: Language, *, iso639_variant: str = ...) -> None: ...
    @classmethod
    def make(cls, ietf: Optional[str]) -> Lang: ...

FRENCH: Incomplete
ENGLISH: Incomplete
JAPANESE: Incomplete
UNDEFINED: Incomplete
