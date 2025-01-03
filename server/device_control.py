from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from tests.MockTuyaAPI import MockTuyaAPI
from server.database import COLLECTION_ROOMS, db

# Configuração do Mock API
router = APIRouter()
openapi = MockTuyaAPI()

load_dotenv()

# Congelar dispositivo
@router.post("/devices/{device_id}/freeze")
async def freeze_device(device_id: str):
    try:
        response = openapi.post(
            f"/v2.0/cloud/thing/{device_id}/freeze",
            {"state": 1}
        )
        if response.get("success"):
            return {"message": f"Dispositivo {device_id} foi congelado com sucesso."}
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao congelar o dispositivo {device_id}: {response.get('msg')}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao tentar congelar o dispositivo: {str(e)}"
        )

# Descongelar dispositivo
@router.post("/devices/{device_id}/unfreeze")
async def unfreeze_device(device_id: str):
    try:
        response = openapi.post(
            f"/v2.0/cloud/thing/{device_id}/freeze",
            {"state": 0}
        )
        if response.get("success"):
            return {"message": f"Dispositivo {device_id} foi descongelado com sucesso."}
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao descongelar o dispositivo {device_id}: {response.get('msg')}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao tentar descongelar o dispositivo: {str(e)}"
        )

# Ligar dispositivo
@router.post("/devices/{device_id}/switch_on")
async def switch_on_device(device_id: str):
    try:
        response = openapi.post(
            f"/v2.0/cloud/thing/{device_id}/shadow/properties/issue",
            {"properties": {"switch_led": True}}
        )
        if response.get("success"):
            return {"message": f"Dispositivo {device_id} foi ligado com sucesso."}
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao ligar o dispositivo {device_id}: {response.get('msg')}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao tentar ligar o dispositivo: {str(e)}"
        )

# Desligar dispositivo
@router.post("/devices/{device_id}/switch_off")
async def switch_off_device(device_id: str):
    try:
        response = openapi.post(
            f"/v2.0/cloud/thing/{device_id}/shadow/properties/issue",
            {"properties": {"switch_led": False}}
        )
        if response.get("success"):
            return {"message": f"Dispositivo {device_id} foi desligado com sucesso."}
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao desligar o dispositivo {device_id}: {response.get('msg')}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao tentar desligar o dispositivo: {str(e)}"
        )

# Não Perturbe - Ativar
@router.post("/devices/{device_id}/DoNotDisturbActivate")
async def do_not_disturb_activate(device_id: str):
    try:
        response = openapi.post(
            f"/v1.0/electric-energy/{device_id}/actions/switch",
            {"switchEnable": True, "switch_code": "switch_1"}
        )
        if response.get("success"):
            await db[COLLECTION_ROOMS].update_one(
                {"devices.id": device_id},
                {"$set": {"devices.$.states.switch_1": "ON"}}
            )
            return {"message": f"Do Not Disturb ativado para o dispositivo {device_id}."}
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao ativar Não Perturbe no dispositivo {device_id}: {response.get('msg')}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao tentar ativar Não Perturbe: {str(e)}"
        )

# Não Perturbe - Desativar
@router.post("/devices/{device_id}/DoNotDisturbDeactivate")
async def do_not_disturb_deactivate(device_id: str):
    try:
        response = openapi.post(
            f"/v1.0/electric-energy/{device_id}/actions/switch",
            {"switchEnable": False, "switch_code": "switch_1"}
        )
        if response.get("success"):
            await db[COLLECTION_ROOMS].update_one(
                {"devices.id": device_id},
                {"$set": {"devices.$.states.switch_1": "OFF"}}
            )
            return {"message": f"Do Not Disturb desativado para o dispositivo {device_id}."}
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao desativar Não Perturbe no dispositivo {device_id}: {response.get('msg')}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao tentar desativar Não Perturbe: {str(e)}"
        )

# Limpeza - Ativar
@router.post("/devices/{device_id}/CleaningActivate")
async def cleaning_activate(device_id: str):
    try:
        response = openapi.post(
            f"/v1.0/electric-energy/{device_id}/actions/switch",
            {"switchEnable": True, "switch_code": "switch_2"}
        )
        if response.get("success"):
            await db[COLLECTION_ROOMS].update_one(
                {"devices.id": device_id},
                {"$set": {"devices.$.states.switch_2": "ON"}}
            )
            return {"message": f"Limpeza ativada para o dispositivo {device_id}."}
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao ativar Limpeza no dispositivo {device_id}: {response.get('msg')}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao tentar ativar Limpeza: {str(e)}"
        )

# Limpeza - Desativar
@router.post("/devices/{device_id}/CleaningDeactivate")
async def cleaning_deactivate(device_id: str):
    try:
        response = openapi.post(
            f"/v1.0/electric-energy/{device_id}/actions/switch",
            {"switchEnable": False, "switch_code": "switch_2"}
        )
        if response.get("success"):
            await db[COLLECTION_ROOMS].update_one(
                {"devices.id": device_id},
                {"$set": {"devices.$.states.switch_2": "OFF"}}
            )
            return {"message": f"Limpeza desativada para o dispositivo {device_id}."}
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao desativar Limpeza no dispositivo {device_id}: {response.get('msg')}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao tentar desativar Limpeza: {str(e)}"
        )

# Campainha - Ativar
@router.post("/devices/{device_id}/BellActivate")
async def bell_activate(device_id: str):
    try:
        response = openapi.post(
            f"/v1.0/electric-energy/{device_id}/actions/switch",
            {"switchEnable": True, "switch_code": "switch_3"}
        )
        if response.get("success"):
            await db[COLLECTION_ROOMS].update_one(
                {"devices.id": device_id},
                {"$set": {"devices.$.states.switch_3": "ON"}}
            )
            return {"message": f"Campainha ativada para o dispositivo {device_id}."}
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao ativar Campainha no dispositivo {device_id}: {response.get('msg')}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao tentar ativar Campainha: {str(e)}"
        )

# Campainha - Desativar
@router.post("/devices/{device_id}/BellDeactivate")
async def bell_deactivate(device_id: str):
    try:
        response = openapi.post(
            f"/v1.0/electric-energy/{device_id}/actions/switch",
            {"switchEnable": False, "switch_code": "switch_3"}
        )
        if response.get("success"):
            await db[COLLECTION_ROOMS].update_one(
                {"devices.id": device_id},
                {"$set": {"devices.$.states.switch_3": "OFF"}}
            )
            return {"message": f"Campainha desativada para o dispositivo {device_id}."}
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao desativar Campainha no dispositivo {device_id}: {response.get('msg')}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao tentar desativar Campainha: {str(e)}"
        )


# from dotenv import load_dotenv
# from fastapi import APIRouter, HTTPException
# from tests.MockTuyaAPI import MockTuyaAPI
# from server.database import COLLECTION_ROOMS, db
# from server.tuya_setup import initialize_tuya_openapi
#
# router = APIRouter()
#
# # openapi = initialize_tuya_openapi()
# openapi = MockTuyaAPI()
#
# load_dotenv()
# @router.post("/devices/{device_id}/freeze")
# async def freeze_device(device_id: str):
#     try:
#         body = {
#             "state": 1
#         }
#         response = openapi.post(
#             f"/v2.0/cloud/thing/{device_id}/freeze",
#             body
#         )
#         if response.get("success"):
#             return {"message": f"Dispositivo {device_id} foi congelado com sucesso."}
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Erro ao congelar o dispositivo {device_id}: {response.get('msg')}"
#             )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Erro interno ao tentar congelar o dispositivo: {str(e)}"
#         )
#
# @router.post("/devices/{device_id}/unfreeze")
# async def unfreeze_device(device_id: str):
#     try:
#         body = {
#             "state": 0,
#         }
#         response = openapi.post(
#             f"/v2.0/cloud/thing/{device_id}/freeze",
#             body
#         )
#         if response.get("success"):
#             return {"message": f"Dispositivo {device_id} foi descongelado com sucesso."}
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Erro ao descongelar o dispositivo {device_id}: {response.get('msg')}"
#             )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Erro interno ao tentar descongelar o dispositivo: {str(e)}"
#         )
#
# @router.post("/devices/{device_id}/switch_off")
# async def switch_off_device(device_id: str):
#     try:
#         body = {
#             "properties": {
#                 "switch_led": False
#             }
#         }
#         response = openapi.post(
#             f"/v2.0/cloud/thing/{device_id}/shadow/properties/issue",
#             body
#         )
#         if response.get("success"):
#             return {"message": f"Device {device_id} turned off successfully."}
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Error turning off device {device_id}: {response.get('msg')}"
#             )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal error: {str(e)}"
#         )
#
# @router.post("/devices/{device_id}/switch_on")
# async def switch_on_device(device_id: str):
#     try:
#         body = {
#             "properties": {
#                 "switch_led": True
#             }
#         }
#         response = openapi.post(
#             f"/v2.0/cloud/thing/{device_id}/shadow/properties/issue",
#             body
#         )
#         if response.get("success"):
#             return {"message": f"Device {device_id} turned on successfully."}
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Error turning on device {device_id}: {response.get('msg')}"
#             )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal error: {str(e)}"
#          )
#
# @router.post("/devices/{device_id}/DoNotDisturbActivate")
# async def do_not_disturb_activate(device_id: str):
#     try:
#         body = {
#             "switchEnable": True,
#             "switch_code": "switch_1"
#         }
#         response = openapi.post(f"/v1.0/electric-energy/{device_id}/actions/switch", body)
#         if response.get("success"):
#             return {"message": f"Device {device_id} switched successfully."}
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Error switching device {device_id}: {response.get('msg')}"
#             )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal error: {str(e)}"
#         )
#
# @router.post("/devices/{device_id}/DoNotDisturbDeactivate")
# async def do_not_disturb_deactivate(device_id: str):
#     try:
#         body = {
#             "switchEnable": False,
#             "switch_code": "switch_1"
#         }
#         response = openapi.post(f"/v1.0/electric-energy/{device_id}/actions/switch", body)
#         if response.get("success"):
#             return {"message": f"Device {device_id} switched successfully."}
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Error switching device {device_id}: {response.get('msg')}"
#             )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal error: {str(e)}"
#         )
#
# @router.post("/devices/{device_id}/CleaningActivate")
# async def cleaning_activate(device_id: str):
#     try:
#         body = {
#             "switchEnable": True,
#             "switch_code": "switch_2"
#         }
#         response = openapi.post(f"/v1.0/electric-energy/{device_id}/actions/switch", body)
#         if response.get("success"):
#             return {"message": f"Device {device_id} switched successfully."}
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Error switching device {device_id}: {response.get('msg')}"
#             )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal error: {str(e)}"
#         )
#
# @router.post("/devices/{device_id}/CleaningDeactivate")
# async def cleaning_deactivate(device_id: str):
#     try:
#         body = {
#             "switchEnable": False,
#             "switch_code": "switch_2"
#         }
#         response = openapi.post(f"/v1.0/electric-energy/{device_id}/actions/switch", body)
#         if response.get("success"):
#             return {"message": f"Device {device_id} switched successfully."}
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Error switching device {device_id}: {response.get('msg')}"
#             )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal error: {str(e)}"
#         )
#
# @router.post("/devices/{device_id}/BellDeactivate")
# async def bell_deactivate(device_id: str):
#     try:
#         body = {
#             "switchEnable": False,
#             "switch_code": "switch_3"
#         }
#         response = openapi.post(f"/v1.0/electric-energy/{device_id}/actions/switch", body)
#         if response.get("success"):
#             return {"message": f"Device {device_id} switched successfully."}
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Error switching device {device_id}: {response.get('msg')}"
#             )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal error: {str(e)}"
#         )
#
# @router.post("/devices/{device_id}/BellActivate")
# async def bell_activate(device_id: str):
#     try:
#         body = {
#             "switchEnable": True,
#             "switch_code": "switch_3"
#         }
#         response = openapi.post(f"/v1.0/electric-energy/{device_id}/actions/switch", body)
#         if response.get("success"):
#             return {"message": f"Device {device_id} switched successfully."}
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Error switching device {device_id}: {response.get('msg')}"
#             )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal error: {str(e)}"
#         )
#
#
# # ---------------------------------------------------------------------------------------
# # ---------------------------------------------------------------------------------------
#
# # Apenas para teste
# #
# # @router.post("/devices/{device_id}/DoNotDisturbActivate")
# # async def do_not_disturb_activate(device_id: str):
# #     try:
# #         # Atualizar o estado do dispositivo no banco de dados
# #         await db[COLLECTION_ROOMS].update_one(
# #             {"devices.id": device_id},
# #             {"$set": {"devices.$.states.switch_3": "ON"}}
# #         )
# #         return {"message": f"Do Not Disturb activated for device {device_id}."}
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Internal error: {str(e)}"
# #         )
# #
# #
# # @router.post("/devices/{device_id}/DoNotDisturbDeactivate")
# # async def do_not_disturb_deactivate(device_id: str):
# #     try:
# #         # Atualizar o estado do dispositivo no banco de dados
# #         await db[COLLECTION_ROOMS].update_one(
# #             {"devices.id": device_id},
# #             {"$set": {"devices.$.states.switch_3": "OFF"}}
# #         )
# #         return {"message": f"Do Not Disturb deactivated for device {device_id}."}
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Internal error: {str(e)}"
# #         )
# #
# #
# # @router.post("/devices/{device_id}/CleaningActivate")
# # async def cleaning_activate(device_id: str):
# #     try:
# #         # Atualizar o estado do dispositivo no banco de dados
# #         await db[COLLECTION_ROOMS].update_one(
# #             {"devices.id": device_id},
# #             {"$set": {"devices.$.states.switch_1": "ON"}}
# #         )
# #         return {"message": f"Cleaning activated for device {device_id}."}
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Internal error: {str(e)}"
# #         )
# #
# #
# # @router.post("/devices/{device_id}/CleaningDeactivate")
# # async def cleaning_deactivate(device_id: str):
# #     try:
# #         # Atualizar o estado do dispositivo no banco de dados
# #         await db[COLLECTION_ROOMS].update_one(
# #             {"devices.id": device_id},
# #             {"$set": {"devices.$.states.switch_1": "OFF"}}
# #         )
# #         return {"message": f"Cleaning deactivated for device {device_id}."}
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Internal error: {str(e)}"
# #         )
# #
# #
# # @router.post("/devices/{device_id}/BellActivate")
# # async def bell_activate(device_id: str):
# #     try:
# #         # Atualizar o estado do dispositivo no banco de dados
# #         await db[COLLECTION_ROOMS].update_one(
# #             {"devices.id": device_id},
# #             {"$set": {"devices.$.states.switch_2": "ON"}}
# #         )
# #         return {"message": f"Bell activated for device {device_id}."}
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Internal error: {str(e)}"
# #         )
# #
# #
# # @router.post("/devices/{device_id}/BellDeactivate")
# # async def bell_deactivate(device_id: str):
# #     try:
# #         # Atualizar o estado do dispositivo no banco de dados
# #         await db[COLLECTION_ROOMS].update_one(
# #             {"devices.id": device_id},
# #             {"$set": {"devices.$.states.switch_2": "OFF"}}
# #         )
# #         return {"message": f"Bell deactivated for device {device_id}."}
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"Internal error: {str(e)}"
# #         )