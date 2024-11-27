from os import getenv

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware

from app.api.asset.v1.router import asset_stock_router
from app.api.asset.v2.router import asset_stock_router_v2
from app.api.auth.v1.router import auth_router
from app.api.chart.v1.router import chart_router
from app.common.middleware.request import TimeoutMiddleware

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

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chart_router, prefix="/api/chart", tags=["chart"])
app.include_router(asset_stock_router, prefix="/api", tags=["asset"])
app.include_router(asset_stock_router_v2, prefix="/api/asset", tags=["asset_v2"])

# 테스트 서버에서는 모니터링을 열지 않아 임시 주석처리 했습니다.
# Instrumentator().instrument(app).expose(app, include_in_schema=False, endpoint="/metrics")


@app.get("/health")
async def health():
    return {"status": "ok"}
