import asyncio

import ray

from app.data.naver.realtime_index.realtime_index_collector_korea import RealtimeIndexKoreaCollector
from app.data.naver.realtime_index.realtime_index_collector_world import RealtimeIndexWorldCollector
from app.data.naver.realtime_index.realtime_index_monitor import RealtimeIndexMonitor


async def execute_async_task():
    monitor = RealtimeIndexMonitor.remote()

    # korea_index_collector = RealtimeIndexKoreaCollector.remote()
    world_index_collector = RealtimeIndexWorldCollector.remote()

    # monitor.register_collector.remote(korea_index_collector)
    monitor.register_collector.remote(world_index_collector)

    await monitor.check.remote()


def main():
    ray.init()
    asyncio.run(execute_async_task())
    ray.shutdown()


if __name__ == "__main__":
    main()
