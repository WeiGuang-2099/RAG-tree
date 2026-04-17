"""NetworkX graph construction service."""

import networkx as nx
from typing import Optional


class GraphService:
    """Builds and manages code dependency graphs using NetworkX."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(
        self,
        node_id: str,
        name: str,
        node_type: str,
        file_path: str,
        start_line: int,
        end_line: int,
        source_code: str = "",
    ):
        self.graph.add_node(
            node_id,
            name=name,
            type=node_type,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            source_code=source_code,
        )

    def add_edge(self, source_id: str, target_id: str, edge_type: str):
        self.graph.add_edge(source_id, target_id, type=edge_type)

    def get_neighbors(self, node_id: str, depth: int = 1) -> dict:
        """Get neighboring nodes within a given depth."""
        visited = {node_id}
        current_level = {node_id}

        for _ in range(depth):
            next_level = set()
            for nid in current_level:
                for neighbor in self.graph.predecessors(nid):
                    if neighbor not in visited:
                        next_level.add(neighbor)
                        visited.add(neighbor)
                for neighbor in self.graph.successors(nid):
                    if neighbor not in visited:
                        next_level.add(neighbor)
                        visited.add(neighbor)
            current_level = next_level

        subgraph = self.graph.subgraph(visited)
        return self._graph_to_dict(subgraph)

    def get_full_graph(self) -> dict:
        return self._graph_to_dict(self.graph)

    def get_node(self, node_id: str) -> Optional[dict]:
        if node_id not in self.graph:
            return None
        node_data = self.graph.nodes[node_id]
        return {
            "id": node_id,
            **node_data,
        }

    def find_path(self, source_id: str, target_id: str) -> Optional[list[str]]:
        """Find shortest path between two nodes."""
        try:
            return nx.shortest_path(self.graph, source_id, target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_stats(self) -> dict:
        """Get graph statistics."""
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_dag": nx.is_directed_acyclic_graph(self.graph),
        }

    def _graph_to_dict(self, g: nx.DiGraph) -> dict:
        nodes = []
        for node_id, data in g.nodes(data=True):
            nodes.append({"id": node_id, **data})

        edges = []
        for source, target, data in g.edges(data=True):
            edges.append({"source": source, "target": target, **data})

        return {"nodes": nodes, "edges": edges}
