#!/usr/bin/env python3
"""
Test Suite for Pyrogram Optimized
Comprehensive tests for all optimization features
"""

import asyncio
import pytest
import time
import sys
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

try:
    from .client_optimized import ClientOptimized, ConnectionPool, OptimizedCache
    from .connection_optimized import OptimizedConnection
    from .session_optimized import OptimizedSession
    from .crypto_optimized import CryptoOptimized
    from .config import PyrogramOptimizedConfig, PresetConfigs
except ImportError:
    from client_optimized import ClientOptimized, ConnectionPool, OptimizedCache
    from connection_optimized import OptimizedConnection
    from session_optimized import OptimizedSession
    from crypto_optimized import CryptoOptimized
    from config import PyrogramOptimizedConfig, PresetConfigs

class TestOptimizedCache:
    """Test cases for OptimizedCache"""
    
    @pytest.fixture
    async def cache(self):
        """Create a test cache instance"""
        cache = OptimizedCache(max_size=100, default_ttl=1.0)
        yield cache
        await cache.clear()
    
    @pytest.mark.asyncio
    async def test_basic_operations(self, cache):
        """Test basic cache operations"""
        # Test set and get
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"
        
        # Test non-existent key
        result = await cache.get("nonexistent")
        assert result is None
        
        # Test default value
        result = await cache.get("nonexistent", "default")
        assert result == "default"
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache):
        """Test TTL expiration"""
        await cache.set("key1", "value1", ttl=0.1)
        
        # Should be available immediately
        result = await cache.get("key1")
        assert result == "value1"
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        result = await cache.get("key1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_size_limit(self, cache):
        """Test cache size limit"""
        # Fill cache beyond limit
        for i in range(150):
            await cache.set(f"key{i}", f"value{i}")
        
        # Check that cache size is maintained
        stats = await cache.get_stats()
        assert stats['size'] <= 100
    
    @pytest.mark.asyncio
    async def test_metrics(self, cache):
        """Test cache metrics"""
        # Generate some cache activity
        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss
        
        stats = await cache.get_stats()
        assert stats['hits'] >= 1
        assert stats['misses'] >= 1
        assert stats['hit_rate'] > 0

class TestCryptoOptimized:
    """Test cases for CryptoOptimized"""
    
    @pytest.fixture
    def crypto(self):
        """Create a test crypto instance"""
        return CryptoOptimized()
    
    @pytest.mark.asyncio
    async def test_sha256(self, crypto):
        """Test SHA256 hashing"""
        data = b"Hello, World!"
        hash1 = await crypto.sha256(data)
        hash2 = await crypto.sha256(data)
        
        # Should produce consistent results
        assert hash1 == hash2
        assert len(hash1) == 32  # SHA256 produces 32 bytes
    
    @pytest.mark.asyncio
    async def test_sha1(self, crypto):
        """Test SHA1 hashing"""
        data = b"Hello, World!"
        hash1 = await crypto.sha1(data)
        hash2 = await crypto.sha1(data)
        
        # Should produce consistent results
        assert hash1 == hash2
        assert len(hash1) == 20  # SHA1 produces 20 bytes
    
    @pytest.mark.asyncio
    async def test_ige_encryption(self, crypto):
        """Test IGE encryption/decryption"""
        data = b"This is a test message for IGE encryption!" * 2
        key = b"0123456789abcdef" * 2  # 32 bytes
        iv = b"fedcba9876543210" * 2   # 32 bytes
        
        # Encrypt
        encrypted = await crypto.ige_encrypt(data, key, iv)
        assert encrypted != data
        assert len(encrypted) >= len(data)
        
        # Decrypt
        decrypted = await crypto.ige_decrypt(encrypted, key, iv)
        assert decrypted == data
    
    @pytest.mark.asyncio
    async def test_ctr_encryption(self, crypto):
        """Test CTR encryption/decryption"""
        data = b"This is a test message for CTR encryption!"
        key = b"0123456789abcdef" * 2  # 32 bytes
        iv = b"fedcba9876543210"       # 16 bytes
        
        # Encrypt
        encrypted = await crypto.ctr_encrypt(data, key, iv)
        assert encrypted != data
        assert len(encrypted) == len(data)
        
        # Decrypt (CTR is symmetric)
        decrypted = await crypto.ctr_encrypt(encrypted, key, iv)
        assert decrypted == data
    
    @pytest.mark.asyncio
    async def test_xor_optimization(self, crypto):
        """Test optimized XOR function"""
        a = b"Hello, World!"
        b = b"Secret Key!!!"
        
        result = await crypto.xor(a, b)
        assert len(result) == min(len(a), len(b))
        
        # XOR should be reversible
        reversed_result = await crypto.xor(result, b)
        assert reversed_result == a[:len(b)]

class TestConnectionPool:
    """Test cases for ConnectionPool"""
    
    @pytest.fixture
    def pool_config(self):
        """Create test pool configuration"""
        from .client_optimized import ConnectionPoolConfig
        return ConnectionPoolConfig(
            max_connections=5,
            min_connections=1,
            connection_timeout=1.0
        )
    
    @pytest.fixture
    async def pool(self, pool_config):
        """Create a test connection pool"""
        pool = ConnectionPool(pool_config)
        yield pool
        await pool.close_all()
    
    @pytest.mark.asyncio
    async def test_connection_acquisition(self, pool):
        """Test connection acquisition and release"""
        # Mock connection factory
        mock_connection = AsyncMock()
        mock_connection.is_connected = True
        mock_connection.health_score = 1.0
        
        with patch.object(pool, '_create_connection', return_value=mock_connection):
            # Acquire connection
            conn = await pool.get_connection()
            assert conn is not None
            
            # Release connection
            await pool.release_connection(conn)
            
            # Pool should reuse the connection
            conn2 = await pool.get_connection()
            assert conn2 == conn
    
    @pytest.mark.asyncio
    async def test_pool_limits(self, pool):
        """Test connection pool limits"""
        mock_connection = AsyncMock()
        mock_connection.is_connected = True
        mock_connection.health_score = 1.0
        
        with patch.object(pool, '_create_connection', return_value=mock_connection):
            # Acquire maximum connections
            connections = []
            for _ in range(5):  # max_connections = 5
                conn = await pool.get_connection()
                connections.append(conn)
            
            # Pool should be at capacity
            stats = await pool.get_stats()
            assert stats['active_connections'] == 5
            
            # Release connections
            for conn in connections:
                await pool.release_connection(conn)

class TestOptimizedSession:
    """Test cases for OptimizedSession"""
    
    @pytest.fixture
    def session_config(self):
        """Create test session configuration"""
        from .config import SessionConfig
        return SessionConfig(
            batch_size=5,
            batch_timeout=0.1,
            enable_request_batching=True
        )
    
    @pytest.fixture
    async def session(self, session_config):
        """Create a test session"""
        mock_connection = AsyncMock()
        session = OptimizedSession(mock_connection, session_config)
        yield session
        await session.stop()
    
    @pytest.mark.asyncio
    async def test_request_batching(self, session):
        """Test request batching functionality"""
        # Mock the send method
        session.connection.send = AsyncMock()
        
        # Send multiple requests quickly
        requests = []
        for i in range(3):
            request = Mock()
            request.data = f"request_{i}"
            requests.append(session.send_request(request))
        
        # Wait for batch processing
        await asyncio.sleep(0.2)
        
        # Verify that batching occurred
        assert session.connection.send.called
    
    @pytest.mark.asyncio
    async def test_adaptive_timeout(self, session):
        """Test adaptive timeout functionality"""
        # Enable adaptive timeout
        session.config.adaptive_timeout = True
        
        # Simulate slow response
        session.connection.send = AsyncMock()
        session.connection.send.side_effect = lambda x: asyncio.sleep(0.5)
        
        request = Mock()
        request.data = "test_request"
        
        start_time = time.time()
        try:
            await asyncio.wait_for(session.send_request(request), timeout=1.0)
        except asyncio.TimeoutError:
            pass
        
        # Timeout should have been adjusted
        elapsed = time.time() - start_time
        assert elapsed < 1.0  # Should timeout before 1 second

class TestConfiguration:
    """Test cases for configuration management"""
    
    def test_default_config(self):
        """Test default configuration creation"""
        config = PyrogramOptimizedConfig()
        
        assert config.connection_pool is not None
        assert config.cache is not None
        assert config.crypto is not None
        assert config.session is not None
        assert config.metrics is not None
        assert config.optimization is not None
    
    def test_preset_configs(self):
        """Test preset configurations"""
        # High performance preset
        hp_config = PresetConfigs.high_performance()
        assert hp_config.connection_pool.max_connections == 20
        assert hp_config.cache.max_size == 50000
        assert hp_config.optimization.enable_uvloop is True
        
        # Memory efficient preset
        me_config = PresetConfigs.memory_efficient()
        assert me_config.connection_pool.max_connections == 5
        assert me_config.cache.max_size == 1000
        assert me_config.optimization.enable_compression is False
        
        # Development preset
        dev_config = PresetConfigs.development()
        assert dev_config.metrics.enable_performance_logging is True
        assert dev_config.metrics.log_slow_operations is True
    
    def test_config_serialization(self, tmp_path):
        """Test configuration file serialization"""
        config = PyrogramOptimizedConfig()
        config_file = tmp_path / "test_config.json"
        
        # Save configuration
        config.save_to_file(config_file)
        assert config_file.exists()
        
        # Load configuration
        loaded_config = PyrogramOptimizedConfig.from_file(config_file)
        
        # Verify configuration matches
        assert loaded_config.connection_pool.max_connections == config.connection_pool.max_connections
        assert loaded_config.cache.max_size == config.cache.max_size

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test optimized client initialization"""
        config = PresetConfigs.development()
        
        # Mock the necessary components
        with patch('pyrogram.Client.__init__', return_value=None):
            client = ClientOptimized(
                name="test_client",
                api_id=12345,
                api_hash="test_hash",
                config=config
            )
            
            assert client.config == config
            assert client.cache is not None
            assert client.connection_pool is not None
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self):
        """Test performance monitoring functionality"""
        config = PresetConfigs.development()
        config.metrics.enable_metrics = True
        
        crypto = CryptoOptimized()
        
        # Perform some operations
        data = b"Test data for performance monitoring"
        await crypto.sha256(data)
        await crypto.sha1(data)
        
        # Check metrics
        metrics = crypto.get_metrics()
        assert 'operations_count' in metrics
        assert 'total_time' in metrics
        assert metrics['operations_count'] > 0

# Test runner
def run_tests():
    """Run all tests"""
    # Set event loop policy for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])

if __name__ == "__main__":
    run_tests()