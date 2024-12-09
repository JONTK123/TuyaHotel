from starlette.websockets import WebSocket
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.websockets import WebSocketDisconnect
from server.tuya_setup import initialize_tuya_openapi, initialize_tuya_openpulsar
from server.websocket_manager import websocket_manager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
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

DEVICE_ID = "vdevo173316521541939"
ROOM_ID = "101" #Ficticio

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
    await websocket_manager.connect(websocket, ROOM_ID)

    await websocket.send_text(json.dumps({
        "type": "room_number",
        "data": ROOM_ID
    }))

    await websocket.send_text(json.dumps({
        "type": "device_id",
        "data": DEVICE_ID
    }))

    previous_state = None  # Estado anterior do dispositivo
    try:
        while True:
            try:
                # Obtém o estado atual do dispositivo
                current_state = await get_device_state()

                # Verifica mudanças no estado do dispositivo
                if current_state != previous_state:
                    await websocket.send_json({
                        "type": "device_state",
                        "data": current_state

                    })

                    previous_state = current_state

                await asyncio.sleep(5)  # Aguarda 5 segundos antes da próxima verificação

            except Exception as e:
                print(f"Erro ao enviar informações do dispositivo: {e}")
                break

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        print("WebSocket desconectado")

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


# Sugestoes de diferentes abordagens:

# 1. Req uma vez e a cada notifiacao de mudanca, alterar o estado do dispositivo e atualizar
# 2. Botao para ficar atualizando e executando endpoint
# 3. ( Solucao atual ) Atualizar periodicamente com chamadas no backend e ir atualizando o FE

# Lista de IDs de dispositivos associados a cada quarto

# O backend associado ao Quarto é configurado para lidar apenas com os devices especificados
# Dois clientes (um gerente e um aplicativo de monitoramento) conectam-se ao backend para receber notificações e controlar o dispositivo daquele quarto
# Durante a conexão, eles são associados ao numero do quarto

