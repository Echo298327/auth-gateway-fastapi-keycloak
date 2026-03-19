from fastapi import FastAPI
from .routes import user, health, organization


def init_routes(app: FastAPI):
    app.include_router(health.router, tags=["health"])
    app.include_router(user.router, tags=["user"])
    app.include_router(organization.router, tags=["organization"])
