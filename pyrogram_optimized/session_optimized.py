#  Optimized Session Module for Pyrogram
#  Enhanced with better async handling, request batching, and performance monitoring

import asyncio
import bisect
import logging
import time
from collections import deque, defaultdict
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

import pyrogram
from pyrogram.session.session import Session as BaseSession, Result
from pyrogram.raw.core import TLObject, MsgContainer
from pyrogram.errors import RPCError, FloodWait
from .connection_optimized import OptimizedConnection

log = logging.getLogger(__name__)


@dataclass
class SessionMetrics:
    """Metrics for session performance monitoring"""
    requests_sent: int = 0
    responses_received: int = 0
    errors_count: int = 0
    flood_waits: int = 0
    avg_response_time: float = 0.0
    total_response_time: float = 0.0
    start_time: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    

class RequestBatch:
    """Batch multiple requests for efficient processing"""
    
    def __init__(self, max_size: int = 10, max_wait: float = 0.1):
        self.max_size = max_size
        self.max_wait = max_wait
        self.requests: List[tuple] = []
        self.created_at = time.time()
    
    def add_request(self, query: TLObject, future: asyncio.Future):
        """Add request to batch"""
        self.requests.append((query, future))
    
    def is_ready(self) -> bool:
        """Check if batch is ready for processing"""
        return (len(self.requests) >= self.max_size or 
                time.time() - self.created_at >= self.max_wait)
    
    def is_empty(self) -> bool:
        return len(self.requests) == 0


class OptimizedSession(BaseSession):
    """Enhanced session with performance optimizations"""
    
    # Enhanced timeouts and thresholds
    START_TIMEOUT = 5  # Reduced from 2
    WAIT_TIMEOUT = 30  # Increased from 15
    SLEEP_THRESHOLD = 5  # Reduced from 10
    MAX_RETRIES = 15  # Increased from 10
    ACKS_THRESHOLD = 5  # Reduced from 10
    PING_INTERVAL = 10  # Increased from 5
    STORED_MSG_IDS_MAX_SIZE = 2000  # Increased from 1000
    
    # New optimization parameters
    BATCH_SIZE = 10
    BATCH_TIMEOUT = 0.1
    REQUEST_QUEUE_SIZE = 100
    ADAPTIVE_TIMEOUT = True
    
    def __init__(self, client, dc_id: int, auth_key: bytes, test_mode: bool, 
                 is_media: bool = False, is_cdn: bool = False):
        super().__init__(client, dc_id, auth_key, test_mode, is_media, is_cdn)
        
        # Performance enhancements
        self.metrics = SessionMetrics()
        self.request_queue: asyncio.Queue = asyncio.Queue(maxsize=self.REQUEST_QUEUE_SIZE)
        self.batch_processor_task: Optional[asyncio.Task] = None
        self.current_batch: Optional[RequestBatch] = None
        
        # Adaptive timeout management
        self.response_times: deque = deque(maxlen=100)  # Keep last 100 response times
        self.adaptive_wait_timeout = self.WAIT_TIMEOUT
        
        # Enhanced error handling
        self.error_backoff = defaultdict(float)  # Per-error-type backoff
        self.flood_wait_history: deque = deque(maxlen=50)
        
        # Request prioritization
        self.priority_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.request_priorities = {
            'auth': 0,  # Highest priority
            'message': 1,
            'media': 2,
            'other': 3  # Lowest priority
        }
        
        # Connection health monitoring
        self.connection_health_check_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Enhanced start with optimizations"""
        # Use optimized connection
        self.connection = OptimizedConnection(
            self.dc_id, self.test_mode, self.client.ipv6, 
            self.client.proxy, self.is_media
        )
        
        await super().start()
        
        # Start optimization tasks
        if not self.batch_processor_task:
            self.batch_processor_task = asyncio.create_task(self._batch_processor())
        
        if not self.connection_health_check_task:
            self.connection_health_check_task = asyncio.create_task(self._health_monitor())
        
        log.info(f"Optimized session started for DC{self.dc_id}")
    
    async def stop(self):
        """Enhanced stop with cleanup"""
        # Cancel optimization tasks
        for task in [self.batch_processor_task, self.connection_health_check_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        await super().stop()
        
        # Log session statistics
        self._log_session_stats()
    
    async def send(self, query: TLObject, retries: int = 0, timeout: float = None) -> Any:
        """Enhanced send with batching and adaptive timeout"""
        start_time = time.time()
        
        # Use adaptive timeout if not specified
        if timeout is None:
            timeout = self._get_adaptive_timeout()
        
        # Determine request priority
        priority = self._get_request_priority(query)
        
        try:
            # Check if request can be batched
            if self._can_batch_request(query):
                result = await self._send_batched(query, timeout)
            else:
                result = await self._send_immediate(query, retries, timeout)
            
            # Update metrics
            response_time = time.time() - start_time
            self._update_response_metrics(response_time)
            
            return result
            
        except FloodWait as e:
            self._handle_flood_wait(e)
            raise
        except Exception as e:
            self.metrics.errors_count += 1
            self._update_error_backoff(type(e).__name__)
            raise
    
    async def _send_batched(self, query: TLObject, timeout: float) -> Any:
        """Send request as part of a batch"""
        future = asyncio.Future()
        
        # Add to current batch or create new one
        if not self.current_batch or self.current_batch.is_ready():
            if self.current_batch and not self.current_batch.is_empty():
                await self._process_batch(self.current_batch)
            self.current_batch = RequestBatch(self.BATCH_SIZE, self.BATCH_TIMEOUT)
        
        self.current_batch.add_request(query, future)
        
        # Process batch if ready
        if self.current_batch.is_ready():
            await self._process_batch(self.current_batch)
            self.current_batch = None
        
        return await asyncio.wait_for(future, timeout)
    
    async def _send_immediate(self, query: TLObject, retries: int, timeout: float) -> Any:
        """Send request immediately without batching"""
        return await super().send(query, retries, timeout)
    
    async def _process_batch(self, batch: RequestBatch):
        """Process a batch of requests"""
        if batch.is_empty():
            return
        
        try:
            # Create container for multiple requests
            if len(batch.requests) > 1:
                queries = [req[0] for req in batch.requests]
                container = MsgContainer([self.msg_factory() for _ in queries])
                
                # Send container
                result = await super().send(container)
                
                # Distribute results to futures
                if isinstance(result, list):
                    for i, (_, future) in enumerate(batch.requests):
                        if i < len(result):
                            future.set_result(result[i])
                        else:
                            future.set_exception(Exception("No result for request"))
                else:
                    # Single result for all requests
                    for _, future in batch.requests:
                        future.set_result(result)
            else:
                # Single request
                query, future = batch.requests[0]
                result = await super().send(query)
                future.set_result(result)
                
        except Exception as e:
            # Set exception for all futures in batch
            for _, future in batch.requests:
                if not future.done():
                    future.set_exception(e)
    
    async def _batch_processor(self):
        """Background task to process batches"""
        try:
            while True:
                await asyncio.sleep(self.BATCH_TIMEOUT)
                
                if (self.current_batch and 
                    not self.current_batch.is_empty() and 
                    time.time() - self.current_batch.created_at >= self.BATCH_TIMEOUT):
                    
                    await self._process_batch(self.current_batch)
                    self.current_batch = None
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error(f"Batch processor error: {e}")
    
    async def _health_monitor(self):
        """Monitor connection health and take corrective actions"""
        try:
            while True:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                if hasattr(self.connection, 'get_health_score'):
                    health_score = self.connection.get_health_score()
                    
                    if health_score < 0.3:  # Poor health
                        log.warning(f"Poor connection health ({health_score:.2f}) for DC{self.dc_id}")
                        # Could implement reconnection logic here
                    
                    # Adjust timeouts based on health
                    if health_score < 0.5:
                        self.adaptive_wait_timeout = min(60, self.WAIT_TIMEOUT * 2)
                    else:
                        self.adaptive_wait_timeout = max(self.WAIT_TIMEOUT, 
                                                       self.adaptive_wait_timeout * 0.95)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error(f"Health monitor error: {e}")
    
    def _get_adaptive_timeout(self) -> float:
        """Calculate adaptive timeout based on recent response times"""
        if not self.ADAPTIVE_TIMEOUT or not self.response_times:
            return self.adaptive_wait_timeout
        
        # Use 95th percentile of recent response times
        sorted_times = sorted(self.response_times)
        percentile_95 = sorted_times[int(len(sorted_times) * 0.95)]
        
        # Add buffer and respect limits
        adaptive_timeout = max(self.WAIT_TIMEOUT, percentile_95 * 3)
        return min(120, adaptive_timeout)  # Cap at 2 minutes
    
    def _get_request_priority(self, query: TLObject) -> int:
        """Determine request priority based on query type"""
        query_name = query.__class__.__name__.lower()
        
        if 'auth' in query_name or 'login' in query_name:
            return self.request_priorities['auth']
        elif 'message' in query_name or 'send' in query_name:
            return self.request_priorities['message']
        elif 'media' in query_name or 'photo' in query_name or 'document' in query_name:
            return self.request_priorities['media']
        else:
            return self.request_priorities['other']
    
    def _can_batch_request(self, query: TLObject) -> bool:
        """Determine if request can be batched"""
        # Don't batch auth requests or file uploads
        query_name = query.__class__.__name__.lower()
        non_batchable = ['auth', 'upload', 'download', 'login']
        return not any(term in query_name for term in non_batchable)
    
    def _update_response_metrics(self, response_time: float):
        """Update response time metrics"""
        self.response_times.append(response_time)
        self.metrics.responses_received += 1
        self.metrics.total_response_time += response_time
        self.metrics.avg_response_time = (self.metrics.total_response_time / 
                                        self.metrics.responses_received)
        self.metrics.last_activity = time.time()
    
    def _handle_flood_wait(self, flood_wait: FloodWait):
        """Handle flood wait with tracking"""
        self.metrics.flood_waits += 1
        self.flood_wait_history.append({
            'timestamp': time.time(),
            'value': flood_wait.value
        })
        
        # Adjust adaptive timeout based on flood waits
        if len(self.flood_wait_history) > 5:  # Recent flood waits
            recent_floods = [fw for fw in self.flood_wait_history 
                           if time.time() - fw['timestamp'] < 300]  # Last 5 minutes
            if len(recent_floods) > 3:
                self.adaptive_wait_timeout *= 1.5
    
    def _update_error_backoff(self, error_type: str):
        """Update backoff for specific error types"""
        current_backoff = self.error_backoff[error_type]
        self.error_backoff[error_type] = min(60, max(1, current_backoff * 1.5))
    
    def _log_session_stats(self):
        """Log session performance statistics"""
        uptime = time.time() - self.metrics.start_time
        
        log.info(f"Session DC{self.dc_id} stats - "
                f"Uptime: {uptime:.1f}s, "
                f"Requests: {self.metrics.requests_sent}, "
                f"Responses: {self.metrics.responses_received}, "
                f"Errors: {self.metrics.errors_count}, "
                f"Flood waits: {self.metrics.flood_waits}, "
                f"Avg response time: {self.metrics.avg_response_time:.3f}s")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        uptime = time.time() - self.metrics.start_time
        
        return {
            'dc_id': self.dc_id,
            'uptime': uptime,
            'requests_sent': self.metrics.requests_sent,
            'responses_received': self.metrics.responses_received,
            'errors_count': self.metrics.errors_count,
            'flood_waits': self.metrics.flood_waits,
            'avg_response_time': self.metrics.avg_response_time,
            'adaptive_timeout': self.adaptive_wait_timeout,
            'recent_response_times': list(self.response_times)[-10:],  # Last 10
            'error_backoffs': dict(self.error_backoff),
            'connection_health': (self.connection.get_health_score() 
                                if hasattr(self.connection, 'get_health_score') else None)
        }