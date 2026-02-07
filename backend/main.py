from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from source.config.database import init_db
from source.config.cloudinary import init_cloudinary
from source.config.redis_connection import get_redis_client
from source.utils.local_embeddings_generator import get_model
from source.utils.semantic_cache import SemanticCache
from source.api import register_routes
from source.logging import configure_logging, LogLevels

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    configure_logging(LogLevels.info)

    # Database setup and GridFS bucket initialization
    client, database, bucket = await init_db()
    app.state.db_client = client
    app.state.db = database
    app.state.gridfs_bucket = bucket


    await init_cloudinary()

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
    client.close()

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