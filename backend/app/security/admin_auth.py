import logging
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
from redis.exceptions import RedisError

from app.config import settings
from app.redis import redis_client


logger = logging.getLogger("vertolit")

ADMIN_SESSION_PREFIX = "admin_session:"
ADMIN_COOKIE_NAME = "vertolit_admin_session"

SAFE_METHODS = {
    "GET",
    "HEAD",
    "OPTIONS",
}


bearer_scheme = HTTPBearer(
    auto_error=False,
)


def build_admin_session_key(
    token: str,
) -> str:
    return f"{ADMIN_SESSION_PREFIX}{token}"


def validate_admin_origin(
    request: Request,
) -> None:
    if request.method.upper() in SAFE_METHODS:
        return

    origin = request.headers.get("origin")

    if not origin:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail="Missing Origin header",
        )

    if (
        origin
        not in settings.allowed_cors_origins
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail="Invalid request origin",
        )


async def create_admin_session() -> str:
    token = secrets.token_urlsafe(32)

    try:
        await redis_client.set(
            build_admin_session_key(token),
            "1",
            ex=(
                settings
                .admin_session_ttl_seconds
            ),
        )

    except RedisError as exc:
        logger.error(
            "Admin session store unavailable "
            "action=create error=%s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=(
                status
                .HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Admin authentication "
                "service unavailable"
            ),
        ) from exc

    return token


async def delete_admin_session(
    token: str,
) -> None:
    try:
        await redis_client.delete(
            build_admin_session_key(token)
        )

    except RedisError as exc:
        logger.error(
            "Admin session store unavailable "
            "action=delete error=%s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=(
                status
                .HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Admin authentication "
                "service unavailable"
            ),
        ) from exc


async def require_admin(
    request: Request,
    credentials: (
        HTTPAuthorizationCredentials | None
    ) = Depends(bearer_scheme),
) -> str:
    token: str | None = None
    authenticated_with_cookie = False

    if credentials is not None:
        if (
            credentials.scheme.lower()
            != "bearer"
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_401_UNAUTHORIZED
                ),
                detail=(
                    "Invalid authentication scheme"
                ),
            )

        token = credentials.credentials

    if token is None:
        token = request.cookies.get(
            ADMIN_COOKIE_NAME
        )

        if token is not None:
            authenticated_with_cookie = True

    if not token:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Admin authentication required"
            ),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if authenticated_with_cookie:
        validate_admin_origin(request)

    try:
        exists = await redis_client.exists(
            build_admin_session_key(token)
        )

    except RedisError as exc:
        logger.error(
            "Admin session store unavailable "
            "action=validate error=%s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=(
                status
                .HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Admin authentication "
                "service unavailable"
            ),
        ) from exc

    if not exists:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Admin session expired or invalid"
            ),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return token