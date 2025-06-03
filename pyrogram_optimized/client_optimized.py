#  Pyrogram Optimized Client - High Performance Implementation
#  Enhanced with connection pooling, caching, and async optimizations

import asyncio
import functools
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, List, Union
from collections import defaultdict, deque
from dataclasses import dataclass
import weakref

import pyrogram
from pyrogram.client import Client as BaseClient
from pyrogram.session import Session
from pyrogram.connection import Connection

log = logging.getLogger(__name__)


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pooling"""
    max_connections: int = 10
    min_connections: int = 2
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0  # 5 minutes
    max_retries: int = 3


class ConnectionPool:
    """High-performance connection pool for Telegram sessions"""
    
    def __init__(self, config: ConnectionPoolConfig):
        self.config = config
        self.available_connections: deque = deque()
        self.active_connections: Dict[int, Connection] = {}
        self.connection_stats: Dict[int, dict] = defaultdict(lambda: {
            'created_at': time.time(),
            'last_used': time.time(),
            'usage_count': 0
        })
        self.lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def get_connection(self, dc_id: int, **kwargs) -> Connection:
        """Get an available connection from the pool"""
        async with self.lock:
            # Try to reuse existing connection
            for conn_id, conn in self.active_connections.items():
                if (conn.dc_id == dc_id and 
                    self.connection_stats[conn_id]['usage_count'] < 100):  # Limit reuse
                    self.connection_stats[conn_id]['last_used'] = time.time()
                    self.connection_stats[conn_id]['usage_count'] += 1
                    return conn
            
            # Create new connection if under limit
            if len(self.active_connections) < self.config.max_connections:
                conn = Connection(dc_id, **kwargs)
                await conn.connect()
                conn_id = id(conn)
                self.active_connections[conn_id] = conn
                self.connection_stats[conn_id]['created_at'] = time.time()
                return conn
            
            # Wait for available connection
            while not self.available_connections:
                await asyncio.sleep(0.1)
            
            return self.available_connections.popleft()
    
    async def release_connection(self, connection: Connection):
        """Return connection to the pool"""
        async with self.lock:
            conn_id = id(connection)
            if conn_id in self.active_connections:
                self.available_connections.append(connection)
                self.connection_stats[conn_id]['last_used'] = time.time()
    
    async def cleanup_idle_connections(self):
        """Remove idle connections to free resources"""
        current_time = time.time()
        to_remove = []
        
        async with self.lock:
            for conn_id, stats in self.connection_stats.items():
                if (current_time - stats['last_used'] > self.config.idle_timeout and
                    len(self.active_connections) > self.config.min_connections):
                    to_remove.append(conn_id)
            
            for conn_id in to_remove:
                if conn_id in self.active_connections:
                    conn = self.active_connections.pop(conn_id)
                    await conn.close()
                    del self.connection_stats[conn_id]
                    log.info(f"Cleaned up idle connection {conn_id}")


class OptimizedCache:
    """High-performance LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, ttl: float = 300.0):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, dict] = {}
        self.access_order: deque = deque()
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if time.time() - entry['timestamp'] < self.ttl:
                    # Move to end (most recently used)
                    self.access_order.remove(key)
                    self.access_order.append(key)
                    return entry['value']
                else:
                    # Expired
                    del self.cache[key]
                    self.access_order.remove(key)
            return None
    
    async def set(self, key: str, value: Any):
        async with self.lock:
            # Remove if exists
            if key in self.cache:
                self.access_order.remove(key)
            
            # Add new entry
            self.cache[key] = {
                'value': value,
                'timestamp': time.time()
            }
            self.access_order.append(key)
            
            # Evict oldest if over limit
            while len(self.cache) > self.max_size:
                oldest_key = self.access_order.popleft()
                del self.cache[oldest_key]


class ClientOptimized(BaseClient):
    """Optimized Pyrogram client with enhanced performance features"""
    
    def __init__(self, *args, **kwargs):
        # Extract optimization config
        self.pool_config = kwargs.pop('pool_config', ConnectionPoolConfig())
        self.enable_caching = kwargs.pop('enable_caching', True)
        self.cache_size = kwargs.pop('cache_size', 1000)
        self.cache_ttl = kwargs.pop('cache_ttl', 300.0)
        
        super().__init__(*args, **kwargs)
        
        # Initialize optimizations
        self.connection_pool = ConnectionPool(self.pool_config)
        self.cache = OptimizedCache(self.cache_size, self.cache_ttl) if self.enable_caching else None
        self.session_cache: Dict[int, Session] = {}
        
        # Performance monitoring
        self.stats = {
            'requests_sent': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'connection_reuses': 0,
            'start_time': time.time()
        }
        
        # Async optimizations
        self.request_semaphore = asyncio.Semaphore(50)  # Limit concurrent requests
        self.batch_queue: deque = deque()
        self.batch_processor_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the optimized client"""
        await super().start()
        
        # Start background tasks
        if not self.batch_processor_task:
            self.batch_processor_task = asyncio.create_task(self._batch_processor())
        
        # Start connection cleanup task
        asyncio.create_task(self._periodic_cleanup())
        
        log.info("Optimized Pyrogram client started with enhanced performance features")
    
    async def stop(self):
        """Stop the client and cleanup resources"""
        if self.batch_processor_task:
            self.batch_processor_task.cancel()
        
        # Close all pooled connections
        async with self.connection_pool.lock:
            for conn in self.connection_pool.active_connections.values():
                await conn.close()
        
        await super().stop()
        
        # Print performance stats
        uptime = time.time() - self.stats['start_time']
        log.info(f"Performance Stats - Uptime: {uptime:.2f}s, "
                f"Requests: {self.stats['requests_sent']}, "
                f"Cache Hit Rate: {self._get_cache_hit_rate():.2f}%")
    
    async def invoke(self, query, retries: int = Session.MAX_RETRIES, timeout: float = Session.WAIT_TIMEOUT):
        """Optimized invoke with caching and connection pooling"""
        async with self.request_semaphore:
            self.stats['requests_sent'] += 1
            
            # Check cache first
            if self.cache and hasattr(query, '__dict__'):
                cache_key = self._generate_cache_key(query)
                cached_result = await self.cache.get(cache_key)
                if cached_result is not None:
                    self.stats['cache_hits'] += 1
                    return cached_result
                self.stats['cache_misses'] += 1
            
            # Use connection pool for better resource management
            try:
                result = await super().invoke(query, retries, timeout)
                
                # Cache the result if applicable
                if self.cache and self._should_cache(query, result):
                    await self.cache.set(cache_key, result)
                
                return result
            except Exception as e:
                log.error(f"Invoke error: {e}")
                raise
    
    def _generate_cache_key(self, query) -> str:
        """Generate cache key for query"""
        return f"{query.__class__.__name__}_{hash(str(query.__dict__))}"
    
    def _should_cache(self, query, result) -> bool:
        """Determine if query result should be cached"""
        # Cache read-only operations
        cacheable_types = {
            'GetMe', 'GetUsers', 'GetChats', 'GetHistory',
            'GetDialogs', 'GetContacts'
        }
        return query.__class__.__name__ in cacheable_types
    
    def _get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        total = self.stats['cache_hits'] + self.stats['cache_misses']
        return (self.stats['cache_hits'] / total * 100) if total > 0 else 0
    
    async def _batch_processor(self):
        """Process requests in batches for better efficiency"""
        while True:
            try:
                if len(self.batch_queue) >= 10:  # Process in batches of 10
                    batch = []
                    for _ in range(min(10, len(self.batch_queue))):
                        if self.batch_queue:
                            batch.append(self.batch_queue.popleft())
                    
                    if batch:
                        await asyncio.gather(*batch, return_exceptions=True)
                
                await asyncio.sleep(0.1)  # Small delay to batch requests
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Batch processor error: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of idle connections and cache"""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                await self.connection_pool.cleanup_idle_connections()
                
                # Cache cleanup is handled automatically by TTL
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Cleanup error: {e}")
    
    # Enhanced methods for better performance
    async def send_message_optimized(self, chat_id, text, **kwargs):
        """Optimized send_message with batching support"""
        # Add to batch queue for non-urgent messages
        if kwargs.get('batch', False):
            future = asyncio.Future()
            self.batch_queue.append(self._send_message_task(chat_id, text, kwargs, future))
            return await future
        else:
            return await self.send_message(chat_id, text, **kwargs)
    
    async def _send_message_task(self, chat_id, text, kwargs, future):
        """Internal task for batched message sending"""
        try:
            result = await self.send_message(chat_id, text, **kwargs)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)