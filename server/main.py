from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from server.tuya_setup import initialize_tuya_openapi, initialize_tuya_openpulsar
from server.database import db, COLLECTION_ROOMS, COLLECTION_DEVICE_LOGS
from server.models import Room
from server.device_control import router as device_control_router
from server.websocket_manager import WebSocketManager
import asyncio

load_dotenv()
app = FastAPI()

# Configurar loop principal do asyncio
main_loop = asyncio.get_event_loop()
app.include_router(device_control_router, prefix="/api")

# Configurar CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
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

# Configurações de dispositivos
DEVICE_STATES = {
    "Lâmpada Inteligente": {
        "category_name": "Light Source",
        "state_fields": ["switch_led"],
    },

    "Interruptor": {
        "category_name": "Switch",
        "state_fields": ["switch_1", "switch_2", "switch_3"],
    }
}

# Listener para mensagens do Tuya Pulsar
def message_listener(msg):
    print(f"Mensagem recebida do Tuya Pulsar: {msg}")
    try:
        device_id = msg.get("devId")
        room = asyncio.run(fetch_room_by_device(device_id))

        if room:
            message = {
                "type": "pulsar_notification",
                "data": msg
            }
            print(f"Mensagem enviada para o WebSocket: {message}")
            asyncio.run(WebSocketManager.send_to_room(room["room_id"], message))
            asyncio.run(save_device_log(device_id, msg))

    except Exception as e:
        print(f"Erro ao processar mensagem do Tuya Pulsar: {e}")

async def fetch_room_by_device(device_id):
    try:
        room = await db[COLLECTION_ROOMS].find_one({"devices.id": device_id})
        return room
    except Exception as e:
        print(f"Erro ao buscar quarto no banco de dados: {e}")
        return None

async def save_device_log(device_id, log_data):
    try:
        log_entry = {
            "device_id": device_id,
            "log": log_data
        }
        await db[COLLECTION_DEVICE_LOGS].insert_one(log_entry)
    except Exception as e:
        print(f"Erro ao salvar log no device_logs: {e}")

async def update_device_state_if_changed(room_id, device_id, new_state):
    try:
        room = await db[COLLECTION_ROOMS].find_one({"room_id": room_id})
        if not room:
            return False

        devices = room.get("devices", [])
        for device in devices:
            if device["id"] == device_id:
                if device.get("states") == new_state:
                    return False

                await db[COLLECTION_ROOMS].update_one(
                    {"room_id": room_id, "devices.id": device_id},
                    {"$set": {"devices.$.states": new_state}}
                )
                return True

        return False
    except Exception as e:
        print(f"Erro ao atualizar estado do dispositivo: {e}")
        return False

async def get_device_state(device_id):
    try:
        # Consultar informações gerais do dispositivo
        general_info_response = openapi.get(f"/v2.0/cloud/thing/{device_id}")
        general_info = general_info_response.get("result", {})

        # Consultar propriedades do dispositivo
        properties_response = openapi.get(f"/v2.0/cloud/thing/{device_id}/shadow/properties")
        properties = properties_response.get("result", {}).get("properties", [])

        device_name = general_info.get("custom_name", "Unnamed Device").strip()  # Remove espaços extras
        device_config = DEVICE_STATES.get(device_name, {})  # Retorna um dicionário vazio se não encontrar
        state_fields = device_config.get("state_fields", [])

        # Construir o objeto de dados do dispositivo
        device_data = {
            "id": device_id,
            "name": general_info.get("custom_name", "Unnamed Device"),
            "category": general_info.get("category", "unknown"),
            "Online": general_info.get("is_online", False),
            "states": {}
        }

        # Preencher os estados com base nos campos relevantes
        for prop in properties:
            code = prop.get("code")
            value = prop.get("value")
            if code in state_fields:  # Somente incluir os campos configurados
                device_data["states"][code] = "ON" if value else "OFF"

        print(f"Final Device Data: {device_data}")  # Debug
        return device_data

    except Exception as e:
        print(f"Erro ao obter estado do dispositivo {device_id}: {e}")
        return None


@app.websocket("/ws/notifications/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await WebSocketManager.connect(websocket, room_id)

    try:
        # Obtenha informações do quarto do banco de dados
        room = await db[COLLECTION_ROOMS].find_one({"room_id": room_id})
        if not room:
            await websocket.send_json({"error": "Quarto não encontrado."})
            return

        devices = room.get("devices", [])

        while True:
            all_device_states = []
            for device in devices:
                device_state = await get_device_state(device["id"])
                if device_state:
                    updated = await update_device_state_if_changed(
                        room_id, device["id"], device_state["states"]
                    )
                    print(f"Estado do dispositivo {device_state} atualizado? {updated}")
                    if updated:
                        all_device_states.append(device_state)

            if all_device_states:
                message = {
                    "type": "device_state",
                    "data": all_device_states
                }

                print(f"Enviando estados dos dispositivos para {room_id}: {message}")
                await WebSocketManager.send_to_room(room_id, message)

            await asyncio.sleep(4.5)

    except WebSocketDisconnect:
        WebSocketManager.disconnect(websocket, room_id)
    except Exception as e:
        print(f"Erro no WebSocket do quarto {room_id}: {e}")

@app.post("/add_rooms")
async def insert_room_with_devices(room: Room):
    try:
        room_data = {
            "room_id": room.room_id,
            "connections": [],
            "devices": [device.dict() for device in room.devices],
        }
        await db[COLLECTION_ROOMS].insert_one(room_data)
        return {"message": f"Quarto {room.room_id} adicionado com sucesso!"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/devices")
async def list_devices():
    try:
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

@app.get("/")
async def root():
    return {"message": "Bem-vindo ao painel de controle dos dispositivos Tuya!"}


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


# 1. Salva no banco de dados o quarto com os dispositivos associados.
# 2. Puxa quarto pelo deviceID. deviceID eh obtido pelo Tuya Pulsar.
# 3. Envia mensagem para o quarto especifico via websocket.
# 4. Salva em uma nova coelcao chamada device_logs.

# 1. Abre websocket para o quarto especifico room_ID.
# 2. Puxa todas informacoes do quarto ( seus dispositivos )
# 3. Puxa informacoes do dispositivo via API Tuya.
# 4. Se houver mudancas -> envia informacoes para o frontend via websocket e salva no BD Se nao, nada atualiza
#
# Caso queira re aproveitar o BD em outro hotel, sera necessario remover o device ID ( pois ele eh unico ) e remover os states dos dispositivos. ( esses dados serao atualizados no outro sistema )


# No primeiro estagio, o usuario ira salvar somente o quarto e os dispositivos associados a ele.
# ( retornados do endpoint devices da Tuya API ) ( EXEMPLO ):
# Exemplo de como sera salvo no banco de dados:
# {
#     "room_id": "quarto_1",
#     "connections": [],
#     "devices": [
#         {
#             "id": "vdevo173316521541939",
#             "name": "Lampada Inteligente",
#             "category": "dj",
#             "Online": true,
#             "states": {}
#         }
#     ]
# }

# No estagio final, sera salvo assim no banco de dados, depois de obter os estados ( EXEMPLO ):
# Exemplo de como sera salvo no banco de dados:
# {
#     "room_id": "quarto_1",
#     "connections": [],
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
