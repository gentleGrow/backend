import asyncio

import ray
from more_itertools import chunked

from app.data.common.service import StockCodeFileReader
from app.data.naver.realtime_stock.korea_realtime_stock_collector import KoreaRealtimeStockCollector
from app.data.naver.realtime_stock.realtime_stock_monitor import RealtimeStockMonitor

# from app.data.naver.realtime_stock.world_realtime_stock_collector import WorldRealtimeStockCollector
# from app.data.naver.sources.constant import REALTIME_STOCK_LIST, WORLD_REALTIME_STOCK_LIST
from app.data.naver.sources.constant import REALTIME_STOCK_LIST


async def execute_async_task():
    monitor = RealtimeStockMonitor.remote()
    korea_stock_code_list = StockCodeFileReader.get_korea_stock_code_list()
    korea_stock_code_list_chunks = chunked(korea_stock_code_list, REALTIME_STOCK_LIST)

    # 작업이 완료되면 주석 해제하겠습니다.

    # world_stock_code_list = StockCodeFileReader.get_world_stock_code_list()
    # world_stock_code_list_chunks = chunked(world_stock_code_list, WORLD_REALTIME_STOCK_LIST)

    # actor_pool = [
    #     *[
    #         KoreaRealtimeStockCollector.remote(stock_code_list_chunk)
    #         for stock_code_list_chunk in korea_stock_code_list_chunks
    #     ],
    #     *[
    #         WorldRealtimeStockCollector.remote(stock_code_list_chunk)
    #         for stock_code_list_chunk in world_stock_code_list_chunks
    #     ],
    # ]

    actor_pool = [
        KoreaRealtimeStockCollector.remote(stock_code_list_chunk)
        for stock_code_list_chunk in korea_stock_code_list_chunks
    ]

    for collector in actor_pool:
        monitor.register_collector.remote(collector)
        collector.collect.remote()

    await monitor.check.remote()


def main():
    ray.init()
    asyncio.run(execute_async_task())
    ray.shutdown()


if __name__ == "__main__":
    main()
