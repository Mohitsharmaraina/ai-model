from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db

from app.routes.user_prompts import router as user_prompts_router
from app.routes.user import router as user_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    await init_db()
    yield
    # Shutdown code (if any)

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