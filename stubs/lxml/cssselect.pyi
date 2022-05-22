import cssselect as external_cssselect
from . import etree
from _typeshed import Incomplete

SelectorSyntaxError: Incomplete
ExpressionError: Incomplete
SelectorError: Incomplete

class LxmlTranslator(external_cssselect.GenericTranslator):
    def xpath_contains_function(self, xpath, function): ...

class LxmlHTMLTranslator(LxmlTranslator, external_cssselect.HTMLTranslator): ...

class CSSSelector(etree.XPath):
    css: Incomplete
    def __init__(self, css, namespaces: Incomplete | None = ..., translator: str = ...) -> None: ...
