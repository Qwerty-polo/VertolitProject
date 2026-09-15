import secrets

from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.config import settings
from app.redis import redis_client


ADMIN_SESSION_PREFIX = "admin_session:"
ADMIN_COOKIE_NAME = "vertolit_admin_session"


bearer_scheme = HTTPBearer(
    auto_error=False,
)


def build_admin_session_key(
    token: str,
) -> str:
    return f"{ADMIN_SESSION_PREFIX}{token}"


async def create_admin_session() -> str:
    token = secrets.token_urlsafe(32)

    await redis_client.set(
        build_admin_session_key(token),
        "1",
        ex=settings.admin_session_ttl_seconds,
    )

    return token


async def delete_admin_session(
    token: str,
) -> None:
    await redis_client.delete(
        build_admin_session_key(token)
    )


async def require_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials
    | None = Depends(bearer_scheme),
) -> str:
    token: str | None = None

    # Варіант 1:
    # Bearer token — потрібен для Swagger.
    if credentials is not None:
        if credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )

        token = credentials.credentials

    # Варіант 2:
    # HttpOnly cookie — для нашої admin.html.
    if token is None:
        token = request.cookies.get(
            ADMIN_COOKIE_NAME
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    exists = await redis_client.exists(
        build_admin_session_key(token)
    )

    if not exists:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin session expired or invalid",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return token