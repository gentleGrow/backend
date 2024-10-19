import asyncio
import ray

from icecream import ic


@ray.remote
class RealtimeStockMonitor:
    def __init__(self):
        self.collectors = []

    def register_collector(self, collector):
        self.collectors.append(collector)

    async def check(self):
        while True:
            for collector in self.collectors:
                is_running = await collector.is_running.remote()
                if not is_running:
                    ic("collector 작업이 멈추어서 재시작합니다")
                    await collector.collect.remote()
            await asyncio.sleep(10)
