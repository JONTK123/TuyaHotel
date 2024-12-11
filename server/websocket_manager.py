from starlette.websockets import WebSocket
import websockets
import json

class WebSocketManager:
    def __init__(self):
        self.room_connections = {}  # Mapa: ROOM_ID -> [WebSocket]
        self.centralizador_connection = None  # Conexão com o centralizador

    async def connect_centralizador(self, centralizador_url: str):
        """
        Conecta ao centralizador via WebSocket e salva a conexão.
        """
        try:
            self.centralizador_connection = await websockets.connect(centralizador_url)
            print("Conectado ao centralizador com sucesso!")
        except Exception as e:
            print(f"Erro ao conectar com o centralizador: {e}")

    async def send_to_centralizador(self, message: dict):
        """
        Envia uma mensagem para o centralizador.
        """
        if self.centralizador_connection:
            try:
                await self.centralizador_connection.send(json.dumps(message))
                # Tratar o recebimento de um novo servidor individual no centralizador. "Sucesso ao adicionar novo servidor individual"
                response = await self.centralizador_connection.recv()
                print(f"Resposta do centralizador: {response}")
            except Exception as e:
                print(f"Erro ao enviar mensagem para o centralizador: {e}")
        else:
            print("Nenhuma conexão com o centralizador.")

    def disconnect_centralizador(self):
        """
        Desconecta do centralizador.
        """
        if self.centralizador_connection:
            try:
                self.centralizador_connection.close()
                print("Conexão com o centralizador encerrada.")
            except Exception as e:
                print(f"Erro ao desconectar do centralizador: {e}")


    async def listen_to_centralizador(self):
        """
        Escuta mensagens do centralizador via WebSocket e processa os comandos recebidos.
        """
        if self.centralizador_connection:
            try:
                while True:
                    # Receber mensagem do centralizador
                    message = await self.centralizador_connection.recv()
                    print(f"Mensagem recebida do centralizador: {message}")

            except Exception as e:
                print(f"Erro ao escutar mensagens do centralizador: {e}")
        else:
            print("Nenhuma conexão ativa com o centralizador para escutar mensagens.")


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
#     "room_101": {
#         "connections": [websocket_client_1, websocket_client_2],  # Lista de conexões WebSocket conectadas ao quarto
#         "do_not_disturb": True,  # Estado "Não Perturbe"
#         "cleaning_requested": False  # Estado "Solicitação de Limpeza"
#     }
# }


# Tudo é o mesmo backend / servidor, mas com diferentes quartos e usuários associados a eles.
# O backend usara as mesmas credenciais de acesso da API mas com mesmo backend

# 1 quarto = 1 backend com mesma chave de acesso mas com dispositivos diferentes