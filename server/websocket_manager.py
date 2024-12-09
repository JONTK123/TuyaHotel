from starlette.websockets import WebSocket

class WebSocketManager:
    def __init__(self):
        self.room_connections = {}  # Mapa: ROOM_ID -> [WebSocket]

    async def connect(self, websocket: WebSocket, room_id: str):
        """
        Adiciona uma conexão WebSocket ao quarto especificado.
        """
        await websocket.accept()
        if room_id not in self.room_connections:
            # Inicializa a key room_id e o array para essa key
            self.room_connections[room_id] = []
        # Adiciona a conexao websocket para a key associada
        self.room_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Remove uma conexão WebSocket associada a qualquer quarto.
        """
        # Percorre dicionário de conexões
        for room_id, connections in self.room_connections.items():
            # Se conectado, remove a conexão
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    # Remove o quarto se não houver mais conexões
                    del self.room_connections[room_id]
                break

    async def send_message(self, room_id: str, message: str):
        """
        Envia uma mensagem para todas as conexões associadas ao quarto especificado.
        """
        # Verifica se o quarto está conectado
        if room_id in self.room_connections:
            for connection in self.room_connections[room_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Erro ao enviar mensagem WebSocket: {e}")

    async def broadcast(self, message: dict):
        """
        Envia uma mensagem para todas as conexões de todos os quartos.
        """
        for connections in self.room_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Erro ao enviar mensagem WebSocket: {e}")

websocket_manager = WebSocketManager()

# Lista de conexões por quarto

# Send message envia para os clientes conectados ao quarto especificado
# Broadcast envia para todos os clientes conectados ao backend

# websocket_manager.room_connections = {
#     "room_101": [websocket_client_1, websocket_client_2],  # Clientes conectados ao quarto 101
#     "room_102": [websocket_client_3]                      # Clientes conectados ao quarto 102
# }

# Tudo é o mesmo backend / servidor, mas com diferentes quartos e usuários associados a eles.
# O backend usara as mesmas credenciais de acesso da API mas com mesmo backend

# 1 quarto = 1 backend com mesma chave de acesso mas com dispositivos diferentes