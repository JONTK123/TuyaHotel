from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from server.tuya_setup import initialize_tuya_openapi, initialize_tuya_openpulsar
from server.database import db, COLLECTION_ROOMS, COLLECTION_DEVICE_LOGS
from server.models import Room
from server.device_control import router as device_control_router
from server.websocket_manager import WebSocketManager
import asyncio

from tests.MockTuyaAPI import MockTuyaAPI

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
    "http://localhost:3004",
    "http://localhost:3006"

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# openapi = initialize_tuya_openapi()
openapi = MockTuyaAPI()


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

async def update_device_state(room_id, device_id, current_device_state):
    try:
        room = await db[COLLECTION_ROOMS].find_one({"room_id": room_id})
        if not room:
            return False

        devices = room.get("devices", [])
        for device in devices:
            if device["id"] == device_id:
                device["states"] = current_device_state

                await db[COLLECTION_ROOMS].update_one(
                    {"room_id": room_id, "devices.id": device_id},
                    {"$set": {"devices.$.states": current_device_state}}
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

        return device_data

    except Exception as e:
        print(f"Erro ao obter estado do dispositivo {device_id}: {e}")
        return None

@app.websocket("/ws/device_panel/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await WebSocketManager.connect(websocket, room_id)

    try:
        # Obtenha informações do quarto do banco de dados
        room = await db[COLLECTION_ROOMS].find_one({"room_id": room_id})
        if not room:

            message = {
                "type": "error",
                "data": f"Quarto '{room_id}' não encontrado no banco de dados."
            }

            await websocket.send_json(message)
            return

        devices = room.get("devices", [])

        previous_device_states = {}

        while True:
            all_device_states = []
            for device in devices:
                current_device_state = await get_device_state(device["id"])
                if current_device_state:
                    previous_device_state = previous_device_states.get(device["id"])
                    if current_device_state != previous_device_state:
                        await update_device_state(room_id, device["id"], current_device_state["states"])
                        previous_device_states[device["id"]] = current_device_state

                    all_device_states.append(current_device_state)

            if all_device_states:
                message = {
                    "type": "device_state",
                    "data": all_device_states
                }

                print(f"Enviando estados dos dispositivos para {room_id}: {message}")
                await WebSocketManager.send_to_room(room_id, message)

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        WebSocketManager.disconnect(websocket, room_id)
    except Exception as e:
        print(f"Erro no WebSocket do quarto {room_id}: {e}")

@app.websocket("/ws/central_monitor")
async def central_monitor_websocket(websocket: WebSocket):
    await WebSocketManager.connect(websocket, "central_monitor")

    try:
        while True:
            # Consultar o banco de dados periodicamente
            rooms = await db[COLLECTION_ROOMS].find().to_list(1000)
            if rooms:
                data = [
                    {
                        "room_id": room["room_id"],
                        "devices": [
                            {
                                "id": device["id"],
                                "name": device["name"],
                                "category_name": device["category_name"],
                                "category": device["category"],
                                "states": {
                                    "do_not_disturb": (device.get("states") or {}).get("switch_1", "OFF"),
                                    "cleaning": (device.get("states") or {}).get("switch_2", "OFF"),
                                    "bell": (device.get("states") or {}).get("switch_3", "OFF")
                                } if device["name"] == "NH-YM 蓝牙mesh 2L 单零火-vdevo" else device["states"]
                            }
                            for device in room["devices"]
                        ],
                    }
                    for room in rooms
                ]

                message = {
                    "type": "room_switch",
                    "data": data
                }

                await websocket.send_json(message)

            else:
                message = {
                    "type": "error",
                    "data": "Nenhum quarto encontrado no banco de dados."
                }
                await websocket.send_json(message)

            await asyncio.sleep(2)  # Intervalo de 2 segundos
    except WebSocketDisconnect:
        WebSocketManager.disconnect(websocket, "central_monitor")
    except Exception as e:
        print(f"Erro no WebSocket do monitor central: {e}")

@app.post("/add_rooms")
async def insert_room_with_devices(room: Room):
    try:
        room_data = {
            "room_id": room.room_id,
            "devices": [device.dict() for device in room.devices],
        }

        existing_room = await db[COLLECTION_ROOMS].find_one({"room_id": room.room_id})
        if existing_room:
            # Update the devices in the existing room
            existing_devices = existing_room.get("devices", [])
            new_devices = room_data["devices"]

            # Merge existing devices with new devices
            device_ids = {device["id"] for device in existing_devices}
            for new_device in new_devices:
                if new_device["id"] in device_ids:
                    # Update existing device
                    await db[COLLECTION_ROOMS].update_one(
                        {"room_id": room.room_id, "devices.id": new_device["id"]},
                        {"$set": {"devices.$": new_device}}
                    )
                else:
                    # Add new device
                    await db[COLLECTION_ROOMS].update_one(
                        {"room_id": room.room_id},
                        {"$push": {"devices": new_device}}
                    )
        else:
            # Insert new room with devices
            await db[COLLECTION_ROOMS].insert_one(room_data)

        return {"message": f"Quarto {room.room_id} adicionado ou atualizado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/add_rooms")
# async def insert_room_with_devices(room: Room):
#     try:
#         room_data = {
#             "room_id": room.room_id,
#             "devices": [device.dict() for device in room.devices],
#         }
#         print(f"Dados processados para salvar: {room_data}")  # Log do que será salvo
#
#         existing_room = await db[COLLECTION_ROOMS].find_one({"room_id": room.room_id})
#         if existing_room:
#             print(f"Quarto já existe: {existing_room}")  # Quarto encontrado no BD
#             # Atualiza o quarto existente
#             ...
#         else:
#             print("Inserindo novo quarto no banco de dados.")  # Inserindo novo quarto
#             await db[COLLECTION_ROOMS].insert_one(room_data)
#
#         return {"message": f"Quarto {room.room_id} adicionado ou atualizado com sucesso!"}
#     except Exception as e:
#         print(f"Erro ao adicionar ou atualizar quarto: {e}")  # Log do erro
#         raise HTTPException(status_code=500, detail=str(e))

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

# ---------------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------------

# APENAS PARA TESTE
# @app.get("/devices")
# async def list_devices():
#     try:
#
#         DEVICES = {
#     "58d66e312239423c83d162d7": {
#         "name": "Lâmpada Inteligente",
#         "category_name": "Light Source",
#         "category": "dj"
#     },
#     "df4e4271a56d42a6a0633972": {
#         "name": "Interruptor",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "e2ea663b37e24557ba4b3009": {
#         "name": "NH-YM 蓝牙mesh 2L 单零火-vdevo",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "3240228c2c2a45acb123baff": {
#         "name": "Lâmpada Inteligente",
#         "category_name": "Light Source",
#         "category": "dj"
#     },
#     "b26389a806c24f56b83ef1f6": {
#         "name": "Interruptor",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "3d8f2037d7eb4e058cabf187": {
#         "name": "NH-YM 蓝牙mesh 2L 单零火-vdevo",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "cf0a78969a3d49eebfb3d8c3": {
#         "name": "Lâmpada Inteligente",
#         "category_name": "Light Source",
#         "category": "dj"
#     },
#     "f6ea3eb8bf404b36a0744ad5": {
#         "name": "Interruptor",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "c49dcc55ba7f437092304714": {
#         "name": "NH-YM 蓝牙mesh 2L 单零火-vdevo",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "d8f8a6497a794e6c8d3be235": {
#         "name": "Lâmpada Inteligente",
#         "category_name": "Light Source",
#         "category": "dj"
#     },
#     "80bb2ab393a44c4ab2f3f488": {
#         "name": "Interruptor",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "8e140d4ac98248d987393697": {
#         "name": "NH-YM 蓝牙mesh 2L 单零火-vdevo",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "d5a034bd4e3f4fdb853f705c": {
#         "name": "Lâmpada Inteligente",
#         "category_name": "Light Source",
#         "category": "dj"
#     },
#     "9e1a971d43b3454688f36111": {
#         "name": "Interruptor",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "48d20963bd474f37882888bf": {
#         "name": "NH-YM 蓝牙mesh 2L 单零火-vdevo",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "441b8a5a859b4c39abf1ca53": {
#         "name": "Lâmpada Inteligente",
#         "category_name": "Light Source",
#         "category": "dj"
#     },
#     "c7915e8ed9cc42bca03ebab2": {
#         "name": "Interruptor",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "c1ac7c76b1674ac0ae606774": {
#         "name": "NH-YM 蓝牙mesh 2L 单零火-vdevo",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "2ba7a3b9ae274294999aa195": {
#         "name": "Lâmpada Inteligente",
#         "category_name": "Light Source",
#         "category": "dj"
#     },
#     "64bb3609545e4f26919b5d46": {
#         "name": "Interruptor",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "aaa15d99a65041a183e483d4": {
#         "name": "NH-YM 蓝牙mesh 2L 单零火-vdevo",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "958358bf3a064e8389b4692f": {
#         "name": "Lâmpada Inteligente",
#         "category_name": "Light Source",
#         "category": "dj"
#     },
#     "93ba79e535854ba2b38f71c9": {
#         "name": "Interruptor",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "d55e44b3a45440078775c72b": {
#         "name": "NH-YM 蓝牙mesh 2L 单零火-vdevo",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "185ea02374414cef9ca73873": {
#         "name": "Lâmpada Inteligente",
#         "category_name": "Light Source",
#         "category": "dj"
#     },
#     "c8fece608e024ecf9c53feea": {
#         "name": "Interruptor",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "be08d674a0c84ab08375c123": {
#         "name": "NH-YM 蓝牙mesh 2L 单零火-vdevo",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "ddd5b18b75014124b9facf50": {
#         "name": "Lâmpada Inteligente",
#         "category_name": "Light Source",
#         "category": "dj"
#     },
#     "7c8109c10cbf49639990afcb": {
#         "name": "Interruptor",
#         "category_name": "Switch",
#         "category": "kg"
#     },
#     "783d0c451505455b9d047338": {
#         "name": "NH-YM 蓝牙mesh 2L 单零火-vdevo",
#         "category_name": "Switch",
#         "category": "kg"
#     }
#         }
#
#         # Converter o dicionário em uma lista
#         devices_list = [{"id": device_id, **device} for device_id, device in DEVICES.items()]
#
#         return {"devices": devices_list}
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Erro ao listar dispositivos: {str(e)}"
#         )


def convert_objectid_to_str(room):
    if "_id" in room:
        room["_id"] = str(room["_id"])
    return room

@app.get("/rooms")
async def list_rooms():
    try:
        # Consulta todos os quartos no banco de dados
        rooms = await db[COLLECTION_ROOMS].find().to_list(1000)

        # Converte ObjectId para string
        rooms = [convert_objectid_to_str(room) for room in rooms]

        # Retorna a lista de quartos
        return rooms
    except Exception as e:
        print(f"Erro ao listar quartos: {e}")  # Log do erro no console
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar quartos: {str(e)}"
        )

@app.delete("/delete_room/{room_id}")
async def delete_room(room_id: str):
    try:
        result = await db[COLLECTION_ROOMS].delete_one({"room_id": room_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Room not found")
        return {"message": f"Room {room_id} deleted successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting room: {str(e)}")
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
