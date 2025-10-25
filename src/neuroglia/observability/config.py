"""
OpenTelemetry Configuration Module

Handles initialization and configuration of OpenTelemetry SDK components including
TracerProvider, MeterProvider, and automatic instrumentation.
"""

import logging
import os
import socket
from dataclasses import dataclass, field
from typing import Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import (
    SERVICE_INSTANCE_ID,
    SERVICE_NAME,
    SERVICE_VERSION,
    Resource,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

log = logging.getLogger(__name__)


@dataclass
class OpenTelemetryConfig:
    """Configuration for OpenTelemetry SDK initialization"""

    # Service identification
    service_name: str = field(default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "unknown-service"))
    service_version: str = field(default_factory=lambda: os.getenv("OTEL_SERVICE_VERSION", "0.0.0"))
    service_instance_id: Optional[str] = field(default_factory=lambda: os.getenv("HOSTNAME", socket.gethostname()))
    deployment_environment: str = field(default_factory=lambda: os.getenv("DEPLOYMENT_ENVIRONMENT", "development"))

    # OTLP Exporter configuration
    otlp_endpoint: str = field(default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))
    otlp_protocol: str = field(default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc"))
    otlp_timeout: int = 10  # seconds

    # Export configuration
    enable_console_export: bool = field(default_factory=lambda: os.getenv("OTEL_ENABLE_CONSOLE_EXPORT", "false").lower() == "true")
    enable_otlp_export: bool = field(default_factory=lambda: os.getenv("OTEL_TRACES_EXPORTER", "otlp").lower() == "otlp")

    # Batch processing configuration
    batch_span_processor_max_queue_size: int = 2048
    batch_span_processor_schedule_delay_millis: int = 5000
    batch_span_processor_max_export_batch_size: int = 512

    # Metrics configuration
    metric_export_interval_millis: int = 60000  # 1 minute
    metric_export_timeout_millis: int = 30000  # 30 seconds

    # Instrumentation flags
    enable_fastapi_instrumentation: bool = True
    enable_httpx_instrumentation: bool = True
    enable_logging_instrumentation: bool = True
    enable_system_metrics: bool = True

    # Additional resource attributes
    additional_resource_attributes: dict = field(default_factory=dict)


# Global tracer provider reference
_tracer_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None
_config: Optional[OpenTelemetryConfig] = None


def configure_opentelemetry(service_name: Optional[str] = None, service_version: Optional[str] = None, otlp_endpoint: Optional[str] = None, enable_console_export: bool = False, config: Optional[OpenTelemetryConfig] = None, **kwargs) -> OpenTelemetryConfig:
    """
    Configure and initialize OpenTelemetry SDK with tracing, metrics, and logging.

    Args:
        service_name: Name of the service (overrides config or env var)
        service_version: Version of the service (overrides config or env var)
        otlp_endpoint: OTLP collector endpoint (overrides config or env var)
        enable_console_export: Enable console exporters for debugging
        config: Pre-configured OpenTelemetryConfig instance
        **kwargs: Additional configuration parameters

    Returns:
        OpenTelemetryConfig: The configuration used for initialization

    Example:
        >>> configure_opentelemetry(
        ...     service_name="mario-pizzeria",
        ...     service_version="1.0.0",
        ...     otlp_endpoint="http://otel-collector:4317"
        ... )
    """
    global _tracer_provider, _meter_provider, _config

    # Create or update configuration
    if config is None:
        config = OpenTelemetryConfig(**kwargs)

    # Override with explicit parameters
    if service_name:
        config.service_name = service_name
    if service_version:
        config.service_version = service_version
    if otlp_endpoint:
        config.otlp_endpoint = otlp_endpoint
    if enable_console_export:
        config.enable_console_export = True

    _config = config

    # Create resource with service information
    resource = Resource.create(
        {
            SERVICE_NAME: config.service_name,
            SERVICE_VERSION: config.service_version,
            SERVICE_INSTANCE_ID: config.service_instance_id,
            "deployment.environment": config.deployment_environment,
            **config.additional_resource_attributes,
        }
    )

    # Configure Tracing
    _tracer_provider = TracerProvider(resource=resource)

    # Add OTLP span exporter
    if config.enable_otlp_export:
        try:
            otlp_span_exporter = OTLPSpanExporter(
                endpoint=config.otlp_endpoint,
                timeout=config.otlp_timeout,
            )
            _tracer_provider.add_span_processor(
                BatchSpanProcessor(
                    otlp_span_exporter,
                    max_queue_size=config.batch_span_processor_max_queue_size,
                    schedule_delay_millis=config.batch_span_processor_schedule_delay_millis,
                    max_export_batch_size=config.batch_span_processor_max_export_batch_size,
                )
            )
            log.info(f"✅ OTLP Span Exporter configured: {config.otlp_endpoint}")
        except Exception as ex:
            log.error(f"❌ Failed to configure OTLP Span Exporter: {ex}")

    # Add console exporter for debugging
    if config.enable_console_export:
        _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        log.info("✅ Console Span Exporter enabled (debugging)")

    # Set global tracer provider
    trace.set_tracer_provider(_tracer_provider)

    # Configure Metrics
    metric_readers = []

    # Add OTLP metric exporter
    if config.enable_otlp_export:
        try:
            otlp_metric_exporter = OTLPMetricExporter(
                endpoint=config.otlp_endpoint,
                timeout=config.otlp_timeout,
            )
            metric_readers.append(
                PeriodicExportingMetricReader(
                    otlp_metric_exporter,
                    export_interval_millis=config.metric_export_interval_millis,
                    export_timeout_millis=config.metric_export_timeout_millis,
                )
            )
            log.info(f"✅ OTLP Metric Exporter configured: {config.otlp_endpoint}")
        except Exception as ex:
            log.error(f"❌ Failed to configure OTLP Metric Exporter: {ex}")

    # Add console metric exporter for debugging
    if config.enable_console_export:
        metric_readers.append(PeriodicExportingMetricReader(ConsoleMetricExporter()))
        log.info("✅ Console Metric Exporter enabled (debugging)")

    # Add Prometheus metric reader if available
    try:
        from neuroglia.observability.metrics import create_prometheus_metrics_reader

        prometheus_reader = create_prometheus_metrics_reader()
        if prometheus_reader:
            metric_readers.append(prometheus_reader)
            log.info("✅ Prometheus Metric Reader configured")
    except ImportError:
        log.debug("Prometheus metrics not available - skipping")
    except Exception as ex:
        log.warning(f"⚠️ Failed to configure Prometheus metrics: {ex}")

    _meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
    metrics.set_meter_provider(_meter_provider)

    # Configure automatic instrumentation
    if config.enable_logging_instrumentation:
        try:
            LoggingInstrumentor().instrument(set_logging_format=True)
            log.info("✅ Logging instrumentation enabled")
        except Exception as ex:
            log.warning(f"⚠️ Failed to enable logging instrumentation: {ex}")

    if config.enable_httpx_instrumentation:
        try:
            HTTPXClientInstrumentor().instrument()
            log.info("✅ HTTPX instrumentation enabled")
        except Exception as ex:
            log.warning(f"⚠️ Failed to enable HTTPX instrumentation: {ex}")

    if config.enable_system_metrics:
        try:
            SystemMetricsInstrumentor().instrument()
            log.info("✅ System metrics instrumentation enabled")
        except Exception as ex:
            log.warning(f"⚠️ Failed to enable system metrics: {ex}")

    log.info(f"🔭 OpenTelemetry initialized for service '{config.service_name}' v{config.service_version}")

    return config


def shutdown_opentelemetry():
    """
    Gracefully shutdown OpenTelemetry SDK, flushing remaining telemetry.
    Should be called during application shutdown.
    """
    global _tracer_provider, _meter_provider

    if _tracer_provider:
        try:
            _tracer_provider.shutdown()
            log.info("✅ TracerProvider shutdown complete")
        except Exception as ex:
            log.error(f"❌ Error shutting down TracerProvider: {ex}")

    if _meter_provider:
        try:
            _meter_provider.shutdown()
            log.info("✅ MeterProvider shutdown complete")
        except Exception as ex:
            log.error(f"❌ Error shutting down MeterProvider: {ex}")


def get_config() -> Optional[OpenTelemetryConfig]:
    """Get the current OpenTelemetry configuration"""
    return _config


def is_configured() -> bool:
    """Check if OpenTelemetry has been configured"""
    return _tracer_provider is not None and _meter_provider is not None


def instrument_fastapi_app(app, app_name: Optional[str] = None):
    """
    Instrument a FastAPI application with OpenTelemetry.

    This enables automatic HTTP request/response instrumentation including:
    - Request duration metrics
    - HTTP status code tracking
    - Endpoint-level metrics
    - Distributed tracing spans

    Args:
        app: FastAPI application instance
        app_name: Optional name for the instrumented app (for multi-app scenarios)
    """
    global _config

    if not _config or not _config.enable_fastapi_instrumentation:
        log.warning("⚠️ FastAPI instrumentation not enabled in config")
        return

    try:
        # Check if app is already instrumented to avoid double instrumentation
        if hasattr(app, "_is_otel_instrumented"):
            log.info(f"📊 FastAPI app '{app_name or 'unknown'}' already instrumented")
            return

        # Apply FastAPI instrumentation
        FastAPIInstrumentor.instrument_app(app)

        # Mark app as instrumented
        app._is_otel_instrumented = True

        log.info(f"📊 FastAPI app '{app_name or 'default'}' instrumented for HTTP metrics")

    except Exception as ex:
        log.error(f"❌ Failed to instrument FastAPI app '{app_name}': {ex}")
