"""Cache management for optimizing performance."""

import logging
from typing import Optional, Any, Callable
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json

logger = logging.getLogger(__name__)


class CacheEntry:
    """A single cache entry with expiration."""

    def __init__(self, value: Any, ttl_seconds: int):
        """Initialize cache entry."""
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry_time

    def get_remaining_ttl(self) -> int:
        """Get remaining TTL in seconds."""
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        remaining = (expiry_time - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))


class CacheManager:
    """In-memory cache manager with TTL support."""

    def __init__(self):
        """Initialize cache manager."""
        self.cache: dict[str, CacheEntry] = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set a cache entry."""
        try:
            self.cache[key] = CacheEntry(value, ttl_seconds)
            self.stats['sets'] += 1
            logger.debug(f"Cache SET: {key} (TTL: {ttl_seconds}s)")
        except Exception as e:
            logger.error(f"Error setting cache for {key}: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get a cache entry if not expired."""
        try:
            if key not in self.cache:
                self.stats['misses'] += 1
                logger.debug(f"Cache MISS: {key}")
                return None

            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                self.stats['misses'] += 1
                logger.debug(f"Cache EXPIRED: {key}")
                return None

            self.stats['hits'] += 1
            logger.debug(f"Cache HIT: {key}")
            return entry.value

        except Exception as e:
            logger.error(f"Error getting cache for {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        try:
            if key in self.cache:
                del self.cache[key]
                self.stats['deletes'] += 1
                logger.debug(f"Cache DELETE: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting cache for {key}: {e}")
            return False

    def clear(self):
        """Clear all cache entries."""
        try:
            self.cache.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'total_requests': total_requests,
            'hit_rate_percentage': round(hit_rate, 2),
            'cached_items': len(self.cache)
        }

    def generate_key(self, prefix: str, **kwargs) -> str:
        """Generate a cache key from prefix and parameters."""
        key_parts = [prefix]

        # Sort kwargs for consistent key generation
        for k in sorted(kwargs.keys()):
            v = kwargs[k]
            if v is not None:
                key_parts.append(f"{k}={v}")

        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


# Global cache instance
_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    return _cache_manager


def cached(ttl_seconds: int = 300, prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()

            # Generate cache key
            key_prefix = prefix or func.__name__
            cache_key = cache.generate_key(key_prefix, **kwargs)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Returning cached result for {func.__name__}")
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)

            return result

        return wrapper
    return decorator


class QueryCache:
    """Cache for database queries with expiration."""

    @staticmethod
    def get_knowledge_base_key(category: Optional[str] = None) -> str:
        """Generate cache key for knowledge base queries."""
        cache = get_cache_manager()
        return cache.generate_key("knowledge_base", category=category)

    @staticmethod
    def get_copilot_history_key(engineer_id: str) -> str:
        """Generate cache key for copilot history."""
        cache = get_cache_manager()
        return cache.generate_key("copilot_history", engineer_id=engineer_id)

    @staticmethod
    def get_embedding_stats_key(engineer_id: Optional[str] = None) -> str:
        """Generate cache key for embedding statistics."""
        cache = get_cache_manager()
        return cache.generate_key("embedding_stats", engineer_id=engineer_id)

    @staticmethod
    def invalidate_knowledge_base():
        """Invalidate knowledge base cache."""
        cache = get_cache_manager()
        # Clear all knowledge_base keys
        keys_to_delete = [k for k in cache.cache.keys() if 'knowledge_base' in k]
        for key in keys_to_delete:
            cache.delete(key)
        logger.info(f"Invalidated {len(keys_to_delete)} knowledge base cache entries")

    @staticmethod
    def invalidate_copilot_history(engineer_id: str):
        """Invalidate copilot history cache for engineer."""
        cache = get_cache_manager()
        key = QueryCache.get_copilot_history_key(engineer_id)
        cache.delete(key)
        logger.info(f"Invalidated copilot history cache for {engineer_id}")


class PerformanceMonitor:
    """Monitor application performance metrics."""

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: dict[str, list[float]] = {}
        self.request_times: list[float] = []

    def record_metric(self, name: str, value: float):
        """Record a performance metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)

    def record_request_time(self, duration_ms: float):
        """Record request duration."""
        self.request_times.append(duration_ms)

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get summary of performance metrics."""
        summary = {}

        for metric_name, values in self.metrics.items():
            if values:
                summary[metric_name] = {
                    'count': len(values),
                    'avg': round(sum(values) / len(values), 2),
                    'min': round(min(values), 2),
                    'max': round(max(values), 2)
                }

        if self.request_times:
            summary['request_times'] = {
                'count': len(self.request_times),
                'avg_ms': round(sum(self.request_times) / len(self.request_times), 2),
                'min_ms': round(min(self.request_times), 2),
                'max_ms': round(max(self.request_times), 2)
            }

        return summary

    def clear(self):
        """Clear all metrics."""
        self.metrics.clear()
        self.request_times.clear()


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _performance_monitor
