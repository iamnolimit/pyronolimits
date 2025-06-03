#  Pyrogram Optimized - High Performance Telegram MTProto API Client
#  Based on Pyrogram by Dan <https://github.com/delivrance>
#  Performance optimizations and enhancements

__version__ = "2.1.21-optimized"
__license__ = "GNU Lesser General Public License v3.0 (LGPL-3.0)"
__copyright__ = "Copyright (C) 2017-present Dan <https://github.com/delivrance>"

import asyncio
import os
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Dict, Any


class StopTransmission(Exception):
    pass


class StopPropagation(StopAsyncIteration):
    pass


class ContinuePropagation(StopAsyncIteration):
    pass


# Get CPU count synchronously at import time
CPU_COUNT = os.cpu_count() or 4

# Jika CPU_COUNT ternyata adalah Future
if isinstance(CPU_COUNT, asyncio.Future):
    import asyncio
    loop = asyncio.get_event_loop()
    CPU_COUNT = loop.run_until_complete(CPU_COUNT)


# Optimized thread pool with better sizing
crypto_executor = ThreadPoolExecutor(
    max_workers=min(4, CPU_COUNT),
    thread_name_prefix="CryptoWorker"
)

# Connection pool for better resource management
connection_pool = ThreadPoolExecutor(
    max_workers=min(8, CPU_COUNT * 2),
    thread_name_prefix="ConnectionWorker"
)

# Global cache for frequently accessed data
global_cache: Dict[str, Any] = {}
cache_lock = asyncio.Lock()

from .client_optimized import ClientOptimized