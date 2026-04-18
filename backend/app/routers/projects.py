from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, delete
from sqlalchemy import func
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
