from pymongo import AsyncMongoClient # type: ignore
from beanie import init_beanie # pyright: ignore[reportMissingImports]
from app.models import ChatSession, User
from config_secrets import settings

# Call this from within your event loop to get beanie setup.

async def init_db():
     # Create Async PyMongo client
    client = AsyncMongoClient(settings.mongo_uri)
    # Init beanie with the Product document class
    await init_beanie(database=client.AI_Model_Collections, document_models=[ ChatSession, User])