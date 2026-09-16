import secrets

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

from app.config import settings
from app.schemas.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
)
from app.security.admin_auth import (
    ADMIN_COOKIE_NAME,
    create_admin_session,
    delete_admin_session,
    require_admin,
)
from app.security.admin_login_rate_limit import (
    admin_login_rate_limit,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.post(
    "/login",
    response_model=AdminLoginResponse,
    dependencies=[Depends(admin_login_rate_limit)],
)
async def admin_login(
    login_data: AdminLoginRequest,
    response: Response,
):
    password_is_valid = secrets.compare_digest(
        login_data.password,
        settings.admin_password,
    )

    if not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password",
        )

    token = await create_admin_session()

    response.set_cookie(
        key=ADMIN_COOKIE_NAME,
        value=token,
        max_age=settings.admin_session_ttl_seconds,
        httponly=True,
        secure=settings.admin_cookie_secure,
        samesite="lax",
        path="/",
    )

    return AdminLoginResponse(
        access_token=token,
        expires_in=settings.admin_session_ttl_seconds,
    )


@router.get("/session")
async def admin_session(
    _token: str = Depends(require_admin),
):
    return {
        "authenticated": True,
    }


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def admin_logout(
    response: Response,
    token: str = Depends(require_admin),
):
    await delete_admin_session(token)

    response.delete_cookie(
        key=ADMIN_COOKIE_NAME,
        path="/",
        secure=settings.admin_cookie_secure,
        httponly=True,
        samesite="lax",
    )
