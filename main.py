from os import getenv

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.asset.v1.router import asset_stock_router
from app.api.auth.v1.router import auth_router
from app.api.chart.v1.router import chart_router
from app.api.event.v1.router import event_router
from app.common.exception.base import AppException
from app.common.middleware.request import TimeoutMiddleware
from database.enum import EnvironmentType

load_dotenv()


SESSION_KEY = getenv("SESSION_KEY", None)
SENTRY_DSN = getenv("SENTRY_DSN", None)
ENVIRONMENT = getenv("ENVIRONMENT", None)

if ENVIRONMENT == EnvironmentType.PROD.value:
    app = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        debug=False,
    )

    ALLOWED_ORIGINS = getenv("ALLOWED_ORIGINS", "").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
else:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.add_middleware(SessionMiddleware, secret_key=SESSION_KEY)
app.add_middleware(TimeoutMiddleware)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chart_router, prefix="/api/chart", tags=["chart"])
app.include_router(asset_stock_router, prefix="/api/asset", tags=["asset"])
app.include_router(event_router, prefix="/api/event", tags=["event"])


@app.exception_handler(AppException)
async def custom_app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail["message"],
            "code": exc.detail["code"],
            "status": exc.status_code,
            "path": request.url.path,
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
