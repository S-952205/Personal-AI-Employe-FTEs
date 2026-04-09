"""
Retry Handler with Exponential Backoff - Gold Tier

Provides decorator-based retry logic for transient failures.
Used throughout the AI Employee for resilient operations.

Usage:
    @with_retry(max_attempts=3, base_delay=1, max_delay=60)
    def send_email(to, subject, body):
        # Your code here
        pass
"""

import time
import logging
import random
from functools import wraps
from typing import Tuple, Type, Optional, Callable, Any

logger = logging.getLogger('RetryHandler')


class TransientError(Exception):
    """Error that may resolve itself on retry (network timeout, rate limit, etc.)"""
    pass


class PermanentError(Exception):
    """Error that will not resolve on retry (auth failure, invalid input, etc.)"""
    pass


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable] = None
):
    """
    Decorator for automatic retry with exponential backoff and jitter.
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Base delay between retries in seconds (default: 1)
        max_delay: Maximum delay between retries in seconds (default: 60)
        retryable_exceptions: Tuple of exception types to retry on (default: all)
        on_retry: Optional callback function(attempt, error, delay) called on retry
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @with_retry(max_attempts=3, base_delay=2, max_delay=30)
        def send_email(to, subject, body):
            # Email sending code
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is a retryable error
                    if retryable_exceptions and not isinstance(e, retryable_exceptions):
                        logger.error(f"❌ Permanent error in {func.__name__}: {e}")
                        raise
                    
                    # Check if we have retries left
                    if attempt == max_attempts:
                        logger.error(f"❌ {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    # Calculate delay with exponential backoff + jitter
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    # Add jitter (±25%) to prevent thundering herd
                    jitter = delay * 0.25 * (random.random() - 0.5) * 2
                    actual_delay = max(0.1, delay + jitter)
                    
                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {actual_delay:.1f}s..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt, e, actual_delay)
                    
                    time.sleep(actual_delay)
            
            # Should not reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


class RetryableOperation:
    """
    Class-based retry handler for more complex scenarios.
    
    Example:
        retry_op = RetryableOperation(max_attempts=5, base_delay=2)
        result = retry_op.execute(
            func=my_function,
            args=(arg1, arg2),
            kwargs={'key': 'value'}
        )
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        name: str = "unnamed"
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retryable_exceptions = retryable_exceptions
        self.name = name
        self.attempts_made = 0
        self.last_error = None
    
    def execute(self, func: Callable, args: tuple = (), kwargs: dict = None) -> Any:
        """Execute function with retry logic."""
        if kwargs is None:
            kwargs = {}
        
        self.attempts_made = 0
        self.last_error = None
        
        for attempt in range(1, self.max_attempts + 1):
            self.attempts_made = attempt
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"✅ {self.name} succeeded on attempt {attempt}")
                return result
                
            except Exception as e:
                self.last_error = e
                
                # Check if retryable
                if self.retryable_exceptions and not isinstance(e, self.retryable_exceptions):
                    logger.error(f"❌ {self.name} permanent error: {e}")
                    raise
                
                if attempt == self.max_attempts:
                    logger.error(f"❌ {self.name} failed after {self.max_attempts} attempts: {e}")
                    raise
                
                # Calculate delay
                delay = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
                jitter = delay * 0.25 * (random.random() - 0.5) * 2
                actual_delay = max(0.1, delay + jitter)
                
                logger.warning(
                    f"⚠️ {self.name} attempt {attempt}/{self.max_attempts} failed: {e}. "
                    f"Retrying in {actual_delay:.1f}s..."
                )
                
                time.sleep(actual_delay)
        
        raise self.last_error
    
    def execute_and_return_status(self, func: Callable, args: tuple = (), kwargs: dict = None) -> dict:
        """Execute function and return detailed status dict."""
        if kwargs is None:
            kwargs = {}
        
        try:
            result = self.execute(func, args, kwargs)
            return {
                'success': True,
                'result': result,
                'attempts': self.attempts_made,
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'result': None,
                'attempts': self.attempts_made,
                'error': str(e)
            }


# Common retryable exceptions for AI Employee
GMAIL_RETRYABLE = (
    ConnectionError,
    TimeoutError,
    TransientError,
)

MCP_RETRYABLE = (
    ConnectionError,
    TimeoutError,
    TransientError,
    OSError,  # Network-related OS errors
)

API_RETRYABLE = (
    ConnectionError,
    TimeoutError,
    TransientError,
)


# Convenience decorators for common scenarios
retry_gmail = with_retry(
    max_attempts=3,
    base_delay=2,
    max_delay=30,
    retryable_exceptions=GMAIL_RETRYABLE
)

retry_mcp = with_retry(
    max_attempts=3,
    base_delay=1,
    max_delay=60,
    retryable_exceptions=MCP_RETRYABLE
)

retry_api = with_retry(
    max_attempts=3,
    base_delay=1,
    max_delay=30,
    retryable_exceptions=API_RETRYABLE
)
