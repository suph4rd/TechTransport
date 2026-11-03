from fastapi import FastAPI
from app.core.errors import register_exception_handlers
from app.core.lifespan import Lifespan
from app.auth.endpoints import router as auth_router
from app.core.routers.health import router as health_router

app = FastAPI(title="Tech Transport API", version="0.1.0", lifespan=Lifespan)
register_exception_handlers(app)
app.include_router(health_router)

app.include_router(auth_router)
