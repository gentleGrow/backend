import asyncio
from os import getenv

import pytest
from dotenv import load_dotenv
from httpx import AsyncClient
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.common.auth.security import verify_jwt_token
from app.module.auth.constant import DUMMY_USER_ID
from database.config import MySQLBase
from database.constant import DEV_POOL_SIZE
from database.dependency import get_mysql_session_router, get_redis_pool
from main import app

load_dotenv()


TEST_DATABASE_URL = getenv("TEST_DATABASE_URL", None)
test_engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True, poolclass=AsyncAdaptedQueuePool)
TestSessionLocal = sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

TEST_REDIS_HOST = getenv("TEST_REDIS_HOST", None)
TEST_REDIS_PORT = int(getenv("TEST_REDIS_PORT", 6379))


# [INFO] 세션 단위로 event loop를 관리하여 모든 테스트가 같은 루프에서 실행되도록 해야합니다.
@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def session():
    async def create_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(MySQLBase.metadata.create_all)

    async def drop_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(MySQLBase.metadata.drop_all)

    async with TestSessionLocal() as test_session:
        await create_tables()
        yield test_session
        await test_session.rollback()
        await drop_tables()


@pytest.fixture(scope="function")
async def redis_client():
    def get_test_redis_pool() -> Redis:
        pool = ConnectionPool(
            host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, max_connections=DEV_POOL_SIZE, decode_responses=True
        )
        return Redis(connection_pool=pool)

    redis = get_test_redis_pool()
    yield redis
    await redis.flushall()
    await redis.close()


@pytest.fixture(scope="function")
def override_dependencies(session, redis_client):
    async def override_get_mysql_session():
        return session

    async def override_redis_pool():
        return redis_client

    def override_verify_jwt_token():
        return {"user": DUMMY_USER_ID}

    app.dependency_overrides[verify_jwt_token] = override_verify_jwt_token
    app.dependency_overrides[get_mysql_session_router] = override_get_mysql_session
    app.dependency_overrides[get_redis_pool] = override_redis_pool
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def client(override_dependencies):
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
