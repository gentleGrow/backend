import asyncio

import ray

from app.data.common.service import StockCodeFileReader
from app.data.naver.realtime_stock.korea_realtime_stock_collector import KoreaRealtimeStockCollector
from app.data.naver.realtime_stock.realtime_stock_monitor import RealtimeStockMonitor


async def execute_async_task():
    monitor = RealtimeStockMonitor.remote()
    korea_stock_code_list = StockCodeFileReader.get_korea_stock_code_list()

    # 임시로 데이터 수집 속도로 인해, 한국 주식은 yahoo/realtime_stock/realtime_stock_app과 2개로 나누었습니다. 개수도 120개로 줄여서 추후 해결하겠습니다.
    second_chunk = second_chunk = korea_stock_code_list[40:]

    collector = KoreaRealtimeStockCollector.remote(second_chunk)
    monitor.register_collector.remote(collector)
    collector.collect.remote()

    await monitor.check.remote()


def main():
    ray.init()
    asyncio.run(execute_async_task())
    ray.shutdown()


if __name__ == "__main__":
    main()
