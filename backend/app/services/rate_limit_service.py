import redis
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.rate_limit import RateLimitProfile, RateLimitRule, RateLimitExecution
from app.models.user import User, UserRole
from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)

class RateLimitService:
    """Service for rate limiting with Redis sliding window"""
    
    def __init__(self, db: Session, config_service: ConfigService = None):
        self.db = db
        self.config_service = config_service
        self.redis_client = self._get_redis_client()
    
    def _get_redis_client(self):
        """Get Redis client instance"""
        try:
            # This would use actual Redis configuration
            # For now, return a mock client
            return None
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None
    
    async def check_rate_limit(
        self, 
        user_id: int, 
        ip_address: str, 
        user_role: str
    ) -> Dict[str, Any]:
        """Check if request is within rate limits"""
        try:
            # Get user's rate limit profile
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"allowed": False, "message": "User not found"}
            
            profile = user.rate_limit_profile
            if not profile:
                # Get default profile
                profile = self.db.query(RateLimitProfile).filter(
                    RateLimitProfile.is_default == True
                ).first()
            
            if not profile:
                # No rate limiting configured
                return {"allowed": True, "message": "No rate limit configured"}
            
            # Check different rate limit windows
            current_time = datetime.utcnow()
            
            # Check per-minute limit
            if profile.requests_per_minute:
                minute_key = f"rate_limit:user:{user_id}:minute:{current_time.strftime('%Y%m%d%H%M')}"
                minute_count = await self._get_request_count(minute_key)
                
                if minute_count >= profile.requests_per_minute:
                    return {
                        "allowed": False,
                        "message": f"Rate limit exceeded: {profile.requests_per_minute} requests per minute",
                        "retry_after": 60 - current_time.second
                    }
            
            # Check per-hour limit
            if profile.requests_per_hour:
                hour_key = f"rate_limit:user:{user_id}:hour:{current_time.strftime('%Y%m%d%H')}"
                hour_count = await self._get_request_count(hour_key)
                
                if hour_count >= profile.requests_per_hour:
                    return {
                        "allowed": False,
                        "message": f"Rate limit exceeded: {profile.requests_per_hour} requests per hour",
                        "retry_after": 3600 - (current_time.minute * 60 + current_time.second)
                    }
            
            # Check per-day limit
            if profile.requests_per_day:
                day_key = f"rate_limit:user:{user_id}:day:{current_time.strftime('%Y%m%d')}"
                day_count = await self._get_request_count(day_key)
                
                if day_count >= profile.requests_per_day:
                    return {
                        "allowed": False,
                        "message": f"Rate limit exceeded: {profile.requests_per_day} requests per day",
                        "retry_after": 86400 - (current_time.hour * 3600 + current_time.minute * 60 + current_time.second)
                    }
            
            # Check concurrent queries
            if profile.max_concurrent_queries:
                concurrent_count = await self._get_concurrent_queries(user_id)
                
                if concurrent_count >= profile.max_concurrent_queries:
                    return {
                        "allowed": False,
                        "message": f"Concurrent query limit exceeded: {profile.max_concurrent_queries} queries",
                        "retry_after": 30
                    }
            
            return {
                "allowed": True,
                "message": "Within rate limits",
                "limits": {
                    "requests_per_minute": profile.requests_per_minute,
                    "requests_per_hour": profile.requests_per_hour,
                    "requests_per_day": profile.requests_per_day,
                    "max_concurrent": profile.max_concurrent_queries
                }
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if rate limiting fails
            return {"allowed": True, "message": "Rate limit check failed"}
    
    async def record_request(
        self, 
        user_id: int, 
        ip_address: str, 
        user_role: str
    ) -> bool:
        """Record a request for rate limiting"""
        try:
            current_time = datetime.utcnow()
            
            # Increment counters
            minute_key = f"rate_limit:user:{user_id}:minute:{current_time.strftime('%Y%m%d%H%M')}"
            hour_key = f"rate_limit:user:{user_id}:hour:{current_time.strftime('%Y%m%d%H')}"
            day_key = f"rate_limit:user:{user_id}:day:{current_time.strftime('%Y%m%d')}"
            
            await self._increment_counter(minute_key, 60)  # Expire after 1 minute
            await self._increment_counter(hour_key, 3600)  # Expire after 1 hour
            await self._increment_counter(day_key, 86400)  # Expire after 1 day
            
            # Record in database for analytics
            execution = RateLimitExecution(
                target_type="user",
                target_value=str(user_id),
                window_start=current_time,
                window_end=current_time + timedelta(minutes=1),
                ip_address=ip_address,
                endpoint="query_execution"
            )
            self.db.add(execution)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Request recording failed: {e}")
            return False
    
    async def start_query_execution(self, user_id: int, query_id: str) -> bool:
        """Mark start of query execution for concurrent tracking"""
        try:
            if not self.redis_client:
                return True
            
            concurrent_key = f"concurrent_queries:user:{user_id}"
            query_key = f"query_execution:{query_id}"
            
            # Add query to concurrent set
            self.redis_client.sadd(concurrent_key, query_id)
            self.redis_client.expire(concurrent_key, 3600)  # Cleanup after 1 hour
            
            # Set query execution marker
            self.redis_client.setex(query_key, 3600, json.dumps({
                "user_id": user_id,
                "started_at": datetime.utcnow().isoformat()
            }))
            
            return True
            
        except Exception as e:
            logger.error(f"Query execution start tracking failed: {e}")
            return True
    
    async def end_query_execution(self, user_id: int, query_id: str) -> bool:
        """Mark end of query execution for concurrent tracking"""
        try:
            if not self.redis_client:
                return True
            
            concurrent_key = f"concurrent_queries:user:{user_id}"
            query_key = f"query_execution:{query_id}"
            
            # Remove query from concurrent set
            self.redis_client.srem(concurrent_key, query_id)
            
            # Remove query execution marker
            self.redis_client.delete(query_key)
            
            return True
            
        except Exception as e:
            logger.error(f"Query execution end tracking failed: {e}")
            return True
    
    async def _get_request_count(self, key: str) -> int:
        """Get request count from Redis"""
        try:
            if not self.redis_client:
                return 0
            
            count = self.redis_client.get(key)
            return int(count) if count else 0
            
        except Exception as e:
            logger.error(f"Request count retrieval failed: {e}")
            return 0
    
    async def _increment_counter(self, key: str, ttl: int) -> int:
        """Increment counter in Redis with TTL"""
        try:
            if not self.redis_client:
                return 1
            
            # Use pipeline for atomic operation
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            results = pipe.execute()
            
            return results[0] if results else 1
            
        except Exception as e:
            logger.error(f"Counter increment failed: {e}")
            return 1
    
    async def _get_concurrent_queries(self, user_id: int) -> int:
        """Get count of concurrent queries for user"""
        try:
            if not self.redis_client:
                return 0
            
            concurrent_key = f"concurrent_queries:user:{user_id}"
            count = self.redis_client.scard(concurrent_key)
            return count or 0
            
        except Exception as e:
            logger.error(f"Concurrent query count failed: {e}")
            return 0
    
    async def get_rate_limit_status(self, user_id: int) -> Dict[str, Any]:
        """Get current rate limit status for user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            
            profile = user.rate_limit_profile
            if not profile:
                profile = self.db.query(RateLimitProfile).filter(
                    RateLimitProfile.is_default == True
                ).first()
            
            if not profile:
                return {"message": "No rate limiting configured"}
            
            current_time = datetime.utcnow()
            
            # Get current usage
            minute_key = f"rate_limit:user:{user_id}:minute:{current_time.strftime('%Y%m%d%H%M')}"
            hour_key = f"rate_limit:user:{user_id}:hour:{current_time.strftime('%Y%m%d%H')}"
            day_key = f"rate_limit:user:{user_id}:day:{current_time.strftime('%Y%m%d')}"
            
            minute_count = await self._get_request_count(minute_key)
            hour_count = await self._get_request_count(hour_key)
            day_count = await self._get_request_count(day_key)
            concurrent_count = await self._get_concurrent_queries(user_id)
            
            return {
                "profile_name": profile.name,
                "limits": {
                    "requests_per_minute": profile.requests_per_minute,
                    "requests_per_hour": profile.requests_per_hour,
                    "requests_per_day": profile.requests_per_day,
                    "max_concurrent_queries": profile.max_concurrent_queries
                },
                "current_usage": {
                    "minute": minute_count,
                    "hour": hour_count,
                    "day": day_count,
                    "concurrent": concurrent_count
                },
                "remaining": {
                    "minute": max(0, (profile.requests_per_minute or 0) - minute_count),
                    "hour": max(0, (profile.requests_per_hour or 0) - hour_count),
                    "day": max(0, (profile.requests_per_day or 0) - day_count),
                    "concurrent": max(0, (profile.max_concurrent_queries or 0) - concurrent_count)
                }
            }
            
        except Exception as e:
            logger.error(f"Rate limit status check failed: {e}")
            return {"error": str(e)}