from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models.project import CodeNode, CodeEdge, Project, File as FileModel
from app.services.graph_service import GraphService
from typing import Optional

router = APIRouter(prefix="/api/graph", tags=["graph"])


def _node_to_dict(node: CodeNode, session: Session) -> dict:
    file_record = session.get(FileModel, node.file_id)
    file_path = file_record.file_path if file_record else ""
    return {
        "id": str(node.id),
        "name": node.name,
        "type": node.node_type,
        "file_path": file_path,
        "start_line": node.start_line,
        "end_line": node.end_line,
        "source_code": node.source_code,
    }


@router.get("/nodes/{project_id}")
def get_nodes(
    project_id: int,
    session: Session = Depends(get_session),
    node_type: Optional[str] = Query(None),
):
    """Get all code nodes for a project."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    statement = select(CodeNode).where(CodeNode.project_id == project_id)
    if node_type:
        statement = statement.where(CodeNode.node_type == node_type)

    nodes = session.exec(statement).all()
    return [_node_to_dict(node, session) for node in nodes]


@router.get("/edges/{project_id}")
def get_edges(
    project_id: int,
    session: Session = Depends(get_session),
    edge_type: Optional[str] = Query(None),
):
    """Get all code edges for a project."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    statement = select(CodeEdge).where(CodeEdge.project_id == project_id)
    if edge_type:
        statement = statement.where(CodeEdge.edge_type == edge_type)

    edges = session.exec(statement).all()
    return [
        {
            "source": str(edge.source_node_id),
            "target": str(edge.target_node_id),
            "type": edge.edge_type,
        }
        for edge in edges
    ]


@router.get("/full/{project_id}")
def get_full_graph(
    project_id: int,
    session: Session = Depends(get_session),
):
    """Get full graph data (nodes + edges) for a project."""
    nodes = get_nodes(project_id, session, node_type=None)
    edges = get_edges(project_id, session, edge_type=None)
    return {"nodes": nodes, "edges": edges}


@router.get("/neighbors/{project_id}/{node_id}")
def get_neighbors(
    project_id: int,
    node_id: int,
    session: Session = Depends(get_session),
    depth: int = Query(default=1, ge=1, le=3),
):
    """Get neighboring nodes within a given depth."""
    gs = _build_graph_service(project_id, session)
    return gs.get_neighbors(str(node_id), depth=depth)


@router.get("/path/{project_id}")
def get_path(
    project_id: int,
    from_id: int = Query(..., alias="from"),
    to_id: int = Query(..., alias="to"),
    session: Session = Depends(get_session),
):
    """Find shortest path between two nodes."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    gs = _build_graph_service(project_id, session)
    path = gs.find_path(str(from_id), str(to_id))
    if path is None:
        return {"path": None, "found": False}
    return {"path": path, "found": True}


@router.get("/stats/{project_id}")
def get_stats(
    project_id: int,
    session: Session = Depends(get_session),
):
    """Get graph statistics."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    gs = _build_graph_service(project_id, session)
    return gs.get_stats()


def _build_graph_service(project_id: int, session: Session) -> GraphService:
    """Build an in-memory GraphService from DB data for a project."""
    nodes = session.exec(
        select(CodeNode).where(CodeNode.project_id == project_id)
    ).all()
    edges = session.exec(
        select(CodeEdge).where(CodeEdge.project_id == project_id)
    ).all()

    gs = GraphService()
    node_id_map: dict[int, str] = {}
    for n in nodes:
        str_id = str(n.id)
        node_id_map[n.id] = str_id
        file_record = session.get(FileModel, n.file_id)
        file_path = file_record.file_path if file_record else ""
        gs.add_node(
            str_id, n.name, n.node_type,
            file_path, n.start_line, n.end_line, n.source_code or "",
        )
    for e in edges:
        src_str = node_id_map.get(e.source_node_id)
        tgt_str = node_id_map.get(e.target_node_id)
        if src_str and tgt_str:
            gs.add_edge(src_str, tgt_str, e.edge_type)
    return gs


@router.get("/cycles/{project_id}")
def get_cycles(
    project_id: int,
    session: Session = Depends(get_session),
):
    """Detect circular dependencies in the project graph."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    gs = _build_graph_service(project_id, session)
    cycles = gs.detect_cycles()
    return {"cycles": cycles, "count": len(cycles)}
