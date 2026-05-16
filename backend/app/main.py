from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging
    logging.basicConfig(level=settings.log_level)
    yield


app = FastAPI(
    title="智能办公Agent API",
    description="全模态智能办公助手后端服务",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.chat import router as chat_router
from app.api.knowledge import router as knowledge_router
from app.api.tools import router as tools_router

app.include_router(chat_router)
app.include_router(knowledge_router)
app.include_router(tools_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
