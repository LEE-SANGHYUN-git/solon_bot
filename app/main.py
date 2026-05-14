from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import summarize
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행되는 lifespan 이벤트 핸들러."""
    print(f"🚀 {settings.APP_NAME} 서버 시작 (v{settings.APP_VERSION})")
    yield
    print("🛑 서버 종료")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Gemini API를 활용한 텍스트 요약 서비스",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summarize.router, prefix="/api/v1", tags=["요약"])


@app.get("/", tags=["Health Check"])
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy"}
