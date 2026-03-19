import httpx
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from core.config import settings
from auth_gateway_serverkit.keycloak.config import settings as kc_settings

router = APIRouter()

_health_client = httpx.AsyncClient(timeout=5)


@router.get("/health")
async def health():
    return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_200_OK)


@router.get("/readyz")
async def readyz():
    checks = {}

    try:
        client = settings.get_motor_client()
        await client.admin.command("ping")
        checks["mongodb"] = True
    except Exception:
        checks["mongodb"] = False

    try:
        resp = await _health_client.get(
            f"{kc_settings.SERVER_URL}/realms/{kc_settings.REALM}/.well-known/openid-configuration"
        )
        checks["keycloak"] = resp.status_code == 200
    except Exception:
        checks["keycloak"] = False

    all_healthy = all(checks.values())
    return JSONResponse(
        content={"status": "ready" if all_healthy else "not_ready", "checks": checks},
        status_code=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
