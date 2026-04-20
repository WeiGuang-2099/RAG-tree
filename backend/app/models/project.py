from sqlmodel import SQLModel, Field
from sqlalchemy import Index
from typing import Optional
from datetime import datetime, timezone


class Project(SQLModel, table=True):
    __tablename__ = "projects"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"


class File(SQLModel, table=True):
    __tablename__ = "files"
    __table_args__ = (
        Index("idx_file_project_id", "project_id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    file_path: str
    language: str
    status: str = "pending"


class CodeNode(SQLModel, table=True):
    __tablename__ = "code_nodes"
    __table_args__ = (
        Index("idx_codenode_project_id", "project_id"),
        Index("idx_codenode_file_id", "file_id"),
        Index("idx_codenode_name", "name"),
    )
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
    __table_args__ = (
        Index("idx_codeedge_project_id", "project_id"),
        Index("idx_codeedge_source_node_id", "source_node_id"),
        Index("idx_codeedge_target_node_id", "target_node_id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    source_node_id: int = Field(foreign_key="code_nodes.id")
    target_node_id: int = Field(foreign_key="code_nodes.id")
    edge_type: str
