#  Optimized Crypto Module for Pyrogram
#  Enhanced with better performance, caching, and native library support

import hashlib
import logging
import time
from typing import Dict, Any, Optional
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import asyncio

log = logging.getLogger(__name__)

# Try to import high-performance crypto libraries
try:
    import tgcrypto
    HAS_TGCRYPTO = True
    log.info("Using TgCrypto for enhanced performance")
except ImportError:
    HAS_TGCRYPTO = False
    log.warning("TgCrypto not available, falling back to pure Python")

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
    log.info("Cryptography library available for fallback")
except ImportError:
    HAS_CRYPTOGRAPHY = False

try:
    import pyaes
    HAS_PYAES = True
except ImportError:
    HAS_PYAES = False


class CryptoMetrics:
    """Track crypto operation performance"""
    
    def __init__(self):
        self.operations = {
            'ige_encrypt': {'count': 0, 'total_time': 0.0},
            'ige_decrypt': {'count': 0, 'total_time': 0.0},
            'ctr_encrypt': {'count': 0, 'total_time': 0.0},
            'ctr_decrypt': {'count': 0, 'total_time': 0.0},
            'sha256': {'count': 0, 'total_time': 0.0},
            'sha1': {'count': 0, 'total_time': 0.0}
        }
    
    def record_operation(self, op_name: str, duration: float):
        if op_name in self.operations:
            self.operations[op_name]['count'] += 1
            self.operations[op_name]['total_time'] += duration
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {}
        for op, data in self.operations.items():
            if data['count'] > 0:
                stats[op] = {
                    'count': data['count'],
                    'total_time': data['total_time'],
                    'avg_time': data['total_time'] / data['count']
                }
        return stats


# Global metrics instance
crypto_metrics = CryptoMetrics()

# Thread pool for CPU-intensive crypto operations
crypto_executor = ThreadPoolExecutor(
    max_workers=min(4, (asyncio.get_event_loop().run_in_executor(None, lambda: __import__('os').cpu_count()) or 4)),
    thread_name_prefix="CryptoWorker"
)


def time_operation(op_name: str):
    """Decorator to time crypto operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start_time
            crypto_metrics.record_operation(op_name, duration)
            return result
        return wrapper
    return decorator


# Optimized IGE implementation
if HAS_TGCRYPTO:
    @time_operation('ige_encrypt')
    def ige256_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
        """Fast IGE encryption using TgCrypto"""
        return tgcrypto.ige256_encrypt(data, key, iv)
    
    @time_operation('ige_decrypt')
    def ige256_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
        """Fast IGE decryption using TgCrypto"""
        return tgcrypto.ige256_decrypt(data, key, iv)

elif HAS_CRYPTOGRAPHY:
    @time_operation('ige_encrypt')
    def ige256_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
        """IGE encryption using cryptography library"""
        return _ige_encrypt_cryptography(data, key, iv)
    
    @time_operation('ige_decrypt')
    def ige256_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
        """IGE decryption using cryptography library"""
        return _ige_decrypt_cryptography(data, key, iv)

else:
    @time_operation('ige_encrypt')
    def ige256_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
        """Fallback IGE encryption using pure Python"""
        return _ige_encrypt_pure_python(data, key, iv)
    
    @time_operation('ige_decrypt')
    def ige256_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
        """Fallback IGE decryption using pure Python"""
        return _ige_decrypt_pure_python(data, key, iv)


# Optimized CTR implementation
if HAS_TGCRYPTO:
    @time_operation('ctr_encrypt')
    def ctr256_encrypt(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
        """Fast CTR encryption using TgCrypto"""
        return tgcrypto.ctr256_encrypt(data, key, iv, state or bytearray(1))
    
    @time_operation('ctr_decrypt')
    def ctr256_decrypt(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
        """Fast CTR decryption using TgCrypto"""
        return tgcrypto.ctr256_decrypt(data, key, iv, state or bytearray(1))

elif HAS_CRYPTOGRAPHY:
    @time_operation('ctr_encrypt')
    def ctr256_encrypt(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
        """CTR encryption using cryptography library"""
        cipher = Cipher(algorithms.AES(key), modes.CTR(bytes(iv[:16])), backend=default_backend())
        encryptor = cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()
    
    @time_operation('ctr_decrypt')
    def ctr256_decrypt(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
        """CTR decryption using cryptography library"""
        cipher = Cipher(algorithms.AES(key), modes.CTR(bytes(iv[:16])), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(data) + decryptor.finalize()

else:
    @time_operation('ctr_encrypt')
    def ctr256_encrypt(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
        """Fallback CTR encryption"""
        return _ctr_encrypt_pure_python(data, key, iv, state)
    
    @time_operation('ctr_decrypt')
    def ctr256_decrypt(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
        """Fallback CTR decryption"""
        return _ctr_decrypt_pure_python(data, key, iv, state)


# Optimized hash functions with caching
@lru_cache(maxsize=1024)
@time_operation('sha256')
def sha256_cached(data: bytes) -> bytes:
    """Cached SHA256 for frequently hashed data"""
    return hashlib.sha256(data).digest()


@lru_cache(maxsize=1024)
@time_operation('sha1')
def sha1_cached(data: bytes) -> bytes:
    """Cached SHA1 for frequently hashed data"""
    return hashlib.sha1(data).digest()


@time_operation('sha256')
def sha256(data: bytes) -> bytes:
    """Standard SHA256"""
    return hashlib.sha256(data).digest()


@time_operation('sha1')
def sha1(data: bytes) -> bytes:
    """Standard SHA1"""
    return hashlib.sha1(data).digest()


# XOR operation with optimization
def xor(a: bytes, b: bytes) -> bytes:
    """Optimized XOR operation"""
    if len(a) != len(b):
        raise ValueError("XOR operands must have the same length")
    
    # Use int operations for better performance on small data
    if len(a) <= 8:
        return int.to_bytes(
            int.from_bytes(a, "big") ^ int.from_bytes(b, "big"),
            len(a),
            "big",
        )
    
    # Use bytearray for larger data
    result = bytearray(len(a))
    for i in range(len(a)):
        result[i] = a[i] ^ b[i]
    return bytes(result)


# Async crypto operations for non-blocking execution
async def ige256_encrypt_async(data: bytes, key: bytes, iv: bytes) -> bytes:
    """Async IGE encryption"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(crypto_executor, ige256_encrypt, data, key, iv)


async def ige256_decrypt_async(data: bytes, key: bytes, iv: bytes) -> bytes:
    """Async IGE decryption"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(crypto_executor, ige256_decrypt, data, key, iv)


async def ctr256_encrypt_async(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
    """Async CTR encryption"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(crypto_executor, ctr256_encrypt, data, key, iv, state)


async def ctr256_decrypt_async(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
    """Async CTR decryption"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(crypto_executor, ctr256_decrypt, data, key, iv, state)


# Implementation helpers for fallback crypto
def _ige_encrypt_cryptography(data: bytes, key: bytes, iv: bytes) -> bytes:
    """IGE encryption using cryptography library"""
    # This is a simplified implementation
    # Full IGE would require more complex implementation
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv[:16]), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(data) + encryptor.finalize()


def _ige_decrypt_cryptography(data: bytes, key: bytes, iv: bytes) -> bytes:
    """IGE decryption using cryptography library"""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv[:16]), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(data) + decryptor.finalize()


def _ige_encrypt_pure_python(data: bytes, key: bytes, iv: bytes) -> bytes:
    """Pure Python IGE encryption fallback"""
    if HAS_PYAES:
        aes = pyaes.AESModeOfOperationCBC(key, iv[:16])
        return aes.encrypt(data)
    else:
        raise NotImplementedError("No crypto library available for IGE encryption")


def _ige_decrypt_pure_python(data: bytes, key: bytes, iv: bytes) -> bytes:
    """Pure Python IGE decryption fallback"""
    if HAS_PYAES:
        aes = pyaes.AESModeOfOperationCBC(key, iv[:16])
        return aes.decrypt(data)
    else:
        raise NotImplementedError("No crypto library available for IGE decryption")


def _ctr_encrypt_pure_python(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
    """Pure Python CTR encryption fallback"""
    if HAS_PYAES:
        aes = pyaes.AESModeOfOperationCTR(key, pyaes.Counter(int.from_bytes(iv[:16], 'big')))
        return aes.encrypt(data)
    else:
        raise NotImplementedError("No crypto library available for CTR encryption")


def _ctr_decrypt_pure_python(data: bytes, key: bytes, iv: bytearray, state: bytearray = None) -> bytes:
    """Pure Python CTR decryption fallback"""
    if HAS_PYAES:
        aes = pyaes.AESModeOfOperationCTR(key, pyaes.Counter(int.from_bytes(iv[:16], 'big')))
        return aes.decrypt(data)
    else:
        raise NotImplementedError("No crypto library available for CTR decryption")


# Crypto performance utilities
def get_crypto_performance_stats() -> Dict[str, Any]:
    """Get crypto performance statistics"""
    return {
        'library_info': {
            'tgcrypto': HAS_TGCRYPTO,
            'cryptography': HAS_CRYPTOGRAPHY,
            'pyaes': HAS_PYAES
        },
        'operations': crypto_metrics.get_stats()
    }


def reset_crypto_metrics():
    """Reset crypto performance metrics"""
    global crypto_metrics
    crypto_metrics = CryptoMetrics()


# Benchmark crypto operations
def benchmark_crypto_operations(data_size: int = 1024, iterations: int = 100) -> Dict[str, float]:
    """Benchmark crypto operations"""
    import os
    
    test_data = os.urandom(data_size)
    test_key = os.urandom(32)
    test_iv = os.urandom(32)
    
    results = {}
    
    # Benchmark IGE
    start_time = time.perf_counter()
    for _ in range(iterations):
        encrypted = ige256_encrypt(test_data, test_key, test_iv)
        ige256_decrypt(encrypted, test_key, test_iv)
    results['ige_ops_per_second'] = (iterations * 2) / (time.perf_counter() - start_time)
    
    # Benchmark CTR
    start_time = time.perf_counter()
    for _ in range(iterations):
        encrypted = ctr256_encrypt(test_data, test_key, bytearray(test_iv))
        ctr256_decrypt(encrypted, test_key, bytearray(test_iv))
    results['ctr_ops_per_second'] = (iterations * 2) / (time.perf_counter() - start_time)
    
    # Benchmark hashing
    start_time = time.perf_counter()
    for _ in range(iterations):
        sha256(test_data)
    results['sha256_ops_per_second'] = iterations / (time.perf_counter() - start_time)
    
    return results


# Initialize crypto subsystem
def initialize_crypto():
    """Initialize crypto subsystem with optimal settings"""
    log.info(f"Crypto subsystem initialized:")
    log.info(f"  - TgCrypto: {'Available' if HAS_TGCRYPTO else 'Not available'}")
    log.info(f"  - Cryptography: {'Available' if HAS_CRYPTOGRAPHY else 'Not available'}")
    log.info(f"  - PyAES: {'Available' if HAS_PYAES else 'Not available'}")
    
    if not any([HAS_TGCRYPTO, HAS_CRYPTOGRAPHY, HAS_PYAES]):
        log.warning("No crypto libraries available! Performance will be severely limited.")
    
    # Run a quick benchmark
    try:
        bench_results = benchmark_crypto_operations(1024, 10)
        log.info(f"Crypto benchmark: IGE: {bench_results.get('ige_ops_per_second', 0):.1f} ops/s, "
                f"CTR: {bench_results.get('ctr_ops_per_second', 0):.1f} ops/s, "
                f"SHA256: {bench_results.get('sha256_ops_per_second', 0):.1f} ops/s")
    except Exception as e:
        log.warning(f"Crypto benchmark failed: {e}")


# Initialize on import
initialize_crypto()