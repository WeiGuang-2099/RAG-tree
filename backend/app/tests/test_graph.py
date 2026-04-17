from app.services.graph_service import GraphService


def test_add_node():
    gs = GraphService()
    gs.add_node("n1", "main", "Function", "main.py", 1, 10, "def main(): pass")
    node = gs.get_node("n1")
    assert node is not None
    assert node["name"] == "main"
    assert node["type"] == "Function"


def test_add_edge():
    gs = GraphService()
    gs.add_node("n1", "main", "Function", "main.py", 1, 10, "")
    gs.add_node("n2", "helper", "Function", "util.py", 1, 5, "")
    gs.add_edge("n1", "n2", "calls")
    full = gs.get_full_graph()
    assert len(full["edges"]) == 1
    assert full["edges"][0]["type"] == "calls"


def test_get_neighbors():
    gs = GraphService()
    gs.add_node("a", "A", "Module", "a.py", 1, 1, "")
    gs.add_node("b", "B", "Module", "b.py", 1, 1, "")
    gs.add_node("c", "C", "Module", "c.py", 1, 1, "")
    gs.add_edge("a", "b", "imports")
    gs.add_edge("b", "c", "imports")
    result = gs.get_neighbors("a", depth=1)
    node_ids = [n["id"] for n in result["nodes"]]
    assert "a" in node_ids
    assert "b" in node_ids


def test_get_neighbors_depth_2():
    gs = GraphService()
    gs.add_node("a", "A", "Module", "a.py", 1, 1, "")
    gs.add_node("b", "B", "Module", "b.py", 1, 1, "")
    gs.add_node("c", "C", "Module", "c.py", 1, 1, "")
    gs.add_edge("a", "b", "imports")
    gs.add_edge("b", "c", "imports")
    result = gs.get_neighbors("a", depth=2)
    node_ids = [n["id"] for n in result["nodes"]]
    assert "c" in node_ids


def test_find_path():
    gs = GraphService()
    gs.add_node("a", "A", "Module", "a.py", 1, 1, "")
    gs.add_node("b", "B", "Module", "b.py", 1, 1, "")
    gs.add_node("c", "C", "Module", "c.py", 1, 1, "")
    gs.add_edge("a", "b", "imports")
    gs.add_edge("b", "c", "imports")
    path = gs.find_path("a", "c")
    assert path == ["a", "b", "c"]


def test_find_path_no_path():
    gs = GraphService()
    gs.add_node("a", "A", "Module", "a.py", 1, 1, "")
    gs.add_node("b", "B", "Module", "b.py", 1, 1, "")
    path = gs.find_path("a", "b")
    assert path is None


def test_get_stats():
    gs = GraphService()
    gs.add_node("n1", "A", "Module", "a.py", 1, 1, "")
    gs.add_node("n2", "B", "Module", "b.py", 1, 1, "")
    gs.add_edge("n1", "n2", "imports")
    stats = gs.get_stats()
    assert stats["node_count"] == 2
    assert stats["edge_count"] == 1
    assert isinstance(stats["density"], float)
    assert stats["is_dag"] is True


def test_get_stats_with_cycle():
    gs = GraphService()
    gs.add_node("a", "A", "Module", "a.py", 1, 1, "")
    gs.add_node("b", "B", "Module", "b.py", 1, 1, "")
    gs.add_edge("a", "b", "imports")
    gs.add_edge("b", "a", "imports")
    stats = gs.get_stats()
    assert stats["is_dag"] is False


def test_get_full_graph_empty():
    gs = GraphService()
    result = gs.get_full_graph()
    assert result["nodes"] == []
    assert result["edges"] == []


def test_get_node_not_found():
    gs = GraphService()
    assert gs.get_node("nonexistent") is None
