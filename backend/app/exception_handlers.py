import logging

from fastapi import Request
from fastapi.responses import JSONResponse


logger = logging.getLogger("vertolit")


async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    request_id = getattr(request.state, "request_id", "unknown")

    logger.exception(
        "Unhandled exception on %s %s request_id=%s",
        request.method,
        request.url.path,
        request_id,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": "abc-123"
        }
    )
