"""Tests for cache manager."""

import pytest
import time
from shared.cache_manager import CacheManager, CacheEntry, QueryCache, PerformanceMonitor, cached


class TestCacheEntry:
    """Test cache entry functionality."""

    def test_cache_entry_not_expired(self):
        """Cache entry should not be expired immediately."""
        entry = CacheEntry("test_value", 300)
        assert not entry.is_expired()

    def test_cache_entry_expired(self):
        """Cache entry should expire after TTL."""
        entry = CacheEntry("test_value", 1)
        time.sleep(1.1)
        assert entry.is_expired()

    def test_cache_entry_remaining_ttl(self):
        """Get remaining TTL."""
        entry = CacheEntry("test_value", 100)
        remaining = entry.get_remaining_ttl()
        assert 90 < remaining <= 100


class TestCacheManager:
    """Test cache manager functionality."""

    @pytest.fixture
    def cache(self):
        """Create a fresh cache manager for each test."""
        return CacheManager()

    def test_set_and_get(self, cache):
        """Set and retrieve cache value."""
        cache.set("key1", "value1", 300)
        assert cache.get("key1") == "value1"

    def test_get_nonexistent(self, cache):
        """Get nonexistent key returns None."""
        assert cache.get("nonexistent") is None

    def test_delete(self, cache):
        """Delete cache entry."""
        cache.set("key1", "value1", 300)
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_delete_nonexistent(self, cache):
        """Delete nonexistent key returns False."""
        assert cache.delete("nonexistent") is False

    def test_expiration(self, cache):
        """Cache entry expires after TTL."""
        cache.set("key1", "value1", 1)
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_clear(self, cache):
        """Clear all cache entries."""
        cache.set("key1", "value1", 300)
        cache.set("key2", "value2", 300)
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_statistics(self, cache):
        """Track cache statistics."""
        cache.set("key1", "value1", 300)
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        cache.get("key1")  # hit

        stats = cache.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['sets'] == 1

    def test_generate_key(self, cache):
        """Generate consistent cache keys."""
        key1 = cache.generate_key("prefix", a=1, b=2)
        key2 = cache.generate_key("prefix", a=1, b=2)
        key3 = cache.generate_key("prefix", a=1, b=3)

        assert key1 == key2
        assert key1 != key3

    def test_generate_key_with_none(self, cache):
        """Generate key ignoring None values."""
        key1 = cache.generate_key("prefix", a=1, b=None)
        key2 = cache.generate_key("prefix", a=1)

        assert key1 == key2


class TestCachedDecorator:
    """Test cached function decorator."""

    def test_cached_decorator(self):
        """Decorator caches function results."""
        from shared.cache_manager import get_cache_manager

        cache = get_cache_manager()
        cache.clear()  # Clear cache before test

        call_count = 0

        @cached(ttl_seconds=300, prefix="test_func1")
        def expensive_function(x=None):
            nonlocal call_count
            call_count += 1
            return x * 2 if x else 0

        # First call with keyword arg
        result1 = expensive_function(x=5)
        assert result1 == 10
        assert call_count == 1

        # Second call (should be cached)
        result2 = expensive_function(x=5)
        assert result2 == 10
        assert call_count == 1  # Not incremented

        # Different argument (should not use cache)
        result3 = expensive_function(x=6)
        assert result3 == 12
        assert call_count == 2

    def test_cached_decorator_expiration(self):
        """Cached decorator respects TTL."""
        from shared.cache_manager import get_cache_manager

        cache = get_cache_manager()
        cache.clear()  # Clear cache before test

        call_count = 0

        @cached(ttl_seconds=1, prefix="test_func2")
        def timed_function():
            nonlocal call_count
            call_count += 1
            return "result"

        # First call
        result1 = timed_function()
        assert result1 == "result"
        assert call_count == 1

        # Second call (cached)
        result2 = timed_function()
        assert result2 == "result"
        assert call_count == 1

        # Wait for expiration
        time.sleep(1.1)

        # Third call (cache expired)
        result3 = timed_function()
        assert result3 == "result"
        assert call_count == 2


class TestQueryCache:
    """Test query cache utilities."""

    def test_knowledge_base_key_generation(self):
        """Generate knowledge base cache keys."""
        key1 = QueryCache.get_knowledge_base_key()
        key2 = QueryCache.get_knowledge_base_key("troubleshooting")

        assert key1 != key2
        assert isinstance(key1, str)
        assert isinstance(key2, str)

    def test_copilot_history_key(self):
        """Generate copilot history cache keys."""
        key1 = QueryCache.get_copilot_history_key("engineer-1")
        key2 = QueryCache.get_copilot_history_key("engineer-2")

        assert key1 != key2

    def test_invalidate_knowledge_base(self):
        """Invalidate knowledge base cache."""
        from shared.cache_manager import get_cache_manager

        cache = get_cache_manager()
        cache.set("knowledge_base:1", "value1", 300)
        cache.set("knowledge_base:2", "value2", 300)
        cache.set("other:key", "value3", 300)

        QueryCache.invalidate_knowledge_base()

        assert cache.get("knowledge_base:1") is None
        assert cache.get("knowledge_base:2") is None
        assert cache.get("other:key") == "value3"


class TestPerformanceMonitor:
    """Test performance monitoring."""

    @pytest.fixture
    def monitor(self):
        """Create a fresh monitor for each test."""
        return PerformanceMonitor()

    def test_record_metric(self, monitor):
        """Record performance metrics."""
        monitor.record_metric("db_query", 45.2)
        monitor.record_metric("db_query", 52.3)
        monitor.record_metric("api_call", 120.5)

        summary = monitor.get_metrics_summary()

        assert summary["db_query"]["count"] == 2
        assert summary["db_query"]["avg"] == pytest.approx(48.75)
        assert summary["api_call"]["count"] == 1

    def test_record_request_time(self, monitor):
        """Record request times."""
        monitor.record_request_time(100.5)
        monitor.record_request_time(150.3)
        monitor.record_request_time(120.1)

        summary = monitor.get_metrics_summary()

        assert summary["request_times"]["count"] == 3
        assert summary["request_times"]["avg_ms"] == pytest.approx(123.63)
        assert summary["request_times"]["min_ms"] == pytest.approx(100.5)
        assert summary["request_times"]["max_ms"] == pytest.approx(150.3)

    def test_clear_metrics(self, monitor):
        """Clear all metrics."""
        monitor.record_metric("test", 50)
        monitor.record_request_time(100)

        monitor.clear()
        summary = monitor.get_metrics_summary()

        assert summary == {}
