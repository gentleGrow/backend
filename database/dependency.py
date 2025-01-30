from contextlib import asynccontextmanager
from os import getenv
from typing import AsyncGenerator

from dotenv import load_dotenv
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import collection_mysql_session_factory, mysql_session_factory
from database.constant import POOL_SIZE, REDIS_SOCKET_CONNECTION_TIMEOUT_SECOND
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)

if ENVIRONMENT == EnvironmentType.DEV:
    REDIS_HOST = getenv("LOCAL_REDIS_HOST", None)
else:
    REDIS_HOST = getenv("REDIS_HOST", None)

REDIS_PORT = int(getenv("REDIS_PORT", 6379))

TEST_REDIS_HOST = getenv("TEST_REDIS_HOST", None)
TEST_REDIS_PORT = int(getenv("TEST_REDIS_PORT", 6379))


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
        max_connections=POOL_SIZE,
        decode_responses=True,
        socket_connect_timeout=REDIS_SOCKET_CONNECTION_TIMEOUT_SECOND,
        socket_timeout=REDIS_SOCKET_CONNECTION_TIMEOUT_SECOND,
    )
    return Redis(connection_pool=pool)


def get_test_redis_pool() -> Redis:
    pool = ConnectionPool(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, max_connections=POOL_SIZE, decode_responses=True)
    return Redis(connection_pool=pool)
