# 🍕 Mario's Pizzeria - Complete Sample Application

A comprehensive sample application demonstrating all major Neuroglia framework features through a realistic pizza ordering and management system with modern web UI, authentication, and observability.

> **📢 Framework Compatibility**: This sample is fully compatible with Neuroglia v0.4.8+
> See [MARIO_QUICK_REFERENCE.md](./MARIO_QUICK_REFERENCE.md) for quick setup and management commands.

## 🎯 Overview

Mario's Pizzeria showcases the complete Neuroglia framework implementation including:

- **Clean Architecture**: Proper layer separation (API, Application, Domain, Integration)
- **CQRS Pattern**: Commands for writes, Queries for reads with distributed tracing
- **Domain-Driven Design**: Rich domain entities with business logic and events
- **Event-Driven Architecture**: CloudEvents integration with domain event publishing
- **Repository Pattern**: MongoDB async persistence with Motor driver
- **Dependency Injection**: Enhanced service registration and scoped resolution
- **MVC Controllers**: Dual-app architecture with separate API and UI controllers
- **Authentication**: Keycloak SSO with role-based access control (RBAC)
- **Web UI**: Modern responsive interface with Parcel bundling and SCSS styling
- **Observability**: OpenTelemetry tracing, Prometheus metrics, Grafana dashboards

## 🏗️ Architecture

```
mario-pizzeria/
├── api/                     # 🌐 API Layer (OAuth2/JWT)
│   ├── controllers/         # RESTful API endpoints with authentication
│   ├── dtos/               # Data transfer objects
│   └── services/           # OpenAPI configuration
├── application/            # 💼 Application Layer
│   ├── commands/           # Write operations with tracing
│   ├── queries/            # Read operations with metrics
│   ├── events/             # Integration event handlers
│   ├── services/           # Application services (auth, etc.)
│   └── settings.py         # Configuration management
├── domain/                 # 🏛️ Domain Layer
│   ├── entities/           # Business entities with event sourcing
│   ├── events.py           # CloudEvent-decorated domain events
│   └── repositories/       # Repository interfaces
├── integration/            # 🔌 Integration Layer
│   └── repositories/       # MongoDB Motor async implementations
├── ui/                     # 🎨 Web UI Layer (Session-based auth)
│   ├── controllers/        # Web page controllers with Keycloak SSO
│   ├── templates/          # Jinja2 HTML templates
│   ├── src/               # TypeScript/SCSS source files
│   └── static/            # Built assets (Parcel)
├── observability/          # 📊 Observability
│   └── metrics.py         # Business-specific metrics
└── deployment/            # 🐳 Infrastructure
    ├── keycloak/          # Identity provider config
    └── mongo/             # Database initialization
```

## 🚀 Features

### Multi-Application Architecture

- **API App**: RESTful backend with OAuth2/JWT authentication (`/api`)
- **UI App**: Web interface with Keycloak SSO session authentication (`/`)
- **Dual Authentication**: Supports both token-based (API) and session-based (UI) auth
- **Role-Based Access**: Customer, Kitchen Staff, Manager, and Admin roles

### Order Management

- Place new pizza orders with customer profiles
- Real-time order status tracking with notifications
- Support for multiple pizzas per order with line items
- Automatic pricing calculations with tax and discounts
- Order cancellation and modification support

### Kitchen Operations

- Dedicated kitchen dashboard for staff
- View kitchen status, capacity, and current load
- Start cooking orders with automatic status transitions
- Complete orders when ready with delivery coordination
- Queue management with priority handling for rush periods

### Menu System

- Dynamic pizza menu with availability tracking
- Configurable toppings with seasonal pricing
- Size variations (small, medium, large) with scaling prices
- Real-time pricing calculations with promotions
- Menu management interface for administrators

### Customer Management

- Customer profile creation and management
- Order history with detailed tracking
- Contact details and delivery preferences
- Loyalty program integration
- Customer analytics and insights

### Delivery System

- Delivery tracking with real-time updates
- Route optimization for delivery drivers
- Delivery time estimates and notifications
- Driver assignment and coordination

### Authentication & Authorization

- **Keycloak SSO**: Single sign-on with role management
- **OAuth2/OIDC**: Modern authentication standards
- **JWT Tokens**: Secure API access with claims
- **Session Management**: Web UI authentication
- **Role-Based Access Control**: Fine-grained permissions

### Web Interface

- **Responsive Design**: Mobile-first responsive UI
- **Modern Bundling**: Parcel build system with hot reload
- **SCSS Styling**: Maintainable CSS with variables and mixins
- **Real-time Updates**: WebSocket integration for live order status
- **Progressive Web App**: Offline capability and push notifications

### Observability & Monitoring

- **OpenTelemetry Integration**: Distributed tracing across all operations
- **Prometheus Metrics**: Business and system metrics collection
- **Grafana Dashboards**: Pre-configured visualization dashboards
- **Structured Logging**: Loki log aggregation with trace correlation
- **Health Checks**: Comprehensive application health monitoring

## 🏃‍♂️ Quick Start

### 1. Start the Complete Stack

```bash
# Start Mario's Pizzeria with full observability stack
make mario-start

# Check that all services are running
make mario-status
```

### 2. Initialize Sample Data

```bash
# Generate test orders and menu data for dashboards
make mario-test-data
```

### 3. Access the Applications

- **🍕 Web UI**: http://localhost:8080/ (Keycloak SSO login)
- **📖 API Docs**: http://localhost:8080/api/docs (OAuth2 authentication)
- **📊 Grafana**: http://localhost:3001 (admin/admin)
- **🔐 Keycloak Admin**: http://localhost:8090/admin (admin/admin)

### 4. Alternative: Development Mode

```bash
# For local development without Docker (requires MongoDB)
cd samples/mario-pizzeria
python main.py --host 0.0.0.0 --port 8080
```

### 5. Sample API Requests (with Authentication)

First, get an OAuth2 token from Keycloak:

```bash
# Get access token - this command works correctly and returns HTTP 200 OK
TOKEN=$(curl -s -X POST "http://localhost:8090/realms/mario-pizzeria/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=mario-app&client_secret=mario-secret-123" \
  | jq -r '.access_token')

# Verify token was retrieved successfully
echo "Token received: ${TOKEN:0:50}..."
```

**✅ Verified Working**: This command successfully authenticates and returns a valid JWT token.

#### Place an Order

```bash
curl -X POST "http://localhost:8080/api/orders" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Mario Rossi",
    "customer_phone": "+1-555-0123",
    "customer_address": "123 Pizza Street, Little Italy",
    "pizzas": [
      {
        "pizza_name": "Margherita",
        "size": "large",
        "toppings": ["extra_cheese"],
        "quantity": 1
      }
    ],
    "payment_method": "credit_card",
    "special_instructions": "Extra crispy crust"
  }'
```

#### Get Order Status

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/api/orders/{order_id}"
```

#### View Menu

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/api/menu"
```

#### Check Kitchen Status (Kitchen Staff role required)

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/api/kitchen/status"
```

## 📊 Order Lifecycle

1. **Placed** → Order received, validated, and payment processed
2. **Confirmed** → Order confirmed and added to kitchen queue
3. **Cooking** → Kitchen starts preparation with estimated time
4. **Ready** → Pizza is ready, customer notified for pickup/delivery
5. **Out for Delivery** → Driver assigned, en route to customer
6. **Delivered** → Order completed successfully, customer confirmation
7. **Cancelled** → Order cancelled (with refund processing if applicable)

Each status transition triggers domain events and CloudEvent notifications for real-time updates.

## 💾 Data Storage

The application uses **MongoDB** with async Motor driver for all persistence:

- **Customers**: MongoDB collection with customer profiles and preferences
- **Orders**: MongoDB collection with full order details and status history
- **Pizzas**: MongoDB collection with menu items, pricing, and availability
- **Kitchen**: MongoDB collection with kitchen status, capacity, and queue
- **CloudEvents**: Event streaming with optional EventStore integration
- **Sessions**: Redis-compatible session storage for UI authentication

### Development Data Access

- **MongoDB Express**: http://localhost:8081 (admin/admin123)
- **Database**: `mario_pizzeria`
- **Collections**: `customers`, `orders`, `pizzas`, `kitchen`

## 🔧 Configuration

### Docker Environment Variables

- `LOCAL_DEV`: Enable development mode (default: true)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `CONNECTION_STRINGS`: JSON object with database connections
- `CLOUD_EVENT_SINK`: CloudEvent publishing endpoint
- `CLOUD_EVENT_SOURCE`: Source identifier for events

### Keycloak Configuration

- `KEYCLOAK_SERVER_URL`: Internal Keycloak server URL
- `KEYCLOAK_REALM`: Realm name (default: mario-pizzeria)
- `KEYCLOAK_CLIENT_ID`: OAuth2 client ID (default: mario-app)
- `KEYCLOAK_CLIENT_SECRET`: OAuth2 client secret

### Application Settings

Key settings in `application/settings.py`:

- **Authentication**: Keycloak URLs, JWT validation, OAuth2 scopes
- **Database**: MongoDB connection strings and collection names
- **CloudEvents**: Event publishing configuration and retry policies
- **Session Management**: Secret keys, timeouts, security settings
- **Observability**: OpenTelemetry service configuration

### Command Line Options (Development Mode)

- `--port <port>`: Set the application port (default: 8080)
- `--host <host>`: Set the bind address (default: 0.0.0.0)

## 🧪 Testing

```bash
# Run all Mario's Pizzeria tests
pytest samples/mario-pizzeria/tests/ -v

# Run tests with coverage
pytest samples/mario-pizzeria/tests/ --cov=samples.mario-pizzeria -v

# Run specific test categories
pytest samples/mario-pizzeria/tests/unit/ -v           # Unit tests
pytest samples/mario-pizzeria/tests/integration/ -v    # Integration tests
pytest samples/mario-pizzeria/tests/api/ -v           # API endpoint tests

# Test with live MongoDB (requires Docker stack)
make mario-start  # Start the stack first
pytest samples/mario-pizzeria/tests/integration/ -v --live-db
```

### Test Environment

The test suite includes:

- **Unit Tests**: Domain entities, handlers, and business logic
- **Integration Tests**: Repository implementations and database operations
- **API Tests**: HTTP endpoints with authentication flows
- **UI Tests**: Web interface and form submissions
- **Contract Tests**: CloudEvent schemas and API contracts

## 📝 API Endpoints

All API endpoints require OAuth2 Bearer token authentication and are prefixed with `/api`.

### Authentication

- `POST /api/auth/login` - OAuth2 token exchange
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/profile` - Get current user profile
- `POST /api/auth/logout` - Invalidate token

### Orders

- `GET /api/orders` - List orders (filtered by user role)
- `POST /api/orders` - Place a new order
- `GET /api/orders/{id}` - Get specific order details
- `PUT /api/orders/{id}/status` - Update order status (kitchen staff+)
- `GET /api/orders/status/{status}` - Get orders by status
- `GET /api/orders/active` - Get active orders for kitchen
- `DELETE /api/orders/{id}` - Cancel order (time restrictions apply)

### Menu

- `GET /api/menu` - Get full menu with availability
- `GET /api/menu/{pizza_name}` - Get specific pizza details
- `POST /api/menu` - Add new menu item (admin only)
- `PUT /api/menu/{pizza_name}` - Update menu item (admin only)
- `DELETE /api/menu/{pizza_name}` - Remove menu item (admin only)

### Kitchen

- `GET /api/kitchen/status` - Get kitchen status and capacity
- `POST /api/kitchen/start-cooking/{order_id}` - Start cooking (kitchen staff+)
- `POST /api/kitchen/complete/{order_id}` - Mark ready (kitchen staff+)
- `GET /api/kitchen/queue` - Get cooking queue (kitchen staff+)
- `PUT /api/kitchen/capacity` - Update kitchen capacity (manager+)

### Delivery

- `GET /api/delivery/active` - Get active deliveries (driver+)
- `POST /api/delivery/{order_id}/assign` - Assign driver (manager+)
- `PUT /api/delivery/{order_id}/status` - Update delivery status (driver+)
- `GET /api/delivery/routes` - Get optimized delivery routes (driver+)

### Customer Profile

- `GET /api/profile` - Get customer profile
- `PUT /api/profile` - Update customer profile
- `GET /api/profile/orders` - Get customer order history
- `GET /api/profile/favorites` - Get favorite orders

### Analytics & Reporting (Manager+ roles)

- `GET /api/reports/sales` - Sales analytics
- `GET /api/reports/performance` - Kitchen performance metrics
- `GET /api/reports/customers` - Customer analytics
- `GET /api/metrics` - Prometheus metrics endpoint

## 🎨 Domain Model

### Core Entities

#### Order (Aggregate Root)

- **Properties**: ID, Customer, Line Items, Status, Totals, Payment, Timestamps
- **Business Logic**: Status transitions, pricing calculations, validation rules
- **Events**: OrderCreatedEvent, CookingStartedEvent, OrderReadyEvent, OrderDeliveredEvent
- **CloudEvents**: Decorated for external integration and event streaming

#### Customer (Aggregate Root)

- **Properties**: ID, Profile, Contact Details, Preferences, Order History
- **Business Logic**: Profile validation, loyalty calculations, preference management
- **Events**: CustomerRegisteredEvent, PreferencesUpdatedEvent
- **Authentication**: Linked to Keycloak user identity

#### Pizza (Entity)

- **Properties**: Name, Description, Sizes, Base Price, Available Toppings
- **Business Logic**: Dynamic pricing, availability checks, nutritional info
- **Validation**: Size constraints, topping compatibility, seasonal availability

#### Kitchen (Aggregate Root)

- **Properties**: Capacity, Current Load, Queue, Staff Assignment
- **Business Logic**: Capacity management, queue optimization, load balancing
- **Events**: KitchenCapacityChangedEvent, QueueFullEvent
- **Real-time**: Live status updates for dashboard

#### LineItem (Entity)

- **Properties**: Pizza Reference, Quantity, Size, Toppings, Price, Special Instructions
- **Business Logic**: Individual item pricing, customization validation
- **Immutability**: Once order is confirmed, line items are locked

### Value Objects

- **Money**: Currency, amount with precision handling
- **Address**: Street, city, postal code with validation
- **PhoneNumber**: Formatted phone with country code
- **OrderStatus**: Strongly-typed status with transition rules
- **PizzaSize**: Enum with pricing multipliers

## 🔄 CQRS Implementation

### Commands (Write Operations)

- `PlaceOrderCommand` - Create new orders with validation and payment
- `StartCookingCommand` - Begin order preparation with kitchen assignment
- `CompleteOrderCommand` - Mark orders as ready with notification
- `CancelOrderCommand` - Cancel orders with refund processing
- `UpdateOrderStatusCommand` - Status transitions with business rules
- `CreateCustomerProfileCommand` - Register new customers
- `AssignDeliveryCommand` - Assign delivery driver to orders

### Queries (Read Operations)

- `GetOrderByIdQuery` - Retrieve specific order with authorization checks
- `GetActiveOrdersQuery` - Get orders for kitchen dashboard
- `GetOrdersByStatusQuery` - Filter orders by status with pagination
- `GetMenuQuery` - Get available menu items with pricing
- `GetKitchenStatusQuery` - Real-time kitchen capacity and queue
- `GetCustomerProfileQuery` - Customer details and preferences
- `GetOrderHistoryQuery` - Customer order history with filtering
- `GetDeliveryRoutesQuery` - Optimized delivery route planning

### Event Handlers (Domain Event Processing)

- `OrderPlacedHandler` - Send confirmation emails, update inventory
- `CookingStartedHandler` - Notify customer of preparation start
- `OrderReadyHandler` - Trigger delivery assignment, customer notification
- `DeliveryCompletedHandler` - Process payment completion, update loyalty points

All commands and queries are traced with OpenTelemetry and include comprehensive error handling with typed results.

## 🎯 Learning Objectives

This sample demonstrates:

1. **Clean Architecture & Domain-Driven Design**

   - Strict layer separation with dependency inversion
   - Rich domain models with business logic and invariants
   - Bounded contexts and aggregate design patterns
   - Ubiquitous language throughout the codebase

2. **CQRS with Distributed Tracing**

   - Complete separation of read and write operations
   - OpenTelemetry tracing for all command/query flows
   - Performance monitoring and bottleneck identification
   - Cross-cutting concerns with pipeline behaviors

3. **Event-Driven Architecture & CloudEvents**

   - Domain events for business workflow coordination
   - CloudEvents standard for external integrations
   - Event sourcing patterns with MongoDB
   - Asynchronous processing and event publishing

4. **Modern Authentication & Authorization**

   - OAuth2/OIDC with Keycloak integration
   - Role-based access control (RBAC) implementation
   - JWT token validation and claims processing
   - Session management for web applications

5. **Multi-Application Architecture**

   - API-first design with separate UI application
   - Different authentication strategies per application type
   - Shared services and dependency injection
   - FastAPI sub-application mounting patterns

6. **Production-Ready Observability**

   - OpenTelemetry integration (tracing, metrics, logs)
   - Grafana dashboards with business KPIs
   - Prometheus metrics collection and alerting
   - Distributed tracing across all operations

7. **Async Data Persistence**

   - MongoDB with Motor async driver
   - Repository pattern with interface abstractions
   - Unit of Work pattern for transaction management
   - Data consistency and concurrent access handling

8. **Modern Web UI Development**

   - Server-side rendering with Jinja2 templates
   - Modern asset bundling with Parcel
   - SCSS styling with component organization
   - Progressive enhancement and accessibility

9. **Infrastructure as Code**

   - Docker Compose for complete development environment
   - Keycloak configuration and realm management
   - MongoDB initialization with validation schemas
   - Observability stack orchestration (Grafana, Prometheus, etc.)

10. **Testing Strategies**

    - Unit testing with comprehensive mocking
    - Integration testing with live databases
    - API testing with authentication flows
    - Contract testing for event schemas

## � Management Commands

Quick commands for managing the complete environment:

```bash
# Complete stack management
make mario-start              # Start everything (app + observability)
make mario-stop               # Stop everything
make mario-status             # Check all service health
make mario-logs               # View all service logs
make mario-test-data          # Generate sample data

# Data management
make mario-clean-orders       # Remove all orders (keep other data)
make mario-create-menu        # Initialize default pizza menu
make mario-reset              # Complete environment reset

# Monitoring shortcuts
make mario-open               # Open key services in browser
```

See [MARIO_QUICK_REFERENCE.md](./MARIO_QUICK_REFERENCE.md) for detailed setup and operational guidance.

## �🔗 Related Documentation

### Framework Features

- [Getting Started](../../docs/getting-started.md) - Framework setup and basics
- [CQRS & Mediation](../../docs/features/cqrs-mediation.md) - Command/Query patterns
- [MVC Controllers](../../docs/features/mvc-controllers.md) - API and UI controller development
- [Data Access](../../docs/features/data-access.md) - Repository patterns and MongoDB
- [Dependency Injection](../../docs/features/dependency-injection.md) - Service registration
- [OpenTelemetry Guide](../../docs/guides/otel-framework-integration-analysis.md) - Observability setup

### Sample Documentation

- [Mario's Pizzeria Overview](../../docs/samples/mario-pizzeria.md) - Detailed sample walkthrough
- [Quick Reference](./MARIO_QUICK_REFERENCE.md) - Operational commands and URLs
- [Migration Notes](./notes/migrations/) - Framework upgrade guidance

## 📞 Support & Contribution

This sample is part of the Neuroglia Python framework ecosystem:

- **Framework Documentation**: [docs/](../../docs/)
- **Sample Applications**: [samples/](../)
- **Framework Issues**: Create an issue in the main repository
- **Sample Issues**: Use the mario-pizzeria label for sample-specific issues

### Development Notes

- **Framework Version**: Neuroglia v0.4.8+
- **Python Version**: 3.11+
- **Key Dependencies**: FastAPI, MongoDB Motor, Keycloak, OpenTelemetry
- **Development Setup**: Docker Compose with hot reload support
- **Production Ready**: Includes security, monitoring, and deployment configurations
