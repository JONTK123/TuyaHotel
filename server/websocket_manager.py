from starlette.websockets import WebSocket

class WebSocketManager:
    def __init__(self):
        self.rooms = {}  # Estrutura para gerenciar conexões por quarto

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.rooms:
            self.rooms[room_id].remove(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def send_to_room(self, room_id: str, message: dict):
        if room_id in self.rooms:
            for websocket in self.rooms[room_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"Erro ao enviar mensagem para {room_id}: {e}")

    async def broadcast(self, message: dict):
        for room_id, websockets in self.rooms.items():
            for websocket in websockets:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"Erro ao enviar mensagem para todos: {e}")

WebSocketManager = WebSocketManager()
