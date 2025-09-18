from fastapi import FastAPI
from .routes import user


def init_routes(app: FastAPI):
    app.include_router(user.router, tags=["user"])