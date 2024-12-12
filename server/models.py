from pydantic import BaseModel
from typing import List, Dict

# Estrutura de dados das variaveis passadas do frontend para o backend salvar no BD, deve seguir esse padrao
class Device(BaseModel):
    id: str
    name: str
    status: str

class Room(BaseModel):
    room_id: str
    devices: List[Device]