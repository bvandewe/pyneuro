# 🔭 Observability with OpenTelemetry

_Estimated reading time: 15 minutes_

## 🎯 What & Why

**Observability** is the ability to understand what's happening inside your application by examining its outputs. The Neuroglia framework provides comprehensive observability through **OpenTelemetry integration**, supporting the three pillars:

1. **Metrics** - What's happening (counters, gauges, histograms)
2. **Tracing** - Where requests flow (distributed traces across services)
3. **Logging** - Why things happened (structured logs with trace correlation)

### The Problem Without Observability

```python
# ❌ Without observability - debugging is painful
@app.post("/orders")
async def create_order(data: dict):
    # Why is this slow?
    # Which service failed?
    # How many orders per minute?
    # What's the error rate?
    order = await order_service.create(data)
    return order
```

### The Solution With Observability

```python
# ✅ With observability - full visibility
from neuroglia.observability import Observability

builder = WebApplicationBuilder(app_settings)
Observability.configure(builder)  # Automatic instrumentation!

# Now you get:
# - Automatic request tracing
# - Response time metrics
# - Correlated logs with trace IDs
# - Service dependency maps
# - Error rate tracking
# - System metrics (CPU, memory)
```

## 🚀 Getting Started

### Framework-Style Configuration (Recommended)

The easiest way to enable observability is through `WebApplicationBuilder`:

```python
from neuroglia.hosting.web import WebApplicationBuilder
from neuroglia.observability import Observability, ApplicationSettingsWithObservability

# Step 1: Use settings class with observability
class PizzeriaSettings(ApplicationSettingsWithObservability):
    # Your app settings
    database_url: str = Field(default="mongodb://localhost:27017")

    # Observability settings inherited:
    # - service_name, service_version, deployment_environment
    # - otel_enabled, otel_endpoint, tracing_enabled, metrics_enabled
    # - instrument_fastapi, instrument_httpx, instrument_logging

# Step 2: Configure observability
builder = WebApplicationBuilder(PizzeriaSettings())
Observability.configure(builder)  # Uses settings automatically

# Step 3: Build and run
app = builder.build()
app.run()

# 🎉 You now have:
# - /metrics endpoint with Prometheus metrics
# - /health endpoint with service health
# - Distributed tracing to OTLP collector
# - Structured logs with trace correlation
```

### Manual Configuration (Advanced)

For fine-grained control:

```python
from neuroglia.observability import configure_opentelemetry

# Configure OpenTelemetry directly
configure_opentelemetry(
    service_name="mario-pizzeria",
    service_version="1.0.0",
    otlp_endpoint="http://otel-collector:4317",
    enable_console_export=False,  # Set True for debugging
    deployment_environment="production",

    # Instrumentation toggles
    enable_fastapi_instrumentation=True,
    enable_httpx_instrumentation=True,
    enable_logging_instrumentation=True,
    enable_system_metrics=True,

    # Performance tuning
    batch_span_processor_max_queue_size=2048,
    batch_span_processor_schedule_delay_millis=5000,
    metric_export_interval_millis=60000  # 1 minute
)
```

## 🏗️ Core Components

### 1. Observability Framework Integration

The `Observability` class provides framework-integrated configuration:

```python
from neuroglia.observability import Observability

# Basic configuration
Observability.configure(builder)

# With overrides
Observability.configure(
    builder,
    tracing_enabled=True,      # Override from settings
    metrics_enabled=True,      # Override from settings
    logging_enabled=True       # Override from settings
)
```

**Key Features:**

- Reads configuration from `app_settings` (must inherit from `ObservabilitySettingsMixin`)
- Configures OpenTelemetry SDK based on enabled pillars
- Registers `/metrics` and `/health` endpoints automatically
- Applies tracing middleware to CQRS handlers

### 2. Distributed Tracing

Trace requests across service boundaries with automatic span creation:

```python
from neuroglia.observability import trace_async, get_tracer, add_span_attributes

# Automatic tracing with decorator
@trace_async(name="create_order")  # Custom span name
async def create_order(order_data: dict):
    # Span automatically created and closed

    # Add custom attributes
    add_span_attributes({
        "order.id": order_data["id"],
        "order.total": order_data["total"],
        "customer.type": "premium"
    })

    # Call other services - trace propagates automatically
    await payment_service.charge(order_data["total"])
    await inventory_service.reserve(order_data["items"])

    return order

# Manual tracing for fine control
tracer = get_tracer(__name__)

async def process_payment(amount: float):
    with tracer.start_as_current_span("payment_processing") as span:
        span.set_attribute("payment.amount", amount)

        # Add events for important moments
        from neuroglia.observability import add_span_event
        add_span_event("payment_validated", {
            "validation_result": "approved"
        })

        result = await payment_gateway.charge(amount)
        span.set_attribute("payment.transaction_id", result.transaction_id)

        return result
```

### 3. Metrics Collection

Create and record metrics for monitoring:

```python
from neuroglia.observability import get_meter, create_counter, create_histogram

# Get meter for your component
meter = get_meter(__name__)

# Create metrics
order_counter = create_counter(
    meter,
    name="orders_created_total",
    description="Total number of orders created",
    unit="orders"
)

order_value_histogram = create_histogram(
    meter,
    name="order_value",
    description="Distribution of order values",
    unit="USD"
)

# Record metrics
def record_order_created(order: Order):
    order_counter.add(1, {
        "order.type": order.order_type,
        "customer.segment": order.customer_segment
    })

    order_value_histogram.record(order.total_amount, {
        "order.type": order.order_type
    })
```

**Available Metric Types:**

- **Counter**: Monotonically increasing value (e.g., total requests)
- **UpDownCounter**: Can increase or decrease (e.g., active connections)
- **Histogram**: Distribution of values (e.g., request duration)
- **ObservableGauge**: Callback-based metric (e.g., queue size)

### 4. Structured Logging with Trace Correlation

Logs automatically include trace context:

```python
from neuroglia.observability import get_logger_with_trace_context, log_with_trace
import logging

# Get logger with automatic trace correlation
logger = get_logger_with_trace_context(__name__)

async def process_order(order_id: str):
    # Logs automatically include trace_id and span_id
    logger.info(f"Processing order: {order_id}")

    try:
        result = await order_service.process(order_id)
        logger.info(f"Order processed successfully: {order_id}")
        return result
    except Exception as e:
        # Exception automatically recorded in current span
        logger.error(f"Order processing failed: {order_id}", exc_info=True)

        # Record exception in span
        from neuroglia.observability import record_exception
        record_exception(e)
        raise

# Manual trace correlation
log_with_trace(
    logger.info,
    "Custom log message",
    extra_attributes={"custom.field": "value"}
)
```

## 💡 Real-World Example: Mario's Pizzeria

Complete observability setup for Mario's Pizzeria:

```python
# settings.py
from neuroglia.observability import ApplicationSettingsWithObservability
from pydantic import Field

class PizzeriaSettings(ApplicationSettingsWithObservability):
    # Application settings
    database_url: str = Field(default="mongodb://localhost:27017")
    redis_url: str = Field(default="redis://localhost:6379")

    # Observability settings (inherited):
    # service_name: str = "mario-pizzeria"
    # service_version: str = "1.0.0"
    # otel_enabled: bool = True
    # otel_endpoint: str = "http://otel-collector:4317"
    # tracing_enabled: bool = True
    # metrics_enabled: bool = True
    # logging_enabled: bool = True

# main.py
from neuroglia.hosting.web import WebApplicationBuilder
from neuroglia.observability import Observability

def create_app():
    # Load settings from environment
    settings = PizzeriaSettings()

    # Create builder with observability-enabled settings
    builder = WebApplicationBuilder(settings)

    # Register application services
    services = builder.services
    services.add_scoped(IOrderRepository, MongoOrderRepository)
    services.add_scoped(OrderService)
    services.add_mediator()

    # Configure observability (automatic!)
    Observability.configure(builder)

    # Register controllers
    builder.add_controllers(["api.controllers"], prefix="/api")

    # Build application
    app = builder.build_app_with_lifespan(
        title="Mario's Pizzeria API",
        version="1.0.0"
    )

    return app

# order_handler.py
from neuroglia.observability import trace_async, add_span_attributes, create_counter, get_meter
from neuroglia.mediation import CommandHandler

# Create metrics
meter = get_meter(__name__)
orders_created = create_counter(meter, "orders_created_total", "Total orders created")

class CreateOrderHandler(CommandHandler[CreateOrderCommand, OperationResult[OrderDto]]):
    def __init__(
        self,
        order_repository: IOrderRepository,
        payment_service: PaymentService,
        mapper: Mapper
    ):
        super().__init__()
        self.order_repository = order_repository
        self.payment_service = payment_service
        self.mapper = mapper

    @trace_async(name="create_order_handler")  # Automatic tracing
    async def handle_async(self, command: CreateOrderCommand) -> OperationResult[OrderDto]:
        # Add span attributes for filtering/analysis
        add_span_attributes({
            "order.customer_id": command.customer_id,
            "order.item_count": len(command.items),
            "order.total": command.total_amount
        })

        # Create order entity
        order = Order(
            customer_id=command.customer_id,
            items=command.items,
            total_amount=command.total_amount
        )

        # Process payment (automatically traced via httpx instrumentation)
        payment_result = await self.payment_service.charge(
            command.customer_id,
            command.total_amount
        )

        if not payment_result.success:
            return self.bad_request("Payment failed")

        # Save order (MongoDB operations automatically traced)
        await self.order_repository.save_async(order)

        # Record metric
        orders_created.add(1, {
            "customer.segment": "premium" if command.total_amount > 50 else "standard"
        })

        # Return result (logs automatically include trace_id)
        self.logger.info(f"Order created successfully: {order.id}")
        return self.created(self.mapper.map(order, OrderDto))

# Run the application
if __name__ == "__main__":
    import uvicorn
    app = create_app()

    # Uvicorn automatically instrumented via FastAPI instrumentation
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**What You Get:**

```bash
# Prometheus metrics at /metrics
curl http://localhost:8000/metrics

# Sample output:
# orders_created_total{customer_segment="premium"} 42
# orders_created_total{customer_segment="standard"} 158
# http_server_duration_milliseconds_bucket{http_route="/api/orders",http_method="POST",le="100"} 95
# http_server_active_requests{http_route="/api/orders"} 3

# Health check at /health
curl http://localhost:8000/health

# Sample output:
# {
#   "status": "healthy",
#   "service": "mario-pizzeria",
#   "version": "1.0.0",
#   "timestamp": "2024-01-15T10:30:00Z"
# }

# Traces exported to OTLP collector
# - View in Jaeger UI: http://localhost:16686
# - Each request shows full trace with:
#   - HTTP request span
#   - create_order_handler span
#   - Payment service call span
#   - MongoDB query spans
#   - Timing for each operation

# Logs with trace correlation
# [2024-01-15 10:30:00] INFO [trace_id=abc123 span_id=def456] Order created successfully: ord_789
```

## 🔧 Advanced Features

### 1. Custom Resource Attributes

Add metadata to all telemetry:

```python
from neuroglia.observability import configure_opentelemetry

configure_opentelemetry(
    service_name="mario-pizzeria",
    service_version="1.0.0",
    additional_resource_attributes={
        "deployment.region": "us-east-1",
        "deployment.zone": "zone-a",
        "environment": "production",
        "team": "backend",
        "cost_center": "engineering"
    }
)

# All traces, metrics, and logs now include these attributes
```

### 2. Custom Instrumentation

Instrument specific code sections:

```python
from neuroglia.observability import get_tracer, trace_sync

tracer = get_tracer(__name__)

# Async function tracing
@trace_async(name="complex_calculation")
async def complex_calculation(data: list):
    with tracer.start_as_current_span("data_validation"):
        validated = validate_data(data)

    with tracer.start_as_current_span("processing"):
        result = await process_data(validated)

    with tracer.start_as_current_span("persistence"):
        await save_result(result)

    return result

# Sync function tracing
@trace_sync(name="legacy_sync_function")
def legacy_function(x: int) -> int:
    return x * 2
```

### 3. Performance Tuning

Optimize for high-throughput scenarios:

```python
from neuroglia.observability import configure_opentelemetry

configure_opentelemetry(
    service_name="high-throughput-service",

    # Increase queue size for high request volume
    batch_span_processor_max_queue_size=8192,  # Default: 2048

    # Export more frequently
    batch_span_processor_schedule_delay_millis=2000,  # Default: 5000 (5s)

    # Larger export batches
    batch_span_processor_max_export_batch_size=1024,  # Default: 512

    # Metrics export every 30 seconds instead of 60
    metric_export_interval_millis=30000,
    metric_export_timeout_millis=15000
)
```

### 4. Context Propagation

Propagate trace context across service boundaries:

```python
from neuroglia.observability import add_baggage, get_baggage
import httpx

async def call_external_service():
    # Add baggage (propagates with trace)
    add_baggage("user.id", "user_123")
    add_baggage("request.priority", "high")

    # HTTPx automatically includes trace headers
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://other-service/api/process",
            json={"data": "value"}
        )
        # Trace context automatically propagated!

# In the other service:
async def process_request():
    # Retrieve baggage
    user_id = get_baggage("user.id")  # "user_123"
    priority = get_baggage("request.priority")  # "high"
```

### 5. Selective Instrumentation

Control which components get instrumented:

```python
from pydantic import Field

class PizzeriaSettings(ApplicationSettingsWithObservability):
    # Fine-grained control over instrumentation
    otel_instrument_fastapi: bool = Field(default=True)
    otel_instrument_httpx: bool = Field(default=True)
    otel_instrument_logging: bool = Field(default=True)
    otel_instrument_system_metrics: bool = Field(default=False)  # Disable for serverless

builder = WebApplicationBuilder(settings)
Observability.configure(builder)  # Respects instrumentation flags
```

## 🧪 Testing with Observability

Test observability components in your test suite:

```python
import pytest
from neuroglia.observability import configure_opentelemetry, get_tracer, get_meter

@pytest.fixture
def observability_configured():
    """Configure observability for tests"""
    configure_opentelemetry(
        service_name="mario-pizzeria-test",
        service_version="test",
        enable_console_export=True,  # See traces in test output
        otlp_endpoint="http://localhost:4317"
    )
    yield

    from neuroglia.observability import shutdown_opentelemetry
    shutdown_opentelemetry()

@pytest.mark.asyncio
async def test_order_handler_creates_span(observability_configured):
    """Test that handler creates trace span"""
    tracer = get_tracer(__name__)

    # Execute handler
    handler = CreateOrderHandler(mock_repository, mock_payment)
    command = CreateOrderCommand(customer_id="123", items=[], total_amount=50.0)

    with tracer.start_as_current_span("test_span") as span:
        result = await handler.handle_async(command)

        # Verify span created
        assert span.is_recording()
        assert result.is_success

@pytest.mark.asyncio
async def test_metrics_recorded():
    """Test that metrics are recorded correctly"""
    meter = get_meter(__name__)
    counter = meter.create_counter("test_counter")

    # Record metric
    counter.add(1, {"test": "value"})

    # Verify (in real tests, you'd check Prometheus endpoint)
    # In tests, just verify no exceptions
    assert True
```

## ⚠️ Common Mistakes

### 1. Forgetting to Configure Before Running

```python
# ❌ Wrong - observability not configured
app = FastAPI()
uvicorn.run(app)  # No traces, no metrics

# ✅ Correct - configure during app setup
builder = WebApplicationBuilder(settings)
Observability.configure(builder)
app = builder.build()
uvicorn.run(app)  # Full observability!
```

### 2. Instrumenting Sub-Apps

```python
# ❌ Wrong - duplicate instrumentation
from neuroglia.observability import instrument_fastapi_app

app = FastAPI()
api_app = FastAPI()
app.mount("/api", api_app)

instrument_fastapi_app(app, "main")
instrument_fastapi_app(api_app, "api")  # Causes warnings!

# ✅ Correct - only instrument main app
instrument_fastapi_app(app, "main")  # Captures all endpoints
```

### 3. Missing Settings Mixin

```python
# ❌ Wrong - no observability settings
class MySettings(ApplicationSettings):
    database_url: str

builder = WebApplicationBuilder(MySettings())
Observability.configure(builder)  # Raises ValueError!

# ✅ Correct - inherit from ApplicationSettingsWithObservability
class MySettings(ApplicationSettingsWithObservability):
    database_url: str

builder = WebApplicationBuilder(MySettings())
Observability.configure(builder)  # Works!
```

## 🚫 When NOT to Use

### 1. Serverless Functions with Cold Start Sensitivity

OpenTelemetry adds ~100-200ms to cold starts. For AWS Lambda or similar:

```python
# Consider lightweight alternatives:
# - CloudWatch Logs only
# - X-Ray for tracing
# - Custom metrics to CloudWatch
```

### 2. Ultra-High Throughput Services

For services handling >100k requests/second:

```python
# Consider:
# - Sampling traces (only 1% of requests)
# - Tail-based sampling
# - Metrics-only observability
# - Custom lightweight instrumentation
```

### 3. Development/Prototyping

For quick prototypes:

```python
# Simple logging may be sufficient:
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Order created")
```

## 📝 Key Takeaways

1. **Framework Integration**: Use `Observability.configure(builder)` for automatic setup
2. **Three Pillars**: Traces show flow, metrics show health, logs show details
3. **Automatic Instrumentation**: FastAPI, HTTPx, and logging instrumented by default
4. **Trace Correlation**: Logs automatically include trace_id and span_id
5. **Decorator Pattern**: Use `@trace_async()` for easy span creation
6. **Performance Aware**: Tune batch processing for your throughput needs

## 🔗 Related Documentation

- [Getting Started](../getting-started.md) - Initial framework setup
- [Tutorial Part 8: Observability](../tutorials/part-8-observability.md) - Step-by-step observability guide
- [Application Hosting](hosting.md) - WebApplicationBuilder integration
- [CQRS & Mediation](simple-cqrs.md) - Handler tracing integration

## 📚 API Reference

### Observability.configure()

```python
@classmethod
def configure(
    cls,
    builder: WebApplicationBuilder,
    **overrides
) -> None:
    """
    Configure comprehensive observability for the application.

    Args:
        builder: WebApplicationBuilder with app_settings
        **overrides: Optional configuration overrides
                     (tracing_enabled, metrics_enabled, logging_enabled)

    Raises:
        ValueError: If app_settings doesn't have observability configuration
    """
```

### configure_opentelemetry()

```python
def configure_opentelemetry(
    service_name: str,
    service_version: str = "unknown",
    otlp_endpoint: str = "http://localhost:4317",
    enable_console_export: bool = False,
    deployment_environment: str = "development",
    additional_resource_attributes: Optional[dict[str, str]] = None,
    enable_fastapi_instrumentation: bool = True,
    enable_httpx_instrumentation: bool = True,
    enable_logging_instrumentation: bool = True,
    enable_system_metrics: bool = False,
    batch_span_processor_max_queue_size: int = 2048,
    batch_span_processor_schedule_delay_millis: int = 5000,
    batch_span_processor_max_export_batch_size: int = 512,
    metric_export_interval_millis: int = 60000,
    metric_export_timeout_millis: int = 30000
) -> None:
    """
    Configure OpenTelemetry SDK with comprehensive observability setup.

    Initializes tracing, metrics, logging, and instrumentation.
    """
```

### @trace_async() / @trace_sync()

```python
def trace_async(name: Optional[str] = None) -> Callable:
    """
    Decorator for automatic async function tracing.

    Args:
        name: Optional span name (defaults to function name)

    Returns:
        Decorator function
    """

def trace_sync(name: Optional[str] = None) -> Callable:
    """
    Decorator for automatic sync function tracing.

    Args:
        name: Optional span name (defaults to function name)

    Returns:
        Decorator function
    """
```

### get_tracer()

```python
def get_tracer(name: str) -> Tracer:
    """
    Get a tracer instance for manual instrumentation.

    Args:
        name: Tracer name (typically __name__)

    Returns:
        OpenTelemetry Tracer instance
    """
```

### get_meter()

```python
def get_meter(name: str) -> Meter:
    """
    Get a meter instance for creating metrics.

    Args:
        name: Meter name (typically __name__)

    Returns:
        OpenTelemetry Meter instance
    """
```

### ApplicationSettingsWithObservability

```python
class ApplicationSettingsWithObservability(ApplicationSettings, ObservabilitySettingsMixin):
    """
    Base settings class with built-in observability configuration.

    Attributes:
        service_name: str = Field(default="neuroglia-service")
        service_version: str = Field(default="1.0.0")
        deployment_environment: str = Field(default="development")
        otel_enabled: bool = Field(default=True)
        otel_endpoint: str = Field(default="http://localhost:4317")
        otel_console_export: bool = Field(default=False)
        tracing_enabled: bool = Field(default=True)
        metrics_enabled: bool = Field(default=True)
        logging_enabled: bool = Field(default=True)
        instrument_fastapi: bool = Field(default=True)
        instrument_httpx: bool = Field(default=True)
        instrument_logging: bool = Field(default=True)
        instrument_system_metrics: bool = Field(default=True)
    """
```
