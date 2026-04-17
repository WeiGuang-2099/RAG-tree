from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from app.database import get_session
from app.models.project import CodeNode, CodeEdge, Project
from app.services.ai_service import AiService
from app.config import get_settings

router = APIRouter(prefix="/api/ai", tags=["ai"])
settings = get_settings()


class ChatRequest(BaseModel):
    project_id: int
    message: str
    context_node_id: int | None = None


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
):
    """Send a chat message to the AI assistant about the codebase."""
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

    ai_service = AiService()
    try:
        similar = ai_service.find_similar_nodes(
            query=request.message,
            nodes=[
                {
                    "name": n.name,
                    "type": n.node_type,
                    "file_path": n.file_path,
                    "source_code": n.source_code or "",
                }
                for n in nodes[:200]
            ],
            top_k=5,
        )
        if similar:
            top_contexts = []
            for s in similar[:3]:
                code = s.get("source_code", "")
                if len(code) > 800:
                    code = code[:800]
                top_contexts.append(
                    f"- {s['name']} ({s['type']}) in {s['file_path']}: {code}"
                )
            embedding_context = "\n\nSemantically relevant code (via Embedding-3):\n" + "\n".join(top_contexts)
            if context:
                context = context + embedding_context
            else:
                context = embedding_context
    except Exception:
        pass

    response = await ai_service.chat(
        message=request.message,
        graph_context=graph_summary,
        node_context=context,
    )

    return {"response": response}


@router.post("/architecture")
async def generate_architecture(
    request: ArchitectureRequest,
    session: Session = Depends(get_session),
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

    ai_service = AiService()
    response = await ai_service.analyze_architecture(
        nodes_summary=node_info, edges_summary=edge_info
    )

    return {"architecture": response}


@router.post("/search")
async def semantic_search(
    request: SemanticSearchRequest,
    session: Session = Depends(get_session),
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

    ai_service = AiService()
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
