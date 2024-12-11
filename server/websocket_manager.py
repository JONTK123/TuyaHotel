from starlette.websockets import WebSocket

class WebSocketManager:
    def __init__(self):
        self.rooms = {}  # Armazena todos os quartos e suas conexões/dispositivos

    async def connect(self, websocket: WebSocket, room_id: str):
        """
        Adiciona uma conexão WebSocket ao quarto especificado.
        """
        await websocket.accept()
        if room_id not in self.rooms:
            # Inicializa o quarto se ele ainda não existir
            self.rooms[room_id] = {
                "connections": [],
                "devices": [],  # Lista de dispositivos do quarto
                "do_not_disturb": False,
                "cleaning_requested": False,
            }
        self.rooms[room_id]["connections"].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        """
        Remove uma conexão WebSocket associada ao quarto.
        """
        if room_id in self.rooms:
            connections = self.rooms[room_id]["connections"]
            if websocket in connections:
                connections.remove(websocket)
            if not connections:
                del self.rooms[room_id]  # Remove o quarto se não houver mais conexões

    async def send_message(self, room_id: str, message: str):
        """
        Envia uma mensagem para todas as conexões associadas ao quarto especificado.
        """
        if room_id in self.rooms:
            for connection in self.rooms[room_id]["connections"]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Erro ao enviar mensagem WebSocket: {e}")

    async def broadcast(self, message: dict):
        """
        Envia uma mensagem para todas as conexões de todos os quartos.
        """
        for room in self.rooms.values():
            for connection in room["connections"]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Erro ao enviar mensagem WebSocket: {e}")

websocket_manager = WebSocketManager()

# Estrutura centralizada de gerenciamento de conexões e estados por quarto

# Send message: Envia uma mensagem para todas as conexões associadas a um quarto específico.
# Broadcast: Envia uma mensagem para todas as conexões WebSocket de todos os quartos gerenciados pelo backend.

# Estrutura de exemplo:
# websocket_manager.rooms = {
#     "room_101": {
#         "connections": [websocket_client_1, websocket_client_2],  # Lista de conexões WebSocket conectadas ao quarto
#         "devices": [                                              # Lista de dispositivos associados ao quarto
#             {"id": "device_1", "name": "Lamp", "status": "OFF"},
#             {"id": "device_2", "name": "Fan", "status": "ON"}
#         ],
#         "do_not_disturb": True,  # Estado "Não Perturbe"
#         "cleaning_requested": False  # Estado "Solicitação de Limpeza"
#     },
#     "room_102": {
#         "connections": [websocket_client_3],                      # Conexões WebSocket para o quarto 102
#         "devices": [                                              # Dispositivos do quarto 102
#             {"id": "device_3", "name": "TV", "status": "OFF"},
#             {"id": "device_4", "name": "AC", "status": "ON"}
#         ],
#         "do_not_disturb": False,  # Estado "Não Perturbe"
#         "cleaning_requested": True  # Estado "Solicitação de Limpeza"
#     }
# }

# Todo o gerenciamento de quartos, dispositivos e conexões WebSocket ocorre no mesmo backend.
# Cada quarto e seus dados são centralizados em uma única estrutura chamada `rooms`.

# O backend utiliza as mesmas credenciais da API Tuya para gerenciar dispositivos de todos os quartos.
# Isso elimina a necessidade de backends separados para cada quarto.

# Um único backend gerencia:
# 1. Múltiplos quartos e dispositivos associados.
# 2. Conexões WebSocket ativas para os usuários que acessam os quartos.
# 3. Estados como "Não Perturbe" e "Solicitação de Limpeza" para cada quarto.
# 4. Comunicação centralizada entre frontend e dispositivos IoT.

# Este modelo reduz a complexidade, facilita a escalabilidade e permite integrar tanto o painel central (dashboard) quanto os painéis específicos de cada quarto.

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Outra abordagem era:

# Lista de conexões por quarto

# Send message envia para os clientes conectados ao quarto especificado
# Broadcast envia para todos os clientes conectados ao backend

# websocket_manager.room_connections = {
#     "room_101": {
#         "connections": [websocket_client_1, websocket_client_2],  # Lista de conexões WebSocket conectadas ao quarto
#         "do_not_disturb": True,  # Estado "Não Perturbe"
#         "cleaning_requested": False  # Estado "Solicitação de Limpeza"
#     }
# }

# Tudo é o mesmo backend / servidor, mas com diferentes quartos e usuários associados a eles.
# O backend usara as mesmas credenciais de acesso da API mas com mesmo backend

# 1 quarto = 1 backend com mesma chave de acesso mas com dispositivos diferentes
# Esses quartos se conectam a outro backend central para receber o status de cada quarto e atualizar o frontend do Painel central

# Dificil de escalar e manter, pois cada quarto teria um backend separado, mas o backend central seria responsável por atualizar o frontend do Painel central. Outro repo