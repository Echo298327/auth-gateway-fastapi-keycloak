from fastapi import FastAPI
from core.config import settings
from api import init_routes

app = FastAPI(title="Gateway",)
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
