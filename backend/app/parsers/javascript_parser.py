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
        class_names = {m.group(1) for m in self.CLASS_PATTERN.finditer(source_code)}

        # Build function scope map: (func_name, start_pos, end_pos)
        func_scopes = []
        for match in self.FUNC_DECL_PATTERN.finditer(source_code):
            func_name = match.group(1)
            func_start = match.start()
            func_body_start = source_code.find("{", func_start)
            if func_body_start == -1:
                continue
            brace_count = 0
            func_body_end = func_body_start
            for i, char in enumerate(source_code[func_body_start:], func_body_start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        func_body_end = i + 1
                        break
            func_scopes.append((func_name, func_body_start, func_body_end))

        # Also handle arrow functions with their scope
        for match in self.ARROW_FUNC_PATTERN.finditer(source_code):
            func_name = match.group(1)
            func_start = match.start()
            # Arrow function body: either block { ... } or expression
            arrow_pos = source_code.find("=>", func_start)
            if arrow_pos == -1:
                continue
            after_arrow = arrow_pos + 2
            while after_arrow < len(source_code) and source_code[after_arrow] in " \t":
                after_arrow += 1
            if after_arrow < len(source_code) and source_code[after_arrow] == "{":
                # Block body
                brace_count = 0
                func_body_start = after_arrow
                func_body_end = func_body_start
                for i, char in enumerate(source_code[func_body_start:], func_body_start):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            func_body_end = i + 1
                            break
                func_scopes.append((func_name, func_body_start, func_body_end))
            else:
                # Expression body - find end of line or semicolon
                expr_start = after_arrow
                expr_end = source_code.find(";", expr_start)
                if expr_end == -1:
                    newline_pos = source_code.find("\n", expr_start)
                    if newline_pos == -1:
                        expr_end = len(source_code)
                    else:
                        expr_end = newline_pos
                else:
                    expr_end += 1
                func_scopes.append((func_name, expr_start, expr_end))

        # Track edges to avoid duplicates
        existing_edges = set()
        for edge in edges:
            existing_edges.add((edge.get("source"), edge.get("target"), edge.get("type")))

        # Find function calls within each function's scope
        for func_name, body_start, body_end in func_scopes:
            func_body = source_code[body_start:body_end]
            for called_name in known_names:
                if called_name == func_name:
                    continue  # Skip self-calls
                # Look for calls to other known functions/classes
                call_pattern = re.compile(rf"\b{re.escape(called_name)}\s*\(")
                if call_pattern.search(func_body):
                    edge_type = "instantiates" if called_name in class_names else "calls"
                    edge_key = (func_name, called_name, edge_type)
                    if edge_key not in existing_edges:
                        edges.append(
                            self._make_edge(
                                source=func_name,
                                target=called_name,
                                edge_type=edge_type,
                            )
                        )
                        existing_edges.add(edge_key)

        return {"nodes": nodes, "edges": edges}

    def _get_line_number(self, source: str, substring: str) -> int:
        """Get the 1-based line number of a substring in source."""
        idx = source.find(substring)
        if idx == -1:
            return 0
        return source[:idx].count("\n") + 1
