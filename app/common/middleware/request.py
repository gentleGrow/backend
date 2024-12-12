import asyncio
from os import getenv

from dotenv import load_dotenv
from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.middleware.constant import REQUEST_TIMEOUT_SECOND

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)


class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT_SECOND)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="요청 시간이 초과 되었습니다.")
