import asyncio
from fastapi import HTTPException, APIRouter
from server.websocket_manager import WebSocketManager
from server.database import db, COLLECTION_ROOMS, COLLECTION_DEVICE_LOGS
from server.tuya_setup import initialize_tuya_openapi

router = APIRouter()
openapi = initialize_tuya_openapi()

class MockTuyaAPI:
    def __init__(self):
        self.devices = {
            "vdevo173316521541939": {
                "id": "vdevo173316521541939",
                "name": "Lampada Inteligente",
                "category": "dj",
                "category_name": "Lampada",
                "states": {
                    "switch_led": "ON"
                },
            },
            "6836066470039f3b913c": {
                "id": "6836066470039f3b913c",
                "name": "Interruptor Inteligente",
                "category": "kg",
                "category_name": "Switch",
                "states": {
                    "switch_1": "OFF",
                    "switch_2": "OFF",
                    "switch_3": "OFF"
                },
            },
            "vdevo173455209899022": {
                "id": "vdevo173455209899022",
                "name": "NH-YM 蓝牙mesh 2L 单零火-vdevo",
                "category": "kg",
                "category_name": "Switch",
                "states": {
                    "switch_1": "OFF",
                    "switch_2": "OFF",
                    "switch_3": "OFF"
                },
            },
        }

    def get(self, endpoint):
        if "/v1.3/iot-03/devices" in endpoint:
            return {
                "success": True,
                "result": list(self.devices.values())
            }
        elif "/shadow/properties" in endpoint:
            device_id = endpoint.split("/")[-3]
            if device_id in self.devices:
                device = self.devices[device_id]
                return {
                    "success": True,
                    "result": {
                        "properties": [
                            {"code": k, "value": v}
                            for k, v in device["states"].items()
                        ]
                    }
                }
        elif "/v2.0/cloud/thing/" in endpoint:
            device_id = endpoint.split("/")[-1]
            if device_id in self.devices:
                device = self.devices[device_id]
                return {
                    "success": True,
                    "result": {
                        "custom_name": device["name"],
                        "category": device["category"],
                        "is_online": True,
                    }
                }
        return {"success": False, "msg": "Endpoint not found"}

    def post(self, endpoint, body):
        device_id = endpoint.split("/")[-3]
        if device_id in self.devices:
            if "switch_led" in body.get("properties", {}):
                self.devices[device_id]["states"]["switch_led"] = body["properties"]["switch_led"]
            if body.get("switch_code") in self.devices[device_id]["states"]:
                self.devices[device_id]["states"][body["switch_code"]] = body["switchEnable"]
            return {"success": True}
        return {"success": False, "msg": "Device not found"}

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

async def get_device_state(device_id):
    try:
        general_info_response = openapi.get(f"/v2.0/cloud/thing/{device_id}")
        general_info = general_info_response.get("result", {})

        properties_response = openapi.get(f"/v2.0/cloud/thing/{device_id}/shadow/properties")
        properties = properties_response.get("result", {}).get("properties", [])

        device_name = general_info.get("custom_name", "Unnamed Device").strip()
        device_data = {
            "id": device_id,
            "name": general_info.get("custom_name", "Unnamed Device"),
            "category": general_info.get("category", "unknown"),
            "Online": general_info.get("is_online", False),
            "states": {}
        }

        for prop in properties:
            code = prop.get("code")
            value = prop.get("value")
            device_data["states"][code] = "ON" if value else "OFF"

        return device_data

    except Exception as e:
        print(f"Erro ao obter estado do dispositivo {device_id}: {e}")
        return None

@router.post("/devices/{device_id}/freeze")
async def freeze_device(device_id: str):
    try:
        response = openapi.post(
            f"/v2.0/cloud/thing/{device_id}/freeze",
            {"state": 1}
        )
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

@router.post("/devices/{device_id}/unfreeze")
async def unfreeze_device(device_id: str):
    try:
        response = openapi.post(
            f"/v2.0/cloud/thing/{device_id}/freeze",
            {"state": 0}
        )
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

@router.post("/devices/{device_id}/switch_off")
async def switch_off_device(device_id: str):
    try:
        response = openapi.post(
            f"/v2.0/cloud/thing/{device_id}/shadow/properties/issue",
            {"properties": {"switch_led": False}}
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

@router.post("/devices/{device_id}/switch_on")
async def switch_on_device(device_id: str):
    try:
        response = openapi.post(
            f"/v2.0/cloud/thing/{device_id}/shadow/properties/issue",
            {"properties": {"switch_led": True}}
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

@router.post("/devices/{device_id}/DoNotDisturbActivate")
async def do_not_disturb_activate(device_id: str):
    try:
        response = openapi.post(
            f"/v1.0/electric-energy/{device_id}/actions/switch",
            {"switchEnable": True, "switch_code": "switch_1"}
        )
        if response.get("success"):
            return {"message": f"Device {device_id} switched successfully."}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Error switching device {device_id}: {response.get('msg')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

@router.post("/devices/{device_id}/DoNotDisturbDeactivate")
async def do_not_disturb_deactivate(device_id: str):
    try:
        response = openapi.post(
            f"/v1.0/electric-energy/{device_id}/actions/switch",
            {"switchEnable": False, "switch_code": "switch_1"}
        )
        if response.get("success"):
            return {"message": f"Device {device_id} switched successfully."}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Error switching device {device_id}: {response.get('msg')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

@router.post("/devices/{device_id}/CleaningActivate")
async def cleaning_activate(device_id: str):
    try:
        response = openapi.post(
            f"/v1.0/electric-energy/{device_id}/actions/switch",
            {"switchEnable": True, "switch_code": "switch_2"}
        )
        if response.get("success"):
            return {"message": f"Device {device_id} switched successfully."}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Error switching device {device_id}: {response.get('msg')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

@router.post("/devices/{device_id}/CleaningDeactivate")
async def cleaning_deactivate(device_id: str):
    try:
        response = openapi.post(
            f"/v1.0/electric-energy/{device_id}/actions/switch",
            {"switchEnable": False, "switch_code": "switch_2"}
        )
        if response.get("success"):
            return {"message": f"Device {device_id} switched successfully."}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Error switching device {device_id}: {response.get('msg')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

@router.post("/devices/{device_id}/BellActivate")
async def bell_activate(device_id: str):
    try:
        response = openapi.post(
            f"/v1.0/electric-energy/{device_id}/actions/switch",
            {"switchEnable": True, "switch_code": "switch_3"}
        )
        if response.get("success"):
            return {"message": f"Device {device_id} switched successfully."}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Error switching device {device_id}: {response.get('msg')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

@router.post("/devices/{device_id}/BellDeactivate")
async def bell_deactivate(device_id: str):
    try:
        response = openapi.post(
            f"/v1.0/electric-energy/{device_id}/actions/switch",
            {"switchEnable": False, "switch_code": "switch_3"}
        )
        if response.get("success"):
            return {"message": f"Device {device_id} switched successfully."}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Error switching device {device_id}: {response.get('msg')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )
