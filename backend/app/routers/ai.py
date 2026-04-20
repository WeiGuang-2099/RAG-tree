from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from pydantic import BaseModel
from app.database import get_session, get_ai_service, get_graph_service
from app.models.project import CodeNode, CodeEdge, Project
from app.services.ai_service import AiService
from app.services.graph_service import GraphService
from app.config import get_settings

router = APIRouter(prefix="/api/ai", tags=["ai"])
settings = get_settings()


class ChatRequest(BaseModel):
    project_id: int
    message: str
    context_node_id: int | None = None
    history: list[dict] = []


class ArchitectureRequest(BaseModel):
    project_id: int


class SemanticSearchRequest(BaseModel):
    project_id: int
    query: str
    top_k: int = 10


@router.post("/chat")
async def chat(
    request: ChatRequest,
    session: Session = Depends(get_session),
    ai_service: AiService = Depends(get_ai_service),
    gs: GraphService = Depends(get_graph_service),
):
    """Send a chat message to the AI assistant about the codebase.

    Three-stage Graph-RAG pipeline:
    1. embed_search - find semantically similar nodes
    2. graph_expand - expand subgraph around seed nodes
    3. prompt_inject - serialize graph context into system prompt
    """
    if not settings.zhipuai_api_key:
        raise HTTPException(
            status_code=500,
            detail="ZhipuAI API key not configured.",
        )

    project = session.get(Project, request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    context = ""
    if request.context_node_id:
        node = session.get(CodeNode, request.context_node_id)
        if node:
            context = f"Context node: {node.name} ({node.node_type})\n```\n{node.source_code}\n```"

    nodes = session.exec(
        select(CodeNode).where(CodeNode.project_id == request.project_id)
    ).all()
    edges = session.exec(
        select(CodeEdge).where(CodeEdge.project_id == request.project_id)
    ).all()

    graph_summary = f"Project has {len(nodes)} nodes and {len(edges)} edges."

    # Build in-memory graph for subgraph extraction
    node_id_map: dict[int, str] = {}
    for n in nodes:
        str_id = str(n.id)
        node_id_map[n.id] = str_id
        gs.add_node(
            str_id, n.name, n.node_type,
            getattr(n, "file_path", ""), n.start_line, n.end_line,
            n.source_code or "",
        )
    for e in edges:
        src_str = node_id_map.get(e.source_node_id)
        tgt_str = node_id_map.get(e.target_node_id)
        if src_str and tgt_str:
            gs.add_edge(src_str, tgt_str, e.edge_type)

    # Stage 1: embed_search - find semantically similar nodes
    referenced_node_ids: list[int] = []
    seed_str_ids: list[str] = []

    try:
        similar = ai_service.find_similar_nodes(
            query=request.message,
            nodes=[
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.node_type,
                    "file_path": getattr(n, "file_path", ""),
                    "source_code": n.source_code or "",
                }
                for n in nodes[:200]
            ],
            top_k=3,
        )

        if similar:
            for s in similar[:3]:
                if s.get("id") is not None:
                    referenced_node_ids.append(s["id"])
                    seed_str_ids.append(str(s["id"]))

            # Build embedding-based code context
            top_contexts = []
            for s in similar[:3]:
                code = s.get("source_code", "")
                if len(code) > 800:
                    code = code[:800]
                top_contexts.append(
                    f"- {s['name']} ({s['type']}) in {s.get('file_path', '')}: {code}"
                )
            embedding_context = "\n\nSemantically relevant code (via Embedding-3):\n" + "\n".join(top_contexts)
            if context:
                context = context + embedding_context
            else:
                context = embedding_context
    except Exception:
        pass

    # Stage 2: graph_expand - extract subgraph around seed nodes
    graph_context = graph_summary
    if seed_str_ids:
        subgraph = gs.get_subgraph_for_nodes(seed_str_ids, depth=2)

        # Stage 3: prompt_inject - serialize graph context
        serialized = AiService._serialize_graph_context(
            subgraph["nodes"], subgraph["edges"]
        )
        if serialized:
            graph_context = f"{graph_summary}\n\nGraph topology context:\n{serialized}"

    response = await ai_service.chat(
        message=request.message,
        graph_context=graph_context,
        node_context=context,
        history=request.history,
    )

    return {"response": response, "referenced_node_ids": referenced_node_ids}


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    session: Session = Depends(get_session),
    ai_service: AiService = Depends(get_ai_service),
    gs: GraphService = Depends(get_graph_service),
):
    """Stream a chat response via Server-Sent Events."""
    if not settings.zhipuai_api_key:
        raise HTTPException(
            status_code=500,
            detail="ZhipuAI API key not configured.",
        )

    project = session.get(Project, request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    context = ""
    if request.context_node_id:
        node = session.get(CodeNode, request.context_node_id)
        if node:
            context = f"Context node: {node.name} ({node.node_type})\n```\n{node.source_code}\n```"

    nodes = session.exec(
        select(CodeNode).where(CodeNode.project_id == request.project_id)
    ).all()
    edges = session.exec(
        select(CodeEdge).where(CodeEdge.project_id == request.project_id)
    ).all()

    graph_summary = f"Project has {len(nodes)} nodes and {len(edges)} edges."

    # Build in-memory graph for subgraph extraction
    node_id_map: dict[int, str] = {}
    for n in nodes:
        str_id = str(n.id)
        node_id_map[n.id] = str_id
        gs.add_node(
            str_id, n.name, n.node_type,
            getattr(n, "file_path", ""), n.start_line, n.end_line,
            n.source_code or "",
        )
    for e in edges:
        src_str = node_id_map.get(e.source_node_id)
        tgt_str = node_id_map.get(e.target_node_id)
        if src_str and tgt_str:
            gs.add_edge(src_str, tgt_str, e.edge_type)

    # Stage 1: embed_search
    seed_str_ids: list[str] = []
    referenced_node_ids: list[int] = []

    try:
        similar = ai_service.find_similar_nodes(
            query=request.message,
            nodes=[
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.node_type,
                    "file_path": getattr(n, "file_path", ""),
                    "source_code": n.source_code or "",
                }
                for n in nodes[:200]
            ],
            top_k=3,
        )
        if similar:
            for s in similar[:3]:
                if s.get("id") is not None:
                    referenced_node_ids.append(s["id"])
                    seed_str_ids.append(str(s["id"]))
            top_contexts = []
            for s in similar[:3]:
                code = s.get("source_code", "")
                if len(code) > 800:
                    code = code[:800]
                top_contexts.append(
                    f"- {s['name']} ({s['type']}) in {s.get('file_path', '')}: {code}"
                )
            embedding_context = "\n\nSemantically relevant code (via Embedding-3):\n" + "\n".join(top_contexts)
            if context:
                context = context + embedding_context
            else:
                context = embedding_context
    except Exception:
        pass

    # Stage 2: graph_expand
    graph_context = graph_summary
    if seed_str_ids:
        subgraph = gs.get_subgraph_for_nodes(seed_str_ids, depth=2)
        serialized = AiService._serialize_graph_context(
            subgraph["nodes"], subgraph["edges"]
        )
        if serialized:
            graph_context = f"{graph_summary}\n\nGraph topology context:\n{serialized}"

    # Stream response via SSE
    async def event_generator():
        # First event: send referenced_node_ids
        import json
        yield f"data: {json.dumps({'type': 'meta', 'referenced_node_ids': referenced_node_ids})}\n\n"

        async for chunk in ai_service.chat_stream(
            message=request.message,
            graph_context=graph_context,
            node_context=context,
            history=request.history,
        ):
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/architecture")
async def generate_architecture(
    request: ArchitectureRequest,
    session: Session = Depends(get_session),
    ai_service: AiService = Depends(get_ai_service),
):
    """Generate architecture overview using AI."""
    if not settings.zhipuai_api_key:
        raise HTTPException(
            status_code=500,
            detail="ZhipuAI API key not configured.",
        )

    project = session.get(Project, request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    nodes = session.exec(
        select(CodeNode).where(CodeNode.project_id == request.project_id)
    ).all()
    edges = session.exec(
        select(CodeEdge).where(CodeEdge.project_id == request.project_id)
    ).all()

    node_info = "\n".join(
        f"- {n.name} ({n.node_type}) in {n.file_path}" for n in nodes
    )
    edge_info = "\n".join(
        f"- {e.source_node_id} -> {e.target_node_id} ({e.edge_type})" for e in edges
    )

    response = await ai_service.analyze_architecture(
        nodes_summary=node_info, edges_summary=edge_info
    )

    return {"architecture": response}


@router.post("/search")
async def semantic_search(
    request: SemanticSearchRequest,
    session: Session = Depends(get_session),
    ai_service: AiService = Depends(get_ai_service),
):
    """Search code nodes using Embedding-3 semantic similarity."""
    if not settings.zhipuai_api_key:
        raise HTTPException(
            status_code=500,
            detail="ZhipuAI API key not configured.",
        )

    project = session.get(Project, request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    nodes = session.exec(
        select(CodeNode).where(CodeNode.project_id == request.project_id)
    ).all()

    if not nodes:
        return {"results": []}

    try:
        results = ai_service.find_similar_nodes(
            query=request.query,
            nodes=[
                {
                    "name": n.name,
                    "type": n.node_type,
                    "file_path": n.file_path,
                    "start_line": n.start_line,
                    "end_line": n.end_line,
                    "source_code": n.source_code or "",
                }
                for n in nodes
            ],
            top_k=request.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding search failed: {str(e)}")

    return {
        "results": [
            {
                "name": r["name"],
                "type": r["type"],
                "file_path": r["file_path"],
                "start_line": r.get("start_line", 0),
                "end_line": r.get("end_line", 0),
                "similarity": round(r["similarity"], 4),
            }
            for r in results
        ]
    }
