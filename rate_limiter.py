import time
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import redis.asyncio as redis
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from messages import BotMessages


@dataclass
class RateLimit:
    requests: int
    window_seconds: int
    block_duration_seconds: int = 300


class RateLimitConfig:
    
    def __init__(self):
        self.default_limits = {
            "message": RateLimit(requests=10, window_seconds=60),
            "callback": RateLimit(requests=20, window_seconds=60),
            "start": RateLimit(requests=5, window_seconds=300),
        }


class RedisRateLimitChecker:
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
    
    async def check_redis_limit(
        self, 
        key: str, 
        limit: RateLimit, 
        current_time: int, 
        window_start: int
    ) -> bool:
        pipe = self.redis_client.pipeline()
        
        pipe.zremrangebyscore(key, 0, window_start)
        
        pipe.zcard(key)
        
        pipe.zadd(key, {str(current_time): current_time})
        
        pipe.expire(key, limit.window_seconds)
        
        results = await pipe.execute()
        current_requests = results[1]
        
        if current_requests >= limit.requests:
            block_key = f"blocked:{key}"
            is_blocked = await self.redis_client.get(block_key)
            
            if not is_blocked:
                await self.redis_client.setex(
                    block_key, 
                    limit.block_duration_seconds, 
                    "1"
                )
            
            return False
        
        return True


class MemoryRateLimitChecker:
    
    def __init__(self):
        self._memory_store: Dict[str, Dict] = {}
    
    def check_memory_limit(
        self, 
        key: str, 
        limit: RateLimit, 
        current_time: int, 
        window_start: int
    ) -> bool:
        if key not in self._memory_store:
            self._memory_store[key] = {
                "requests": [],
                "blocked_until": 0
            }
        
        store = self._memory_store[key]
        
        # Check if user is blocked
        if store["blocked_until"] > current_time:
            return False
        
        # Remove old requests
        store["requests"] = [
            req_time for req_time in store["requests"] 
            if req_time > window_start
        ]
        
        # Check limit
        if len(store["requests"]) >= limit.requests:
            store["blocked_until"] = current_time + limit.block_duration_seconds
            return False
        
        store["requests"].append(current_time)
        return True
    
    def _get_current_requests(self, key: str, window_start: int) -> int:
        if key in self._memory_store:
            store = self._memory_store[key]
            store["requests"] = [
                req_time for req_time in store["requests"] 
                if req_time > window_start
            ]
            return len(store["requests"])
        return 0


class RateLimiter:
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.config = RateLimitConfig()
        self.redis_checker: Optional[RedisRateLimitChecker] = None
        self.memory_checker = MemoryRateLimitChecker()
    
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
            
            # Test connection
            await self.redis_client.ping()
            self.redis_checker = RedisRateLimitChecker(self.redis_client)
            
        except Exception as e:
            # Fallback to in-memory rate limiting
            self.redis_client = None
            self.redis_checker = None
    
    async def is_allowed(
        self, 
        user_id: int, 
        action: str, 
        custom_limit: Optional[RateLimit] = None
    ) -> bool:
        limit = custom_limit or self.config.default_limits.get(action)
        if not limit:
            return True
        
        key = f"rate_limit:{action}:{user_id}"
        current_time = int(time.time())
        window_start = current_time - limit.window_seconds
        
        try:
            if self.redis_checker:
                return await self.redis_checker.check_redis_limit(key, limit, current_time, window_start)
            else:
                return self.memory_checker.check_memory_limit(key, limit, current_time, window_start)
                
        except Exception as e:
            return True  # Allow on error to avoid blocking legitimate users
    
    async def get_remaining_requests(self, user_id: int, action: str) -> int:
        limit = self.config.default_limits.get(action)
        if not limit:
            return float('inf')
        
        key = f"rate_limit:{action}:{user_id}"
        current_time = int(time.time())
        window_start = current_time - limit.window_seconds
        
        try:
            if self.redis_client:
                await self.redis_client.zremrangebyscore(key, 0, window_start)
                current_requests = await self.redis_client.zcard(key)
            else:
                current_requests = self.memory_checker._get_current_requests(key, window_start)
            
            return max(0, limit.requests - current_requests)
            
        except Exception as e:
            return limit.requests
    
    async def close(self):
        if self.redis_client:
            await self.redis_client.close()


class RateLimitMiddleware(BaseMiddleware):
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: Dict
    ) -> any:
        user_id = None
        action = None
        
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            if event.text and event.text.startswith('/'):
                action = "start" if event.text.startswith('/start') else "message"
            else:
                action = "message"
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            action = "callback"
        
        if not user_id or not action:
            return await handler(event, data)
        
        is_allowed = await self.rate_limiter.is_allowed(user_id, action)
        
        if not is_allowed:
            if isinstance(event, Message):
                await event.answer(
                    BotMessages.RATE_LIMIT_EXCEEDED,
                    show_alert=True
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    BotMessages.RATE_LIMIT_EXCEEDED,
                    show_alert=True
                )
            
            return
        
        remaining = await self.rate_limiter.get_remaining_requests(user_id, action)
        data["remaining_requests"] = remaining
        
        return await handler(event, data)


class RateLimiterFactory:
    
    @staticmethod
    def create_rate_limiter(redis_url: str = "redis://localhost:6379") -> RateLimiter:
        rate_limiter = RateLimiter(redis_url)
        return rate_limiter
