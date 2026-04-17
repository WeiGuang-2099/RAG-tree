from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from app.database import get_session
from app.models.project import Project, File as FileModel, CodeNode, CodeEdge
from datetime import datetime

router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str


class RenameProjectRequest(BaseModel):
    name: str


@router.get("/")
def list_projects(session: Session = Depends(get_session)):
    """List all projects with file/node/edge counts."""
    projects = session.exec(
        select(Project).order_by(Project.created_at.desc())
    ).all()

    result = []
    for p in projects:
        file_count = len(session.exec(
            select(FileModel).where(FileModel.project_id == p.id)
        ).all())
        node_count = len(session.exec(
            select(CodeNode).where(CodeNode.project_id == p.id)
        ).all())
        edge_count = len(session.exec(
            select(CodeEdge).where(CodeEdge.project_id == p.id)
        ).all())
        result.append({
            "id": p.id,
            "name": p.name,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
            "file_count": file_count,
            "node_count": node_count,
            "edge_count": edge_count,
        })
    return result


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
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    file_count = len(session.exec(
        select(FileModel).where(FileModel.project_id == project_id)
    ).all())
    node_count = len(session.exec(
        select(CodeNode).where(CodeNode.project_id == project_id)
    ).all())
    edge_count = len(session.exec(
        select(CodeEdge).where(CodeEdge.project_id == project_id)
    ).all())

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

    edges = session.exec(
        select(CodeEdge).where(CodeEdge.project_id == project_id)
    ).all()
    for edge in edges:
        session.delete(edge)

    nodes = session.exec(
        select(CodeNode).where(CodeNode.project_id == project_id)
    ).all()
    for node in nodes:
        session.delete(node)

    files = session.exec(
        select(FileModel).where(FileModel.project_id == project_id)
    ).all()
    for f in files:
        session.delete(f)

    session.delete(project)
    session.commit()
    return {"detail": "Project deleted."}
