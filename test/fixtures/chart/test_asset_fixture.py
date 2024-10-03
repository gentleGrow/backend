import json

import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.investing.sources.enum import RicePeople
from app.module.asset.enum import Country, MarketIndex
from app.module.asset.schema import MarketIndexData
from app.module.chart.constant import INVESTMENT_TIP, REDIS_RICH_PICK_KEY, REDIS_RICH_PICK_NAME_KEY
from app.module.chart.repository import TipRepository


@pytest.fixture(scope="function")
async def setup_rich_pick_data(session: AsyncSession, redis_client: Redis):
    rich_stock_codes = json.dumps(["AAPL", "TSLA", "005930"])
    stock_name_map = json.dumps({"AAPL": "Apple Inc.", "TSLA": "Tesla Inc.", "005930": "삼성전자"})

    await redis_client.mset({REDIS_RICH_PICK_KEY: rich_stock_codes, REDIS_RICH_PICK_NAME_KEY: stock_name_map})
    yield rich_stock_codes, stock_name_map
    await redis_client.flushall()


@pytest.fixture(scope="function")
async def setup_tip(session: AsyncSession):
    await TipRepository.save_invest_tips(session, INVESTMENT_TIP)


@pytest.fixture
async def setup_rich_portfolio(redis_client: Redis):
    rich_people = [person.value for person in RicePeople]
    rich_portfolio = [
        {"AAPL": "30.1%", "BAC": "14.7%"},
        {"HHC": "18.2%", "QSR": "15.4%"},
        {"TSLA": "23.1%", "DAL": "12.3%"},
        {"MSFT": "10.2%", "FB": "9.8%"},
        {"AAPL": "16.5%", "GOOGL": "14.8%"},
        {"SPY": "24.3%", "GLD": "17.6%"},
        {"V": "22.1%", "PEP": "18.7%"},
    ]

    await redis_client.mset({rich: json.dumps(portfolio) for rich, portfolio in zip(rich_people, rich_portfolio)})
    yield rich_portfolio
    await redis_client.flushall()


@pytest.fixture(scope="function")
async def setup_current_index(redis_client: Redis):
    kospi_index = MarketIndexData(
        country=Country.KOREA,
        name=MarketIndex.KOSPI,
        current_value="3200.0",
        change_value="50.0",
        change_percent="1.5",
        update_time="",
    )

    kospi_index_json = kospi_index.model_dump_json()

    await redis_client.set(MarketIndex.KOSPI, kospi_index_json)
    yield kospi_index_json
    await redis_client.flushall()


@pytest.fixture(scope="function")
async def setup_chart_all(setup_tip, setup_rich_portfolio, setup_current_index, setup_rich_pick_data):
    pass
