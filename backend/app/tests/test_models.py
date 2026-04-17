from app.models.project import Project, File, CodeNode, CodeEdge
from datetime import datetime


def test_project_creation():
    project = Project(name="test-project")
    assert project.name == "test-project"
    assert project.status == "pending"
    assert isinstance(project.created_at, datetime)


def test_file_creation():
    f = File(project_id=1, file_path="main.py", language="py")
    assert f.project_id == 1
    assert f.file_path == "main.py"
    assert f.language == "py"
    assert f.status == "pending"


def test_code_node_creation():
    node = CodeNode(
        project_id=1,
        file_id=1,
        node_type="Function",
        name="hello",
        start_line=1,
        end_line=5,
        source_code="def hello(): pass",
    )
    assert node.node_type == "Function"
    assert node.name == "hello"
    assert node.start_line == 1
    assert node.end_line == 5


def test_code_edge_creation():
    edge = CodeEdge(
        project_id=1,
        source_node_id=1,
        target_node_id=2,
        edge_type="calls",
    )
    assert edge.edge_type == "calls"
    assert edge.source_node_id == 1
    assert edge.target_node_id == 2
