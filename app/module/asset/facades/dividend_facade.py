from collections import defaultdict
from datetime import date

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.model import Asset
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService


class DividendFacade:
    @staticmethod
    async def get_composition(
        assets: list[Asset],
        exchange_rate_map: dict[str, float],
        dividend_map: dict[str, float],
    ) -> list[tuple[str, float, float]]:
        if len(assets) == 0:
            return []

        total_dividend: defaultdict[str, float] = defaultdict(float)
        total_dividend_sum = 0.0

        for asset in assets:
            won_exchange_rate: float = ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)

            dividend = dividend_map.get(asset.asset_stock.stock.code)

            if dividend is None:
                continue

            total_dividend[asset.asset_stock.stock.code] += dividend * won_exchange_rate * asset.asset_stock.quantity
            total_dividend_sum += dividend * won_exchange_rate * asset.asset_stock.quantity

        return sorted(
            [
                (stock_code, dividend, (dividend / total_dividend_sum) * 100 if total_dividend_sum > 0 else 0.0)
                for stock_code, dividend in total_dividend.items()
                if dividend > 0
            ],
            key=lambda x: x[1],
            reverse=True,
        )

    @staticmethod
    def get_full_month_estimate_dividend(
        assets: list[Asset], exchange_rate_map: dict[str, float], dividend_map: dict[tuple[str, date], float]
    ) -> defaultdict[date, float]:
        result: defaultdict[date, float] = defaultdict(float)

        for asset in assets:
            won_exchange_rate: float = ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            closest_dividend_date: date | None = DividendService.get_closest_dividend(asset, dividend_map)
            if closest_dividend_date is None:
                continue

            for (code, current_date), dividend_amount in sorted(dividend_map.items()):
                if code == asset.asset_stock.stock.code and current_date >= closest_dividend_date:
                    result[current_date] += dividend_amount * won_exchange_rate

        return result

    @staticmethod
    async def get_total_dividend(session: AsyncSession, redis_client: Redis, assets: list[Asset]) -> float:
        exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)
        dividend_map: dict[str, float] = await DividendService.get_recent_map(session, assets)

        result = 0.0

        for asset in assets:
            result += (
                dividend_map.get(asset.asset_stock.stock.code, 0.0)
                * asset.asset_stock.quantity
                * ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            )

        return result
