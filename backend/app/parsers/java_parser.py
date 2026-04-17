"""Java parser using regex-based approach.

Note: For production use, consider using tree-sitter-java or javalang for proper AST parsing.
"""

import re
from typing import Any

from app.parsers.base import BaseParser


class JavaParser(BaseParser):
    """Parse Java source code into graph nodes and edges."""

    CLASS_PATTERN = re.compile(
        r"(?:public|private|protected)?\s*(?:abstract\s+)?(?:class|interface|enum)\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?",
        re.MULTILINE,
    )
    METHOD_PATTERN = re.compile(
        r"(?:public|private|protected)?\s*(?:static\s+)?(?:abstract\s+)?(?:synchronized\s+)?(?:<[^>]+>\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(",
        re.MULTILINE,
    )
    IMPORT_PATTERN = re.compile(
        r"import\s+(?:static\s+)?([\w.]+)",
        re.MULTILINE,
    )

    def parse(self, source_code: str) -> dict[str, Any]:
        nodes = []
        edges = []

        # Extract imports
        imports: list[str] = self.IMPORT_PATTERN.findall(source_code)
        for imp in imports:
            class_name = imp.split(".")[-1]
            nodes.append(
                self._make_node(
                    name=class_name,
                    node_type="Module",
                    start_line=self._get_line_number(source_code, imp),
                    end_line=self._get_line_number(source_code, imp),
                    source_code="",
                )
            )

        # Extract class/interface/enum definitions
        class_names: list[str] = []
        for match in self.CLASS_PATTERN.finditer(source_code):
            class_name = match.group(1)
            parent_class = match.group(2)
            interfaces = match.group(3)

            class_names.append(class_name)
            start = self._get_line_number(source_code, match.group(0))
            nodes.append(
                self._make_node(
                    name=class_name,
                    node_type="Class",
                    start_line=start,
                    end_line=start,
                    source_code=match.group(0),
                )
            )

            if parent_class:
                edges.append(
                    self._make_edge(
                        source=class_name,
                        target=parent_class,
                        edge_type="inherits",
                    )
                )

            if interfaces:
                for iface in interfaces.split(","):
                    iface = iface.strip()
                    if iface:
                        edges.append(
                            self._make_edge(
                                source=class_name,
                                target=iface,
                                edge_type="implements",
                            )
                        )

        # Extract method definitions
        method_names: list[str] = []
        for match in self.METHOD_PATTERN.finditer(source_code):
            return_type = match.group(1)
            method_name = match.group(2)
            # Filter out keywords that look like methods
            if return_type in ("if", "while", "for", "switch", "catch", "return"):
                continue
            method_names.append(method_name)
            start = self._get_line_number(source_code, match.group(0))
            nodes.append(
                self._make_node(
                    name=method_name,
                    node_type="Function",
                    start_line=start,
                    end_line=start,
                    source_code=match.group(0),
                )
            )

        return {"nodes": nodes, "edges": edges}

    def _get_line_number(self, source: str, substring: str) -> int:
        idx = source.find(substring)
        if idx == -1:
            return 0
        return source[:idx].count("\n") + 1
