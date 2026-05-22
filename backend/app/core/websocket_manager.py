from fastapi import WebSocket
from typing import Dict, List

class WebSocketManager:
    def __init__(self):
        # room_id -> list of connected websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast_to_room(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            # clean up dead connections
            for conn in disconnected:
                self.active_connections[room_id].remove(conn)

    async def broadcast_to_all(self, message: dict):
        for room_id in list(self.active_connections.keys()):
            await self.broadcast_to_room(room_id, message)

manager = WebSocketManager()