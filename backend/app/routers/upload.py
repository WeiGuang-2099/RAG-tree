import logging

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, BackgroundTasks
from sqlmodel import Session
from app.database import get_session
from app.models.project import Project, File as FileModel, CodeNode, CodeEdge
from app.services.parser_service import parse_file
from app.config import get_settings
from app.ws.manager import manager
import uuid
import os
import asyncio
import traceback

router = APIRouter(prefix="/api/upload", tags=["upload"])
settings = get_settings()
logger = logging.getLogger(__name__)


async def process_files(
    project_id: int,
    file_data: list[tuple[str, str, str]],
    client_id: str | None,
):
    """Background task: parse all files, build graph, optionally run AI analysis."""
    await asyncio.sleep(0.1)

    from app.database import engine
    from sqlmodel import Session as SqlSession

    with SqlSession(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            if client_id:
                await manager.send_error(client_id, f"Project {project_id} not found")
            return

        total = len(file_data)
        all_nodes = []
        all_edges = []
        parse_errors: list[str] = []

        for i, (filename, language, source_code) in enumerate(file_data):
            if client_id:
                await manager.send_progress(
                    client_id,
                    current=i + 1,
                    total=total,
                    status="parsing",
                    detail=f"Parsing {filename}",
                )

            try:
                result = parse_file(filename, source_code, language)
            except Exception as e:
                err_msg = f"Parse error in {filename}: {str(e)}"
                logger.warning(err_msg)
                parse_errors.append(err_msg)
                continue

            file_record = session.exec(
                FileModel.__table__.select().where(
                    FileModel.file_path == filename,
                    FileModel.project_id == project_id,
                )
            ).first()

            if not file_record:
                continue

            file_id = file_record.id

            for node_data in result.get("nodes", []):
                code_node = CodeNode(
                    project_id=project_id,
                    file_id=file_id,
                    node_type=node_data.get("type", "Unknown"),
                    name=node_data.get("name", "Unknown"),
                    start_line=node_data.get("start_line", 0),
                    end_line=node_data.get("end_line", 0),
                    source_code=node_data.get("source_code", ""),
                )
                session.add(code_node)
                session.flush()
                all_nodes.append({
                    "id": str(code_node.id),
                    "name": code_node.name,
                    "type": code_node.node_type,
                    "file_path": filename,
                    "start_line": code_node.start_line,
                    "end_line": code_node.end_line,
                })

            all_edges.extend(result.get("edges", []))

        node_name_to_id: dict[str, str] = {
            n["name"]: n["id"] for n in all_nodes
        }

        for edge_data in all_edges:
            source_name = edge_data.get("source", "")
            target_name = edge_data.get("target", "")
            source_id = node_name_to_id.get(source_name)
            target_id = node_name_to_id.get(target_name)
            if source_id and target_id:
                code_edge = CodeEdge(
                    project_id=project_id,
                    source_node_id=int(source_id),
                    target_node_id=int(target_id),
                    edge_type=edge_data.get("type", "unknown"),
                )
                session.add(code_edge)

        project.status = "completed"
        session.commit()

    if client_id:
        await manager.send_graph_update(
            client_id,
            nodes=all_nodes,
            edges=[],
        )

        if parse_errors:
            await manager.send_error(
                client_id,
                f"Parsed {total} files with {len(parse_errors)} errors: " +
                "; ".join(parse_errors[:5]),
            )

        if settings.zhipuai_api_key and all_nodes:
            await manager.send_progress(
                client_id,
                current=total,
                total=total,
                status="analyzing",
                detail="Running AI architecture analysis...",
            )
            try:
                from app.services.ai_service import AiService
                ai_service = AiService()
                node_summary = "\n".join(
                    f"- {n['name']} ({n['type']}) in {n['file_path']}"
                    for n in all_nodes[:100]
                )
                edge_summary = "\n".join(
                    f"- {e.get('source', '?')} -> {e.get('target', '?')} ({e.get('type', '?')})"
                    for e in all_edges[:100]
                )
                async for chunk in ai_service.analyze_architecture_stream(
                    nodes_summary=node_summary,
                    edges_summary=edge_summary,
                ):
                    await manager.send_ai_stream(client_id, chunk)
            except Exception as e:
                err_msg = f"AI analysis failed: {str(e)}"
                logger.error(f"{err_msg}\n{traceback.format_exc()}")
                await manager.send_error(client_id, err_msg)
        elif not settings.zhipuai_api_key and all_nodes:
            await manager.send_error(
                client_id,
                "AI analysis skipped: ZHIPUAI_API_KEY not configured in backend/.env",
            )

        await manager.send_complete(
            client_id,
            result={
                "project_id": project_id,
                "node_count": len(all_nodes),
                "edge_count": len(all_edges),
            },
        )


@router.post("/")
async def upload_files(
    files: list[UploadFile] = File(...),
    client_id: str = Form(""),
    project_id: str = Form(""),
    session: Session = Depends(get_session),
    background_tasks: BackgroundTasks = None,
):
    """Upload code files for analysis. Creates a new project or adds to existing."""
    if len(files) > settings.max_files:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.max_files} files allowed per upload.",
        )

    if project_id:
        try:
            pid = int(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id.")
        project = session.get(Project, pid)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")
        project.status = "processing"
        session.add(project)
        session.commit()
    else:
        task_id = str(uuid.uuid4())
        project = Project(name=task_id, status="processing")
        session.add(project)
        session.commit()
        session.refresh(project)

    file_data: list[tuple[str, str, str]] = []
    saved_files = []

    for upload_file in files:
        ext = os.path.splitext(upload_file.filename or "")[1]
        if ext not in settings.supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension: {ext}",
            )

        content = await upload_file.read()
        if len(content) > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File {upload_file.filename} exceeds {settings.max_file_size_mb}MB limit.",
            )

        file_record = FileModel(
            project_id=project.id,
            file_path=upload_file.filename or "",
            language=ext.lstrip("."),
            status="pending",
        )
        session.add(file_record)
        session.commit()
        session.refresh(file_record)

        try:
            source_code = content.decode("utf-8")
        except UnicodeDecodeError:
            source_code = content.decode("latin-1")

        file_data.append((
            upload_file.filename or "",
            ext.lstrip("."),
            source_code,
        ))
        saved_files.append(upload_file.filename or "")

    ws_client_id = client_id if client_id else None
    background_tasks.add_task(process_files, project.id, file_data, ws_client_id)

    return {
        "task_id": project.name,
        "project_id": project.id,
        "file_count": len(saved_files),
        "files": saved_files,
        "status": "processing",
    }
