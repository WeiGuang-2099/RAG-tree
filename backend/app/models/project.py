from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Project(SQLModel, table=True):
    __tablename__ = "projects"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"


class File(SQLModel, table=True):
    __tablename__ = "files"
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    file_path: str
    language: str
    status: str = "pending"


class CodeNode(SQLModel, table=True):
    __tablename__ = "code_nodes"
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    file_id: int = Field(foreign_key="files.id")
    node_type: str
    name: str
    start_line: int
    end_line: int
    source_code: str


class CodeEdge(SQLModel, table=True):
    __tablename__ = "code_edges"
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    source_node_id: int = Field(foreign_key="code_nodes.id")
    target_node_id: int = Field(foreign_key="code_nodes.id")
    edge_type: str
