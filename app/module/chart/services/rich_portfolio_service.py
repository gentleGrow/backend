import json

from redis.asyncio import Redis

from app.module.chart.redis_repository import RedisRichPortfolioRepository


class RichPortfolioService:
    async def get_rich_porfolio_map(
        self,
        redis_client: Redis,
    ) -> dict[str, dict]:
        RichPeople = []  # type: ignore # 추후 변경 예정
        rich_people = [person.value for person in RichPeople]
        rich_portfolios: list[str] | None = await RedisRichPortfolioRepository.gets(redis_client, rich_people)

        rich_portfolios = rich_portfolios or []

        return {
            person: json.loads(portfolio)
            for person, portfolio in zip(rich_people, rich_portfolios)
            if person and portfolio
        }
