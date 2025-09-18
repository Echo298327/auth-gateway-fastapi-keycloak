from fastapi import FastAPI
from .routes import gateway


def init_routes(app: FastAPI):
    app.include_router(gateway.router)