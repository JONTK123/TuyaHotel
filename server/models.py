from pydantic import BaseModel
from typing import List, Optional, Dict

class Device(BaseModel):
    id: str
    name: str
    category_name: str
    category: str
    online: bool
    states: Optional[Dict[str, str]] = None # Deixa os states opcionais

class Room(BaseModel):
    room_id: str
    devices: List[Device]
