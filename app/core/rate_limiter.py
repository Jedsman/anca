"""
Token Bucket Rate Limiter for API calls.
"""
import time
import threading
import logging

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Simple token bucket rate limiter.

    Args:
        tokens_per_minute: Maximum requests per minute (default: 15 for Gemini free tier)
    """

    def __init__(self, tokens_per_minute: int = 15):
        self.capacity = tokens_per_minute
        self.tokens = float(tokens_per_minute)
        self.refill_rate = tokens_per_minute / 60.0  # tokens per second
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def acquire(self, timeout: float = 120.0) -> bool:
        """
        Block until a token is available.

        Args:
            timeout: Maximum seconds to wait (default: 2 minutes)

        Returns:
            True if token acquired, False if timeout
        """
        start_time = time.time()

        while True:
            with self.lock:
                now = time.time()

                # Check timeout
                if now - start_time > timeout:
                    logger.warning("Rate limiter timeout - could not acquire token")
                    return False

                # Refill tokens based on elapsed time
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                self.last_refill = now

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    print(f"[RATE] Token acquired. Bucket: {self.tokens:.1f}/{self.capacity}")
                    return True

                # Calculate wait time for next token
                wait_time = (1.0 - self.tokens) / self.refill_rate

            # Wait outside the lock
            print(f"[RATE] Waiting {wait_time:.1f}s... Bucket: {self.tokens:.1f}/{self.capacity}")
            time.sleep(min(wait_time, 1.0))  # Sleep in small increments


# Global rate limiter instance for Gemini (15 RPM free tier)
gemini_rate_limiter = TokenBucket(tokens_per_minute=15)

# Global rate limiter for Gemini 2.0 Flash Lite (Conservative 10 RPM -> 5 RPM due to heavy throttling)
gemini_flash_lite_limiter = TokenBucket(tokens_per_minute=5)

# Global rate limiter instance for Groq (30 RPM free tier)
groq_rate_limiter = TokenBucket(tokens_per_minute=30)
