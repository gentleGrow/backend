from datetime import datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.util.time import get_date_past_day
from app.module.asset.enum import AssetType
from app.module.asset.model import Asset
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.services.asset_service import AssetService
from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.chart.constant import FULL_PERCENTAGE_RATE, PAST_MONTH_DAY
from icecream import ic


class SummaryService:
    def __init__(self, asset_stock_service: AssetStockService, asset_service: AssetService):
        self.asset_stock_service = asset_stock_service
        self.asset_service = asset_service

    async def get_today_review_rate(self, session: AsyncSession, redis_client: Redis, user_id: int) -> float:
        assets: list[Asset] = await AssetRepository.get_eager(session, user_id, AssetType.STOCK)

        past_assets = [
            asset
            for asset in assets
            if asset.asset_stock.trade_date <= datetime.now().date() - timedelta(days=PAST_MONTH_DAY)
        ]

        if len(past_assets) == 0 and len(assets) > 0:
            return FULL_PERCENTAGE_RATE


        past_total_amount = await self.asset_service.get_total_asset_amount(
            session, redis_client, past_assets
        )

        current_total_amount = await self.asset_service.get_total_asset_amount(session, redis_client, assets)

        return self.asset_stock_service.get_total_profit_rate(current_total_amount, past_total_amount)
