"""Parser dispatch service - routes files to appropriate language parsers."""

from app.parsers.base import BaseParser
from app.parsers.python_parser import PythonParser
from app.parsers.javascript_parser import JavaScriptParser
from app.parsers.vue_parser import VueParser


PARSER_REGISTRY: dict[str, type[BaseParser]] = {
    "py": PythonParser,
    "js": JavaScriptParser,
    "ts": JavaScriptParser,
    "tsx": JavaScriptParser,
    "jsx": JavaScriptParser,
    "vue": VueParser,
}


def get_parser(language: str) -> BaseParser:
    """Get the appropriate parser for a given language."""
    parser_cls = PARSER_REGISTRY.get(language)
    if parser_cls is None:
        raise ValueError(f"No parser available for language: {language}")
    return parser_cls()


def parse_file(file_path: str, source_code: str, language: str) -> dict:
    """Parse a file and return extracted nodes and edges."""
    parser = get_parser(language)
    result = parser.parse(source_code)
    result["file_path"] = file_path
    result["language"] = language
    return result
