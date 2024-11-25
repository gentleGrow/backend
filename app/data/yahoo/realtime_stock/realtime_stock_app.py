import asyncio

import ray
from more_itertools import chunked

from app.data.common.service import StockCodeFileReader
from app.data.yahoo.realtime_stock.realtime_stock_collector import RealtimeStockCollector
from app.data.yahoo.realtime_stock.realtime_stock_monitor import RealtimeStockMonitor
from app.data.yahoo.source.constant import REALTIME_STOCK_LIST


async def execute_async_task():
    monitor = RealtimeStockMonitor.remote()
    stock_code_list = StockCodeFileReader.get_korea_stock_code_list()
    stock_code_list_chunks = chunked(stock_code_list, REALTIME_STOCK_LIST)

    # yfinance rate limit으로 인해 분당 60개가 한계입니다. 추후 proxy를 이용해 멀티프로세스로 수집하겠습니다.
    first_chunk = next(iter(stock_code_list_chunks), None)
    collector = RealtimeStockCollector.remote(first_chunk)
    monitor.register_collector.remote(collector)
    collector.collect.remote()

    await monitor.check.remote()


def main():
    ray.init()
    asyncio.run(execute_async_task())
    ray.shutdown()


if __name__ == "__main__":
    main()
