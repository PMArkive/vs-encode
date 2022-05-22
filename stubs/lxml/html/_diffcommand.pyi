from .diff import htmldiff as htmldiff
from _typeshed import Incomplete

description: str
parser: Incomplete

def main(args: Incomplete | None = ...): ...
def read_file(filename): ...

body_start_re: Incomplete
body_end_re: Incomplete

def split_body(html): ...
def annotate(options, args) -> None: ...
