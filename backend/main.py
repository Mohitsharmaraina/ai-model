from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from source.config.database import init_db
from source.config.s3 import init_s3
from source.config.redis_connection import get_redis_client
from source.utils.local_embeddings_generator import get_model
from source.utils.semantic_cache import SemanticCache
from source.api import register_routes
from source.logging import configure_logging, LogLevels
from openai import OpenAI
from config_secrets import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    configure_logging(LogLevels.info)

    # openai client
    open_ai_api_key= settings.open_ai_access_key
    openAI_client = OpenAI(api_key=open_ai_api_key)
    app.state.client = openAI_client

    # Database setup and GridFS bucket initialization
    client, database, bucket = await init_db()
    app.state.db_client = client
    app.state.db = database
    app.state.gridfs_bucket = bucket


    s3_client = init_s3()
    app.state.s3_client = s3_client

    # redis and semantic cache setup
    redis_client = await get_redis_client()
    cache = SemanticCache(redis_client)
    await cache._create_index_if_not_exists() # ensure index is created once at setup
    # store in app.state for access in routes
    app.state.semantic_cache = cache
    get_model()
    yield

    # Shutdown code (if any)
    await redis_client.close()
    await client.close()

app = FastAPI(lifespan=lifespan, title="AI Model Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def health_check():
    return {"Welcome to fastAPI server":"The server is up and running!"}

register_routes(app)