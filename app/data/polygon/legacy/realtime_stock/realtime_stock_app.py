import asyncio

import ray
from more_itertools import chunked

from app.data.common.services.stock_code_file_service import StockCodeFileReader
from app.data.polygon.legacy.constant import REALTIME_USA_STOCK_LIST
from app.data.polygon.legacy.realtime_stock.realtime_stock_collector import RealtimeStockCollector
from app.data.polygon.legacy.realtime_stock.realtime_stock_monitor import RealtimeStockMonitor


async def execute_async_task():
    monitor = RealtimeStockMonitor.remote()
    stock_code_list = StockCodeFileReader.get_usa_stock_code_list()
    stock_code_list_chunks = chunked(stock_code_list, REALTIME_USA_STOCK_LIST)

    actor_pool = [
        RealtimeStockCollector.remote(stock_code_list_chunk) for stock_code_list_chunk in stock_code_list_chunks
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
