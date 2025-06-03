#!/usr/bin/env python3
"""
Example Bot using Pyrogram Optimized
Demonstrates the performance improvements and features
"""

import asyncio
import logging
import time
from typing import Dict, Any

# Import optimized Pyrogram
try:
    from pyrogram_optimized import Client, ConnectionPoolConfig
    from pyrogram_optimized.crypto_optimized import get_crypto_performance_stats
except ImportError:
    print("Please ensure pyrogram_optimized is in your Python path")
    exit(1)

from pyrogram import filters
from pyrogram.types import Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

# Bot configuration
API_ID = "YOUR_API_ID"  # Replace with your API ID
API_HASH = "YOUR_API_HASH"  # Replace with your API hash
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token

# Optimization configuration
pool_config = ConnectionPoolConfig(
    max_connections=15,
    min_connections=3,
    connection_timeout=30.0,
    idle_timeout=300.0,
    max_retries=5
)

# Create optimized client
app = Client(
    "optimized_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    
    # Optimization settings
    pool_config=pool_config,
    enable_caching=True,
    cache_size=2000,
    cache_ttl=600,  # 10 minutes
)

# Performance tracking
bot_stats = {
    'messages_processed': 0,
    'start_time': time.time(),
    'last_stats_print': time.time()
}


@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle /start command"""
    bot_stats['messages_processed'] += 1
    
    welcome_text = (
        "🚀 **Welcome to Pyrogram Optimized Bot!**\n\n"
        "This bot demonstrates the performance improvements of the optimized Pyrogram client.\n\n"
        "**Available commands:**\n"
        "• `/start` - Show this welcome message\n"
        "• `/stats` - Show performance statistics\n"
        "• `/benchmark` - Run a performance benchmark\n"
        "• `/health` - Show connection health\n"
        "• `/bulk <count>` - Send bulk messages (test batching)\n"
        "• `/cache_test` - Test caching performance\n"
    )
    
    await message.reply(welcome_text, parse_mode="markdown")


@app.on_message(filters.command("stats"))
async def stats_command(client: Client, message: Message):
    """Show performance statistics"""
    bot_stats['messages_processed'] += 1
    
    try:
        # Get client performance stats
        if hasattr(client, 'get_performance_metrics'):
            perf_stats = client.get_performance_metrics()
        else:
            perf_stats = {}
        
        # Calculate bot uptime
        uptime = time.time() - bot_stats['start_time']
        messages_per_second = bot_stats['messages_processed'] / uptime if uptime > 0 else 0
        
        # Get crypto stats
        crypto_stats = get_crypto_performance_stats()
        
        stats_text = (
            "📊 **Performance Statistics**\n\n"
            f"**Bot Stats:**\n"
            f"• Uptime: {uptime:.1f} seconds\n"
            f"• Messages processed: {bot_stats['messages_processed']}\n"
            f"• Messages/second: {messages_per_second:.2f}\n\n"
            f"**Client Stats:**\n"
            f"• Requests sent: {perf_stats.get('requests_sent', 'N/A')}\n"
            f"• Cache hits: {perf_stats.get('cache_hits', 'N/A')}\n"
            f"• Cache misses: {perf_stats.get('cache_misses', 'N/A')}\n"
            f"• Cache hit rate: {client._get_cache_hit_rate():.1f}%\n\n"
            f"**Crypto Libraries:**\n"
            f"• TgCrypto: {'✅' if crypto_stats['library_info']['tgcrypto'] else '❌'}\n"
            f"• Cryptography: {'✅' if crypto_stats['library_info']['cryptography'] else '❌'}\n"
            f"• PyAES: {'✅' if crypto_stats['library_info']['pyaes'] else '❌'}\n"
        )
        
        await message.reply(stats_text, parse_mode="markdown")
        
    except Exception as e:
        await message.reply(f"❌ Error getting stats: {e}")


@app.on_message(filters.command("benchmark"))
async def benchmark_command(client: Client, message: Message):
    """Run a performance benchmark"""
    bot_stats['messages_processed'] += 1
    
    await message.reply("🔄 Running benchmark...")
    
    try:
        from pyrogram_optimized.crypto_optimized import benchmark_crypto_operations
        
        # Run crypto benchmark
        start_time = time.time()
        bench_results = benchmark_crypto_operations(data_size=1024, iterations=50)
        benchmark_time = time.time() - start_time
        
        benchmark_text = (
            "⚡ **Benchmark Results**\n\n"
            f"**Crypto Performance:**\n"
            f"• IGE operations/sec: {bench_results.get('ige_ops_per_second', 0):.1f}\n"
            f"• CTR operations/sec: {bench_results.get('ctr_ops_per_second', 0):.1f}\n"
            f"• SHA256 operations/sec: {bench_results.get('sha256_ops_per_second', 0):.1f}\n"
            f"• Benchmark time: {benchmark_time:.3f}s\n\n"
            "*Higher numbers indicate better performance*"
        )
        
        await message.edit(benchmark_text, parse_mode="markdown")
        
    except Exception as e:
        await message.edit(f"❌ Benchmark failed: {e}")


@app.on_message(filters.command("health"))
async def health_command(client: Client, message: Message):
    """Show connection health"""
    bot_stats['messages_processed'] += 1
    
    try:
        # Get connection health info
        health_info = "🏥 **Connection Health**\n\n"
        
        if hasattr(client, 'connection_pool'):
            pool = client.connection_pool
            health_info += (
                f"**Connection Pool:**\n"
                f"• Active connections: {len(pool.active_connections)}\n"
                f"• Available connections: {len(pool.available_connections)}\n"
                f"• Max connections: {pool.config.max_connections}\n\n"
            )
            
            # Show individual connection health
            for conn_id, conn in pool.active_connections.items():
                if hasattr(conn, 'get_health_score'):
                    health_score = conn.get_health_score()
                    health_emoji = "🟢" if health_score > 0.8 else "🟡" if health_score > 0.5 else "🔴"
                    health_info += f"• Connection {conn.dc_id}: {health_emoji} {health_score:.2f}\n"
        else:
            health_info += "Connection pool not available\n"
        
        await message.reply(health_info, parse_mode="markdown")
        
    except Exception as e:
        await message.reply(f"❌ Error getting health info: {e}")


@app.on_message(filters.command("bulk"))
async def bulk_command(client: Client, message: Message):
    """Test bulk message sending with batching"""
    bot_stats['messages_processed'] += 1
    
    try:
        # Parse count from command
        parts = message.text.split()
        count = int(parts[1]) if len(parts) > 1 else 5
        count = min(count, 20)  # Limit to 20 messages
        
        await message.reply(f"🚀 Sending {count} messages using batching...")
        
        # Send messages using batching
        start_time = time.time()
        tasks = []
        
        for i in range(count):
            if hasattr(client, 'send_message_optimized'):
                task = client.send_message_optimized(
                    message.chat.id,
                    f"📦 Batched message #{i+1}/{count}",
                    batch=True
                )
            else:
                task = client.send_message(
                    message.chat.id,
                    f"📦 Message #{i+1}/{count}"
                )
            tasks.append(task)
        
        # Wait for all messages
        await asyncio.gather(*tasks)
        
        elapsed_time = time.time() - start_time
        messages_per_second = count / elapsed_time
        
        await client.send_message(
            message.chat.id,
            f"✅ Sent {count} messages in {elapsed_time:.2f}s\n"
            f"📈 Rate: {messages_per_second:.1f} messages/second"
        )
        
    except ValueError:
        await message.reply("❌ Please provide a valid number: `/bulk 5`")
    except Exception as e:
        await message.reply(f"❌ Error in bulk test: {e}")


@app.on_message(filters.command("cache_test"))
async def cache_test_command(client: Client, message: Message):
    """Test caching performance"""
    bot_stats['messages_processed'] += 1
    
    await message.reply("🔄 Testing cache performance...")
    
    try:
        # Test cache performance by making repeated requests
        start_time = time.time()
        
        # Make the same request multiple times to test caching
        for i in range(5):
            await client.get_me()  # This should be cached after first call
        
        elapsed_time = time.time() - start_time
        
        cache_hit_rate = client._get_cache_hit_rate() if hasattr(client, '_get_cache_hit_rate') else 0
        
        cache_text = (
            "💾 **Cache Test Results**\n\n"
            f"• 5 get_me() calls completed in: {elapsed_time:.3f}s\n"
            f"• Current cache hit rate: {cache_hit_rate:.1f}%\n"
            f"• Average time per call: {elapsed_time/5:.3f}s\n\n"
            "*Lower times and higher hit rates indicate better caching*"
        )
        
        await message.edit(cache_text, parse_mode="markdown")
        
    except Exception as e:
        await message.edit(f"❌ Cache test failed: {e}")


@app.on_message(filters.text & ~filters.command(["start", "stats", "benchmark", "health", "bulk", "cache_test"]))
async def echo_message(client: Client, message: Message):
    """Echo any text message"""
    bot_stats['messages_processed'] += 1
    
    response = (
        f"📝 **Echo:** {message.text}\n\n"
        f"💬 Message #{bot_stats['messages_processed']}\n"
        f"⏱️ Processing time: {time.time() - message.date.timestamp():.3f}s"
    )
    
    await message.reply(response, parse_mode="markdown")


async def performance_monitor():
    """Background task to monitor and log performance"""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            current_time = time.time()
            if current_time - bot_stats['last_stats_print'] >= 300:  # Print every 5 minutes
                uptime = current_time - bot_stats['start_time']
                messages_per_minute = (bot_stats['messages_processed'] / uptime) * 60
                
                log.info(f"Performance: {bot_stats['messages_processed']} messages processed, "
                        f"{messages_per_minute:.1f} msg/min, uptime: {uptime:.1f}s")
                
                bot_stats['last_stats_print'] = current_time
                
        except Exception as e:
            log.error(f"Performance monitor error: {e}")


def main():
    """Main function to run the bot"""
    # Check configuration
    if API_ID == "YOUR_API_ID" or API_HASH == "YOUR_API_HASH" or BOT_TOKEN == "YOUR_BOT_TOKEN":
        print("❌ Please configure your API credentials in the script")
        print("   - Get API_ID and API_HASH from https://my.telegram.org")
        print("   - Get BOT_TOKEN from @BotFather")
        return
    
    log.info("🚀 Starting Pyrogram Optimized Bot...")
    
    # Start performance monitor
    asyncio.create_task(performance_monitor())
    
    # Run the bot
    try:
        app.run()
    except KeyboardInterrupt:
        log.info("👋 Bot stopped by user")
    except Exception as e:
        log.error(f"❌ Bot error: {e}")
    finally:
        # Print final stats
        uptime = time.time() - bot_stats['start_time']
        log.info(f"📊 Final stats: {bot_stats['messages_processed']} messages in {uptime:.1f}s")


if __name__ == "__main__":
    main()