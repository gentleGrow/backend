import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException


class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=10.0)  # Set 10 seconds timeout
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Request timed out")

