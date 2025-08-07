"""
Unit tests for Flask extensions module
Tests caching, Redis client, and extension initialization
"""
import pytest
import time
from unittest.mock import patch, MagicMock
import redis

from app.extensions import (
    CacheManager,
    cache_manager,
    get_redis_client,
    init_extensions,
    _redis_client
)


class TestCacheManager:
    """Test cache manager functionality"""
    
    def test_cache_manager_initialization(self):
        """Test cache manager initialization"""
        cache = CacheManager()
        assert cache._cache == {}
        assert cache._timestamps == {}
        assert cache.default_timeout == 300
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations"""
        cache = CacheManager()
        
        # Test setting and getting a value
        result = cache.set("test_key", "test_value")
        assert result is True
        
        retrieved = cache.get("test_key")
        assert retrieved == "test_value"
    
    def test_cache_get_nonexistent_key(self):
        """Test getting a non-existent key"""
        cache = CacheManager()
        result = cache.get("nonexistent")
        assert result is None
    
    def test_cache_expiration(self):
        """Test cache expiration functionality"""
        cache = CacheManager()
        cache.default_timeout = 0.1  # 100ms for testing
        
        # Set a value
        cache.set("expiring_key", "expiring_value")
        
        # Should be available immediately
        assert cache.get("expiring_key") == "expiring_value"
        
        # Wait for expiration
        time.sleep(0.15)
        
        # Should be expired and return None
        result = cache.get("expiring_key")
        assert result is None
        
        # Key should also be removed from cache
        assert "expiring_key" not in cache._cache
    
    def test_cache_delete(self):
        """Test cache deletion"""
        cache = CacheManager()
        
        # Set a value
        cache.set("delete_me", "value_to_delete")
        assert cache.get("delete_me") == "value_to_delete"
        
        # Delete the key
        result = cache.delete("delete_me")
        assert result is True
        
        # Should no longer exist
        assert cache.get("delete_me") is None
        assert "delete_me" not in cache._cache
        assert "delete_me" not in cache._timestamps
    
    def test_cache_delete_nonexistent(self):
        """Test deleting a non-existent key"""
        cache = CacheManager()
        result = cache.delete("nonexistent_key")
        assert result is True  # Should not raise error
    
    def test_cache_clear(self):
        """Test clearing all cache"""
        cache = CacheManager()
        
        # Set multiple values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Verify they exist
        assert len(cache._cache) == 3
        assert len(cache._timestamps) == 3
        
        # Clear cache
        result = cache.clear()
        assert result is True
        
        # Verify cache is empty
        assert len(cache._cache) == 0
        assert len(cache._timestamps) == 0
        assert cache.get("key1") is None
    
    def test_cache_set_with_custom_timeout(self):
        """Test cache set with custom timeout parameter"""
        cache = CacheManager()
        
        # Set with custom timeout (though current implementation doesn't use it)
        result = cache.set("custom_key", "custom_value", timeout=60)
        assert result is True
        
        # Should still be available
        assert cache.get("custom_key") == "custom_value"


class TestGlobalCacheManager:
    """Test the global cache manager instance"""
    
    def test_global_cache_manager_exists(self):
        """Test that global cache manager is initialized"""
        assert cache_manager is not None
        assert isinstance(cache_manager, CacheManager)
    
    def test_global_cache_manager_functionality(self):
        """Test global cache manager basic functionality"""
        # Clear any existing data
        cache_manager.clear()
        
        # Test basic operations
        cache_manager.set("global_test", "global_value")
        assert cache_manager.get("global_test") == "global_value"
        
        # Clean up
        cache_manager.clear()


class TestRedisClient:
    """Test Redis client functionality"""
    
    def setUp(self):
        """Reset global redis client before each test"""
        global _redis_client
        _redis_client = None
    
    @patch('app.extensions._redis_client', None)
    @patch('redis.Redis')
    def test_get_redis_client_successful_connection(self, mock_redis_class):
        """Test successful Redis client connection"""
        # Mock Redis client
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        # Test getting Redis client
        with patch('app.extensions.logger') as mock_logger:
            client = get_redis_client()
            
            assert client is not None
            assert client == mock_redis_instance
            mock_redis_instance.ping.assert_called_once()
            mock_logger.info.assert_called_with("Redis client initialized successfully")
    
    @patch('app.extensions._redis_client', None)
    @patch('redis.Redis')
    def test_get_redis_client_connection_failure(self, mock_redis_class):
        """Test Redis client connection failure"""
        # Mock Redis client to raise exception on ping
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.side_effect = redis.ConnectionError("Connection failed")
        mock_redis_class.return_value = mock_redis_instance
        
        # Test getting Redis client
        with patch('app.extensions.logger') as mock_logger:
            client = get_redis_client()
            
            assert client is None
            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args[0][0]
            assert "Redis connection failed" in call_args
    
    @patch('app.extensions._redis_client', None)
    @patch('redis.Redis')
    def test_get_redis_client_creation_failure(self, mock_redis_class):
        """Test Redis client creation failure"""
        # Mock Redis class to raise exception on creation
        mock_redis_class.side_effect = Exception("Redis creation failed")
        
        # Test getting Redis client
        with patch('app.extensions.logger') as mock_logger:
            client = get_redis_client()
            
            assert client is None
            mock_logger.warning.assert_called()


class TestExtensionInitialization:
    """Test Flask extension initialization"""
    
    def test_init_extensions(self):
        """Test extension initialization"""
        # Mock Flask app
        mock_app = MagicMock()
        
        # Mock get_redis_client to avoid actual Redis connection
        with patch('app.extensions.get_redis_client') as mock_get_redis, \
             patch('app.extensions.logger') as mock_logger:
            
            init_extensions(mock_app)
            
            mock_get_redis.assert_called_once()
            mock_logger.info.assert_called_with("Extensions initialized")
    
    @patch('app.extensions.get_redis_client')
    def test_init_extensions_with_redis_success(self, mock_get_redis):
        """Test extension initialization with successful Redis connection"""
        mock_app = MagicMock()
        mock_redis_client = MagicMock()
        mock_get_redis.return_value = mock_redis_client
        
        with patch('app.extensions.logger') as mock_logger:
            init_extensions(mock_app)
            
            mock_get_redis.assert_called_once()
            mock_logger.info.assert_called_with("Extensions initialized")
    
    @patch('app.extensions.get_redis_client')
    def test_init_extensions_with_redis_failure(self, mock_get_redis):
        """Test extension initialization with Redis connection failure"""
        mock_app = MagicMock()
        mock_get_redis.return_value = None  # Redis connection failed
        
        with patch('app.extensions.logger') as mock_logger:
            init_extensions(mock_app)
            
            mock_get_redis.assert_called_once()
            mock_logger.info.assert_called_with("Extensions initialized")


class TestCacheManagerEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_cache_with_none_values(self):
        """Test cache operations with None values"""
        cache = CacheManager()
        
        # Test storing None value
        result = cache.set("none_key", None)
        assert result is True
        
        # Should be able to retrieve None
        retrieved = cache.get("none_key")
        assert retrieved is None  # Note: This is ambiguous with non-existent key
    
    def test_cache_with_complex_objects(self):
        """Test cache with complex objects"""
        cache = CacheManager()
        
        test_data = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2, 3)
        }
        
        cache.set("complex_data", test_data)
        retrieved = cache.get("complex_data")
        
        assert retrieved == test_data
        assert isinstance(retrieved["list"], list)
        assert isinstance(retrieved["dict"], dict)
        assert isinstance(retrieved["tuple"], tuple)
    
    def test_cache_key_overwrite(self):
        """Test overwriting existing cache keys"""
        cache = CacheManager()
        
        # Set initial value
        cache.set("overwrite_key", "original_value")
        assert cache.get("overwrite_key") == "original_value"
        
        # Overwrite with new value
        cache.set("overwrite_key", "new_value")
        assert cache.get("overwrite_key") == "new_value"
        
        # Should only have one timestamp entry
        assert len([k for k in cache._timestamps.keys() if k == "overwrite_key"]) == 1