import asyncio
import ray

from icecream import ic
from app.data.yahoo.exchange_rate.exchange_rate_collector import ExchangeRateCollector
from app.data.yahoo.exchange_rate.exchange_rate_monitor import ExchangeRateMonitor

async def execute_async_task():
    collector = ExchangeRateCollector.remote()
    monitor = ExchangeRateMonitor.remote(collector)

    await collector.collect.remote()
    await monitor.check.remote()
    

def main():
    ray.init()
    asyncio.run(execute_async_task())
    ray.shutdown()

if __name__ == "__main__":
    main()
    
