from os import getenv

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from database.constant import (
    COLLECT_MAX_OVERFLOW,
    COLLECT_POOL_SIZE,
    CONNECTION_TIMEOUT_SECOND,
    MAX_OVERFLOW,
    POOL_SIZE,
    POOL_TIMEOUT_SECOND,
)
from database.enum import EnvironmentType

load_dotenv()


ENVIRONMENT = getenv("ENVIRONMENT", None)


if ENVIRONMENT == EnvironmentType.DEV:
    MYSQL_URL = getenv("LOCAL_MYSQL_URL", None)
    mysql_engine = create_async_engine(
        MYSQL_URL, pool_pre_ping=True, echo=False, pool_size=POOL_SIZE, max_overflow=MAX_OVERFLOW
    )
    collection_mysql_engine = create_async_engine(
        MYSQL_URL,
        pool_pre_ping=True,
        pool_size=COLLECT_POOL_SIZE,
        max_overflow=COLLECT_MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT_SECOND,
        connect_args={"connect_timeout": CONNECTION_TIMEOUT_SECOND},
    )
elif ENVIRONMENT == EnvironmentType.TEST:
    MYSQL_URL = getenv("TEST_DATABASE_URL", None)
    mysql_engine = create_async_engine(
        MYSQL_URL, pool_pre_ping=True, echo=False, pool_size=POOL_SIZE, max_overflow=MAX_OVERFLOW
    )
    collection_mysql_engine = create_async_engine(
        MYSQL_URL,
        pool_pre_ping=True,
        pool_size=COLLECT_POOL_SIZE,
        max_overflow=COLLECT_MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT_SECOND,
        connect_args={"connect_timeout": CONNECTION_TIMEOUT_SECOND},
    )
else:
    MYSQL_URL = getenv("MYSQL_URL", None)
    mysql_engine = create_async_engine(
        MYSQL_URL,
        pool_pre_ping=True,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT_SECOND,
        connect_args={"connect_timeout": CONNECTION_TIMEOUT_SECOND},
    )

    collection_mysql_engine = create_async_engine(
        MYSQL_URL,
        pool_pre_ping=True,
        pool_size=COLLECT_POOL_SIZE,
        max_overflow=COLLECT_MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT_SECOND,
        connect_args={"connect_timeout": CONNECTION_TIMEOUT_SECOND},
    )


mysql_session_factory = sessionmaker(bind=mysql_engine, class_=AsyncSession, expire_on_commit=False)
collection_mysql_session_factory = sessionmaker(
    bind=collection_mysql_engine, class_=AsyncSession, expire_on_commit=False
)

MySQLBase = declarative_base()
