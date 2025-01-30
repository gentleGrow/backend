import json
from datetime import date, datetime, timedelta

import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.constant import REQUIRED_ASSET_FIELD, KOREA, USA
from app.module.asset.enum import (
    AccountType,
    AssetType,
    InvestmentBankType,
    MarketIndex,
    PurchaseCurrencyType,
    StockAsset,
    TradeType,
)
from app.module.asset.model import (
    Asset,
    AssetField,
    AssetStock,
    Dividend,
    MarketIndexDaily,
    MarketIndexMinutely,
    Stock,
    StockDaily,
    StockMinutely,
)
from app.module.auth.constant import DUMMY_NAME, DUMMY_USER_ID
from app.module.auth.enum import ProviderEnum, UserRoleEnum
from app.module.auth.model import User

@pytest.fixture(scope="function")
async def setup_user(session: AsyncSession):
    user = User(
        id=DUMMY_USER_ID,
        social_id="test_social_id",
        provider=ProviderEnum.GOOGLE,
        role=UserRoleEnum.USER,
        nickname=DUMMY_NAME,
    )
    session.add(user)
    await session.commit()


@pytest.fixture(scope="function")
async def setup_asset_stock_field(session: AsyncSession, setup_user, setup_stock):
    fields_to_disable = ["stock_volume", "purchase_currency_type", "purchase_price", "purchase_amount"]
    field_preference = [field for field in [field.value for field in StockAsset] if field not in fields_to_disable]
    asset_field = AssetField(user_id=DUMMY_USER_ID, field_preference=field_preference)

    session.add(asset_field)
    await session.commit()


@pytest.fixture(scope="function")
async def setup_asset_field(session: AsyncSession, setup_user, setup_stock):
    asset_field = AssetField(user_id=DUMMY_USER_ID, field_preference=REQUIRED_ASSET_FIELD)

    session.add(asset_field)
    await session.commit()


@pytest.fixture(scope="function")
async def setup_current_market_index(redis_client: Redis):
    market_index_data = {"market_type": MarketIndex.KOSPI.value, "current_value": "3250.0", "previous_value": "3200.0"}

    await redis_client.set(f"{MarketIndex.KOSPI}", json.dumps(market_index_data))
    yield market_index_data
    await redis_client.flushall()


@pytest.fixture(scope="function")
async def setup_realtime_stock_price(redis_client: Redis):
    keys = ["AAPL", "TSLA", "005930"]
    values = ["220.0", "230.0", "70000.0"]
    await redis_client.mset({key: value for key, value in zip(keys, values)})
    yield keys, values
    await redis_client.flushall()


@pytest.fixture(scope="function")
async def setup_exchange_rate(redis_client: Redis):
    keys = ["USD_KRW", "KRW_USD"]
    values = ["1300.0", "0.00075"]
    await redis_client.mset({key: value for key, value in zip(keys, values)})
    yield keys, values
    await redis_client.flushall()


@pytest.fixture(scope="function")
async def setup_dividend(session: AsyncSession, setup_stock):
    dividend1 = Dividend(dividend=1.5, code="AAPL", date=date(2024, 8, 13))

    dividend2 = Dividend(dividend=1.6, code="AAPL", date=date(2024, 8, 14))

    dividend3 = Dividend(dividend=0.8, code="TSLA", date=date(2024, 8, 13))

    dividend4 = Dividend(dividend=0.9, code="TSLA", date=date(2024, 8, 14))

    dividend5 = Dividend(dividend=100.0, code="005930", date=date(2024, 8, 13))

    dividend6 = Dividend(dividend=105.0, code="005930", date=date(2024, 8, 14))

    session.add_all([dividend1, dividend2, dividend3, dividend4, dividend5, dividend6])
    await session.commit()


@pytest.fixture(scope="function")
async def setup_stock(session: AsyncSession):
    stock_1 = Stock(id=1, code="AAPL", country=USA, market_index="NASDAQ", name_kr="애플", name_en="Apple")
    stock_2 = Stock(id=2, code="TSLA", country=USA, market_index="NASDAQ", name_kr="테슬라", name_en="Tesla")
    stock_3 = Stock(id=3, code="005930", country=KOREA, market_index="KOSPI", name_kr="삼성전자", name_en="Samsung")
    session.add_all([stock_1, stock_2, stock_3])
    await session.commit()


@pytest.fixture(scope="function")
async def setup_stock_daily(session: AsyncSession, setup_user, setup_stock):
    stock_daily_1 = StockDaily(
        adj_close_price=150.0,
        close_price=148.0,
        code="AAPL",
        date=date(2024, 8, 13),
        highest_price=152.0,
        lowest_price=147.0,
        opening_price=149.0,
        trade_volume=1000000,
    )

    stock_daily_2 = StockDaily(
        adj_close_price=151.0,
        close_price=149.0,
        code="AAPL",
        date=date(2024, 8, 14),
        highest_price=153.0,
        lowest_price=148.0,
        opening_price=150.0,
        trade_volume=1050000,
    )

    stock_daily_3 = StockDaily(
        adj_close_price=720.0,
        close_price=715.0,
        code="TSLA",
        date=date(2024, 8, 13),
        highest_price=730.0,
        lowest_price=710.0,
        opening_price=720.0,
        trade_volume=1500000,
    )

    stock_daily_4 = StockDaily(
        adj_close_price=725.0,
        close_price=720.0,
        code="TSLA",
        date=date(2024, 8, 14),
        highest_price=735.0,
        lowest_price=715.0,
        opening_price=725.0,
        trade_volume=1600000,
    )

    stock_daily_5 = StockDaily(
        adj_close_price=70000.0,
        close_price=70000.0,
        code="005930",
        date=date(2024, 8, 13),
        highest_price=71000.0,
        lowest_price=69000.0,
        opening_price=70500.0,
        trade_volume=1000,
    )

    stock_daily_6 = StockDaily(
        adj_close_price=72000.0,
        close_price=72000.0,
        code="005930",
        date=date(2024, 8, 14),
        highest_price=73000.0,
        lowest_price=71000.0,
        opening_price=71500.0,
        trade_volume=1500,
    )

    stock_daily_7 = StockDaily(
        adj_close_price=150.0,
        close_price=149.0,
        code="AAPL",
        date=date(2024, 9, 1),
        highest_price=153.0,
        lowest_price=148.0,
        opening_price=150.0,
        trade_volume=1050000,
    )

    stock_daily_8 = StockDaily(
        adj_close_price=700.0,
        close_price=720.0,
        code="TSLA",
        date=date(2024, 9, 1),
        highest_price=735.0,
        lowest_price=715.0,
        opening_price=725.0,
        trade_volume=1600000,
    )

    stock_daily_9 = StockDaily(
        adj_close_price=70000.0,
        close_price=72000.0,
        code="005930",
        date=date(2024, 9, 1),
        highest_price=73000.0,
        lowest_price=71000.0,
        opening_price=71500.0,
        trade_volume=1500,
    )

    session.add_all(
        [
            stock_daily_1,
            stock_daily_2,
            stock_daily_3,
            stock_daily_4,
            stock_daily_5,
            stock_daily_6,
            stock_daily_7,
            stock_daily_8,
            stock_daily_9,
        ]
    )
    await session.commit()


@pytest.fixture(scope="function")
async def setup_asset(session: AsyncSession, setup_user, setup_stock):
    asset_stock1 = AssetStock(
        account_type=AccountType.ISA.value,
        investment_bank=InvestmentBankType.MIRAEASSET.value,
        purchase_currency_type=PurchaseCurrencyType.USA.value,
        trade_date=date(2024, 8, 13),
        trade_price=500.0,
        trade=TradeType.BUY,
        quantity=1,
        stock_id=1,
    )

    asset_stock2 = AssetStock(
        account_type=AccountType.PENSION.value,
        investment_bank=InvestmentBankType.TOSS.value,
        purchase_currency_type=PurchaseCurrencyType.KOREA.value,
        trade_date=date(2024, 8, 14),
        trade_price=1000.0,
        trade=TradeType.BUY,
        quantity=2,
        stock_id=2,
    )

    asset_stock3 = AssetStock(
        account_type=AccountType.REGULAR.value,
        investment_bank=InvestmentBankType.KB.value,
        purchase_currency_type=PurchaseCurrencyType.KOREA.value,
        trade_date=date(2024, 8, 14),
        trade_price=None,
        trade=TradeType.BUY,
        quantity=1,
        stock_id=3,
    )

    asset1 = Asset(id=1, asset_type=AssetType.STOCK.value, user_id=DUMMY_USER_ID, asset_stock=asset_stock1)
    asset2 = Asset(id=2, asset_type=AssetType.STOCK.value, user_id=DUMMY_USER_ID, asset_stock=asset_stock2)
    asset3 = Asset(id=3, asset_type=AssetType.STOCK.value, user_id=DUMMY_USER_ID, asset_stock=asset_stock3)
    session.add_all([asset1, asset2, asset3])
    await session.commit()


@pytest.fixture(scope="function")
async def setup_market_index_daily(session: AsyncSession):
    market_index_daily1 = MarketIndexDaily(
        name=MarketIndex.KOSPI,
        date=date(2024, 8, 10),
        open_price=3000.0,
        close_price=3100.0,
        high_price=3200.0,
        low_price=2990.0,
        volume=1000000,
    )

    market_index_daily2 = MarketIndexDaily(
        name=MarketIndex.KOSPI,
        date=date(2024, 8, 11),
        open_price=3100.0,
        close_price=3150.0,
        high_price=3250.0,
        low_price=3080.0,
        volume=1200000,
    )

    market_index_daily3 = MarketIndexDaily(
        name=MarketIndex.KOSPI,
        date=date(2024, 8, 13),
        close_price=3200.0,
        open_price=3150.0,
        high_price=3250.0,
        low_price=3100.0,
        volume=1500000,
    )

    market_index_daily4 = MarketIndexDaily(
        name=MarketIndex.KOSPI,
        date=date(2024, 8, 14),
        close_price=3250.0,
        open_price=3200.0,
        high_price=3300.0,
        low_price=3150.0,
        volume=1600000,
    )

    market_index_daily5 = MarketIndexDaily(
        name=MarketIndex.KOSPI,
        date=date(2024, 8, 15),
        close_price=3300.0,
        open_price=3250.0,
        high_price=3350.0,
        low_price=3200.0,
        volume=1700000,
    )

    session.add_all(
        [market_index_daily1, market_index_daily2, market_index_daily3, market_index_daily4, market_index_daily5]
    )
    await session.commit()


@pytest.fixture(scope="function")
async def setup_market_index_minutely_data(session: AsyncSession):
    market_type = MarketIndex.KOSPI
    end_date = datetime(2024, 8, 15, 23, 59)
    start_date = end_date - timedelta(days=4)

    mock_data = [
        MarketIndexMinutely(name=market_type.value, datetime=start_date + timedelta(minutes=i), price=3000.0 + i)
        for i in range(0, 60 * 24 * 5, 30)
    ]

    session.add_all(mock_data)
    await session.commit()


@pytest.fixture(scope="function")
async def setup_market_index_minutely(session: AsyncSession):
    market_index_1 = MarketIndexMinutely(
        name=MarketIndex.KOSPI,
        datetime=datetime(2024, 9, 24, 21, 30),
        price=3100.0,
    )

    market_index_2 = MarketIndexMinutely(
        name=MarketIndex.KOSPI,
        datetime=datetime(2024, 9, 24, 22, 30),
        price=3150.0,
    )

    session.add_all([market_index_1, market_index_2])
    await session.commit()


@pytest.fixture(scope="function")
async def setup_stock_minutely(session: AsyncSession):
    stock_minutely_1 = StockMinutely(code="AAPL", datetime=datetime(2024, 8, 13, 10, 30), price=150.0)

    stock_minutely_2 = StockMinutely(code="AAPL", datetime=datetime(2024, 8, 13, 10, 45), price=151.0)

    stock_minutely_3 = StockMinutely(code="TSLA", datetime=datetime(2024, 8, 13, 10, 30), price=720.0)

    stock_minutely_4 = StockMinutely(code="TSLA", datetime=datetime(2024, 8, 13, 10, 45), price=725.0)

    session.add_all([stock_minutely_1, stock_minutely_2, stock_minutely_3, stock_minutely_4])
    await session.commit()


@pytest.fixture(scope="function")
async def setup_all(
    setup_user,
    setup_asset_field,
    setup_current_market_index,
    setup_realtime_stock_price,
    setup_exchange_rate,
    setup_dividend,
    setup_stock,
    setup_stock_daily,
    setup_asset,
    setup_market_index_daily,
    setup_market_index_minutely_data,
    setup_market_index_minutely,
    setup_stock_minutely,
):
    pass
