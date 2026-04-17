"""Go parser using regex-based approach.

Note: For production use, consider using tree-sitter-go for proper AST parsing.
"""

import re
from typing import Any

from app.parsers.base import BaseParser


class GoParser(BaseParser):
    """Parse Go source code into graph nodes and edges."""

    FUNC_PATTERN = re.compile(
        r"func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(",
        re.MULTILINE,
    )
    TYPE_PATTERN = re.compile(
        r"type\s+(\w+)\s+(struct|interface)",
        re.MULTILINE,
    )
    IMPORT_PATTERN = re.compile(
        r'import\s+(?:\(\s*(.*?)\s*\)|"([^"]+)")',
        re.MULTILINE | re.DOTALL,
    )
    CALL_PATTERN = re.compile(r"(\w+)\.\w+\s*\(", re.MULTILINE)

    def parse(self, source_code: str) -> dict[str, Any]:
        nodes = []
        edges = []

        # Extract imports
        imports: list[str] = []
        for match in self.IMPORT_PATTERN.finditer(source_code):
            if match.group(1):
                # Multi-line import block
                for imp in re.findall(r'"([^"]+)"', match.group(1)):
                    imports.append(imp)
            elif match.group(2):
                imports.append(match.group(2))

        for imp in imports:
            module_name = imp.split("/")[-1]
            nodes.append(
                self._make_node(
                    name=module_name,
                    node_type="Module",
                    start_line=self._get_line_number(source_code, imp),
                    end_line=self._get_line_number(source_code, imp),
                    source_code="",
                )
            )

        # Extract type definitions
        type_names: list[str] = []
        for match in self.TYPE_PATTERN.finditer(source_code):
            type_name = match.group(1)
            type_names.append(type_name)
            start = self._get_line_number(source_code, match.group(0))
            nodes.append(
                self._make_node(
                    name=type_name,
                    node_type="Class",
                    start_line=start,
                    end_line=start,
                    source_code=match.group(0),
                )
            )

        # Extract function definitions
        func_names: list[str] = []
        for match in self.FUNC_PATTERN.finditer(source_code):
            func_name = match.group(1)
            func_names.append(func_name)
            start = self._get_line_number(source_code, match.group(0))
            nodes.append(
                self._make_node(
                    name=func_name,
                    node_type="Function",
                    start_line=start,
                    end_line=start,
                    source_code=match.group(0),
                )
            )

        # Create edges for package method calls
        known_names = set(func_names) | set(type_names)
        for match in self.CALL_PATTERN.finditer(source_code):
            pkg_name = match.group(1)
            if pkg_name in known_names or pkg_name in {imp.split("/")[-1] for imp in imports}:
                edges.append(
                    self._make_edge(
                        source=match.group(0).split("(")[0],
                        target=pkg_name,
                        edge_type="calls",
                    )
                )

        return {"nodes": nodes, "edges": edges}

    def _get_line_number(self, source: str, substring: str) -> int:
        idx = source.find(substring)
        if idx == -1:
            return 0
        return source[:idx].count("\n") + 1
