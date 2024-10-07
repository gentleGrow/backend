import asyncio

from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.common.middleware.constant import REQUEST_TIMEOUT_SECOND

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT_SECOND) 
        except asyncio.TimeoutError:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Request timed out")
