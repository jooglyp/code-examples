"""
Throttling Script
"""
import asyncio
import concurrent.futures
import requests
import time

class AsyncLeakyBucket(object):
    """A leaky bucket rate limiter.
    Allows up to max_rate / time_period acquisitions before blocking.
    time_period is measured in seconds; the default is 60.
    object: max_rate, time_period, cores
    - max_rate/time_period: pings per time period
    """

    def __init__(self, max_rate: float, time_period: float = 60, \
                 cores: float = 4) -> None:
        self._max_level = cores
        self._rate_per_sec = cores / max_rate
        self._level = 0.0
        self._last_check = 0.0

    def _leak(self) -> None:
        """Drip out capacity from the bucket."""
        if self._level:
            # drip out enough level for the elapsed time since
            # we last checked
            elapsed = time.time() - self._last_check
            decrement = elapsed * self._rate_per_sec
            self._level = max(self._level - decrement, 0)
        self._last_check = time.time()

    def has_capacity(self, amount: float = 1) -> bool:
        """Check if there is enough space remaining in the bucket"""
        self._leak()
        return self._level + amount <= self._max_level

    async def acquire(self, amount: float = 1) -> None:
        """Acquire space in the bucket.
        If the bucket is full, block until there is space.
        """
        if amount > self._max_level:
            raise ValueError("Can't acquire more than the bucket capacity")
        while not self.has_capacity(amount):
            # wait for the next drip to have left the bucket
            await asyncio.sleep(1 / self._rate_per_sec)
        self._level += amount

    async def __aenter__(self) -> None:
        await self.acquire()
        return None

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass

# --------------------------#

async def main(url, ref):
    async with bucket:
        print('Drip!', time.time() - ref)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            loop = asyncio.get_event_loop()
            with requests.Session() as sess:
                print("start")
                futures = [
                    loop.run_in_executor(executor, requests.get, url)
                    for i in range(8)
                ]
                # requests.requests is a case sensitive method
                for response in await asyncio.gather(*futures):
                    # resp = requests.Session().send(response.prepare())
                    print(response.json(), response.status_code, response.headers.items())
                    pass

# --------------------------#

bucket = AsyncLeakyBucket(2, 1, 8)
# processing 1 main's() max every 4 seconds. Each main is 8 multithreaded tasks.
# => 8 completions per 4 seconds (2 completions per second) => target (2,1)
ref = time.time()
tasks = [main('http://localhost:5000/todo/api/v1.0/tasks', ref) for _ in range(15)]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))