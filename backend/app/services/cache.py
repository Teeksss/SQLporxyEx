"""
Complete Cache Service - Final Version  
Created: 2025-05-29 14:22:58 UTC by Teeksss
"""

import json
import pickle
import logging
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Complete Redis Cache Service"""
    
    def __init__(self):
        self.redis_client = None
        self.connection_pool = None
        self.is_connected = False
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    async def initialize(self):
        """Initialize cache service"""
        try:
            # Create connection pool
            self.connection_pool = redis.ConnectionPool(
                host=self._parse_redis_host(),
                port=self._parse_redis_port(),
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                max_connections=settings.REDIS_POOL_SIZE,
                socket_timeout=settings.REDIS_TIMEOUT,
                socket_connect_timeout=settings.REDIS_TIMEOUT,
                retry_on_timeout=True,
                decode_responses=True
            )
            
            # Create Redis client
            self.redis_client = redis.Redis(
                connection_pool=self.connection_pool,
                decode_responses=True
            )
            
            # Test connection
            await self._test_connection()
            self.is_connected = True
            
            logger.info("✅ Cache Service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Cache Service initialization failed: {e}")
            self.is_connected = False
            raise
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        try:
            if not self.is_connected:
                logger.warning("Cache not connected, returning default")
                return default
            
            # Add prefix to key
            prefixed_key = self._add_prefix(key)
            
            # Get value from Redis
            value = self.redis_client.get(prefixed_key)
            
            if value is None:
                self.stats["misses"] += 1
                return default
            
            # Deserialize value
            deserialized_value = self._deserialize(value)
            self.stats["hits"] += 1
            
            logger.debug(f"Cache HIT: {key}")
            return deserialized_value
            
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            self.stats["errors"] += 1
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Set value in cache"""
        try:
            if not self.is_connected:
                logger.warning("Cache not connected, skipping set")
                return False
            
            # Add prefix to key
            prefixed_key = self._add_prefix(key)
            
            # Serialize value
            serialized_value = self._serialize(value)
            
            # Set TTL
            if ttl is None:
                ttl = settings.CACHE_DEFAULT_TIMEOUT
            
            # Set value in Redis
            result = self.redis_client.set(
                prefixed_key, 
                serialized_value, 
                ex=ttl,
                nx=nx,
                xx=xx
            )
            
            if result:
                self.stats["sets"] += 1
                logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if not self.is_connected:
                logger.warning("Cache not connected, skipping delete")
                return False
            
            # Add prefix to key
            prefixed_key = self._add_prefix(key)
            
            # Delete from Redis
            result = self.redis_client.delete(prefixed_key)
            
            if result:
                self.stats["deletes"] += 1
                logger.debug(f"Cache DELETE: {key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if not self.is_connected:
                return False
            
            # Add prefix to key
            prefixed_key = self._add_prefix(key)
            
            # Check existence
            return bool(self.redis_client.exists(prefixed_key))
            
        except Exception as e:
            logger.error(f"Cache EXISTS error for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        try:
            if not self.is_connected:
                return False
            
            # Add prefix to key
            prefixed_key = self._add_prefix(key)
            
            # Set expiration
            return bool(self.redis_client.expire(prefixed_key, ttl))
            
        except Exception as e:
            logger.error(f"Cache EXPIRE error for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def ttl(self, key: str) -> int:
        """Get time to live for key"""
        try:
            if not self.is_connected:
                return -1
            
            # Add prefix to key
            prefixed_key = self._add_prefix(key)
            
            # Get TTL
            return self.redis_client.ttl(prefixed_key)
            
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            self.stats["errors"] += 1
            return -1
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric value"""
        try:
            if not self.is_connected:
                return None
            
            # Add prefix to key
            prefixed_key = self._add_prefix(key)
            
            # Increment value
            return self.redis_client.incrby(prefixed_key, amount)
            
        except Exception as e:
            logger.error(f"Cache INCR error for key {key}: {e}")
            self.stats["errors"] += 1
            return None
    
    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement numeric value"""
        try:
            if not self.is_connected:
                return None
            
            # Add prefix to key
            prefixed_key = self._add_prefix(key)
            
            # Decrement value
            return self.redis_client.decrby(prefixed_key, amount)
            
        except Exception as e:
            logger.error(f"Cache DECR error for key {key}: {e}")
            self.stats["errors"] += 1
            return None
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        try:
            if not self.is_connected or not keys:
                return {}
            
            # Add prefix to keys
            prefixed_keys = [self._add_prefix(key) for key in keys]
            
            # Get values from Redis
            values = self.redis_client.mget(prefixed_keys)
            
            # Build result dictionary
            result = {}
            for i, key in enumerate(keys):
                value = values[i]
                if value is not None:
                    result[key] = self._deserialize(value)
                    self.stats["hits"] += 1
                else:
                    self.stats["misses"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Cache MGET error: {e}")
            self.stats["errors"] += 1
            return {}
    
    async def set_many(
        self, 
        mapping: Dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in cache"""
        try:
            if not self.is_connected or not mapping:
                return False
            
            # Prepare data
            prefixed_mapping = {}
            for key, value in mapping.items():
                prefixed_key = self._add_prefix(key)
                serialized_value = self._serialize(value)
                prefixed_mapping[prefixed_key] = serialized_value
            
            # Set values in Redis
            result = self.redis_client.mset(prefixed_mapping)
            
            # Set TTL for all keys if specified
            if result and ttl:
                pipe = self.redis_client.pipeline()
                for prefixed_key in prefixed_mapping.keys():
                    pipe.expire(prefixed_key, ttl)
                pipe.execute()
            
            if result:
                self.stats["sets"] += len(mapping)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache MSET error: {e}")
            self.stats["errors"] += 1
            return False
    
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys from cache"""
        try:
            if not self.is_connected or not keys:
                return 0
            
            # Add prefix to keys
            prefixed_keys = [self._add_prefix(key) for key in keys]
            
            # Delete from Redis
            deleted_count = self.redis_client.delete(*prefixed_keys)
            
            self.stats["deletes"] += deleted_count
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache MDEL error: {e}")
            self.stats["errors"] += 1
            return 0
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            if not self.is_connected:
                return 0
            
            # Add prefix to pattern
            prefixed_pattern = self._add_prefix(pattern)
            
            # Find matching keys
            keys = self.redis_client.keys(prefixed_pattern)
            
            if not keys:
                return 0
            
            # Delete keys
            deleted_count = self.redis_client.delete(*keys)
            
            self.stats["deletes"] += deleted_count
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache CLEAR_PATTERN error: {e}")
            self.stats["errors"] += 1
            return 0
    
    async def flush_all(self) -> bool:
        """Flush all cache data"""
        try:
            if not self.is_connected:
                return False
            
            # Flush database
            result = self.redis_client.flushdb()
            
            if result:
                logger.info("Cache flushed successfully")
                # Reset stats
                self.stats = {
                    "hits": 0,
                    "misses": 0,
                    "sets": 0,
                    "deletes": 0,
                    "errors": 0
                }
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache FLUSH error: {e}")
            self.stats["errors"] += 1
            return False
    
    @asynccontextmanager
    async def pipeline(self):
        """Redis pipeline context manager"""
        if not self.is_connected:
            yield None
            return
        
        pipe = self.redis_client.pipeline()
        try:
            yield pipe
            pipe.execute()
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            pipe.reset()
            raise
    
    async def get_info(self) -> Dict[str, Any]:
        """Get Redis server info"""
        try:
            if not self.is_connected:
                return {}
            
            info = self.redis_client.info()
            
            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
            
        except Exception as e:
            logger.error(f"Cache INFO error: {e}")
            return {"error": str(e)}
    
    def _parse_redis_host(self) -> str:
        """Parse Redis host from URL"""
        if "://" in settings.REDIS_URL:
            # Format: redis://host:port/db
            parts = settings.REDIS_URL.split("://")[1].split("/")[0]
            if "@" in parts:
                parts = parts.split("@")[1]
            return parts.split(":")[0]
        return "localhost"
    
    def _parse_redis_port(self) -> int:
        """Parse Redis port from URL"""
        if "://" in settings.REDIS_URL:
            # Format: redis://host:port/db
            parts = settings.REDIS_URL.split("://")[1].split("/")[0]
            if "@" in parts:
                parts = parts.split("@")[1]
            if ":" in parts:
                return int(parts.split(":")[1])
        return 6379
    
    def _add_prefix(self, key: str) -> str:
        """Add prefix to cache key"""
        return f"{settings.CACHE_KEY_PREFIX}{key}"
    
    def _serialize(self, value: Any) -> str:
        """Serialize value for storage"""
        try:
            if isinstance(value, str):
                return value
            elif isinstance(value, (int, float, bool)):
                return json.dumps(value)
            else:
                # Use pickle for complex objects
                return json.dumps({
                    "_type": "pickle",
                    "_data": pickle.dumps(value).hex()
                })
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            return json.dumps(str(value))
    
    def _deserialize(self, value: str) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first
            data = json.loads(value)
            
            # Check if it's a pickled object
            if isinstance(data, dict) and data.get("_type") == "pickle":
                return pickle.loads(bytes.fromhex(data["_data"]))
            
            return data
            
        except json.JSONDecodeError:
            # Return as string if not JSON
            return value
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            return value
    
    async def _test_connection(self):
        """Test Redis connection"""
        try:
            self.redis_client.ping()
            logger.info("✅ Redis connection test successful")
        except Exception as e:
            logger.error(f"❌ Redis connection test failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Service health check"""
        try:
            if not self.is_connected:
                return {
                    "status": "unhealthy",
                    "error": "Not connected to Redis",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Test basic operations
            test_key = "health_check_test"
            test_value = "test_value"
            
            # Set test value
            await self.set(test_key, test_value, ttl=10)
            
            # Get test value
            retrieved = await self.get(test_key)
            
            # Delete test value
            await self.delete(test_key)
            
            # Check if test passed
            test_passed = retrieved == test_value
            
            return {
                "status": "healthy" if test_passed else "degraded",
                "connection": self.is_connected,
                "test_passed": test_passed,
                "stats": self.stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics"""
        try:
            info = await self.get_info()
            
            return {
                "connection_status": self.is_connected,
                "stats": self.stats,
                "hit_rate": (
                    self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])
                    if (self.stats["hits"] + self.stats["misses"]) > 0 else 0
                ),
                "redis_info": info,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        try:
            if self.redis_client:
                self.redis_client.close()
            
            if self.connection_pool:
                self.connection_pool.disconnect()
            
            self.is_connected = False
            logger.info("✅ Cache Service cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Cache Service cleanup error: {e}")


# Global cache instance
cache_service = CacheService()

# Convenience functions
async def get_cache(key: str, default: Any = None) -> Any:
    """Get value from cache"""
    return await cache_service.get(key, default)

async def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set value in cache"""
    return await cache_service.set(key, value, ttl)

async def delete_cache(key: str) -> bool:
    """Delete key from cache"""
    return await cache_service.delete(key)

async def clear_cache_pattern(pattern: str) -> int:
    """Clear all keys matching pattern"""
    return await cache_service.clear_pattern(pattern)