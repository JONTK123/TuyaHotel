from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio

load_dotenv()

# Configurações do MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_ROOMS = "rooms"

# Inicializar cliente MongoDB
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]

# Teste de conexao
async def test_connection():
    collections = await db.list_collection_names()
    print(f"Conexão bem-sucedida! Coleções disponíveis: {collections}")

asyncio.create_task(test_connection())
