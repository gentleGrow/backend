import asyncio

import ray


@ray.remote
class RealtimeStockMonitor:
    def __init__(self):
        self.collectors = []

    def register_collector(self, collector):
        self.collectors.append(collector)

    async def check(self):
        while True:
            for collector in self.collectors:
                is_running = collector.is_running.remote()
                if not is_running:
                    collector.collect.remote()
            await asyncio.sleep(10)
