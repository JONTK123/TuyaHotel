from starlette.websockets import WebSocket
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.websockets import WebSocketDisconnect
from server.tuya_setup import initialize_tuya_openapi, initialize_tuya_openpulsar
from server.websocket_manager import websocket_manager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from server.database import db, COLLECTION_ROOMS
import asyncio
import threading
import json


load_dotenv()
app = FastAPI()

main_loop = asyncio.get_event_loop()

# Configurar CORS para permitir requisições do frontend
origins = [
    "http://localhost:3000",  # URL do React durante o desenvolvimento
    "http://localhost:3001",  # Certifique-se de incluir essa porta
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004"

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openapi = initialize_tuya_openapi()


# Cria o loop de eventos dedicado para o Tuya Pulsar
pulsar_loop = asyncio.new_event_loop()

# Listener para mensagens do Tuya Pulsar
def message_listener(msg):
    print(f"Mensagem recebida do Tuya Pulsar: {msg}")
    try:

        # Prepara a mensagem para enviar ao frontend
        message = {
            "type": "pulsar_notification",
            "data": msg  # Envia o objeto diretamente, sem json.dumps
        }

        # Notificação para todos os clientes conectados a este backend
        asyncio.run_coroutine_threadsafe(
            websocket_manager.send_message(ROOM_ID, json.dumps(message)),  # Converte a mensagem completa para JSON
            main_loop  # Passa o loop principal explicitamente
        )
    except Exception as e:
        print(f"Erro ao processar mensagem do Tuya Pulsar: {e}")

# Função para iniciar o listener do Tuya Pulsar
def start_pulsar_listener():
    asyncio.set_event_loop(pulsar_loop)
    initialize_tuya_openpulsar(message_listener)
    print("Tuya Pulsar Listener iniciado.")
    pulsar_loop.run_forever()

# Inicia o listener do Tuya Pulsar em uma thread separada
pulsar_thread = threading.Thread(target=start_pulsar_listener, daemon=True)
pulsar_thread.start()

# Função para obter o estado do dispositivo via API Tuya
async def get_device_state():
    response = openapi.get(f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties")
    return response.get("result")
# Endpoint WebSocket para notificações
@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    # Conecta o cliente ao quarto especificado
    await websocket_manager.connect(websocket, ROOM_ID)

    # Envia informações iniciais para o cliente
    await websocket.send_text(json.dumps({
        "type": "room_number",
        "data": ROOM_ID
    }))
    await websocket.send_text(json.dumps({
        "type": "device_id",
        "data": DEVICE_ID
    }))

    # Estado anterior do dispositivo
    previous_state = None

    try:
        while True:
            try:
                # Obtém o estado atual do dispositivo
                current_state = await get_device_state()

                # Verifica mudanças no estado do dispositivo
                if current_state != previous_state:
                    # Atualiza o estado do dispositivo em `rooms`
                    update_device_status(ROOM_ID, DEVICE_ID, current_state)

                    # Envia a atualização para os clientes conectados
                    await websocket.send_json({
                        "type": "device_state",
                        "data": current_state
                    })

                    # Atualiza o estado anterior
                    previous_state = current_state

                await asyncio.sleep(5)  # Aguarda 5 segundos antes da próxima verificação

            except Exception as e:
                print(f"Erro ao enviar informações do dispositivo: {e}")
                break

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, ROOM_ID)
        print("WebSocket desconectado")

room_id = "room_101"
devices = [
    {"id": "device_1", "name": "Lamp", "status": "OFF"},
    {"id": "device_2", "name": "Fan", "status": "ON"}
]

@app.post("/rooms")
async def insert_room_with_devices(room_id, devices):
    """
    Insere um quarto com dispositivos no banco de dados.
    """
    try:
        room_data = {
            "room_id": room_id,
            "connections": [],  # Inicialmente vazio
            "devices": devices,
            "do_not_disturb": False,
            "cleaning_requested": False
        }

        result = await db[COLLECTION_ROOMS].insert_one(room_data)
        print(f"Quarto {room_id} inserido com sucesso. ID do documento: {result.inserted_id}")
    except Exception as e:
        print(f"Erro ao inserir quarto: {str(e)}")

# Função para atualizar o estado do dispositivo na estrutura centralizada
def update_device_status(room_id, device_id, current_state):
    """
    Atualiza o estado de um dispositivo específico na estrutura centralizada `rooms`.
    """
    if room_id in websocket_manager.rooms:
        devices = websocket_manager.rooms[room_id]["devices"]
        for device in devices:
            if device["id"] == device_id:
                device["status"] = current_state  # Atualiza o estado do dispositivo
                print(f"Estado do dispositivo {device_id} no quarto {room_id} atualizado: {current_state}")
                return
    else:
        print(f"Quarto {room_id} ou dispositivo {device_id} não encontrado na estrutura centralizada.")

@app.get("/devices")
async def list_devices():
    try:
        # Faz a chamada para o endpoint de listagem de dispositivos
        response = openapi.get("/v1.3/iot-03/devices")

        if response.get("success"):
            return {"devices": response.get("result")}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao listar dispositivos: {response.get('msg')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

# Endpoint raiz para teste
@app.get("/")
async def root():
    return {"message": "Bem vindo ao painel de controle dos dispositivos Tuya!"}
@app.post("/devices/{device_id}/freeze")
async def freeze_device(device_id: str):
    try:
        # Configurar payload para a requisição
        body = {
            "state": 1  # Define o estado como '1' para congelar o dispositivo
        }

        # Faz a chamada à API da Tuya para congelar o dispositivo
        response = openapi.post(
            f"/v2.0/cloud/thing/{device_id}/freeze",
            body  # Passa o payload como dicionário
        )

        # Verifica se a resposta foi bem-sucedida
        if response.get("success"):
            return {"message": f"Dispositivo {device_id} foi congelado com sucesso."}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao congelar o dispositivo {device_id}: {response.get('msg')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao tentar congelar o dispositivo: {str(e)}"
        )

@app.post("/devices/{device_id}/unfreeze")
async def unfreeze_device(device_id: str):
    try:
        # Configurar payload para a requisição
        body = {
            "state": 0, # Certifique-se de que "unfreeze" é o código correto para esta ação
        }

        # Faz a chamada à API da Tuya para descongelar o dispositivo
        response = openapi.post(
            f"/v2.0/cloud/thing/{device_id}/freeze", # Endpoint correto
            body # Passa o payload no formato esperado pela biblioteca
        )

        # Verifica se a resposta foi bem-sucedida
        if response.get("success"):
            return {"message": f"Dispositivo {device_id} foi descongelado com sucesso."}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao descongelar o dispositivo {device_id}: {response.get('msg')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao tentar descongelar o dispositivo: {str(e)}"
        )
# Enviar comando para ligar o dispositivo

# Enviar comando para desligar o dispositivo
@app.post("/devices/{device_id}/switch_off")
async def switch_off_device(device_id: str):
    try:
        body = {
            "properties": {
                "switch_led": False  # Ajusta a propriedade para desligar
            }
        }
        response = openapi.post(
            f"/v2.0/cloud/thing/{device_id}/shadow/properties/issue",
            body
        )

        if response.get("success"):
            return {"message": f"Device {device_id} turned off successfully."}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Error turning off device {device_id}: {response.get('msg')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

@app.post("/devices/{device_id}/switch_on")
async def switch_on_device(device_id: str):
    try:
        body = {
            "properties": {
                "switch_led": True  # Substitua por "switch_1" ou outro código correto
            }
        }
        response = openapi.post(
            f"/v2.0/cloud/thing/{device_id}/shadow/properties/issue",
            body
        )

        if response.get("success"):
            return {"message": f"Device {device_id} turned on successfully."}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Error turning on device {device_id}: {response.get('msg')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

# 1.Add dispositivos IoT no projeto Tuya
# 2.Listar dispositivos disponíveis
# 3.Criar quartos e associar dispositivos e salvar no Banco de Dados
# 4.Carregar dados do banco no backend e sicronizar com websocket
# 5.Efetuar as funcoes da Tuya API get_device_state e switch_off_device por exemplo
# (PRECISO FILTRAR ESSES DADOS PARA SALVAR NO BANCO DE DADOS E ENVIAR PARA O FRONTEND SO O Q PRECISA, NOME, SWTICH_LED, ID POR EXEMPLO)
# 6.Salvar no banco de dados o estado do dispositivo com update_device_state toda vez que houver uma mudança de estado

# 1.Frontend do quarto define status de limpeza e não perturbe e passa para o backend
# 2.Backend salva no banco de dados e sincroniza com websocket
# 3.Envia o status para outra tela frontend Tela de monitoramento central

