from starlette.websockets import WebSocket, WebSocketState

class WebSocketManager:
    def __init__(self):
        self.rooms = {}  # Estrutura para gerenciar conexões por quarto

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.rooms and websocket in self.rooms[room_id]:
            self.rooms[room_id].remove(websocket)
            if not self.rooms[room_id]:  # Remove a sala se estiver vazia
                del self.rooms[room_id]

    async def send_to_room(self, room_id: str, message: dict):
        if room_id in self.rooms:
            disconnected_websockets = []
            for websocket in self.rooms[room_id]:
                try:
                    # Verificar se o WebSocket ainda está ativo
                    if websocket.application_state == WebSocketState.DISCONNECTED:
                        disconnected_websockets.append(websocket)
                    else:
                        await websocket.send_json(message)
                except Exception as e:
                    print(f"Erro ao enviar mensagem para {room_id}: {e}")
                    disconnected_websockets.append(websocket)

            # Remove conexões quebradas
            for ws in disconnected_websockets:
                self.disconnect(ws, room_id)

    async def broadcast(self, message: dict):
        for room_id in list(self.rooms.keys()):
            await self.send_to_room(room_id, message)

    async def get_connections(self, room_id: str):
        return self.rooms.get(room_id, [])

WebSocketManager = WebSocketManager()
