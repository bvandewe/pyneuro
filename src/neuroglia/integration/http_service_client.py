"""HTTP Service Client module for Neuroglia framework.

Provides comprehensive HTTP client capabilities with:
- Retry policies with exponential backoff
- Circuit breaker patterns
- Request/response interceptors
- Comprehensive error handling and logging
- Connection pooling and timeout management
- Authentication and header management
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable, TypeVar
from urllib.parse import urljoin
import json

try:
    import httpx

    HTTP_CLIENT_AVAILABLE = True
except ImportError:
    HTTP_CLIENT_AVAILABLE = False

# Type variables for request/response typing
TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class HttpServiceClientException(Exception):
    """Base exception for HTTP service client operations."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class CircuitBreakerState(Enum):
    """States for the circuit breaker pattern."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


class RetryPolicy(Enum):
    """Retry policy strategies."""

    NONE = "none"
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_DELAY = "linear_delay"


@dataclass
class HttpRequestOptions:
    """Configuration options for HTTP requests."""

    timeout: Optional[float] = 30.0
    max_retries: int = 3
    retry_policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF
    retry_delay: float = 1.0
    retry_multiplier: float = 2.0
    retry_max_delay: float = 60.0
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    circuit_breaker_success_threshold: int = 3
    headers: Dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True
    follow_redirects: bool = True


@dataclass
class HttpResponse:
    """Standardized HTTP response wrapper."""

    status_code: int
    content: bytes
    headers: Dict[str, str]
    request_url: str
    elapsed_time: float
    success: bool = field(init=False)

    def __post_init__(self):
        self.success = 200 <= self.status_code < 300

    def json(self) -> Any:
        """Parse response content as JSON."""
        try:
            return json.loads(self.content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise HttpServiceClientException(f"Failed to parse JSON response: {e}")

    def text(self) -> str:
        """Get response content as text."""
        try:
            return self.content.decode("utf-8")
        except UnicodeDecodeError as e:
            raise HttpServiceClientException(f"Failed to decode response text: {e}")


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""

    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    total_requests: int = 0
    total_failures: int = 0


class RequestInterceptor(ABC):
    """Abstract base class for request interceptors."""

    @abstractmethod
    async def intercept_request(self, request: httpx.Request) -> httpx.Request:
        """Intercept and potentially modify outgoing requests."""
        pass


class ResponseInterceptor(ABC):
    """Abstract base class for response interceptors."""

    @abstractmethod
    async def intercept_response(self, response: HttpResponse) -> HttpResponse:
        """Intercept and potentially modify incoming responses."""
        pass


class BearerTokenInterceptor(RequestInterceptor):
    """Request interceptor for Bearer token authentication."""

    def __init__(self, token_provider: Callable[[], Awaitable[str]]):
        self.token_provider = token_provider

    async def intercept_request(self, request: httpx.Request) -> httpx.Request:
        """Add Bearer token to Authorization header."""
        try:
            token = await self.token_provider()
            request.headers["Authorization"] = f"Bearer {token}"
        except Exception as e:
            logging.warning(f"Failed to add Bearer token: {e}")
        return request


class LoggingInterceptor(ResponseInterceptor):
    """Response interceptor for request/response logging."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    async def intercept_response(self, response: HttpResponse) -> HttpResponse:
        """Log response details."""
        self.logger.info(
            f"HTTP {response.status_code} {response.request_url} " f"({response.elapsed_time:.3f}s)"
        )
        if not response.success:
            self.logger.warning(f"HTTP request failed: {response.text()[:200]}")
        return response


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""

    def __init__(self, options: HttpRequestOptions):
        self.options = options
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    async def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        async with self._lock:
            if self.stats.state == CircuitBreakerState.CLOSED:
                return True

            if self.stats.state == CircuitBreakerState.OPEN:
                # Check if timeout has passed
                if (
                    self.stats.last_failure_time
                    and datetime.now() - self.stats.last_failure_time
                    > timedelta(seconds=self.options.circuit_breaker_timeout)
                ):
                    self.stats.state = CircuitBreakerState.HALF_OPEN
                    self.stats.success_count = 0
                    return True
                return False

            # HALF_OPEN state
            return True

    async def record_success(self):
        """Record a successful execution."""
        async with self._lock:
            self.stats.success_count += 1
            self.stats.last_success_time = datetime.now()
            self.stats.total_requests += 1

            if self.stats.state == CircuitBreakerState.HALF_OPEN:
                if self.stats.success_count >= self.options.circuit_breaker_success_threshold:
                    self.stats.state = CircuitBreakerState.CLOSED
                    self.stats.failure_count = 0

    async def record_failure(self):
        """Record a failed execution."""
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.total_failures += 1
            self.stats.total_requests += 1
            self.stats.last_failure_time = datetime.now()

            if (
                self.stats.state == CircuitBreakerState.CLOSED
                and self.stats.failure_count >= self.options.circuit_breaker_failure_threshold
            ):
                self.stats.state = CircuitBreakerState.OPEN
            elif self.stats.state == CircuitBreakerState.HALF_OPEN:
                self.stats.state = CircuitBreakerState.OPEN
                self.stats.failure_count = 0


class HttpServiceClient:
    """Comprehensive HTTP service client with advanced features."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        options: Optional[HttpRequestOptions] = None,
        request_interceptors: Optional[List[RequestInterceptor]] = None,
        response_interceptors: Optional[List[ResponseInterceptor]] = None,
    ):

        if not HTTP_CLIENT_AVAILABLE:
            raise HttpServiceClientException(
                "httpx is required for HTTP service client. Install it with:\n" " pip install httpx"
            )

        self.base_url = base_url or ""
        self.options = options or HttpRequestOptions()
        self.request_interceptors = request_interceptors or []
        self.response_interceptors = response_interceptors or []

        self._circuit_breaker = CircuitBreaker(self.options)
        self._logger = logging.getLogger(__name__)

        # Create httpx client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=self.options.timeout,
            verify=self.options.verify_ssl,
            follow_redirects=self.options.follow_redirects,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client and clean up resources."""
        if self._client:
            await self._client.aclose()

    def _build_url(self, endpoint: str) -> str:
        """Build complete URL from base URL and endpoint."""
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return urljoin(self.base_url, endpoint)

    async def _apply_request_interceptors(self, request: httpx.Request) -> httpx.Request:
        """Apply all registered request interceptors."""
        for interceptor in self.request_interceptors:
            request = await interceptor.intercept_request(request)
        return request

    async def _apply_response_interceptors(self, response: HttpResponse) -> HttpResponse:
        """Apply all registered response interceptors."""
        for interceptor in self.response_interceptors:
            response = await interceptor.intercept_response(response)
        return response

    async def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate delay before retry based on policy."""
        if self.options.retry_policy == RetryPolicy.NONE:
            return 0.0
        elif self.options.retry_policy == RetryPolicy.FIXED_DELAY:
            return self.options.retry_delay
        elif self.options.retry_policy == RetryPolicy.LINEAR_DELAY:
            return self.options.retry_delay * attempt
        elif self.options.retry_policy == RetryPolicy.EXPONENTIAL_BACKOFF:
            delay = self.options.retry_delay * (self.options.retry_multiplier ** (attempt - 1))
            return min(delay, self.options.retry_max_delay)

        return self.options.retry_delay

    async def _should_retry(self, response: HttpResponse, attempt: int) -> bool:
        """Determine if request should be retried."""
        if attempt >= self.options.max_retries:
            return False

        # Retry on 5xx server errors and specific 4xx errors
        return response.status_code >= 500 or response.status_code in [408, 429, 502, 503, 504]

    async def _execute_request(self, method: str, url: str, **kwargs) -> HttpResponse:
        """Execute HTTP request with retry and circuit breaker logic."""

        # Check circuit breaker
        if not await self._circuit_breaker.can_execute():
            raise HttpServiceClientException(
                "Circuit breaker is OPEN - requests are being rejected", status_code=503
            )

        full_url = self._build_url(url)
        last_exception = None

        for attempt in range(1, self.options.max_retries + 1):
            try:
                start_time = datetime.now()

                # Merge default headers with request-specific headers
                headers = {**self.options.headers, **kwargs.get("headers", {})}
                kwargs["headers"] = headers

                # Create request
                request = self._client.build_request(method, full_url, **kwargs)

                # Apply request interceptors
                request = await self._apply_request_interceptors(request)

                # Execute request
                response = await self._client.send(request)
                elapsed = (datetime.now() - start_time).total_seconds()

                # Create standardized response
                http_response = HttpResponse(
                    status_code=response.status_code,
                    content=response.content,
                    headers=dict(response.headers),
                    request_url=str(response.url),
                    elapsed_time=elapsed,
                )

                # Apply response interceptors
                http_response = await self._apply_response_interceptors(http_response)

                # Check if we should retry
                if not http_response.success and await self._should_retry(http_response, attempt):
                    self._logger.warning(
                        f"Request failed (attempt {attempt}/{self.options.max_retries}): "
                        f"{http_response.status_code} {full_url}"
                    )

                    if attempt < self.options.max_retries:
                        delay = await self._calculate_retry_delay(attempt)
                        await asyncio.sleep(delay)
                        continue

                # Record success or failure in circuit breaker
                if http_response.success:
                    await self._circuit_breaker.record_success()
                else:
                    await self._circuit_breaker.record_failure()

                return http_response

            except httpx.RequestError as e:
                last_exception = e
                self._logger.warning(f"Request error (attempt {attempt}): {e}")

                if attempt < self.options.max_retries:
                    delay = await self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                    continue

            except Exception as e:
                await self._circuit_breaker.record_failure()
                raise HttpServiceClientException(f"Unexpected error during HTTP request: {e}")

        # All retries exhausted
        await self._circuit_breaker.record_failure()

        if last_exception:
            raise HttpServiceClientException(
                f"Request failed after {self.options.max_retries} attempts: {last_exception}"
            )

        # This shouldn't happen, but just in case
        raise HttpServiceClientException("Request failed for unknown reason")

    # HTTP method implementations
    async def get(
        self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs
    ) -> HttpResponse:
        """Execute GET request."""
        return await self._execute_request("GET", url, params=params, **kwargs)

    async def post(
        self, url: str, data: Optional[Any] = None, json: Optional[Any] = None, **kwargs
    ) -> HttpResponse:
        """Execute POST request."""
        return await self._execute_request("POST", url, data=data, json=json, **kwargs)

    async def put(
        self, url: str, data: Optional[Any] = None, json: Optional[Any] = None, **kwargs
    ) -> HttpResponse:
        """Execute PUT request."""
        return await self._execute_request("PUT", url, data=data, json=json, **kwargs)

    async def patch(
        self, url: str, data: Optional[Any] = None, json: Optional[Any] = None, **kwargs
    ) -> HttpResponse:
        """Execute PATCH request."""
        return await self._execute_request("PATCH", url, data=data, json=json, **kwargs)

    async def delete(self, url: str, **kwargs) -> HttpResponse:
        """Execute DELETE request."""
        return await self._execute_request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs) -> HttpResponse:
        """Execute HEAD request."""
        return await self._execute_request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs) -> HttpResponse:
        """Execute OPTIONS request."""
        return await self._execute_request("OPTIONS", url, **kwargs)

    # Convenience methods for typed requests/responses
    async def get_json(self, url: str, response_type: type = dict, **kwargs) -> Any:
        """Execute GET request and parse JSON response."""
        response = await self.get(url, **kwargs)
        if not response.success:
            raise HttpServiceClientException(
                f"GET request failed: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text(),
            )
        return response.json()

    async def post_json(self, url: str, data: Any, response_type: type = dict, **kwargs) -> Any:
        """Execute POST request with JSON data and parse JSON response."""
        response = await self.post(url, json=data, **kwargs)
        if not response.success:
            raise HttpServiceClientException(
                f"POST request failed: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text(),
            )
        return response.json()

    # Circuit breaker monitoring
    def get_circuit_breaker_stats(self) -> CircuitBreakerStats:
        """Get current circuit breaker statistics."""
        return self._circuit_breaker.stats

    async def reset_circuit_breaker(self):
        """Reset circuit breaker to closed state."""
        async with self._circuit_breaker._lock:
            self._circuit_breaker.stats = CircuitBreakerStats()


# Service registration and configuration
class HttpServiceClientBuilder:
    """Builder class for configuring HTTP service clients."""

    @staticmethod
    def configure(
        builder, base_url: Optional[str] = None, options: Optional[HttpRequestOptions] = None
    ):
        """Configure HTTP service client in the DI container."""

        if not HTTP_CLIENT_AVAILABLE:
            raise HttpServiceClientException(
                "httpx is required for HTTP service client. Install it with:\n" " pip install httpx"
            )

        # Register HttpServiceClient as a scoped service
        def create_http_client(sp) -> HttpServiceClient:
            return HttpServiceClient(base_url=base_url, options=options or HttpRequestOptions())

        builder.services.add_scoped(HttpServiceClient, factory=create_http_client)

        return builder


# Utility functions for common scenarios
def create_authenticated_client(
    base_url: str,
    token_provider: Callable[[], Awaitable[str]],
    options: Optional[HttpRequestOptions] = None,
) -> HttpServiceClient:
    """Create HTTP client with Bearer token authentication."""
    request_interceptors = [BearerTokenInterceptor(token_provider)]
    response_interceptors = [LoggingInterceptor()]

    return HttpServiceClient(
        base_url=base_url,
        options=options or HttpRequestOptions(),
        request_interceptors=request_interceptors,
        response_interceptors=response_interceptors,
    )


def create_logging_client(
    base_url: str,
    logger: Optional[logging.Logger] = None,
    options: Optional[HttpRequestOptions] = None,
) -> HttpServiceClient:
    """Create HTTP client with response logging."""
    response_interceptors = [LoggingInterceptor(logger)]

    return HttpServiceClient(
        base_url=base_url,
        options=options or HttpRequestOptions(),
        response_interceptors=response_interceptors,
    )
