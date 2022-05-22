from _typeshed import Incomplete

unichr = chr
unicode = str

class Cleaner:
    scripts: bool
    javascript: bool
    comments: bool
    style: bool
    inline_style: Incomplete
    links: bool
    meta: bool
    page_structure: bool
    processing_instructions: bool
    embedded: bool
    frames: bool
    forms: bool
    annoying_tags: bool
    remove_tags: Incomplete
    allow_tags: Incomplete
    kill_tags: Incomplete
    remove_unknown_tags: bool
    safe_attrs_only: bool
    safe_attrs: Incomplete
    add_nofollow: bool
    host_whitelist: Incomplete
    whitelist_tags: Incomplete
    def __init__(self, **kw) -> None: ...
    def __call__(self, doc) -> None: ...
    def allow_follow(self, anchor): ...
    def allow_element(self, el): ...
    def allow_embedded_url(self, el, url): ...
    def kill_conditional_comments(self, doc): ...
    def clean_html(self, html): ...

clean: Incomplete
clean_html: Incomplete

def autolink(el, link_regexes=..., avoid_elements=..., avoid_hosts=..., avoid_classes=...) -> None: ...
def autolink_html(html, *args, **kw): ...
def word_break(el, max_width: int = ..., avoid_elements=..., avoid_classes=..., break_character=...) -> None: ...
def word_break_html(html, *args, **kw): ...
