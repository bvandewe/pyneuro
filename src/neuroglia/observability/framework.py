"""
Observability framework integration for the Neuroglia framework.

This module provides the main Observability class that follows the framework's
.configure(builder) pattern and integrates with ApplicationSettings to provide
comprehensive observability with minimal configuration.
"""

import datetime
import logging
from typing import TYPE_CHECKING

from fastapi import FastAPI, Response

if TYPE_CHECKING:
    from neuroglia.hosting.web import WebApplicationBuilder

from neuroglia.observability.settings import (
    ObservabilityConfig,
    ObservabilitySettingsMixin,
)

log = logging.getLogger(__name__)


class Observability:
    """
    Observability service configurator following Neuroglia framework patterns.

    Provides comprehensive observability setup with the three pillars:
    - Metrics: OpenTelemetry metrics with Prometheus export
    - Tracing: Distributed tracing with OTLP export
    - Logging: Structured logging with trace correlation

    Usage:
        builder = WebApplicationBuilder(app_settings)
        Observability.configure(builder)  # Uses settings from app_settings

        # Optional overrides
        Observability.configure(builder,
            tracing_enabled=False,
            health_checks=['mongodb']
        )
    """

    @classmethod
    def configure(cls, builder: "WebApplicationBuilder", **overrides) -> None:
        """
        Configure comprehensive observability for the application.

        Args:
            builder: The enhanced web application builder (must contain app_settings)
            **overrides: Optional configuration overrides (tracing_enabled=False, etc.)
        """
        app_settings = builder.app_settings

        # Check if app_settings has observability configuration
        if not cls._has_observability_settings(app_settings):
            raise ValueError("Observability configuration not found in app_settings. " "Please inherit from ApplicationSettingsWithObservability or mix in ObservabilitySettingsMixin. " f"Current settings type: {type(app_settings)}")

        # Create observability configuration from app_settings
        config = ObservabilityConfig(app_settings, **overrides)

        # Register configuration in DI container for access throughout application
        builder.services.add_singleton(ObservabilityConfig, lambda: config)

        # Configure OpenTelemetry if any pillar is enabled
        if config.is_any_pillar_enabled() and config.otel_enabled:
            cls._configure_opentelemetry(builder, config)

        # Configure tracing pipeline behavior if tracing is enabled
        if config.tracing_enabled:
            try:
                from neuroglia.mediation.tracing_middleware import (
                    TracingPipelineBehavior,
                )

                TracingPipelineBehavior.configure(builder)
                log.info("🔍 Tracing pipeline behavior configured")
            except ImportError:
                log.warning("⚠️ TracingPipelineBehavior not available - tracing middleware skipped")

        # Register standard endpoints for automatic addition during app build
        if config.is_any_endpoint_enabled():
            cls._register_standard_endpoints(builder, config)

        log.info(f"🔭 Observability configured for '{config.service_name}' " f"[Metrics: {'✓' if config.metrics_enabled else '✗'}, " f"Tracing: {'✓' if config.tracing_enabled else '✗'}, " f"Logging: {'✓' if config.logging_enabled else '✗'}]")

    @classmethod
    def _has_observability_settings(cls, settings) -> bool:
        """Check if settings object has observability configuration"""
        return isinstance(settings, ObservabilitySettingsMixin) or hasattr(settings, "observability_enabled")

    @classmethod
    def _configure_opentelemetry(cls, builder: "WebApplicationBuilder", config: ObservabilityConfig) -> None:
        """Configure OpenTelemetry SDK based on enabled pillars"""
        try:
            from neuroglia.observability.otel_sdk import configure_opentelemetry

            # Build OpenTelemetry configuration from observability config
            otel_config = {
                "service_name": config.service_name,
                "service_version": config.service_version,
                "otlp_endpoint": config.otel_endpoint,
                "enable_console_export": config.otel_console_export,
                "deployment_environment": config.deployment_environment,
                "additional_resource_attributes": config.resource_attributes,
                # Pillar controls
                "enable_fastapi_instrumentation": config.tracing_enabled and config.instrument_fastapi,
                "enable_httpx_instrumentation": config.tracing_enabled and config.instrument_httpx,
                "enable_logging_instrumentation": config.logging_enabled and config.instrument_logging,
                "enable_system_metrics": config.metrics_enabled and config.instrument_system_metrics,
                # Batch processing
                "batch_span_processor_max_queue_size": config.batch_max_queue_size,
                "batch_span_processor_schedule_delay_millis": config.batch_schedule_delay_ms,
                "batch_span_processor_max_export_batch_size": config.batch_max_export_size,
                # Metrics
                "metric_export_interval_millis": config.metrics_interval_ms,
                "metric_export_timeout_millis": config.metrics_timeout_ms,
            }

            # Configure OpenTelemetry with our settings
            configure_opentelemetry(**otel_config)

            log.info(f"🔭 OpenTelemetry configured: endpoint={config.otel_endpoint}")

        except ImportError as e:
            log.error(f"❌ OpenTelemetry configuration failed - missing dependencies: {e}")
        except Exception as e:
            log.error(f"❌ OpenTelemetry configuration error: {e}")

    @classmethod
    def _register_standard_endpoints(cls, builder: "WebApplicationBuilder", config: ObservabilityConfig) -> None:
        """Register standard endpoints for automatic addition to main app during build"""

        # Store configuration for later use during app building
        builder._observability_config = config

        log.info(f"📊 Standard endpoints registered: " f"health={config.health_path if config.health_endpoint else 'disabled'}, " f"metrics={config.metrics_path if config.metrics_endpoint else 'disabled'}, " f"ready={config.ready_path if config.ready_endpoint else 'disabled'}")


class StandardEndpoints:
    """Standard observability endpoints implementation"""

    @staticmethod
    def add_health_endpoint(app: FastAPI, config: ObservabilityConfig) -> None:
        """Add health check endpoint with dependency monitoring"""

        @app.get(config.health_path, include_in_schema=False, tags=["observability"])
        async def health_check():
            """
            Health check endpoint with dependency status.

            Returns overall service health and status of configured dependencies.
            """
            health_status = {"status": "healthy", "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(), "service": {"name": config.service_name, "version": config.service_version, "environment": config.deployment_environment}}

            # Add dependency checks if configured
            if config.health_checks:
                dependencies = {}
                overall_healthy = True

                for dependency in config.health_checks:
                    # TODO: Implement pluggable health check providers
                    # For now, assume dependencies are healthy
                    dependency_status = await StandardEndpoints._check_dependency_health(dependency)
                    dependencies[dependency] = dependency_status

                    if dependency_status != "healthy":
                        overall_healthy = False

                health_status["dependencies"] = dependencies
                if not overall_healthy:
                    health_status["status"] = "degraded"

            return health_status

    @staticmethod
    def add_ready_endpoint(app: FastAPI, config: ObservabilityConfig) -> None:
        """Add readiness probe endpoint for Kubernetes"""

        @app.get(config.ready_path, include_in_schema=False, tags=["observability"])
        async def readiness_check():
            """
            Readiness probe endpoint for Kubernetes.

            Indicates whether the service is ready to accept traffic.
            """
            ready_status = {"ready": True, "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(), "service": config.service_name}

            # Add basic readiness checks
            checks = {"application": "ready"}

            # TODO: Add pluggable readiness checks
            if config.health_checks:
                for dependency in config.health_checks:
                    checks[dependency] = "ready"  # Placeholder

            ready_status["checks"] = checks
            return ready_status

    @staticmethod
    def add_metrics_endpoint(app: FastAPI, config: ObservabilityConfig) -> None:
        """Add Prometheus metrics endpoint"""

        try:
            from neuroglia.observability.metrics import add_metrics_endpoint

            # Use existing metrics endpoint implementation
            add_metrics_endpoint(app, config.metrics_path)

        except ImportError:
            log.warning("⚠️ Prometheus metrics endpoint not available - missing dependencies")

            # Fallback minimal metrics endpoint
            @app.get(config.metrics_path, include_in_schema=False)
            async def metrics_fallback():
                """Fallback metrics endpoint when Prometheus is not available"""
                return Response(content="# Prometheus metrics not available\n# Install prometheus-client for full metrics support\n", media_type="text/plain")

    @staticmethod
    async def _check_dependency_health(dependency_name: str) -> str:
        """
        Check health of a specific dependency.

        TODO: Implement pluggable health check providers for:
        - MongoDB (check connection)
        - Redis (ping)
        - Keycloak (check auth endpoint)
        - HTTP services (health endpoint check)
        - Database connections
        """
        # Placeholder implementation - always return healthy
        # In real implementation, this would check actual dependency status
        return "healthy"
