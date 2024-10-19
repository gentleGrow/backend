import asyncio
import ray

from icecream import ic
from app.data.yahoo.source.constant import EXCHANGE_RATE_MONITOR_SECOND


@ray.remote
class ExchangeRateMonitor:
    def __init__(self, collector):
        self.collector = collector
        
    async def check(self):
        while True:
            is_running = await self.collector.is_running.remote()
            if not is_running:
                ic("collector 작업이 멈추어서 재시작합니다")
                await self.collector.collect.remote()
            await asyncio.sleep(EXCHANGE_RATE_MONITOR_SECOND)
                
