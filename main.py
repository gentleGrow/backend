from os import getenv
import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from app.common.util.logging import logging
from app.api.asset.v1.router import asset_stock_router
from app.api.auth.v1.router import auth_router
from app.api.chart.v1.router import chart_router
from app.common.middleware.request_timeout import TimeoutMiddleware
from app.module.asset.model import Asset  # noqa: F401 > table 생성 시 필요합니다.
from app.module.auth.model import User  # noqa: F401 > table 생성 시 필요합니다.

app = FastAPI()

load_dotenv()


SESSION_KEY = getenv("SESSION_KEY", None)
SENTRY_DSN = getenv("SENTRY_DSN", None)
ENVIRONMENT = getenv("ENVIRONMENT", None)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=SESSION_KEY)
app.add_middleware(TimeoutMiddleware)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        sentry_sdk.capture_message(f"401 Unauthorized access attempt: {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
    

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chart_router, prefix="/api/chart", tags=["chart"])
app.include_router(asset_stock_router, prefix="/api", tags=["asset"])
