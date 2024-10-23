import asyncio

import ray

from app.data.naver.realtime_index.realtime_index_collector_korea import RealtimeIndexKoreaCollector
from app.data.naver.realtime_index.realtime_index_monitor import RealtimeIndexMonitor


async def execute_async_task():
    monitor = RealtimeIndexMonitor.remote()

    korea_index_collector = RealtimeIndexKoreaCollector.remote()

    monitor.register_collector.remote(korea_index_collector)

    korea_index_collector.collect.remote()

    await monitor.check.remote()


def main():
    ray.init()
    asyncio.run(execute_async_task())
    ray.shutdown()


if __name__ == "__main__":
    main()
