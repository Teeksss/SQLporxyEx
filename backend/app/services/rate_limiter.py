"""
Complete Rate Limiter Service - Final Version
Created: 2025-05-29 14:27:08 UTC by Teeksss
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from collections import defaultdict
from dataclasses import dataclass
import hashlib

from app.core.config import settings
from app.services.cache import cache_service

logger = logging.getLogger(__name__)


@dataclass
class RateLimitRule:
    """Rate limit rule configuration"""
    requests: int
    window_seconds: int
    burst_allowance: float = 1.5
    block_duration_seconds: int = 300


@dataclass
class RateLimitResult:
    """Rate limit check result"""
    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None


class RateLimiterService:
    """Complete Rate Limiting Service"""
    
    def __init__(self):
        self.rules = self._load_rate_limit_rules()
        self.blocked_ips = {}
        self.blocked_users = {}
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "allowed_requests": 0,
            "blocked_ips": 0,
            "blocked_users": 0
        }
        
    async def initialize(self):
        """Initialize rate limiter service"""
        logger.info("Rate Limiter Service initialized")
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_expired_blocks())
    
    async def check_rate_limit(
        self,
        identifier: str,
        rule_type: str = "default",
        ip_address: str = None,
        user_id: int = None,
        user_role: str = None
    ) -> RateLimitResult:
        """Check if request is within rate limits"""
        
        self.stats["total_requests"] += 1
        
        try:
            # Check if IP is blocked
            if ip_address and await self._is_ip_blocked(ip_address):
                self.stats["blocked_requests"] += 1
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=datetime.utcnow() + timedelta(seconds=300),
                    retry_after=300
                )
            
            # Check if user is blocked
            if user_id and await self._is_user_blocked(user_id):
                self.stats["blocked_requests"] += 1
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=datetime.utcnow() + timedelta(seconds=300),
                    retry_after=300
                )
            
            # Get appropriate rule
            rule = self._get_rule_for_type(rule_type, user_role)
            
            # Check rate limit
            result = await self._check_sliding_window(identifier, rule)
            
            # Update stats
            if result.allowed:
                self.stats["allowed_requests"] += 1
            else:
                self.stats["blocked_requests"] += 1
                
                # Block IP/user if too many violations
                await self._handle_rate_limit_violation(
                    identifier, ip_address, user_id, rule
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request on error to avoid blocking legitimate users
            return RateLimitResult(
                allowed=True,
                remaining=100,
                reset_time=datetime.utcnow() + timedelta(seconds=3600)
            )
    
    async def _check_sliding_window(
        self, 
        identifier: str, 
        rule: RateLimitRule
    ) -> RateLimitResult:
        """Check rate limit using sliding window algorithm"""
        
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=rule.window_seconds)
        
        # Create cache key
        cache_key = f"rate_limit:{identifier}:{rule.window_seconds}"
        
        try:
            # Get current window data
            window_data = await cache_service.get(cache_key, {})
            
            # Clean old entries
            cleaned_data = {
                timestamp: count for timestamp, count in window_data.items()
                if datetime.fromisoformat(timestamp) > window_start
            }
            
            # Count requests in window
            total_requests = sum(cleaned_data.values())
            
            # Check if limit exceeded
            if total_requests >= rule.requests:
                # Check burst allowance
                burst_limit = int(rule.requests * rule.burst_allowance)
                if total_requests >= burst_limit:
                    return RateLimitResult(
                        allowed=False,
                        remaining=0,
                        reset_time=now + timedelta(seconds=rule.window_seconds),
                        retry_after=rule.window_seconds
                    )
            
            # Add current request
            current_minute = now.replace(second=0, microsecond=0).isoformat()
            cleaned_data[current_minute] = cleaned_data.get(current_minute, 0) + 1
            
            # Update cache
            await cache_service.set(
                cache_key, 
                cleaned_data, 
                ttl=rule.window_seconds + 60
            )
            
            # Calculate remaining requests
            remaining = max(0, rule.requests - sum(cleaned_data.values()))
            
            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_time=now + timedelta(seconds=rule.window_seconds)
            )
            
        except Exception as e:
            logger.error(f"Sliding window check error: {e}")
            # Allow on error
            return RateLimitResult(
                allowed=True,
                remaining=rule.requests,
                reset_time=now + timedelta(seconds=rule.window_seconds)
            )
    
    async def _handle_rate_limit_violation(
        self,
        identifier: str,
        ip_address: str,
        user_id: int,
        rule: RateLimitRule
    ):
        """Handle rate limit violation"""
        
        violation_key = f"violations:{identifier}"
        
        try:
            # Get violation count
            violations = await cache_service.get(violation_key, 0)
            violations += 1
            
            # Store violation count
            await cache_service.set(violation_key, violations, ttl=3600)
            
            # Block if too many violations
            if violations >= 5:  # Configurable threshold
                if ip_address:
                    await self._block_ip(ip_address, rule.block_duration_seconds)
                
                if user_id:
                    await self._block_user(user_id, rule.block_duration_seconds)
                
                logger.warning(
                    f"Blocked identifier {identifier} after {violations} violations"
                )
            
        except Exception as e:
            logger.error(f"Violation handling error: {e}")
    
    async def _block_ip(self, ip_address: str, duration_seconds: int):
        """Block IP address"""
        
        block_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
        self.blocked_ips[ip_address] = block_until
        
        # Store in cache for persistence
        await cache_service.set(
            f"blocked_ip:{ip_address}",
            block_until.isoformat(),
            ttl=duration_seconds
        )
        
        self.stats["blocked_ips"] += 1
        logger.warning(f"Blocked IP {ip_address} until {block_until}")
    
    async def _block_user(self, user_id: int, duration_seconds: int):
        """Block user"""
        
        block_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
        self.blocked_users[user_id] = block_until
        
        # Store in cache for persistence
        await cache_service.set(
            f"blocked_user:{user_id}",
            block_until.isoformat(),
            ttl=duration_seconds
        )
        
        self.stats["blocked_users"] += 1
        logger.warning(f"Blocked user {user_id} until {block_until}")
    
    async def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        
        # Check memory cache first
        if ip_address in self.blocked_ips:
            if datetime.utcnow() < self.blocked_ips[ip_address]:
                return True
            else:
                del self.blocked_ips[ip_address]
        
        # Check persistent cache
        try:
            block_until_str = await cache_service.get(f"blocked_ip:{ip_address}")
            if block_until_str:
                block_until = datetime.fromisoformat(block_until_str)
                if datetime.utcnow() < block_until:
                    self.blocked_ips[ip_address] = block_until
                    return True
        except Exception as e:
            logger.error(f"IP block check error: {e}")
        
        return False
    
    async def _is_user_blocked(self, user_id: int) -> bool:
        """Check if user is blocked"""
        
        # Check memory cache first
        if user_id in self.blocked_users:
            if datetime.utcnow() < self.blocked_users[user_id]:
                return True
            else:
                del self.blocked_users[user_id]
        
        # Check persistent cache
        try:
            block_until_str = await cache_service.get(f"blocked_user:{user_id}")
            if block_until_str:
                block_until = datetime.fromisoformat(block_until_str)
                if datetime.utcnow() < block_until:
                    self.blocked_users[user_id] = block_until
                    return True
        except Exception as e:
            logger.error(f"User block check error: {e}")
        
        return False
    
    async def unblock_ip(self, ip_address: str) -> bool:
        """Unblock IP address"""
        
        try:
            # Remove from memory cache
            self.blocked_ips.pop(ip_address, None)
            
            # Remove from persistent cache
            await cache_service.delete(f"blocked_ip:{ip_address}")
            
            logger.info(f"Unblocked IP {ip_address}")
            return True
            
        except Exception as e:
            logger.error(f"IP unblock error: {e}")
            return False
    
    async def unblock_user(self, user_id: int) -> bool:
        """Unblock user"""
        
        try:
            # Remove from memory cache
            self.blocked_users.pop(user_id, None)
            
            # Remove from persistent cache
            await cache_service.delete(f"blocked_user:{user_id}")
            
            logger.info(f"Unblocked user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"User unblock error: {e}")
            return False
    
    async def get_rate_limit_status(
        self, 
        identifier: str,
        rule_type: str = "default"
    ) -> Dict[str, Any]:
        """Get current rate limit status"""
        
        try:
            rule = self._get_rule_for_type(rule_type)
            cache_key = f"rate_limit:{identifier}:{rule.window_seconds}"
            
            # Get current window data
            window_data = await cache_service.get(cache_key, {})
            
            # Clean old entries
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=rule.window_seconds)
            
            cleaned_data = {
                timestamp: count for timestamp, count in window_data.items()
                if datetime.fromisoformat(timestamp) > window_start
            }
            
            # Count requests
            total_requests = sum(cleaned_data.values())
            remaining = max(0, rule.requests - total_requests)
            
            return {
                "identifier": identifier,
                "rule_type": rule_type,
                "requests_made": total_requests,
                "requests_remaining": remaining,
                "limit": rule.requests,
                "window_seconds": rule.window_seconds,
                "reset_time": (now + timedelta(seconds=rule.window_seconds)).isoformat(),
                "blocked": total_requests >= rule.requests
            }
            
        except Exception as e:
            logger.error(f"Rate limit status error: {e}")
            return {
                "error": str(e),
                "identifier": identifier,
                "rule_type": rule_type
            }
    
    def _get_rule_for_type(
        self, 
        rule_type: str, 
        user_role: str = None
    ) -> RateLimitRule:
        """Get rate limit rule for type and role"""
        
        # Role-based rules take precedence
        if user_role:
            role_rule = self.rules.get(f"role_{user_role}")
            if role_rule:
                return role_rule
        
        # Return specific rule or default
        return self.rules.get(rule_type, self.rules["default"])
    
    def _load_rate_limit_rules(self) -> Dict[str, RateLimitRule]:
        """Load rate limit rules configuration"""
        
        return {
            "default": RateLimitRule(
                requests=settings.DEFAULT_RATE_LIMIT,
                window_seconds=3600  # 1 hour
            ),
            "auth": RateLimitRule(
                requests=10,
                window_seconds=900,  # 15 minutes
                block_duration_seconds=900
            ),
            "query": RateLimitRule(
                requests=100,
                window_seconds=3600  # 1 hour
            ),
            "api": RateLimitRule(
                requests=1000,
                window_seconds=3600  # 1 hour
            ),
            "role_admin": RateLimitRule(
                requests=2000,
                window_seconds=3600  # 1 hour
            ),
            "role_analyst": RateLimitRule(
                requests=1000,
                window_seconds=3600  # 1 hour
            ),
            "role_powerbi": RateLimitRule(
                requests=500,
                window_seconds=3600  # 1 hour
            ),
            "role_readonly": RateLimitRule(
                requests=200,
                window_seconds=3600  # 1 hour
            )
        }
    
    async def _cleanup_expired_blocks(self):
        """Cleanup expired blocks periodically"""
        
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                now = datetime.utcnow()
                
                # Clean expired IP blocks
                expired_ips = [
                    ip for ip, block_until in self.blocked_ips.items()
                    if now >= block_until
                ]
                
                for ip in expired_ips:
                    del self.blocked_ips[ip]
                
                # Clean expired user blocks
                expired_users = [
                    user_id for user_id, block_until in self.blocked_users.items()
                    if now >= block_until
                ]
                
                for user_id in expired_users:
                    del self.blocked_users[user_id]
                
                if expired_ips or expired_users:
                    logger.info(
                        f"Cleaned {len(expired_ips)} expired IP blocks and "
                        f"{len(expired_users)} expired user blocks"
                    )
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def get_blocked_entities(self) -> Dict[str, Any]:
        """Get all currently blocked entities"""
        
        return {
            "blocked_ips": {
                ip: block_until.isoformat()
                for ip, block_until in self.blocked_ips.items()
            },
            "blocked_users": {
                user_id: block_until.isoformat()
                for user_id, block_until in self.blocked_users.items()
            },
            "total_blocked_ips": len(self.blocked_ips),
            "total_blocked_users": len(self.blocked_users),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Service health check"""
        
        try:
            # Test rate limiting functionality
            test_result = await self.check_rate_limit("health_check_test", "default")
            
            return {
                "status": "healthy",
                "test_passed": test_result.allowed,
                "rules_loaded": len(self.rules),
                "blocked_ips": len(self.blocked_ips),
                "blocked_users": len(self.blocked_users),
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
        """Get rate limiter metrics"""
        
        return {
            "stats": self.stats,
            "rules": {
                name: {
                    "requests": rule.requests,
                    "window_seconds": rule.window_seconds,
                    "burst_allowance": rule.burst_allowance,
                    "block_duration_seconds": rule.block_duration_seconds
                }
                for name, rule in self.rules.items()
            },
            "blocked_entities": await self.get_blocked_entities(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup service resources"""
        
        logger.info("Rate Limiter Service cleanup completed")


# Global rate limiter instance
rate_limiter_service = RateLimiterService()

# Convenience function
async def check_rate_limit(
    identifier: str,
    rule_type: str = "default",
    ip_address: str = None,
    user_id: int = None,
    user_role: str = None
) -> RateLimitResult:
    """Check rate limit"""
    return await rate_limiter_service.check_rate_limit(
        identifier, rule_type, ip_address, user_id, user_role
    )