"""
Circuit Breaker Pattern - Gold Tier

Prevents cascade failures by stopping requests to failing services.
After consecutive failures, circuit "opens" and fails fast without calling the service.
After a timeout, circuit "half-opens" to test if service recovered.

Usage:
    breaker = CircuitBreaker(name="gmail", failure_threshold=5, recovery_timeout=300)
    
    with breaker:
        result = gmail_api.send_email(...)
"""

import time
import logging
from enum import Enum
from typing import Optional, Callable, Any
from datetime import datetime

logger = logging.getLogger('CircuitBreaker')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast, not calling service
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit is open and request is rejected."""
    pass


class CircuitBreaker:
    """
    Circuit Breaker implementation for AI Employee services.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, reject requests immediately (fail fast)
    - HALF_OPEN: Testing service recovery, allow one request through
    
    Transitions:
    - CLOSED -> OPEN: After failure_threshold consecutive failures
    - OPEN -> HALF_OPEN: After recovery_timeout seconds
    - HALF_OPEN -> CLOSED: On successful request
    - HALF_OPEN -> OPEN: On failed request
    
    Example:
        gmail_breaker = CircuitBreaker(
            name="gmail",
            failure_threshold=5,
            recovery_timeout=300  # 5 minutes
        )
        
        try:
            with gmail_breaker:
                send_email(...)
        except CircuitBreakerError:
            logger.error("Gmail service unavailable, queuing request")
            queue_for_later(...)
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 300.0,
        on_state_change: Optional[Callable] = None
    ):
        """
        Args:
            name: Circuit breaker name (for logging)
            failure_threshold: Consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before testing recovery
            on_state_change: Optional callback(state) when state changes
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.on_state_change = on_state_change
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._last_state_change = datetime.now()
        
        logger.info(f"🔌 Circuit breaker '{name}' initialized (threshold: {failure_threshold})")
    
    @property
    def state(self) -> CircuitState:
        """Get current state, checking if OPEN should transition to HALF_OPEN."""
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)
        return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        return self.state == CircuitState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state
        self._last_state_change = datetime.now()
        
        logger.info(
            f"🔌 Circuit '{self.name}': {old_state.value} -> {new_state.value}"
        )
        
        if self.on_state_change:
            self.on_state_change(new_state)
    
    def record_success(self):
        """Record a successful request."""
        if self.state == CircuitState.HALF_OPEN:
            # Service recovered, close circuit
            self._failure_count = 0
            self._success_count = 1
            self._transition_to(CircuitState.CLOSED)
        else:
            self._success_count += 1
            # Reset failure count on success (when closed)
            if self._state == CircuitState.CLOSED:
                self._failure_count = 0
    
    def record_failure(self):
        """Record a failed request."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Service still failing, re-open circuit
            self._transition_to(CircuitState.OPEN)
        elif self._failure_count >= self.failure_threshold:
            # Threshold reached, open circuit
            self._transition_to(CircuitState.OPEN)
    
    def __enter__(self):
        """Context manager entry."""
        if self.is_open:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable. Try again later."
            )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure()
        # Don't suppress exceptions
        return False
    
    def get_status(self) -> dict:
        """Get circuit breaker status as dict."""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self._failure_count,
            'success_count': self._success_count,
            'failure_threshold': self.failure_threshold,
            'recovery_timeout': self.recovery_timeout,
            'last_failure_time': datetime.fromtimestamp(self._last_failure_time).isoformat() if self._last_failure_time > 0 else None,
            'last_state_change': self._last_state_change.isoformat()
        }
    
    def reset(self):
        """Manually reset circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._transition_to(CircuitState.CLOSED)


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    
    Example:
        registry = CircuitBreakerRegistry()
        gmail_breaker = registry.get_or_create("gmail")
        linkedin_breaker = registry.get_or_create("linkedin")
    """
    
    def __init__(self):
        self._breakers = {}
    
    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 300.0,
        on_state_change: Optional[Callable] = None
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                on_state_change=on_state_change
            )
        return self._breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self._breakers.get(name)
    
    def get_all_status(self) -> dict:
        """Get status of all circuit breakers."""
        return {name: breaker.get_status() for name, breaker in self._breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()


# Global registry for AI Employee
_circuit_breakers = CircuitBreakerRegistry()


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create a circuit breaker from global registry."""
    return _circuit_breakers.get_or_create(name, **kwargs)


def get_all_breakers_status() -> dict:
    """Get status of all circuit breakers."""
    return _circuit_breakers.get_all_status()


# Pre-configured circuit breakers for common services
gmail_breaker = _circuit_breakers.get_or_create("gmail", failure_threshold=5, recovery_timeout=300)
linkedin_breaker = _circuit_breakers.get_or_create("linkedin", failure_threshold=3, recovery_timeout=600)
facebook_breaker = _circuit_breakers.get_or_create("facebook", failure_threshold=5, recovery_timeout=300)
twitter_breaker = _circuit_breakers.get_or_create("twitter", failure_threshold=5, recovery_timeout=300)
odoo_breaker = _circuit_breakers.get_or_create("odoo", failure_threshold=3, recovery_timeout=600)
mcp_breaker = _circuit_breakers.get_or_create("mcp", failure_threshold=5, recovery_timeout=120)
