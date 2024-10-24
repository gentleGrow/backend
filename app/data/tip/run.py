import asyncio

from celery import shared_task
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.auth.model import User  # noqa: F401 > relationship 설정시 필요합니다.
from app.module.chart.constant import TIP_EXPIRE_SECOND, TIP_TODAY_ID_REDIS_KEY
from app.module.chart.redis_repository import RedisTipRepository
from app.module.chart.repository import TipRepository
from database.dependency import get_mysql_session, get_redis_pool


async def set_invest_tip_key(session: AsyncSession, redis_client: Redis):
    today_tip_id_str = await RedisTipRepository.get(redis_client, TIP_TODAY_ID_REDIS_KEY)

    if today_tip_id_str is None:
        await RedisTipRepository.save(redis_client, TIP_TODAY_ID_REDIS_KEY, 1, TIP_EXPIRE_SECOND)
        return

    try:
        today_tip_id = int(today_tip_id_str)
    except ValueError:
        await RedisTipRepository.save(redis_client, TIP_TODAY_ID_REDIS_KEY, 1, TIP_EXPIRE_SECOND)
        return

    tip_exists = await TipRepository.check(session, today_tip_id)

    if not tip_exists:
        await RedisTipRepository.save(redis_client, TIP_TODAY_ID_REDIS_KEY, 1, TIP_EXPIRE_SECOND)
    else:
        next_tip_id = today_tip_id + 1
        tip_exists = await TipRepository.check(session, next_tip_id)

        if not tip_exists:
            await RedisTipRepository.save(redis_client, TIP_TODAY_ID_REDIS_KEY, 1, TIP_EXPIRE_SECOND)
        else:
            await RedisTipRepository.save(redis_client, TIP_TODAY_ID_REDIS_KEY, next_tip_id, TIP_EXPIRE_SECOND)

    print("invest tip key 저장을 완료 했습니다.")


async def execute_async_task():
    redis_client = get_redis_pool()
    async with get_mysql_session() as session:
        await set_invest_tip_key(session, redis_client)


@shared_task
def main():
    asyncio.run(execute_async_task())
