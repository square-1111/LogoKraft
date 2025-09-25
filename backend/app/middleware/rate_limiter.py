"""
Rate Limiter Middleware
Implements token bucket algorithm for API rate limiting
"""

import asyncio
import time
import logging
from typing import Dict, Tuple
from fastapi import HTTPException, Request, status
from functools import wraps

logger = logging.getLogger(__name__)

class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: int, refill_period: int = 60):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens to add per refill period
            refill_period: Period in seconds between refills
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        async with self.lock:
            now = time.time()
            
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            if elapsed >= self.refill_period:
                periods = int(elapsed // self.refill_period)
                tokens_to_add = periods * self.refill_rate
                self.tokens = min(self.capacity, self.tokens + tokens_to_add)
                self.last_refill = now
            
            # Try to consume tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            else:
                return False

class RateLimiter:
    """Global rate limiter with per-user buckets."""
    
    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        self.cleanup_interval = 300  # Clean up old buckets every 5 minutes
        self.last_cleanup = time.time()
    
    def _cleanup_old_buckets(self):
        """Remove old unused buckets to prevent memory leaks."""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            # Remove buckets that haven't been used in the last hour
            cutoff = now - 3600
            self.buckets = {
                key: bucket for key, bucket in self.buckets.items()
                if bucket.last_refill > cutoff
            }
            self.last_cleanup = now
    
    async def is_allowed(
        self, 
        identifier: str, 
        limit: int, 
        window: int = 60,
        tokens: int = 1
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            identifier: Unique identifier (usually user ID)
            limit: Maximum requests per window
            window: Time window in seconds
            tokens: Number of tokens to consume
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        self._cleanup_old_buckets()
        
        # Get or create bucket for this identifier
        if identifier not in self.buckets:
            self.buckets[identifier] = TokenBucket(
                capacity=limit,
                refill_rate=limit,
                refill_period=window
            )
        
        bucket = self.buckets[identifier]
        allowed = await bucket.consume(tokens)
        
        rate_limit_info = {
            'limit': limit,
            'remaining': max(0, bucket.tokens),
            'reset': int(bucket.last_refill + bucket.refill_period),
            'window': window
        }
        
        return allowed, rate_limit_info

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(limit: int, window: int = 60, tokens: int = 1):
    """
    Decorator for rate limiting API endpoints.
    
    Args:
        limit: Maximum requests per window
        window: Time window in seconds
        tokens: Number of tokens this request consumes
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and current_user from function arguments
            request = None
            user_id = None
            
            # Look for request in args/kwargs
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # Look for current_user in kwargs (from Depends)
            if 'current_user' in kwargs:
                user_id = kwargs['current_user'].id
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required for rate limiting"
                )
            
            # Check rate limit
            allowed, rate_info = await rate_limiter.is_allowed(
                identifier=user_id,
                limit=limit,
                window=window,
                tokens=tokens
            )
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {limit} requests per {window} seconds.",
                    headers={
                        'X-RateLimit-Limit': str(rate_info['limit']),
                        'X-RateLimit-Remaining': str(rate_info['remaining']),
                        'X-RateLimit-Reset': str(rate_info['reset']),
                        'Retry-After': str(window)
                    }
                )
            
            # Add rate limit headers to successful responses
            response = await func(*args, **kwargs)
            
            # If response has headers attribute, add rate limit info
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])
            
            return response
        
        return wrapper
    return decorator