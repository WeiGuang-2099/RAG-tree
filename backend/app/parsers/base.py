"""Base AST parser class for all language parsers."""

from abc import ABC, abstractmethod
from typing import Any


class BaseParser(ABC):
    """Abstract base class for code parsers."""

    @abstractmethod
    def parse(self, source_code: str) -> dict[str, Any]:
        """Parse source code and extract nodes and edges.

        Returns:
            dict with keys:
                - nodes: list of node dicts
                - edges: list of edge dicts
        """
        ...

    def _make_node(
        self,
        name: str,
        node_type: str,
        start_line: int,
        end_line: int,
        source_code: str,
    ) -> dict:
        return {
            "name": name,
            "type": node_type,
            "start_line": start_line,
            "end_line": end_line,
            "source_code": source_code,
        }

    def _make_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
    ) -> dict:
        return {
            "source": source,
            "target": target,
            "type": edge_type,
        }
