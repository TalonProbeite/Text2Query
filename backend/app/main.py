from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager


from app.core.config import settings
from app.db.database import init_db
from app.core.logger import setup_logging
from app.route.auth_routes import router as auth_router
from app.models import ___init__
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.route.sql_routes import router as sql_router
from app.route.history_routes import router as history_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    setup_logging()
    yield
    pass
    

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(sql_router)
app.include_router(history_router)

app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


 
app.mount(
    "/",
    StaticFiles(directory=settings.static_dir,html=True),
    name="static",
    
)
