from _typeshed import Incomplete
from lxml import etree as _etree

unicode = str
basestring = str
extract_xsd: Incomplete
extract_rng: Incomplete
iso_dsdl_include: Incomplete
iso_abstract_expand: Incomplete
iso_svrl_for_xslt1: Incomplete
svrl_validation_errors: Incomplete
schematron_schema_valid: Incomplete

def stylesheet_params(**kwargs): ...

class Schematron(_etree._Validator):
    ASSERTS_ONLY: Incomplete
    ASSERTS_AND_REPORTS: Incomplete
    def __init__(self, etree: Incomplete | None = ..., file: Incomplete | None = ..., include: bool = ..., expand: bool = ..., include_params=..., expand_params=..., compile_params=..., store_schematron: bool = ..., store_xslt: bool = ..., store_report: bool = ..., phase: Incomplete | None = ..., error_finder=...) -> None: ...
    def __call__(self, etree): ...
    @property
    def schematron(self): ...
    @property
    def validator_xslt(self): ...
    @property
    def validation_report(self): ...
