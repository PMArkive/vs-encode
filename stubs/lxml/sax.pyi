from _typeshed import Incomplete
from lxml import etree as etree
from lxml.etree import Comment as Comment, ElementTree as ElementTree, ProcessingInstruction as ProcessingInstruction, SubElement as SubElement
from xml.sax.handler import ContentHandler

class SaxError(etree.LxmlError): ...

class ElementTreeContentHandler(ContentHandler):
    def __init__(self, makeelement: Incomplete | None = ...) -> None: ...
    etree: Incomplete
    def setDocumentLocator(self, locator) -> None: ...
    def startDocument(self) -> None: ...
    def endDocument(self) -> None: ...
    def startPrefixMapping(self, prefix, uri) -> None: ...
    def endPrefixMapping(self, prefix) -> None: ...
    def startElementNS(self, ns_name, qname, attributes: Incomplete | None = ...) -> None: ...
    def processingInstruction(self, target, data) -> None: ...
    def endElementNS(self, ns_name, qname) -> None: ...
    def startElement(self, name, attributes: Incomplete | None = ...) -> None: ...
    def endElement(self, name) -> None: ...
    def characters(self, data) -> None: ...
    ignorableWhitespace: Incomplete

class ElementTreeProducer:
    def __init__(self, element_or_tree, content_handler) -> None: ...
    def saxify(self) -> None: ...

def saxify(element_or_tree, content_handler): ...