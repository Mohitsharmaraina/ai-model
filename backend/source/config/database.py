from pymongo import AsyncMongoClient # type: ignore
from gridfs.asynchronous import AsyncGridFSBucket
from beanie import init_beanie # pyright: ignore[reportMissingImports]
from source.models.user_models import ChatSession, User
from source.models.training_data_model import TrainingDataset
import config_secrets

# Call this from within your event loop to get beanie setup.

async def init_db():
     # Create Async PyMongo client
    client = AsyncMongoClient(config_secrets.settings.mongo_uri)
    database = client.AI_Model_Collections
    bucket = AsyncGridFSBucket(database, bucket_name="training_files")
    # Init beanie with the Product document class
    await init_beanie(database=database, document_models=[ ChatSession, User, TrainingDataset])

    return client, database, bucket