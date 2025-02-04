from contextlib import asynccontextmanager
from os import getenv
from typing import AsyncGenerator

from dotenv import load_dotenv
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import collection_mysql_session_factory, mysql_session_factory
from database.constant import DEV_POOL_SIZE, PROD_POOL_SIZE, REDIS_SOCKET_CONNECTION_TIMEOUT_SECOND
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)


if ENVIRONMENT == EnvironmentType.LOCAL:
    REDIS_HOST = getenv("LOCAL_REDIS_HOST", None)
    REDIS_POOL_SIZE = DEV_POOL_SIZE
elif ENVIRONMENT == EnvironmentType.DEV:
    REDIS_HOST = getenv("DEV_REDIS_HOST", None)
    REDIS_POOL_SIZE = DEV_POOL_SIZE
elif ENVIRONMENT == EnvironmentType.PROD:
    REDIS_HOST = getenv("PROD_REDIS_HOST", None)
    REDIS_POOL_SIZE = PROD_POOL_SIZE
else:
    raise ValueError("환경변수 설정이 잘못되었습니다.")


REDIS_PORT = int(getenv("REDIS_PORT", 6379))


async def get_mysql_session_router() -> AsyncGenerator[AsyncSession, None]:
    session = mysql_session_factory()
    try:
        yield session
    finally:
        await session.close()


@asynccontextmanager
async def get_mysql_session() -> AsyncGenerator[AsyncSession, None]:
    session = collection_mysql_session_factory()
    try:
        yield session
    finally:
        await session.close()


def get_redis_pool() -> Redis:
    pool = ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        max_connections=REDIS_POOL_SIZE,
        decode_responses=True,
        socket_connect_timeout=REDIS_SOCKET_CONNECTION_TIMEOUT_SECOND,
        socket_timeout=REDIS_SOCKET_CONNECTION_TIMEOUT_SECOND,
    )
    return Redis(connection_pool=pool)
