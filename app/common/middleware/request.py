import asyncio
import time
from fastapi import HTTPException, status, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.common.middleware.constant import REQUEST_TIMEOUT_SECOND
import logging

logger = logging.getLogger("request_middleware")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("/home/backend/request.log", delay=False)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)


class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT_SECOND)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="요청 시간이 초과 되었습니다.")

class RequestTimerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response: Response = await call_next(request) 
        process_time = time.time() - start_time
        
        # 요청 URL, 응답 상태 코드, 처리 시간 로그
        logger.info(
            f"요청 URL: {request.url.path} | "
            f"상태 코드: {response.status_code} | "
            f"처리 시간: {process_time:.4f} 초"
        )
        
        # X-Process-Time 헤더 추가 (선택사항)
        response.headers["X-Process-Time"] = str(process_time)
        
        return response