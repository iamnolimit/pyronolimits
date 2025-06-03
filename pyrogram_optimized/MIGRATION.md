# Migration Guide: Pyrogram to Pyrogram Optimized

This guide will help you migrate from the original Pyrogram to Pyrogram Optimized, taking advantage of all the performance improvements while maintaining compatibility.

## 🚀 Quick Start Migration

### 1. Basic Client Migration

**Before (Original Pyrogram):**

```python
from pyrogram import Client

app = Client(
    "my_account",
    api_id=12345,
    api_hash="your_api_hash"
)

async def main():
    async with app:
        await app.send_message("me", "Hello!")
```

**After (Pyrogram Optimized):**

```python
from pyrogram_optimized import ClientOptimized
from pyrogram_optimized.config import PresetConfigs

# Use optimized client with performance preset
config = PresetConfigs.high_performance()
app = ClientOptimized(
    "my_account",
    api_id=12345,
    api_hash="your_api_hash",
    config=config
)

async def main():
    async with app:
        await app.send_message("me", "Hello!")
```

### 2. Drop-in Replacement

For minimal changes, you can use the optimized client as a drop-in replacement:

```python
# Simply replace the import
from pyrogram_optimized import ClientOptimized as Client

# Rest of your code remains the same
app = Client("my_account", api_id=12345, api_hash="your_api_hash")
```

## 📊 Performance Optimization Levels

### Level 1: Basic Optimization (No Code Changes)

```python
from pyrogram_optimized import ClientOptimized

# Default configuration already includes basic optimizations
app = ClientOptimized("my_account", api_id=12345, api_hash="your_api_hash")
```

**Benefits:**

- ✅ Optimized crypto operations
- ✅ Connection pooling
- ✅ Basic caching
- ✅ Improved error handling

### Level 2: Preset Configuration

```python
from pyrogram_optimized import ClientOptimized
from pyrogram_optimized.config import PresetConfigs

# Choose a preset based on your needs
config = PresetConfigs.high_performance()  # For production
# config = PresetConfigs.memory_efficient()  # For limited resources
# config = PresetConfigs.development()       # For development

app = ClientOptimized(
    "my_account",
    api_id=12345,
    api_hash="your_api_hash",
    config=config
)
```

**Additional Benefits:**

- ✅ Tuned connection pools
- ✅ Optimized cache sizes
- ✅ Request batching
- ✅ Adaptive timeouts

### Level 3: Custom Configuration

```python
from pyrogram_optimized import ClientOptimized
from pyrogram_optimized.config import PyrogramOptimizedConfig, ConnectionPoolConfig, CacheConfig

# Create custom configuration
config = PyrogramOptimizedConfig()
config.connection_pool = ConnectionPoolConfig(
    max_connections=15,
    connection_timeout=20.0
)
config.cache = CacheConfig(
    max_size=20000,
    default_ttl=1800.0
)

app = ClientOptimized(
    "my_account",
    api_id=12345,
    api_hash="your_api_hash",
    config=config
)
```

**Full Control:**

- ✅ Fine-tuned for your specific use case
- ✅ Custom connection pool settings
- ✅ Tailored cache configuration
- ✅ Specific optimization toggles

## 🔄 Common Migration Patterns

### Bot Migration

**Before:**

```python
from pyrogram import Client, filters
from pyrogram.types import Message

app = Client("my_bot", bot_token="your_bot_token")

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply("Hello!")

app.run()
```

**After:**

```python
from pyrogram_optimized import ClientOptimized
from pyrogram_optimized.config import PresetConfigs
from pyrogram import filters
from pyrogram.types import Message

# Use high-performance preset for bots
config = PresetConfigs.high_performance()
app = ClientOptimized(
    "my_bot",
    bot_token="your_bot_token",
    config=config
)

@app.on_message(filters.command("start"))
async def start_command(client: ClientOptimized, message: Message):
    await message.reply("Hello!")

# Enable performance monitoring
@app.on_message(filters.command("stats"))
async def stats_command(client: ClientOptimized, message: Message):
    stats = await client.get_performance_stats()
    await message.reply(f"Performance Stats:\n{stats}")

app.run()
```

### Bulk Operations Migration

**Before:**

```python
# Sending multiple messages sequentially
for user_id in user_list:
    await app.send_message(user_id, "Broadcast message")
```

**After:**

```python
# Using optimized bulk operations
await app.send_bulk_messages(
    [(user_id, "Broadcast message") for user_id in user_list],
    batch_size=10  # Process in batches
)
```

### File Operations Migration

**Before:**

```python
# Basic file download
file_path = await app.download_media(message.document)
```

**After:**

```python
# Optimized file operations with caching
file_path = await app.download_media(
    message.document,
    use_cache=True,  # Cache file metadata
    progress=progress_callback  # Optional progress tracking
)
```

## 🛠️ Configuration Migration

### Environment Variables

Set environment variables for automatic configuration:

```bash
# Connection settings
export PYROGRAM_MAX_CONNECTIONS=20
export PYROGRAM_CONNECTION_TIMEOUT=30

# Cache settings
export PYROGRAM_CACHE_SIZE=50000
export PYROGRAM_CACHE_TTL=7200

# Optimization toggles
export PYROGRAM_ENABLE_UVLOOP=true
export PYROGRAM_ENABLE_CACHING=true
```

```python
from pyrogram_optimized import ClientOptimized
from pyrogram_optimized.config import PyrogramOptimizedConfig

# Load configuration from environment
config = PyrogramOptimizedConfig.from_env()
app = ClientOptimized("my_account", api_id=12345, api_hash="hash", config=config)
```

### Configuration Files

Create a configuration file:

```json
{
  "connection_pool": {
    "max_connections": 20,
    "connection_timeout": 30.0,
    "max_idle_time": 600.0
  },
  "cache": {
    "max_size": 50000,
    "default_ttl": 7200.0
  },
  "optimization": {
    "enable_uvloop": true,
    "enable_caching": true,
    "enable_request_batching": true
  }
}
```

```python
from pyrogram_optimized import ClientOptimized
from pyrogram_optimized.config import PyrogramOptimizedConfig

# Load configuration from file
config = PyrogramOptimizedConfig.from_file("config.json")
app = ClientOptimized("my_account", api_id=12345, api_hash="hash", config=config)
```

## 📈 Performance Monitoring

### Basic Monitoring

```python
# Get performance statistics
stats = await app.get_performance_stats()
print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
print(f"Average response time: {stats['avg_response_time']:.3f}s")
print(f"Active connections: {stats['active_connections']}")
```

### Advanced Monitoring

```python
# Enable detailed metrics
config = PresetConfigs.development()
config.metrics.enable_performance_logging = True
config.metrics.log_slow_operations = True

app = ClientOptimized("my_account", config=config)

# Monitor specific operations
async with app.monitor_operation("bulk_send"):
    await app.send_bulk_messages(messages)
```

## 🔧 Troubleshooting Migration Issues

### Common Issues and Solutions

#### 1. Import Errors

**Problem:**

```python
ImportError: No module named 'pyrogram_optimized'
```

**Solution:**

```bash
# Install the optimized version
pip install -r requirements.txt

# Or install with performance extras
pip install pyrogram-optimized[fast]
```

#### 2. Configuration Conflicts

**Problem:**

```
ConfigurationError: Invalid connection pool settings
```

**Solution:**

```python
# Validate configuration before use
from pyrogram_optimized.config import PyrogramOptimizedConfig

config = PyrogramOptimizedConfig()
# Adjust problematic settings
config.connection_pool.max_connections = min(config.connection_pool.max_connections, 50)
```

#### 3. Memory Usage

**Problem:** High memory usage with large caches

**Solution:**

```python
# Use memory-efficient preset
config = PresetConfigs.memory_efficient()

# Or customize cache settings
config.cache.max_size = 1000
config.cache.cleanup_interval = 60.0
```

#### 4. Connection Issues

**Problem:** Connection timeouts or failures

**Solution:**

```python
# Adjust connection settings
config.connection_pool.connection_timeout = 60.0
config.connection_pool.max_retries = 5
config.connection_pool.retry_delay = 2.0
```

## 📋 Migration Checklist

### Pre-Migration

- [ ] Backup your existing code
- [ ] Review current Pyrogram usage patterns
- [ ] Identify performance bottlenecks
- [ ] Choose appropriate optimization level

### During Migration

- [ ] Replace imports with optimized versions
- [ ] Select and configure optimization preset
- [ ] Update client initialization
- [ ] Test basic functionality
- [ ] Verify performance improvements

### Post-Migration

- [ ] Monitor performance metrics
- [ ] Fine-tune configuration if needed
- [ ] Update documentation
- [ ] Train team on new features
- [ ] Set up monitoring and alerting

## 🎯 Best Practices

### 1. Start Conservative

Begin with basic optimizations and gradually increase:

```python
# Start with default config
app = ClientOptimized("my_account", api_id=12345, api_hash="hash")

# Then move to presets
config = PresetConfigs.high_performance()
app = ClientOptimized("my_account", api_id=12345, api_hash="hash", config=config)

# Finally, customize as needed
```

### 2. Monitor Performance

Always monitor the impact of optimizations:

```python
# Enable metrics in development
config = PresetConfigs.development()
config.metrics.enable_performance_logging = True
```

### 3. Test Thoroughly

Test your application with the optimized version:

```python
# Run the included test suite
python -m pyrogram_optimized.test_optimized

# Run benchmarks
python -m pyrogram_optimized.benchmark
```

### 4. Use Configuration Files

Maintain configurations in files for different environments:

```
config/
├── development.json
├── staging.json
└── production.json
```

## 🆘 Getting Help

If you encounter issues during migration:

1. **Check the documentation**: Review the README.md for detailed information
2. **Run diagnostics**: Use the CLI tool to check your setup
   ```bash
   pyrogram-optimized info
   pyrogram-optimized config validate --config your_config.json
   ```
3. **Enable debug logging**: Set detailed logging to identify issues
4. **Compare benchmarks**: Run before/after performance tests
5. **Community support**: Reach out to the community for help

## 📚 Additional Resources

- [Configuration Reference](config.py)
- [Performance Benchmarks](benchmark.py)
- [Example Applications](example_bot.py)
- [API Documentation](README.md)
- [Test Suite](test_optimized.py)

---

**Happy migrating! 🚀**

The Pyrogram Optimized team is here to help you achieve better performance with minimal effort.
