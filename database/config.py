from os import getenv

from dotenv import load_dotenv

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from database.constant import (
    DEV_COLLECT_MAX_OVERFLOW,
    DEV_COLLECT_POOL_SIZE,
    DEV_MAX_OVERFLOW,
    DEV_POOL_SIZE,
    PROD_COLLECT_MAX_OVERFLOW,
    PROD_COLLECT_POOL_SIZE,
    PROD_MAX_OVERFLOW,
    PROD_POOL_SIZE,
    POOL_TIMEOUT_SECOND,
    CONNECTION_TIMEOUT_SECOND,
)
from database.enum import EnvironmentType

load_dotenv()


ENVIRONMENT = getenv("ENVIRONMENT", None)
QUERY_LOG = getenv("QUERY_LOG", False)


if ENVIRONMENT == EnvironmentType.LOCAL:
    MYSQL_URL = getenv("DEV_MYSQL_URL", None)
    mysql_engine = create_async_engine(
        url=MYSQL_URL, pool_pre_ping=True, echo=False, pool_size=DEV_POOL_SIZE, max_overflow=DEV_MAX_OVERFLOW
    )
    collection_mysql_engine = create_async_engine(
        MYSQL_URL,
        pool_pre_ping=True,
        pool_size=DEV_COLLECT_POOL_SIZE,
        max_overflow=DEV_COLLECT_MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT_SECOND,
        connect_args={"connect_timeout": CONNECTION_TIMEOUT_SECOND},
    )

    # [INFO] api 별 쿼리 실행 계획 확인을 위한 custom 이벤트 리스너
    if QUERY_LOG:
        @event.listens_for(mysql_engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            full_query = statement % parameters
            print(full_query)
            print("_____")
elif ENVIRONMENT == EnvironmentType.DEV:
    MYSQL_URL = getenv("DEV_MYSQL_URL", None)
    mysql_engine = create_async_engine(
        url=MYSQL_URL, pool_pre_ping=True, echo=False, pool_size=DEV_POOL_SIZE, max_overflow=DEV_MAX_OVERFLOW
    )
    collection_mysql_engine = create_async_engine(
        MYSQL_URL,
        pool_pre_ping=True,
        pool_size=DEV_COLLECT_POOL_SIZE,
        max_overflow=DEV_COLLECT_MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT_SECOND,
        connect_args={"connect_timeout": CONNECTION_TIMEOUT_SECOND},
    )
elif ENVIRONMENT == EnvironmentType.PROD:
    MYSQL_URL = getenv("PROD_MYSQL_URL", None)
    mysql_engine = create_async_engine(
        MYSQL_URL,
        pool_pre_ping=True,
        pool_size=PROD_POOL_SIZE,
        max_overflow=PROD_MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT_SECOND,
        connect_args={"connect_timeout": CONNECTION_TIMEOUT_SECOND},
    )

    collection_mysql_engine = create_async_engine(
        MYSQL_URL,
        pool_pre_ping=True,
        pool_size=PROD_COLLECT_POOL_SIZE,
        max_overflow=PROD_COLLECT_MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT_SECOND,
        connect_args={"connect_timeout": CONNECTION_TIMEOUT_SECOND},
    )
else:
    raise ValueError("환경변수 설정이 잘못되었습니다.")


mysql_session_factory = sessionmaker(bind=mysql_engine, class_=AsyncSession, expire_on_commit=False)
collection_mysql_session_factory = sessionmaker(
    bind=collection_mysql_engine, class_=AsyncSession, expire_on_commit=False
)

MySQLBase = declarative_base()
