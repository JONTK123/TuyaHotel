from starlette.websockets import WebSocket
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.websockets import WebSocketDisconnect
from server.tuya_setup import initialize_tuya_openapi, initialize_tuya_openpulsar
from server.websocket_manager import websocket_manager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from server.database import db, COLLECTION_ROOMS
from server.models import Room
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

pulsar_loop = asyncio.new_event_loop()


# Mudar isso
DEVICE_CONFIGS = {
    "lampada": {
        "type": "lampada",
        "state_fields": ["switch_led"],
    },
    "interruptor": {
        "type": "interruptor",
        "state_fields": ["switch_1", "switch_2", "switch_3"],
    },
    # Dispositivos pre definidos na Tuya e que serao usados no quarto do hotel
}
# Listener para mensagens do Tuya Pulsar - Eventos inesperados
def message_listener(msg):
    print(f"Mensagem recebida do Tuya Pulsar: {msg}")
    try:
        # Prepara a mensagem no formato esperado pelo frontend
        message = {
            "type": "pulsar_notification",
            "data": msg  # Dados brutos do Tuya Pulsar
        }

        # Envia a mensagem para todos os clientes conectados
        asyncio.run_coroutine_threadsafe(
            websocket_manager.broadcast(message),  # Broadcast para todos os clientes
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
async def get_device_state(device_id, device_type):
    try:
        # 1. Obter informações gerais do dispositivo
        general_info_response = openapi.get(f"/v2.0/cloud/thing/{device_id}")
        if isinstance(general_info_response, str):  # Verifica se a resposta é uma string
            general_info_response = json.loads(general_info_response)  # Parse JSON string
        general_info = general_info_response.get("result", {})

        # 2. Obter propriedades específicas do dispositivo
        properties_response = openapi.get(f"/v2.0/cloud/thing/{device_id}/shadow/properties")
        if isinstance(properties_response, str): # Verifica se a resposta é uma string
            properties_response = json.loads(properties_response)  # Parse JSON string
        properties = properties_response.get("result", {}).get("properties", [])

        # 3. Processar os dados do dispositivo
        state_fields = DEVICE_CONFIGS.get(device_type, {}).get("state_fields", [])
        device_data = process_device_data(
            device_id=device_id,
            general_info=general_info,
            properties=properties,
            state_fields=state_fields
        )
        return device_data

    except json.JSONDecodeError as e:
        print(f"Erro ao fazer parse da resposta JSON para o dispositivo {device_id}: {e}")
        return None
    except Exception as e:
        print(f"Erro ao obter estado do dispositivo {device_id}: {e}")
        return None

def process_device_data(device_id, general_info, properties, state_fields):
    """
    Processa os dados do dispositivo com base no tipo e nas propriedades retornadas pela API.
    """
    # Dados processados
    device_data = {
        "id": device_id,
        "name": general_info.get("name", "Unnamed Device"),
        "category": general_info.get("category", "unknown"),
        "isOnline": general_info.get("is_online", False),
        "states": {}
    }

    # Processa os campos de estado específicos
    for prop in properties:
        code = prop.get("code")
        value = prop.get("value")

        if code in state_fields:
            device_data["states"][code] = "ON" if value else "OFF"

    return device_data

# Endpoint WebSocket para notificações
@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Dispositivos do quarto / Projeto Tuya
    # Esses dados virao do banco de dados quando o cliente, no frontend, adicionar um novo quarto com seus dispositivos
    # Eh necessario banco de dados pois iremos puxar os dados dele e podemos replicar o sistema em outros hoteis
    devices = [
        {
            "id": "vdevo173316521541939",
            "type": "lampada",
        },
        {
            "id": "6836066470039f3b913c",
            "type": "interruptor",
        }
    ]

    try:
        while True:
            all_device_states = []

            for device in devices:
                # Envia a solicitação para obter o estado do dispositivo, passando seu ID e seu tipo
                device_state = await get_device_state(device["id"], device["type"])
                if device_state:
                    all_device_states.append(device_state)

            # Envia as atualizações para o frontend, e salva no banco de dados nesse formato:
            # {
            #     "devices": [
            #         {
            #             "id": "vdevo173316521541939",
            #             "name": "Lampada Inteligente",
            #             "category": "dj",
            #             "isOnline": true,
            #             "states": {
            #                 "switch_led": "ON"
            #             }
            #         },
            #         {
            #             "id": "6836066470039f3b913c",
            #             "name": "Interruptor Inteligente",
            #             "category": "kg",
            #             "isOnline": true,
            #             "states": {
            #                 "switch_1": "OFF",
            #                 "switch_2": "ON",
            #                 "switch_3": "OFF"
            #             }
            #         }
            #     ]
            # }

            # Prepara a mensagem para enviar ao frontend
            message = {
                "type": "device_state",
                "data": all_device_states  # Envia o objeto diretamente, sem json.dumps
            }

            await websocket.send_json(message)

            # Aguarda 5 segundos antes de atualizar novamente
            await asyncio.sleep(4.5)

    except WebSocketDisconnect:
        print("WebSocket desconectado")

    except Exception as e:
        print(f"Erro no WebSocket: {e}")

@app.post("/rooms")
async def insert_room_with_devices(room: Room):
    """
    Insere um quarto com dispositivos no banco de dados.
    """
    try:
        # Converte os objetos Device para dicionários
        room_data = {
            "room_id": room.room_id,
            "connections": [],
            "devices": [device.dict() for device in room.devices],  # Converte cada Device para dicionário
            "do_not_disturb": False,
            "cleaning_requested": False
        }

        print("Dados para inserção no MongoDB:", room_data)

        # Insere os dados no banco de dados
        result = await db[COLLECTION_ROOMS].insert_one(room_data)
        print(f"Quarto {room.room_id} inserido com sucesso.")
        return {"message": f"Quarto {room.room_id} adicionado com sucesso!"}
    except Exception as e:
        print(f"Erro ao inserir quarto: {str(e)}")
        return {"error": str(e)}

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
# Como mudou o dispositivo foco para o interruptor, preciso mudar o pulsar message para esse dispositivo
# 7.Salvar no banco de dados o estado do dispositivo com update_device_state toda vez que houver uma mudança de estado

# 1.Frontend do quarto define status de limpeza e não perturbe e passa para o backend
# 2.Backend salva no banco de dados e sincroniza com websocket
# 3.Envia o status para outra tela frontend Tela de monitoramento central

# Device Management - Query Device Details
# /v2.0/cloud/thing/vdevo173316521541939

# Device control - Query Properties
# v2.0/cloud/thing/vdevo173316521541939/shadow/properties?codes=switch_led

# Elimine redundancia do state_fields e do DEVICE_CONFIGS


