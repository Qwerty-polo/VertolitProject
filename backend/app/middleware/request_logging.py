import logging
import time
import uuid

from fastapi import Request

logger = logging.getLogger("vertolit.request")


# кожен HTTP-запит автоматично логувався, расування і дебагу запитів
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start_time

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "%s %s %s %.3fs request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
        request_id,
    )

    return response
