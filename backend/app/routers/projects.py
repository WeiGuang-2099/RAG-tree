from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, delete
from sqlalchemy import func
from pydantic import BaseModel
from app.database import get_session
from app.models.project import Project, File as FileModel, CodeNode, CodeEdge
from app.services.graph_service import GraphService
from datetime import datetime
import networkx as nx
import os

router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str


class RenameProjectRequest(BaseModel):
    name: str


@router.get("/")
def list_projects(session: Session = Depends(get_session)):
    """List all projects with file/node/edge counts."""
    # Single aggregated query with outerjoins and counts
    results = session.exec(
        select(
            Project,
            func.count(func.distinct(FileModel.id)).label("file_count"),
            func.count(func.distinct(CodeNode.id)).label("node_count"),
            func.count(func.distinct(CodeEdge.id)).label("edge_count"),
        )
        .outerjoin(FileModel, FileModel.project_id == Project.id)
        .outerjoin(CodeNode, CodeNode.project_id == Project.id)
        .outerjoin(CodeEdge, CodeEdge.project_id == Project.id)
        .group_by(Project.id)
        .order_by(Project.created_at.desc())
    ).all()

    return [
        {
            "id": project.id,
            "name": project.name,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "file_count": file_count,
            "node_count": node_count,
            "edge_count": edge_count,
        }
        for project, file_count, node_count, edge_count in results
    ]


@router.post("/")
def create_project(
    request: CreateProjectRequest,
    session: Session = Depends(get_session),
):
    """Create a new empty project."""
    project = Project(name=request.name, status="empty")
    session.add(project)
    session.commit()
    session.refresh(project)
    return {
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "created_at": project.created_at.isoformat(),
    }


@router.get("/{project_id}")
def get_project(
    project_id: int,
    session: Session = Depends(get_session),
):
    """Get project details."""
    result = session.exec(
        select(
            Project,
            func.count(func.distinct(FileModel.id)).label("file_count"),
            func.count(func.distinct(CodeNode.id)).label("node_count"),
            func.count(func.distinct(CodeEdge.id)).label("edge_count"),
        )
        .outerjoin(FileModel, FileModel.project_id == Project.id)
        .outerjoin(CodeNode, CodeNode.project_id == Project.id)
        .outerjoin(CodeEdge, CodeEdge.project_id == Project.id)
        .where(Project.id == project_id)
        .group_by(Project.id)
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="Project not found.")

    project, file_count, node_count, edge_count = result
    return {
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "created_at": project.created_at.isoformat(),
        "file_count": file_count,
        "node_count": node_count,
        "edge_count": edge_count,
    }


@router.put("/{project_id}")
def rename_project(
    project_id: int,
    request: RenameProjectRequest,
    session: Session = Depends(get_session),
):
    """Rename a project."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    project.name = request.name
    session.add(project)
    session.commit()
    return {
        "id": project.id,
        "name": project.name,
        "status": project.status,
    }


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    session: Session = Depends(get_session),
):
    """Delete a project and all its data."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Bulk delete using delete statements (more efficient than select-then-delete)
    session.exec(delete(CodeEdge).where(CodeEdge.project_id == project_id))
    session.exec(delete(CodeNode).where(CodeNode.project_id == project_id))
    session.exec(delete(FileModel).where(FileModel.project_id == project_id))

    session.delete(project)
    session.commit()
    return {"detail": "Project deleted."}


@router.get("/{project_id}/dashboard")
def get_dashboard(
    project_id: int,
    session: Session = Depends(get_session),
):
    """Get aggregated dashboard metrics for a project."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    nodes = session.exec(
        select(CodeNode).where(CodeNode.project_id == project_id)
    ).all()
    edges = session.exec(
        select(CodeEdge).where(CodeEdge.project_id == project_id)
    ).all()
    files = session.exec(
        select(FileModel).where(FileModel.project_id == project_id)
    ).all()

    # Build in-memory graph
    gs = GraphService()
    node_id_map: dict[int, str] = {}
    for n in nodes:
        str_id = str(n.id)
        node_id_map[n.id] = str_id
        file_record = session.get(FileModel, n.file_id)
        file_path = file_record.file_path if file_record else ""
        gs.add_node(str_id, n.name, n.node_type, file_path, n.start_line, n.end_line, n.source_code or "")
    for e in edges:
        src_str = node_id_map.get(e.source_node_id)
        tgt_str = node_id_map.get(e.target_node_id)
        if src_str and tgt_str:
            gs.add_edge(src_str, tgt_str, e.edge_type)

    stats = gs.get_stats()
    cycles = gs.detect_cycles()

    # Degree centrality for top hubs
    centrality = nx.degree_centrality(gs.graph)
    top_hubs = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
    top_hubs_list = []
    for node_id, score in top_hubs:
        node_data = gs.get_node(node_id)
        top_hubs_list.append({
            "id": node_id,
            "name": node_data["name"] if node_data else node_id,
            "type": node_data["type"] if node_data else "Unknown",
            "centrality": round(score, 4),
        })

    # Language distribution by file extension
    lang_dist: dict[str, int] = {}
    for f in files:
        ext = os.path.splitext(f.file_path)[1] or "unknown"
        # Count nodes in this file
        count = sum(1 for n in nodes if n.file_id == f.id)
        lang_dist[ext] = lang_dist.get(ext, 0) + count

    # Average degree
    num_nodes = stats["node_count"]
    num_edges = stats["edge_count"]
    avg_degree = round(num_edges / num_nodes, 2) if num_nodes > 0 else 0.0

    return {
        "node_count": num_nodes,
        "edge_count": num_edges,
        "cycle_count": len(cycles),
        "avg_degree": avg_degree,
        "density": stats["density"],
        "language_distribution": lang_dist,
        "top_hubs": top_hubs_list,
    }
