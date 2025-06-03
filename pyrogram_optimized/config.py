#!/usr/bin/env python3
"""
Configuration module for Pyrogram Optimized
Centralized configuration management with performance tuning options
"""

import os
import json
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ConnectionPoolConfig:
    """Connection pool configuration"""
    max_connections: int = 10
    min_connections: int = 2
    max_idle_time: float = 300.0  # 5 minutes
    connection_timeout: float = 30.0
    read_timeout: float = 60.0
    write_timeout: float = 30.0
    keepalive_interval: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    health_check_interval: float = 60.0

@dataclass
class CacheConfig:
    """Cache configuration"""
    max_size: int = 10000
    default_ttl: float = 3600.0  # 1 hour
    cleanup_interval: float = 300.0  # 5 minutes
    enable_metrics: bool = True
    compression_threshold: int = 1024  # Compress values larger than 1KB
    
@dataclass
class CryptoConfig:
    """Crypto configuration"""
    prefer_native: bool = True
    thread_pool_size: int = 4
    enable_metrics: bool = True
    cache_hash_results: bool = True
    hash_cache_size: int = 1000
    
@dataclass
class SessionConfig:
    """Session configuration"""
    batch_size: int = 10
    batch_timeout: float = 0.1
    max_batch_wait: float = 1.0
    enable_request_batching: bool = True
    adaptive_timeout: bool = True
    min_timeout: float = 5.0
    max_timeout: float = 300.0
    timeout_multiplier: float = 1.5
    priority_queue_size: int = 1000
    
@dataclass
class MetricsConfig:
    """Metrics and monitoring configuration"""
    enable_metrics: bool = True
    metrics_interval: float = 60.0
    max_metrics_history: int = 1000
    enable_performance_logging: bool = False
    log_slow_operations: bool = True
    slow_operation_threshold: float = 1.0
    
@dataclass
class OptimizationConfig:
    """General optimization configuration"""
    enable_uvloop: bool = True
    enable_orjson: bool = True
    enable_compression: bool = True
    compression_level: int = 6
    enable_connection_pooling: bool = True
    enable_request_batching: bool = True
    enable_caching: bool = True
    enable_adaptive_timeouts: bool = True
    
@dataclass
class PyrogramOptimizedConfig:
    """Main configuration class for Pyrogram Optimized"""
    connection_pool: ConnectionPoolConfig = None
    cache: CacheConfig = None
    crypto: CryptoConfig = None
    session: SessionConfig = None
    metrics: MetricsConfig = None
    optimization: OptimizationConfig = None
    
    def __post_init__(self):
        if self.connection_pool is None:
            self.connection_pool = ConnectionPoolConfig()
        if self.cache is None:
            self.cache = CacheConfig()
        if self.crypto is None:
            self.crypto = CryptoConfig()
        if self.session is None:
            self.session = SessionConfig()
        if self.metrics is None:
            self.metrics = MetricsConfig()
        if self.optimization is None:
            self.optimization = OptimizationConfig()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PyrogramOptimizedConfig':
        """Create config from dictionary"""
        return cls(
            connection_pool=ConnectionPoolConfig(**data.get('connection_pool', {})),
            cache=CacheConfig(**data.get('cache', {})),
            crypto=CryptoConfig(**data.get('crypto', {})),
            session=SessionConfig(**data.get('session', {})),
            metrics=MetricsConfig(**data.get('metrics', {})),
            optimization=OptimizationConfig(**data.get('optimization', {}))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'connection_pool': asdict(self.connection_pool),
            'cache': asdict(self.cache),
            'crypto': asdict(self.crypto),
            'session': asdict(self.session),
            'metrics': asdict(self.metrics),
            'optimization': asdict(self.optimization)
        }
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'PyrogramOptimizedConfig':
        """Load configuration from JSON file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    def save_to_file(self, file_path: Union[str, Path]):
        """Save configuration to JSON file"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def from_env(cls) -> 'PyrogramOptimizedConfig':
        """Create configuration from environment variables"""
        config = cls()
        
        # Connection pool settings
        if os.getenv('PYROGRAM_MAX_CONNECTIONS'):
            config.connection_pool.max_connections = int(os.getenv('PYROGRAM_MAX_CONNECTIONS'))
        if os.getenv('PYROGRAM_CONNECTION_TIMEOUT'):
            config.connection_pool.connection_timeout = float(os.getenv('PYROGRAM_CONNECTION_TIMEOUT'))
        
        # Cache settings
        if os.getenv('PYROGRAM_CACHE_SIZE'):
            config.cache.max_size = int(os.getenv('PYROGRAM_CACHE_SIZE'))
        if os.getenv('PYROGRAM_CACHE_TTL'):
            config.cache.default_ttl = float(os.getenv('PYROGRAM_CACHE_TTL'))
        
        # Crypto settings
        if os.getenv('PYROGRAM_CRYPTO_THREADS'):
            config.crypto.thread_pool_size = int(os.getenv('PYROGRAM_CRYPTO_THREADS'))
        
        # Session settings
        if os.getenv('PYROGRAM_BATCH_SIZE'):
            config.session.batch_size = int(os.getenv('PYROGRAM_BATCH_SIZE'))
        
        # Optimization settings
        if os.getenv('PYROGRAM_ENABLE_UVLOOP'):
            config.optimization.enable_uvloop = os.getenv('PYROGRAM_ENABLE_UVLOOP').lower() == 'true'
        if os.getenv('PYROGRAM_ENABLE_CACHING'):
            config.optimization.enable_caching = os.getenv('PYROGRAM_ENABLE_CACHING').lower() == 'true'
        
        return config

# Predefined configurations for different use cases
class PresetConfigs:
    """Predefined configuration presets"""
    
    @staticmethod
    def high_performance() -> PyrogramOptimizedConfig:
        """High-performance configuration for production use"""
        config = PyrogramOptimizedConfig()
        
        # Aggressive connection pooling
        config.connection_pool.max_connections = 20
        config.connection_pool.min_connections = 5
        config.connection_pool.max_idle_time = 600.0
        
        # Large cache
        config.cache.max_size = 50000
        config.cache.default_ttl = 7200.0  # 2 hours
        
        # More crypto threads
        config.crypto.thread_pool_size = 8
        
        # Larger batches
        config.session.batch_size = 20
        config.session.batch_timeout = 0.05
        
        # Enable all optimizations
        config.optimization.enable_uvloop = True
        config.optimization.enable_orjson = True
        config.optimization.enable_compression = True
        config.optimization.enable_connection_pooling = True
        config.optimization.enable_request_batching = True
        config.optimization.enable_caching = True
        
        return config
    
    @staticmethod
    def memory_efficient() -> PyrogramOptimizedConfig:
        """Memory-efficient configuration for resource-constrained environments"""
        config = PyrogramOptimizedConfig()
        
        # Conservative connection pooling
        config.connection_pool.max_connections = 5
        config.connection_pool.min_connections = 1
        config.connection_pool.max_idle_time = 120.0
        
        # Small cache
        config.cache.max_size = 1000
        config.cache.default_ttl = 1800.0  # 30 minutes
        config.cache.cleanup_interval = 60.0
        
        # Fewer crypto threads
        config.crypto.thread_pool_size = 2
        config.crypto.hash_cache_size = 100
        
        # Smaller batches
        config.session.batch_size = 5
        config.session.priority_queue_size = 100
        
        # Disable some optimizations to save memory
        config.optimization.enable_compression = False
        config.metrics.max_metrics_history = 100
        
        return config
    
    @staticmethod
    def development() -> PyrogramOptimizedConfig:
        """Development configuration with extensive logging and metrics"""
        config = PyrogramOptimizedConfig()
        
        # Moderate settings
        config.connection_pool.max_connections = 5
        config.cache.max_size = 5000
        
        # Enable extensive metrics and logging
        config.metrics.enable_metrics = True
        config.metrics.enable_performance_logging = True
        config.metrics.log_slow_operations = True
        config.metrics.slow_operation_threshold = 0.5
        config.metrics.metrics_interval = 30.0
        
        # Enable all features for testing
        config.optimization.enable_uvloop = True
        config.optimization.enable_orjson = True
        config.optimization.enable_compression = True
        config.optimization.enable_connection_pooling = True
        config.optimization.enable_request_batching = True
        config.optimization.enable_caching = True
        
        return config

# Global configuration instance
_global_config: Optional[PyrogramOptimizedConfig] = None

def get_config() -> PyrogramOptimizedConfig:
    """Get the global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = PyrogramOptimizedConfig()
    return _global_config

def set_config(config: PyrogramOptimizedConfig):
    """Set the global configuration instance"""
    global _global_config
    _global_config = config

def load_config_from_file(file_path: Union[str, Path]):
    """Load configuration from file and set as global"""
    config = PyrogramOptimizedConfig.from_file(file_path)
    set_config(config)

def load_config_from_env():
    """Load configuration from environment variables and set as global"""
    config = PyrogramOptimizedConfig.from_env()
    set_config(config)

def use_preset(preset_name: str):
    """Use a predefined configuration preset"""
    presets = {
        'high_performance': PresetConfigs.high_performance,
        'memory_efficient': PresetConfigs.memory_efficient,
        'development': PresetConfigs.development
    }
    
    if preset_name not in presets:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")
    
    config = presets[preset_name]()
    set_config(config)