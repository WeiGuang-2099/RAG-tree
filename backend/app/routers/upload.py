import logging

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, BackgroundTasks
from sqlmodel import Session, select, delete
from sqlalchemy import or_
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

    all_nodes = []
    all_edges = []
    resolved_edges = []  # Edges with resolved IDs for WebSocket
    parse_errors: list[str] = []
    total = len(file_data)

    try:
        with SqlSession(engine) as session:
            project = session.get(Project, project_id)
            if not project:
                if client_id:
                    await manager.send_error(client_id, f"Project {project_id} not found")
                return

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

            # Composite key mapping: (file_path, name) -> node_id
            node_key_to_id: dict[tuple[str, str], str] = {
                (n["file_path"], n["name"]): n["id"] for n in all_nodes
            }
            # Name-only lookup for cross-file references (imports): name -> [id1, id2, ...]
            node_name_to_ids: dict[str, list[str]] = {}
            for n in all_nodes:
                name = n["name"]
                if name not in node_name_to_ids:
                    node_name_to_ids[name] = []
                node_name_to_ids[name].append(n["id"])

            for edge_data in all_edges:
                source_name = edge_data.get("source", "")
                target_name = edge_data.get("target", "")
                source_file = edge_data.get("source_file", "")
                target_file = edge_data.get("target_file", "")

                # Try same-file lookup first
                source_id = node_key_to_id.get((source_file, source_name))
                target_id = node_key_to_id.get((target_file, target_name))

                # Fall back to name-only lookup for cross-file references
                if not source_id and source_name in node_name_to_ids:
                    source_id = node_name_to_ids[source_name][0]
                if not target_id and target_name in node_name_to_ids:
                    target_id = node_name_to_ids[target_name][0]

                if source_id and target_id:
                    code_edge = CodeEdge(
                        project_id=project_id,
                        source_node_id=int(source_id),
                        target_node_id=int(target_id),
                        edge_type=edge_data.get("type", "unknown"),
                    )
                    session.add(code_edge)
                    resolved_edges.append({
                        "source": source_id,
                        "target": target_id,
                        "type": edge_data.get("type", "unknown"),
                    })

            # Build cross-file import edges
            node_id_to_info = {n["id"]: n for n in all_nodes}
            created_cross_edges: set[tuple] = set()
            for node in all_nodes:
                if node["type"] == "Module":
                    module_name = node["name"]
                    node_file = node["file_path"]
                    if module_name in node_name_to_ids:
                        for target_id in node_name_to_ids[module_name]:
                            target_node = node_id_to_info.get(target_id)
                            if (
                                target_node
                                and target_node["file_path"] != node_file
                                and target_node["type"] in ("Function", "Class")
                            ):
                                edge_key = (node["id"], target_id)
                                if edge_key not in created_cross_edges:
                                    created_cross_edges.add(edge_key)
                                    code_edge = CodeEdge(
                                        project_id=project_id,
                                        source_node_id=int(node["id"]),
                                        target_node_id=int(target_id),
                                        edge_type="imports",
                                    )
                                    session.add(code_edge)
                                    resolved_edges.append({
                                        "source": node["id"],
                                        "target": target_id,
                                        "type": "imports",
                                    })

            project.status = "completed"
            session.commit()

    except Exception as e:
        # Top-level error handling: set project status to "error"
        err_msg = f"Background processing failed: {str(e)}"
        logger.error(f"{err_msg}\n{traceback.format_exc()}")
        try:
            with SqlSession(engine) as err_session:
                project = err_session.get(Project, project_id)
                if project:
                    project.status = "error"
                    err_session.commit()
        except Exception:
            logger.error(f"Failed to update project {project_id} status to error")

        if client_id:
            await manager.send_error(client_id, err_msg)
            await manager.send_complete(
                client_id,
                result={"project_id": project_id, "node_count": 0, "edge_count": 0, "error": True},
            )
        return

    if client_id:
        await manager.send_graph_update(
            client_id,
            nodes=all_nodes,
            edges=resolved_edges,
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
                "edge_count": len(resolved_edges),
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

        # Check if a file with the same path already exists in this project
        existing_file = session.exec(
            select(FileModel).where(
                FileModel.project_id == project.id,
                FileModel.file_path == (upload_file.filename or ""),
            )
        ).first()

        if existing_file:
            # Delete old nodes and their associated edges to avoid duplicates
            old_nodes = session.exec(
                select(CodeNode).where(CodeNode.file_id == existing_file.id)
            ).all()
            old_node_ids = [n.id for n in old_nodes]
            if old_node_ids:
                session.exec(
                    delete(CodeEdge).where(
                        or_(
                            CodeEdge.source_node_id.in_(old_node_ids),
                            CodeEdge.target_node_id.in_(old_node_ids),
                        )
                    )
                )
                session.exec(delete(CodeNode).where(CodeNode.file_id == existing_file.id))
            existing_file.status = "pending"
            session.add(existing_file)
            session.commit()
            session.refresh(existing_file)
            file_record = existing_file
        else:
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
    if background_tasks is None:
        raise HTTPException(status_code=500, detail="BackgroundTasks not available")
    background_tasks.add_task(process_files, project.id, file_data, ws_client_id)

    return {
        "task_id": project.name,
        "project_id": project.id,
        "file_count": len(saved_files),
        "files": saved_files,
        "status": "processing",
    }
