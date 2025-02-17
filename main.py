from os import getenv

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from starlette.middleware.sessions import SessionMiddleware

from app.api.asset.v1.router import asset_stock_router
from app.api.auth.v1.router import auth_router
from app.api.chart.v1.router import chart_router
from app.api.event.v1.router import event_router
from app.common.middleware.request import TimeoutMiddleware
from database.enum import EnvironmentType

load_dotenv()


SESSION_KEY = getenv("SESSION_KEY", None)
SENTRY_DSN = getenv("SENTRY_DSN", None)
ENVIRONMENT = getenv("ENVIRONMENT", None)
ALLOWED_ORIGINS = getenv("ALLOWED_ORIGINS", "").split(",") if ENVIRONMENT == EnvironmentType.PROD.value else ["*"]

app = FastAPI(
    docs_url=None if ENVIRONMENT == EnvironmentType.PROD.value else "/docs",
    redoc_url=None if ENVIRONMENT == EnvironmentType.PROD.value else "/redoc",
    openapi_url=None if ENVIRONMENT == EnvironmentType.PROD.value else "/openapi.json",
    debug=ENVIRONMENT != EnvironmentType.PROD.value
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
)

app.add_middleware(SessionMiddleware, secret_key=SESSION_KEY)
app.add_middleware(TimeoutMiddleware)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chart_router, prefix="/api/chart", tags=["chart"])
app.include_router(asset_stock_router, prefix="/api/asset", tags=["asset"])
app.include_router(event_router, prefix="/api/event", tags=["event"])



@app.get("/health")
async def health():
    return {"status": "ok"}

