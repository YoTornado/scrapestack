"""Async rate limiter with random delays to avoid detection."""

import asyncio
import random


class RateLimiter:
    """Async semaphore-based rate limiter with configurable random delays."""

    def __init__(self, delay_range: tuple[float, float] = (2, 4), max_concurrent: int = 1):
        self.delay_range = delay_range
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def wait(self):
        """Wait for a random delay within the configured range."""
        async with self.semaphore:
            delay = random.uniform(*self.delay_range)
            await asyncio.sleep(delay)

    async def __aenter__(self):
        await self.semaphore.acquire()
        delay = random.uniform(*self.delay_range)
        await asyncio.sleep(delay)
        return self

    async def __aexit__(self, *args):
        self.semaphore.release()
