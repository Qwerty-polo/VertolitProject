import pytest
from fastapi import Request
from starlette.responses import JSONResponse

from app.exception_handlers import global_exception_handler
from app.middleware.request_logging import request_logging_middleware


@pytest.mark.asyncio
async def test_request_logging_adds_request_id():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "query_string": b"",
        "server": ("test", 80),
        "client": ("test", 123),
        "scheme": "http",
    }

    request = Request(scope)

    async def call_next(request):
        return JSONResponse({"status": "ok"})

    response = await request_logging_middleware(
        request,
        call_next,
    )

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert request.state.request_id == response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_global_exception_handler():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/broken",
        "headers": [],
        "query_string": b"",
        "server": ("test", 80),
        "client": ("test", 123),
        "scheme": "http",
    }

    request = Request(scope)
    request.state.request_id = "test-request-id"

    response = await global_exception_handler(
        request,
        RuntimeError("Test error"),
    )

    assert response.status_code == 500
    assert b"Internal server error" in response.body
