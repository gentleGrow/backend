import asyncio

import ray
from icecream import ic

from app.data.yahoo.source.constant import REALTIME_INDEX_MONITOR_WAIT_SECOND
from app.module.auth.model import User  # noqa: F401 > relationship 설정시 필요합니다.


@ray.remote
class RealtimeIndexMonitor:
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
                    collector.collect.remote()
            await asyncio.sleep(REALTIME_INDEX_MONITOR_WAIT_SECOND)
