from fastapi import Request 
from starlette.middleware.base import BaseHTTPMiddleware
import time

from app.core.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next):
        start = time.perf_counter()
        logger.info(f"Incoming: {request.method} {request.url.path} | IP: {request.client.host}")
        resp = await call_next(request)
        end = (time.perf_counter()-start) *1000
        logger.info(f"Completed: {request.method} {request.url.path} | {resp.status_code} | {end:.2f}ms")
        return resp