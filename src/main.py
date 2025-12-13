from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .app.auth.router import router as router_auth
from src.app.dao.api_alembic import admin_router
from src.app.auth.role_router import router as role_router

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[dict, None]:
    logger.info("Application initialization...")
    yield
    logger.info("Shutting down the application...")


def create_app() -> FastAPI:
        app = FastAPI(
            title = "Аутенфикация",
            version = "0.0.1",
            lifespan=lifespan,
        )
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        register_routers(app)
        
        return app
    
def register_routers(app: FastAPI) -> None:
    root_router = APIRouter()
    
    
    @root_router.get("/", tags=["Root"])
    def home_page():
        return {"message": "Authentication service is running"}
    
    app.include_router(root_router, tags=["Root"])
    app.include_router(router_auth, prefix="/auth", tags=["Authentication"])
    app.include_router(admin_router, prefix="/alembic", tags=["Alembic"])
    app.include_router(role_router, prefix="/roles", tags=["Roles"])

app = create_app()


