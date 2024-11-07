from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.chart.services.rich_service import RichFacade


class TestRichFacade:
    async def test_get_rich_top_10_pick(self, session: AsyncSession, redis_client: Redis, setup_chart_all):
        # When
        top_10_stock_codes, stock_name_map = await RichFacade.get_rich_top_10_pick(session, redis_client)

        # Then
        assert all(code in stock_name_map for code in top_10_stock_codes)
        assert stock_name_map[top_10_stock_codes[0]] == "Apple Inc."
