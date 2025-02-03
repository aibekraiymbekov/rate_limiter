from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass
import threading
import time
from collections import defaultdict
from typing import Dict, List, Tuple

class Provider(str, Enum):
    CONNEXPAY = "connexpay"
    QOLO = "qolo"

class RateLimitConfig(BaseModel):
    rate_limit: int = Field(gt=0, description="Maximum number of requests allowed")
    time_window: int = Field(gt=0, description="Time window in seconds")

DEFAULT_PROVIDER_CONFIGS = {
    Provider.CONNEXPAY: RateLimitConfig(rate_limit=5, time_window=30),
    Provider.QOLO: RateLimitConfig(rate_limit=200, time_window=60)
}

@dataclass
class RequestWindow:
    timestamps: List[float]
    window_start: float

class ProviderRateLimiter:
    def __init__(self, config: RateLimitConfig):
        self.rate_limit = config.rate_limit
        self.time_window = config.time_window
        self.requests: Dict[str, RequestWindow] = defaultdict(
            lambda: RequestWindow(timestamps=[], window_start=time.time())
        )
        self.lock = threading.Lock()

    def _cleanup_old_requests(self, token: str, current_time: float) -> None:
        window = self.requests[token]
        if current_time - window.window_start > self.time_window:
            window.timestamps = []
            window.window_start = current_time
        else:
            window.timestamps = [
                ts for ts in window.timestamps
                if current_time - ts <= self.time_window
            ]

    def check_rate_limit(self, token: str, increment: bool = True) -> Tuple[bool, Dict[str, str]]:
        with self.lock:
            current_time = time.time()
            self._cleanup_old_requests(token, current_time)

            window = self.requests[token]
            current_requests = len(window.timestamps)

            is_limited = current_requests >= self.rate_limit

            if increment and not is_limited:
                window.timestamps.append(current_time)
                current_requests += 1

            reset_time = int(self.time_window - (current_time - window.window_start))
            remaining = max(self.rate_limit - current_requests, 0)

            headers = {
                "X-RateLimit-Limit": str(self.rate_limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time)
            }

            return current_requests >= self.rate_limit, headers

class RateLimiterRegistry:
    def __init__(self):
        self.provider_limiters: Dict[Provider, ProviderRateLimiter] = {}
        self.lock = threading.Lock()

    def get_limiter(self, provider: Provider) -> ProviderRateLimiter:
        with self.lock:
            if provider not in self.provider_limiters:
                config = DEFAULT_PROVIDER_CONFIGS[provider]
                self.provider_limiters[provider] = ProviderRateLimiter(config)
            return self.provider_limiters[provider]

    def update_config(self, provider: Provider, config: RateLimitConfig) -> None:
        with self.lock:
            self.provider_limiters[provider] = ProviderRateLimiter(config)