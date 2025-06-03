#!/usr/bin/env python3
"""
Command Line Interface for Pyrogram Optimized
Provides tools for configuration, benchmarking, and monitoring
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

try:
    from .config import PyrogramOptimizedConfig, PresetConfigs, use_preset
    from .benchmark import PerformanceBenchmark
except ImportError:
    from config import PyrogramOptimizedConfig, PresetConfigs, use_preset
    from benchmark import PerformanceBenchmark

def create_config_command(args):
    """Create a new configuration file"""
    if args.preset:
        if args.preset == 'high_performance':
            config = PresetConfigs.high_performance()
        elif args.preset == 'memory_efficient':
            config = PresetConfigs.memory_efficient()
        elif args.preset == 'development':
            config = PresetConfigs.development()
        else:
            print(f"❌ Unknown preset: {args.preset}")
            print("Available presets: high_performance, memory_efficient, development")
            return 1
    else:
        config = PyrogramOptimizedConfig()
    
    output_path = Path(args.output)
    try:
        config.save_to_file(output_path)
        print(f"✅ Configuration saved to: {output_path}")
        
        if args.preset:
            print(f"📋 Used preset: {args.preset}")
        
        print("\n📝 Configuration summary:")
        print(f"   Max connections: {config.connection_pool.max_connections}")
        print(f"   Cache size: {config.cache.max_size}")
        print(f"   Crypto threads: {config.crypto.thread_pool_size}")
        print(f"   Batch size: {config.session.batch_size}")
        
        return 0
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return 1

def validate_config_command(args):
    """Validate a configuration file"""
    config_path = Path(args.config)
    
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return 1
    
    try:
        config = PyrogramOptimizedConfig.from_file(config_path)
        print(f"✅ Configuration is valid: {config_path}")
        
        print("\n📊 Configuration details:")
        print(f"   Connection Pool:")
        print(f"     Max connections: {config.connection_pool.max_connections}")
        print(f"     Connection timeout: {config.connection_pool.connection_timeout}s")
        print(f"     Max idle time: {config.connection_pool.max_idle_time}s")
        
        print(f"   Cache:")
        print(f"     Max size: {config.cache.max_size}")
        print(f"     Default TTL: {config.cache.default_ttl}s")
        print(f"     Cleanup interval: {config.cache.cleanup_interval}s")
        
        print(f"   Crypto:")
        print(f"     Thread pool size: {config.crypto.thread_pool_size}")
        print(f"     Prefer native: {config.crypto.prefer_native}")
        print(f"     Cache hash results: {config.crypto.cache_hash_results}")
        
        print(f"   Session:")
        print(f"     Batch size: {config.session.batch_size}")
        print(f"     Batch timeout: {config.session.batch_timeout}s")
        print(f"     Enable batching: {config.session.enable_request_batching}")
        
        print(f"   Optimizations:")
        print(f"     UV Loop: {config.optimization.enable_uvloop}")
        print(f"     OrJSON: {config.optimization.enable_orjson}")
        print(f"     Compression: {config.optimization.enable_compression}")
        print(f"     Connection pooling: {config.optimization.enable_connection_pooling}")
        print(f"     Request batching: {config.optimization.enable_request_batching}")
        print(f"     Caching: {config.optimization.enable_caching}")
        
        return 0
    except Exception as e:
        print(f"❌ Invalid configuration: {e}")
        return 1

async def benchmark_command(args):
    """Run performance benchmarks"""
    print("🚀 Starting Pyrogram Optimized Benchmark")
    
    benchmark = PerformanceBenchmark()
    
    if args.crypto_only:
        print("\n🔐 Running crypto benchmarks only...")
        results = await benchmark.benchmark_crypto_operations(args.iterations)
        benchmark.print_results(results)
    elif args.quick:
        print("\n⚡ Running quick benchmark...")
        results = {}
        
        # Quick crypto test
        crypto_results = await benchmark.benchmark_crypto_operations(100)
        results.update(crypto_results)
        
        # Quick connection pool test
        pool_result = await benchmark.benchmark_connection_pool(5, 50)
        results['connection_pool'] = pool_result
        
        benchmark.print_results(results)
    else:
        # Full benchmark
        await benchmark.run_full_benchmark()
    
    return 0

def info_command(args):
    """Show information about Pyrogram Optimized"""
    print("📋 Pyrogram Optimized Information")
    print("=" * 40)
    
    try:
        from . import __version__
    except ImportError:
        from __init__ import __version__
    
    print(f"Version: {__version__}")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Check optional dependencies
    print("\n📦 Optional Dependencies:")
    
    optional_deps = [
        ('tgcrypto', 'Fast crypto operations'),
        ('cryptography', 'Alternative crypto backend'),
        ('uvloop', 'Fast event loop (Unix only)'),
        ('orjson', 'Fast JSON serialization'),
        ('aiofiles', 'Async file operations'),
        ('msgpack', 'Fast serialization'),
        ('lz4', 'Fast compression'),
        ('xxhash', 'Fast hashing'),
        ('psutil', 'System monitoring')
    ]
    
    for dep, description in optional_deps:
        try:
            __import__(dep)
            status = "✅ Installed"
        except ImportError:
            status = "❌ Not installed"
        
        print(f"   {dep:15} - {description:30} {status}")
    
    print("\n🔧 Configuration Presets:")
    print("   high_performance  - Maximum performance for production")
    print("   memory_efficient  - Minimal memory usage")
    print("   development      - Development with extensive logging")
    
    return 0

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Pyrogram Optimized CLI Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a high-performance configuration
  pyrogram-optimized config create --preset high_performance --output config.json
  
  # Validate a configuration file
  pyrogram-optimized config validate --config config.json
  
  # Run a quick benchmark
  pyrogram-optimized benchmark --quick
  
  # Run crypto benchmarks only
  pyrogram-optimized benchmark --crypto-only --iterations 1000
  
  # Show system information
  pyrogram-optimized info
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='config_action')
    
    # Config create
    create_parser = config_subparsers.add_parser('create', help='Create configuration file')
    create_parser.add_argument('--output', '-o', default='pyrogram_config.json',
                              help='Output configuration file path')
    create_parser.add_argument('--preset', '-p', 
                              choices=['high_performance', 'memory_efficient', 'development'],
                              help='Use a predefined configuration preset')
    
    # Config validate
    validate_parser = config_subparsers.add_parser('validate', help='Validate configuration file')
    validate_parser.add_argument('--config', '-c', required=True,
                                help='Configuration file to validate')
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Run performance benchmarks')
    benchmark_parser.add_argument('--iterations', '-i', type=int, default=1000,
                                 help='Number of iterations for benchmarks')
    benchmark_parser.add_argument('--crypto-only', action='store_true',
                                 help='Run only crypto benchmarks')
    benchmark_parser.add_argument('--quick', action='store_true',
                                 help='Run quick benchmark with fewer iterations')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show system and library information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Set event loop policy for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        if args.command == 'config':
            if args.config_action == 'create':
                return create_config_command(args)
            elif args.config_action == 'validate':
                return validate_config_command(args)
            else:
                config_parser.print_help()
                return 1
        
        elif args.command == 'benchmark':
            return asyncio.run(benchmark_command(args))
        
        elif args.command == 'info':
            return info_command(args)
        
        else:
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())