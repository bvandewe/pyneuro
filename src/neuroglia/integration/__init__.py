"""
Integration patterns and models for Neuroglia.

Provides integration events, cache repositories, HTTP service clients, and external service patterns.
"""

from .models import IntegrationEvent

# Cache repository imports - optional dependencies
try:
    from .cache_repository import (
        AsyncCacheRepository,
        AsyncHashCacheRepository,
        CacheRepositoryOptions,
        CacheClientPool,
        CacheRepositoryException,
    )

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    AsyncCacheRepository = None
    AsyncHashCacheRepository = None
    CacheRepositoryOptions = None
    CacheClientPool = None
    CacheRepositoryException = None

# HTTP service client imports - httpx dependency
try:
    from .http_service_client import (
        HttpServiceClient,
        HttpServiceClientException,
        HttpRequestOptions,
        HttpResponse,
        RetryPolicy,
        CircuitBreakerState,
        CircuitBreakerStats,
        RequestInterceptor,
        ResponseInterceptor,
        BearerTokenInterceptor,
        LoggingInterceptor,
        HttpServiceClientBuilder,
        create_authenticated_client,
        create_logging_client,
    )

    HTTP_CLIENT_AVAILABLE = True
except ImportError:
    HTTP_CLIENT_AVAILABLE = False
    HttpServiceClient = None
    HttpServiceClientException = None
    HttpRequestOptions = None
    HttpResponse = None
    RetryPolicy = None
    CircuitBreakerState = None
    CircuitBreakerStats = None
    RequestInterceptor = None
    ResponseInterceptor = None
    BearerTokenInterceptor = None
    LoggingInterceptor = None
    HttpServiceClientBuilder = None
    create_authenticated_client = None
    create_logging_client = None

__all__ = [
    "IntegrationEvent",
    # Cache repositories (when available)
    "AsyncCacheRepository",
    "AsyncHashCacheRepository",
    "CacheRepositoryOptions",
    "CacheClientPool",
    "CacheRepositoryException",
    "CACHE_AVAILABLE",
    # HTTP service client (when available)
    "HttpServiceClient",
    "HttpServiceClientException",
    "HttpRequestOptions",
    "HttpResponse",
    "RetryPolicy",
    "CircuitBreakerState",
    "CircuitBreakerStats",
    "RequestInterceptor",
    "ResponseInterceptor",
    "BearerTokenInterceptor",
    "LoggingInterceptor",
    "HttpServiceClientBuilder",
    "create_authenticated_client",
    "create_logging_client",
    "HTTP_CLIENT_AVAILABLE",
]
