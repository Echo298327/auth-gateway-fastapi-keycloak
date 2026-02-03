from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.config import settings
from api import init_routes
from shared.logging import log_header, log_ready, log_shutdown

SERVICE_NAME = "Gateway"
VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_header(SERVICE_NAME, VERSION)
    log_ready(
        service_name=SERVICE_NAME,
        environment=settings.ENVIRONMENT,
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS
    )
    yield
    log_shutdown(SERVICE_NAME)


app = FastAPI(title=SERVICE_NAME, lifespan=lifespan)
init_routes(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=settings.reload
    )
