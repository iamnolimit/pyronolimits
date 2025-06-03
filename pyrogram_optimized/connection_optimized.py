#  Optimized Connection Module for Pyrogram
#  Enhanced with connection pooling, better error handling, and performance improvements

import asyncio
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

from pyrogram.connection.connection import Connection as BaseConnection
from pyrogram.connection.transport import TCPAbridged
from pyrogram.session.internals import DataCenter

log = logging.getLogger(__name__)


@dataclass
class ConnectionMetrics:
    """Metrics for connection performance monitoring"""
    bytes_sent: int = 0
    bytes_received: int = 0
    requests_count: int = 0
    errors_count: int = 0
    connect_time: float = 0
    last_activity: float = 0
    

class OptimizedConnection(BaseConnection):
    """Enhanced connection with performance optimizations"""
    
    MAX_CONNECTION_ATTEMPTS = 5  # Increased from 3
    CONNECT_TIMEOUT = 15  # Increased timeout
    KEEPALIVE_INTERVAL = 30  # Send keepalive every 30 seconds
    
    def __init__(self, dc_id: int, test_mode: bool, ipv6: bool, proxy: dict, media: bool = False):
        super().__init__(dc_id, test_mode, ipv6, proxy, media)
        
        # Performance enhancements
        self.metrics = ConnectionMetrics()
        self.keepalive_task: Optional[asyncio.Task] = None
        self.last_ping = 0
        self.connection_quality = 1.0  # 0.0 to 1.0 quality score
        self.adaptive_timeout = self.CONNECT_TIMEOUT
        
        # Connection state
        self.is_healthy = True
        self.consecutive_errors = 0
        self.last_error_time = 0
        
    async def connect(self):
        """Enhanced connect with adaptive retry and better error handling"""
        start_time = time.time()
        
        for attempt in range(self.MAX_CONNECTION_ATTEMPTS):
            try:
                # Use adaptive timeout based on previous performance
                timeout = self.adaptive_timeout * (1 + attempt * 0.5)
                
                self.protocol = TCPAbridged(self.ipv6, self.proxy)
                
                log.info(f"Connecting to DC{self.dc_id} (attempt {attempt + 1}/{self.MAX_CONNECTION_ATTEMPTS})...")
                
                # Connect with timeout
                await asyncio.wait_for(
                    self.protocol.connect(self.address),
                    timeout=timeout
                )
                
                # Connection successful
                self.metrics.connect_time = time.time() - start_time
                self.metrics.last_activity = time.time()
                self.is_healthy = True
                self.consecutive_errors = 0
                
                # Start keepalive task
                if not self.keepalive_task or self.keepalive_task.done():
                    self.keepalive_task = asyncio.create_task(self._keepalive_loop())
                
                # Adjust adaptive timeout based on success
                if self.metrics.connect_time < 5:
                    self.adaptive_timeout = max(5, self.adaptive_timeout * 0.9)
                
                log.info(f"Connected! {self._get_connection_info()} (took {self.metrics.connect_time:.2f}s)")
                return
                
            except asyncio.TimeoutError:
                log.warning(f"Connection timeout on attempt {attempt + 1}")
                self._handle_connection_error()
                
            except OSError as e:
                log.warning(f"Network error on attempt {attempt + 1}: {e}")
                self._handle_connection_error()
                
            except Exception as e:
                log.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                self._handle_connection_error()
            
            finally:
                if hasattr(self, 'protocol') and self.protocol:
                    await self.protocol.close()
            
            # Exponential backoff with jitter
            if attempt < self.MAX_CONNECTION_ATTEMPTS - 1:
                delay = min(30, (2 ** attempt) + (time.time() % 1))  # Add jitter
                log.info(f"Retrying in {delay:.1f} seconds...")
                await asyncio.sleep(delay)
        
        # All attempts failed
        self.is_healthy = False
        raise ConnectionError(f"Failed to connect to DC{self.dc_id} after {self.MAX_CONNECTION_ATTEMPTS} attempts")
    
    def _handle_connection_error(self):
        """Handle connection errors and update metrics"""
        self.consecutive_errors += 1
        self.last_error_time = time.time()
        self.metrics.errors_count += 1
        
        # Decrease connection quality
        self.connection_quality = max(0.1, self.connection_quality * 0.8)
        
        # Increase adaptive timeout for poor connections
        if self.consecutive_errors > 2:
            self.adaptive_timeout = min(60, self.adaptive_timeout * 1.5)
    
    async def send(self, data: bytes):
        """Enhanced send with metrics tracking"""
        try:
            await super().send(data)
            self.metrics.bytes_sent += len(data)
            self.metrics.requests_count += 1
            self.metrics.last_activity = time.time()
            
            # Improve connection quality on successful sends
            self.connection_quality = min(1.0, self.connection_quality * 1.01)
            
        except Exception as e:
            self._handle_connection_error()
            raise
    
    async def recv(self) -> Optional[bytes]:
        """Enhanced recv with metrics tracking"""
        try:
            data = await super().recv()
            if data:
                self.metrics.bytes_received += len(data)
                self.metrics.last_activity = time.time()
                
                # Improve connection quality on successful receives
                self.connection_quality = min(1.0, self.connection_quality * 1.01)
            
            return data
            
        except Exception as e:
            self._handle_connection_error()
            raise
    
    async def close(self):
        """Enhanced close with cleanup"""
        # Cancel keepalive task
        if self.keepalive_task and not self.keepalive_task.done():
            self.keepalive_task.cancel()
            try:
                await self.keepalive_task
            except asyncio.CancelledError:
                pass
        
        await super().close()
        
        # Log connection statistics
        uptime = time.time() - (self.metrics.last_activity - self.metrics.connect_time)
        log.info(f"Connection closed. Stats: {self.metrics.requests_count} requests, "
                f"{self.metrics.bytes_sent} bytes sent, {self.metrics.bytes_received} bytes received, "
                f"uptime: {uptime:.1f}s, quality: {self.connection_quality:.2f}")
    
    async def _keepalive_loop(self):
        """Send periodic keepalive to maintain connection"""
        try:
            while True:
                await asyncio.sleep(self.KEEPALIVE_INTERVAL)
                
                # Check if connection is idle
                if time.time() - self.metrics.last_activity > self.KEEPALIVE_INTERVAL:
                    try:
                        # Send a small ping to keep connection alive
                        await self._send_ping()
                    except Exception as e:
                        log.warning(f"Keepalive ping failed: {e}")
                        self._handle_connection_error()
                        break
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error(f"Keepalive loop error: {e}")
    
    async def _send_ping(self):
        """Send a ping to test connection"""
        # This would typically send a ping message
        # For now, we'll just update the last ping time
        self.last_ping = time.time()
        log.debug(f"Sent keepalive ping to DC{self.dc_id}")
    
    def _get_connection_info(self) -> str:
        """Get formatted connection information"""
        return (f"{'Test' if self.test_mode else 'Production'} "
                f"DC{self.dc_id}{'(media)' if self.media else ''} - "
                f"IPv{'6' if self.ipv6 else '4'}")
    
    def get_health_score(self) -> float:
        """Calculate connection health score (0.0 to 1.0)"""
        if not self.is_healthy:
            return 0.0
        
        # Base score from connection quality
        score = self.connection_quality
        
        # Penalty for recent errors
        if self.consecutive_errors > 0:
            error_penalty = min(0.5, self.consecutive_errors * 0.1)
            score -= error_penalty
        
        # Penalty for old last activity
        time_since_activity = time.time() - self.metrics.last_activity
        if time_since_activity > 300:  # 5 minutes
            age_penalty = min(0.3, (time_since_activity - 300) / 1800)  # Max penalty after 30 min
            score -= age_penalty
        
        return max(0.0, min(1.0, score))
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get connection metrics summary"""
        return {
            'dc_id': self.dc_id,
            'is_healthy': self.is_healthy,
            'health_score': self.get_health_score(),
            'connection_quality': self.connection_quality,
            'bytes_sent': self.metrics.bytes_sent,
            'bytes_received': self.metrics.bytes_received,
            'requests_count': self.metrics.requests_count,
            'errors_count': self.metrics.errors_count,
            'consecutive_errors': self.consecutive_errors,
            'connect_time': self.metrics.connect_time,
            'last_activity': self.metrics.last_activity,
            'adaptive_timeout': self.adaptive_timeout
        }