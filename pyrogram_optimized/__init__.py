#  Pyrogram Optimized - High Performance Telegram MTProto API Client
#  Based on Pyrogram by Dan <https://github.com/delivrance>
#  Performance optimizations and enhancements

__version__ = "2.1.21-optimized"
__license__ = "GNU Lesser General Public License v3.0 (LGPL-3.0)"
__copyright__ = "Copyright (C) 2017-present Dan <https://github.com/delivrance>"

import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Dict, Any


class StopTransmission(Exception):
    pass


class StopPropagation(StopAsyncIteration):
    pass


class ContinuePropagation(StopAsyncIteration):
    pass


# Optimized thread pool with better sizing
CPU_COUNT = asyncio.get_event_loop().run_in_executor(None, lambda: __import__('os').cpu_count()) or 4
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

from . import raw, types, filters, handlers, emoji, enums
from .client_optimized import ClientOptimized as Client
from .sync import idle, compose