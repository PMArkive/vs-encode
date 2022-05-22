from . import defs as defs
from .. import etree
from ._setmixin import SetMixin
from _typeshed import Incomplete
from collections import MutableMapping, MutableSet
from collections.abc import Generator

unicode = str

class Classes(MutableSet):
    def __init__(self, attributes) -> None: ...
    def add(self, value) -> None: ...
    def discard(self, value) -> None: ...
    def remove(self, value) -> None: ...
    def __contains__(self, name): ...
    def __iter__(self): ...
    def __len__(self): ...
    def update(self, values) -> None: ...
    def toggle(self, value): ...

class HtmlMixin:
    def set(self, key, value: Incomplete | None = ...) -> None: ...
    @property
    def classes(self): ...
    @classes.setter
    def classes(self, classes) -> None: ...
    @property
    def base_url(self): ...
    @property
    def forms(self): ...
    @property
    def body(self): ...
    @property
    def head(self): ...
    @property
    def label(self): ...
    @label.setter
    def label(self, label) -> None: ...
    def label(self) -> None: ...
    def drop_tree(self) -> None: ...
    def drop_tag(self) -> None: ...
    def find_rel_links(self, rel): ...
    def find_class(self, class_name): ...
    def get_element_by_id(self, id, *default): ...
    def text_content(self): ...
    def cssselect(self, expr, translator: str = ...): ...
    def make_links_absolute(self, base_url: Incomplete | None = ..., resolve_base_href: bool = ..., handle_failures: Incomplete | None = ...): ...
    def resolve_base_href(self, handle_failures: Incomplete | None = ...) -> None: ...
    def iterlinks(self) -> Generator[Incomplete, None, None]: ...
    def rewrite_links(self, link_repl_func, resolve_base_href: bool = ..., base_href: Incomplete | None = ...) -> None: ...

class _MethodFunc:
    name: Incomplete
    copy: Incomplete
    __doc__: Incomplete
    def __init__(self, name, copy: bool = ..., source_class=...) -> None: ...
    def __call__(self, doc, *args, **kw): ...

find_rel_links: Incomplete
find_class: Incomplete
make_links_absolute: Incomplete
resolve_base_href: Incomplete
iterlinks: Incomplete
rewrite_links: Incomplete

class HtmlComment(etree.CommentBase, HtmlMixin): ...

class HtmlElement(etree.ElementBase, HtmlMixin):
    cssselect: Incomplete
    set: Incomplete

class HtmlProcessingInstruction(etree.PIBase, HtmlMixin): ...
class HtmlEntity(etree.EntityBase, HtmlMixin): ...

class HtmlElementClassLookup(etree.CustomElementClassLookup):
    def __init__(self, classes: Incomplete | None = ..., mixins: Incomplete | None = ...) -> None: ...
    def lookup(self, node_type, document, namespace, name): ...

def document_fromstring(html, parser: Incomplete | None = ..., ensure_head_body: bool = ..., **kw): ...
def fragments_fromstring(html, no_leading_text: bool = ..., base_url: Incomplete | None = ..., parser: Incomplete | None = ..., **kw): ...
def fragment_fromstring(html, create_parent: bool = ..., base_url: Incomplete | None = ..., parser: Incomplete | None = ..., **kw): ...
def fromstring(html, base_url: Incomplete | None = ..., parser: Incomplete | None = ..., **kw): ...
def parse(filename_or_url, parser: Incomplete | None = ..., base_url: Incomplete | None = ..., **kw): ...

class FormElement(HtmlElement):
    @property
    def inputs(self): ...
    @property
    def fields(self): ...
    @fields.setter
    def fields(self, value) -> None: ...
    def form_values(self): ...
    @property
    def action(self): ...
    @action.setter
    def action(self, value) -> None: ...
    def action(self) -> None: ...
    @property
    def method(self): ...
    @method.setter
    def method(self, value) -> None: ...

def submit_form(form, extra_values: Incomplete | None = ..., open_http: Incomplete | None = ...): ...

class FieldsDict(MutableMapping):
    inputs: Incomplete
    def __init__(self, inputs) -> None: ...
    def __getitem__(self, item): ...
    def __setitem__(self, item, value) -> None: ...
    def __delitem__(self, item) -> None: ...
    def keys(self): ...
    def __contains__(self, item): ...
    def __iter__(self): ...
    def __len__(self): ...

class InputGetter:
    form: Incomplete
    def __init__(self, form) -> None: ...
    def __getitem__(self, name): ...
    def __contains__(self, name): ...
    def keys(self): ...
    def items(self): ...
    def __iter__(self): ...
    def __len__(self): ...

class InputMixin:
    @property
    def name(self): ...
    @name.setter
    def name(self, value) -> None: ...
    def name(self) -> None: ...

class TextareaElement(InputMixin, HtmlElement):
    @property
    def value(self): ...
    text: Incomplete
    @value.setter
    def value(self, value) -> None: ...
    def value(self) -> None: ...

class SelectElement(InputMixin, HtmlElement):
    @property
    def value(self): ...
    @value.setter
    def value(self, value) -> None: ...
    def value(self) -> None: ...
    @property
    def value_options(self): ...
    @property
    def multiple(self): ...
    @multiple.setter
    def multiple(self, value) -> None: ...

class MultipleSelectOptions(SetMixin):
    select: Incomplete
    def __init__(self, select) -> None: ...
    @property
    def options(self): ...
    def __iter__(self): ...
    def add(self, item) -> None: ...
    def remove(self, item) -> None: ...

class RadioGroup(list):
    @property
    def value(self): ...
    @value.setter
    def value(self, value) -> None: ...
    def value(self) -> None: ...
    @property
    def value_options(self): ...

class CheckboxGroup(list):
    @property
    def value(self): ...
    @value.setter
    def value(self, value) -> None: ...
    def value(self) -> None: ...
    @property
    def value_options(self): ...

class CheckboxValues(SetMixin):
    group: Incomplete
    def __init__(self, group) -> None: ...
    def __iter__(self): ...
    def add(self, value) -> None: ...
    def remove(self, value) -> None: ...

class InputElement(InputMixin, HtmlElement):
    @property
    def value(self): ...
    @value.setter
    def value(self, value) -> None: ...
    def value(self) -> None: ...
    @property
    def type(self): ...
    @type.setter
    def type(self, value) -> None: ...
    @property
    def checkable(self): ...
    @property
    def checked(self): ...
    @checked.setter
    def checked(self, value) -> None: ...

class LabelElement(HtmlElement):
    @property
    def for_element(self): ...
    @for_element.setter
    def for_element(self, other) -> None: ...
    def for_element(self) -> None: ...

def tostring(doc, pretty_print: bool = ..., include_meta_content_type: bool = ..., encoding: Incomplete | None = ..., method: str = ..., with_tail: bool = ..., doctype: Incomplete | None = ...): ...
def open_in_browser(doc, encoding: Incomplete | None = ...) -> None: ...

class HTMLParser(etree.HTMLParser):
    def __init__(self, **kwargs) -> None: ...

class XHTMLParser(etree.XMLParser):
    def __init__(self, **kwargs) -> None: ...

def Element(*args, **kw): ...
