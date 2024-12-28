import json
from datetime import date, datetime

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.constant import USER_DATA_EXPIRE_TIME_SEC, USER_DATA_KEY
from app.module.asset.model import Asset, StockDaily
from app.module.asset.redis_repository import RedisAllDataRepostiroy
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.stock.stock_service import StockService
from app.module.asset.services.stock_daily_service import StockDailyService


class AssetQuery:
    def __init__(
        self,
        stock_daily_service: StockDailyService,
        exchange_rate_service: ExchangeRateService,
        stock_service: StockService,
        dividend_service: DividendService,
    ):
        self.stock_daily_service = stock_daily_service
        self.exchange_rate_service = exchange_rate_service
        self.stock_service = stock_service
        self.dividend_service = dividend_service

    async def get_full_required_assets(
        self, session: AsyncSession, user_id: int | str, asset_type: AssetType
    ) -> list[Asset]:
        assets: list = await AssetRepository.get_eager(session, user_id, asset_type)
        return [filterd_asset for filterd_asset in filter(self._filter_full_required_asset, assets)]

    def _filter_full_required_asset(self, asset: Asset):
        return (
            asset.asset_stock.stock
            and asset.asset_stock.quantity
            and asset.asset_stock.trade_date
            and asset.asset_stock.trade
            and asset.asset_stock.purchase_currency_type
        )


    async def cache_user_data(
        self, session: AsyncSession, redis_client: Redis, assets: list[Asset], user_id: str | int
    ) -> tuple[
        dict[tuple[str, date], StockDaily],  # stock_daily_map
        dict[str, StockDaily],  # lastest_stock_daily_map
        dict[str, float],  # dividend_map
        dict[str, float],  # exchange_rate_map
        dict[str, float],  # current_stock_price_map
    ]:
        (
            stock_daily_map,
            lastest_stock_daily_map,
            dividend_map,
            exchange_rate_map,
            current_stock_price_map,
        ) = await self._get_all_data(session, redis_client, assets)

        user_data = self._convert_to_string(
            stock_daily_map,
            lastest_stock_daily_map,
            dividend_map,
            exchange_rate_map,
            current_stock_price_map,
        )

        await RedisAllDataRepostiroy.set(
            redis_client, self._get_user_data_key(user_id), user_data, USER_DATA_EXPIRE_TIME_SEC
        )

        return (stock_daily_map, lastest_stock_daily_map, dividend_map, exchange_rate_map, current_stock_price_map)

    async def get_user_data(
        self, session: AsyncSession, redis_client: Redis, assets: list[Asset], user_id: str | int
    ) -> tuple[
        dict[tuple[str, date], StockDaily],  # stock_daily_map
        dict[str, StockDaily],  # lastest_stock_daily_map
        dict[str, float],  # dividend_map
        dict[str, float],  # exchange_rate_map
        dict[str, float],  # current_stock_price_map
    ]:
        user_data = await RedisAllDataRepostiroy.get(redis_client, self._get_user_data_key(user_id))
        if user_data:
            return self._convert_to_original(user_data)

        (
            stock_daily_map,
            lastest_stock_daily_map,
            dividend_map,
            exchange_rate_map,
            current_stock_price_map,
        ) = await self._get_all_data(session, redis_client, assets)

        user_data = self._convert_to_string(
            stock_daily_map,
            lastest_stock_daily_map,
            dividend_map,
            exchange_rate_map,
            current_stock_price_map,
        )

        await RedisAllDataRepostiroy.set(
            redis_client, self._get_user_data_key(user_id), user_data, USER_DATA_EXPIRE_TIME_SEC
        )

        return (stock_daily_map, lastest_stock_daily_map, dividend_map, exchange_rate_map, current_stock_price_map)

    def _convert_to_original(
        self, user_data: str
    ) -> tuple[
        dict[tuple[str, date], StockDaily], dict[str, StockDaily], dict[str, float], dict[str, float], dict[str, float]
    ]:
        data = json.loads(user_data)

        stock_daily_map = {
            (k.split("|")[0], datetime.strptime(k.split("|")[1], "%Y-%m-%d").date()): StockDaily.from_dict(v)
            for k, v in data["stock_daily_map"].items()
        }
        lastest_stock_daily_map = {k: StockDaily.from_dict(v) for k, v in data["lastest_stock_daily_map"].items()}

        dividend_map = data["dividend_map"]
        exchange_rate_map = data["exchange_rate_map"]
        current_stock_price_map = data["current_stock_price_map"]

        return stock_daily_map, lastest_stock_daily_map, dividend_map, exchange_rate_map, current_stock_price_map

    def _convert_to_string(
        self,
        stock_daily_map: dict[tuple[str, date], StockDaily],
        lastest_stock_daily_map: dict[str, StockDaily],
        dividend_map: dict[str, float],
        exchange_rate_map: dict[str, float],
        current_stock_price_map: dict[str, float],
    ) -> str:
        stock_daily_map_str = {"|".join(map(str, k)): v.to_dict() for k, v in stock_daily_map.items()}
        lastest_stock_daily_map_str = {k: v.to_dict() for k, v in lastest_stock_daily_map.items()}

        data = {
            "stock_daily_map": stock_daily_map_str,
            "lastest_stock_daily_map": lastest_stock_daily_map_str,
            "dividend_map": dividend_map,
            "exchange_rate_map": exchange_rate_map,
            "current_stock_price_map": current_stock_price_map,
        }

        return json.dumps(data)

    def _get_user_data_key(self, user_id: str | int) -> str:
        return f"{user_id}_{USER_DATA_KEY}"

    async def _get_all_data(
        self, session: AsyncSession, redis_client: Redis, assets: list[Asset]
    ) -> tuple[
        dict[tuple[str, date], StockDaily],  # stock_daily_map
        dict[str, StockDaily],  # lastest_stock_daily_map
        dict[str, float],  # dividend_map
        dict[str, float],  # exchange_rate_map
        dict[str, float],  # current_stock_price_map
    ]:
        stock_daily_map: dict[tuple[str, date], StockDaily] = await self.stock_daily_service.get_map_range(
            session, assets
        )
        lastest_stock_daily_map: dict[str, StockDaily] = await self.stock_daily_service.get_latest_map(session, assets)
        dividend_map: dict[str, float] = await self.dividend_service.get_recent_map(session, assets)
        exchange_rate_map: dict[str, float] = await self.exchange_rate_service.get_exchange_rate_map(redis_client)
        current_stock_price_map: dict[str, float] = await self.stock_service.get_current_stock_price(
            redis_client, lastest_stock_daily_map, assets
        )

        return (stock_daily_map, lastest_stock_daily_map, dividend_map, exchange_rate_map, current_stock_price_map)
