from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.config import settings
from api import init_routes
from middleware.security_headers import SecurityHeadersMiddleware
from shared.logging import log_startup, log_shutdown

SERVICE_NAME = "Gateway"
VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_startup(
        service_name=SERVICE_NAME,
        version=VERSION,
        environment=settings.ENVIRONMENT,
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS
    )
    yield
    log_shutdown(SERVICE_NAME)


app = FastAPI(title=SERVICE_NAME, lifespan=lifespan)
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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
