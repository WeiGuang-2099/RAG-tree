"""Python AST parser using the built-in ast module."""

import ast
from typing import Any

from app.parsers.base import BaseParser


class PythonParser(BaseParser):
    """Parse Python source code into graph nodes and edges."""

    def parse(self, source_code: str) -> dict[str, Any]:
        nodes = []
        edges = []

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return {"nodes": nodes, "edges": edges}

        # Track imports for edge creation
        imports: dict[str, str] = {}
        class_defs: dict[str, list[str]] = {}
        function_defs: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = alias.name
                    nodes.append(
                        self._make_node(
                            name=name,
                            node_type="Module",
                            start_line=node.lineno,
                            end_line=node.end_lineno or node.lineno,
                            source_code="",
                        )
                    )

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = f"{module_name}.{alias.name}"
                    nodes.append(
                        self._make_node(
                            name=name,
                            node_type="Module",
                            start_line=node.lineno,
                            end_line=node.end_lineno or node.lineno,
                            source_code="",
                        )
                    )

            elif isinstance(node, ast.ClassDef):
                class_defs[node.name] = []
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                for base_name in bases:
                    edges.append(
                        self._make_edge(
                            source=node.name,
                            target=base_name,
                            edge_type="inherits",
                        )
                    )
                nodes.append(
                    self._make_node(
                        name=node.name,
                        node_type="Class",
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        source_code=ast.get_source_segment(source_code, node) or "",
                    )
                )

            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                function_defs.append(node.name)
                nodes.append(
                    self._make_node(
                        name=node.name,
                        node_type="Function",
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        source_code=ast.get_source_segment(source_code, node) or "",
                    )
                )

        # Create edges: function calls within functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func_name = self._get_call_name(child)
                        if func_name:
                            edges.append(
                                self._make_edge(
                                    source=node.name,
                                    target=func_name,
                                    edge_type="calls",
                                )
                            )

        return {"nodes": nodes, "edges": edges}

    def _get_call_name(self, call: ast.Call) -> str:
        """Extract the function name from a Call node."""
        if isinstance(call.func, ast.Name):
            return call.func.id
        elif isinstance(call.func, ast.Attribute):
            return call.func.attr
        return ""
