from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import init_db
from app.config.cloudinary import init_cloudinary
from app.config.redis_connection import get_redis_client
from app.routes.user_prompts import router as user_prompts_router
from app.routes.user import router as user_router
from app.routes.super_admin import router as super_admin_router
from app.routes.admin import router as admin_router
from app.utils.local_embeddings_generator import get_model
from app.utils.semantic_cache import SemanticCache


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code

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

app.include_router(user_prompts_router)
app.include_router(user_router)
app.include_router(super_admin_router)
app.include_router(admin_router)