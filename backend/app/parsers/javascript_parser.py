"""JavaScript/TypeScript parser using regex-based approach.

Note: For production use, consider integrating tree-sitter or @babel/parser
via a subprocess for proper AST parsing of JS/TS/JSX/TSX files.
"""

import re
from typing import Any

from app.parsers.base import BaseParser


class JavaScriptParser(BaseParser):
    """Parse JavaScript/TypeScript source code into graph nodes and edges."""

    # Patterns for function declarations
    FUNC_DECL_PATTERN = re.compile(
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
        re.MULTILINE,
    )
    ARROW_FUNC_PATTERN = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(",
        re.MULTILINE,
    )
    CLASS_PATTERN = re.compile(
        r"(?:export\s+)?(?:default\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?",
        re.MULTILINE,
    )
    IMPORT_PATTERN = re.compile(
        r"(?:import|export)\s+(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    CALL_PATTERN = re.compile(r"(\w+)\s*\(", re.MULTILINE)

    def parse(self, source_code: str) -> dict[str, Any]:
        nodes = []
        edges = []

        # Extract imports
        imports: list[str] = self.IMPORT_PATTERN.findall(source_code)
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

        # Extract class definitions
        class_matches = self.CLASS_PATTERN.finditer(source_code)
        for match in class_matches:
            class_name = match.group(1)
            parent_class = match.group(2)
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

        # Extract function declarations
        func_names: list[str] = []
        for match in self.FUNC_DECL_PATTERN.finditer(source_code):
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

        # Extract arrow functions
        for match in self.ARROW_FUNC_PATTERN.finditer(source_code):
            func_name = match.group(1)
            if func_name not in func_names:
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

        # Extract function calls and create edges
        known_names = set(func_names) | {m.group(1) for m in self.CLASS_PATTERN.finditer(source_code)}
        for match in self.CALL_PATTERN.finditer(source_code):
            called_name = match.group(1)
            if called_name in known_names and called_name not in func_names:
                # This is a class instantiation or method call
                for func_name in func_names:
                    # Simple heuristic: if the call appears inside a function scope
                    pass

        return {"nodes": nodes, "edges": edges}

    def _get_line_number(self, source: str, substring: str) -> int:
        """Get the 1-based line number of a substring in source."""
        idx = source.find(substring)
        if idx == -1:
            return 0
        return source[:idx].count("\n") + 1
