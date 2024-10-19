import asyncio
import ray

from more_itertools import chunked
from app.data.common.service import StockCodeFileReader
from app.data.yahoo.realtime_stock.realtime_stock_collector import RealtimeStockCollector
from app.data.yahoo.realtime_stock.realtime_stock_monitor import RealtimeStockMonitor
from app.data.yahoo.source.constant import REALTIME_STOCK_LIST

async def execute_async_task():
    monitor = RealtimeStockMonitor.remote()
    stock_code_list = StockCodeFileReader.get_all_stock_code_list()
    stock_code_list_chunks = chunked(stock_code_list, REALTIME_STOCK_LIST)

    actor_pool = [
        RealtimeStockCollector.remote(stock_code_list_chunk) for stock_code_list_chunk in stock_code_list_chunks
    ]

    await asyncio.gather(
        *[monitor.register_collector.remote(collector) for collector in actor_pool],
        *[collector.collect.remote() for collector in actor_pool],
    )
    
    await monitor.check.remote()


def main():
    ray.init()
    asyncio.run(execute_async_task())
    ray.shutdown()


if __name__ == "__main__":
    main()

