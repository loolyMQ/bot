import json
import asyncio
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import redis.asyncio as redis
from functools import wraps


class CacheConfig:
    
    def __init__(self):
        self.default_ttl = 3600
        self.key_prefix = "arcana_bot:"


class RedisCacheOperations:
    
    def __init__(self, redis_client: redis.Redis, config: CacheConfig):
        self.redis_client = redis_client
        self.config = config
    
    async def get(self, key: str) -> Optional[Any]:
        full_key = f"{self.config.key_prefix}{key}"
        try:
            value = await self.redis_client.get(full_key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        full_key = f"{self.config.key_prefix}{key}"
        ttl = ttl or self.config.default_ttl
        try:
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(full_key, ttl, serialized_value)
            return True
        except Exception as e:
            return False
    
    async def delete(self, key: str) -> bool:
        full_key = f"{self.config.key_prefix}{key}"
        try:
            result = await self.redis_client.delete(full_key)
            return result > 0
        except Exception as e:
            return False


class MemoryCacheOperations:
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._memory_cache: Dict[str, Dict] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        full_key = f"{self.config.key_prefix}{key}"
        if full_key in self._memory_cache:
            cache_entry = self._memory_cache[full_key]
            if cache_entry["expires_at"] > datetime.now():
                return cache_entry["value"]
            else:
                del self._memory_cache[full_key]
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        full_key = f"{self.config.key_prefix}{key}"
        ttl = ttl or self.config.default_ttl
        self._memory_cache[full_key] = {
            "value": value,
            "expires_at": datetime.now() + timedelta(seconds=ttl)
        }
        return True
    
    async def delete(self, key: str) -> bool:
        full_key = f"{self.config.key_prefix}{key}"
        if full_key in self._memory_cache:
            del self._memory_cache[full_key]
            return True
        return False


class CacheManager:
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.config = CacheConfig()
        self.redis_ops: Optional[RedisCacheOperations] = None
        self.memory_ops = MemoryCacheOperations(self.config)
    
    async def initialize(self):
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            await self.redis_client.ping()
            self.redis_ops = RedisCacheOperations(self.redis_client, self.config)
            
        except Exception as e:
            self.redis_client = None
            self.redis_ops = None
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            if self.redis_ops:
                return await self.redis_ops.get(key)
            else:
                return await self.memory_ops.get(key)
        except Exception as e:
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        try:
            if self.redis_ops:
                return await self.redis_ops.set(key, value, ttl)
            else:
                return await self.memory_ops.set(key, value, ttl)
        except Exception as e:
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            if self.redis_ops:
                return await self.redis_ops.delete(key)
            else:
                return await self.memory_ops.delete(key)
        except Exception as e:
            return False
    
    async def exists(self, key: str) -> bool:
        full_key = f"{self.config.key_prefix}{key}"
        
        try:
            if self.redis_client:
                return await self.redis_client.exists(full_key) > 0
            else:
                return await self.memory_ops.get(key) is not None
                
        except Exception as e:
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        full_pattern = f"{self.config.key_prefix}{pattern}"
        
        try:
            if self.redis_client:
                keys = await self.redis_client.keys(full_pattern)
                if keys:
                    return await self.redis_client.delete(*keys)
            else:
                keys_to_delete = [
                    key for key in self.memory_ops._memory_cache.keys() 
                    if key.startswith(full_pattern.replace("*", ""))
                ]
                for key in keys_to_delete:
                    del self.memory_ops._memory_cache[key]
                return len(keys_to_delete)
            
            return 0
            
        except Exception as e:
            return 0
    
    async def get_or_set(
        self, 
        key: str, 
        factory_func, 
        ttl: Optional[int] = None
    ) -> Any:
        value = await self.get(key)
        if value is not None:
            return value
        
        if asyncio.iscoroutinefunction(factory_func):
            value = await factory_func()
        else:
            value = factory_func()
        
        await self.set(key, value, ttl)
        return value
    
    async def close(self):
        if self.redis_client:
            await self.redis_client.close()


def cached(cache_manager: CacheManager, ttl: int = 3600, key_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await cache_manager.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


class CacheManagerFactory:
    
    @staticmethod
    def create_cache_manager(redis_url: str = "redis://localhost:6379") -> CacheManager:
        cache_manager = CacheManager(redis_url)
        return cache_manager
