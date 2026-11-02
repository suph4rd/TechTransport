from fastapi import FastAPI
from app.errors import register_exception_handlers
from app.lifespan import Lifespan
from app.routers.health import router as health_router

app = FastAPI(title="Tech Transport API", version="0.1.0", lifespan=Lifespan)
register_exception_handlers(app)
app.include_router(health_router)
