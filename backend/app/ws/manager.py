"""WebSocket connection manager for real-time updates."""

from fastapi import WebSocket
from typing import Optional
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections for broadcasting real-time updates."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)

    async def send_personal_message(self, message: dict, client_id: str):
        connection = self.active_connections.get(client_id)
        if connection:
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)

    async def send_progress(
        self,
        client_id: str,
        current: int,
        total: int,
        status: str,
        detail: str = "",
    ):
        """Send a progress update to a specific client."""
        await self.send_personal_message(
            {
                "type": "progress",
                "data": {
                    "current": current,
                    "total": total,
                    "status": status,
                    "detail": detail,
                },
            },
            client_id,
        )

    async def send_graph_update(
        self,
        client_id: str,
        nodes: list,
        edges: list,
    ):
        """Send graph data update to a specific client."""
        await self.send_personal_message(
            {
                "type": "graph_update",
                "data": {"nodes": nodes, "edges": edges},
            },
            client_id,
        )

    async def send_complete(self, client_id: str, result: dict):
        """Send completion message to a specific client."""
        await self.send_personal_message(
            {
                "type": "complete",
                "data": result,
            },
            client_id,
        )

    async def send_error(self, client_id: str, error: str):
        """Send error message to a specific client."""
        await self.send_personal_message(
            {
                "type": "error",
                "data": {"message": error},
            },
            client_id,
        )

    async def send_ai_stream(self, client_id: str, chunk: str):
        """Send AI streaming response chunk to a specific client."""
        await self.send_personal_message(
            {
                "type": "ai_stream",
                "data": {"chunk": chunk},
            },
            client_id,
        )

    async def send_ping(self, client_id: str):
        """Send a ping message to a specific client."""
        connection = self.active_connections.get(client_id)
        if connection:
            try:
                await connection.send_json({"type": "ping"})
            except Exception:
                self.disconnect(client_id)

    async def heartbeat_all(self):
        """Send ping to all active connections and remove failed ones."""
        disconnected = []
        for client_id, connection in list(self.active_connections.items()):
            try:
                await connection.send_json({"type": "ping"})
            except Exception:
                disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)


# Global connection manager instance
manager = ConnectionManager()
