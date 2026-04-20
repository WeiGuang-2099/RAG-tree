import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.routers import upload, graph, ai, projects
from app.ws.manager import manager
from contextlib import asynccontextmanager


async def heartbeat_task():
    """Background task to send periodic heartbeats to all connected clients."""
    while True:
        await asyncio.sleep(settings.ws_heartbeat_interval)
        await manager.heartbeat_all()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Start heartbeat task
    heartbeat = asyncio.create_task(heartbeat_task())
    yield
    heartbeat.cancel()
    try:
        await heartbeat
    except asyncio.CancelledError:
        pass


settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(graph.router)
app.include_router(ai.router)
app.include_router(projects.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.version}


@app.get("/api/ai/status")
async def ai_status():
    return {"available": bool(settings.zhipuai_api_key)}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle heartbeat response
            if data == "pong":
                continue
            try:
                msg = json.loads(data)
                if isinstance(msg, dict) and msg.get("type") == "pong":
                    continue
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(client_id)
