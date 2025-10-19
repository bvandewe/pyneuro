# 🍕 Mario's Pizzeria - Complete Sample Application

A comprehensive sample application demonstrating all major Neuroglia framework features through a realistic pizza ordering and management system.

> **📢 Framework Compatibility**: This sample is fully compatible with Neuroglia v0.4.6+
> See [UPGRADE_NOTES_v0.4.6.md](./UPGRADE_NOTES_v0.4.6.md) for details on the latest framework improvements.

## 🎯 Overview

Mario's Pizzeria showcases the complete Neuroglia framework implementation including:

- **Clean Architecture**: Proper layer separation (API, Application, Domain, Integration)
- **CQRS Pattern**: Commands for writes, Queries for reads
- **Domain-Driven Design**: Rich domain entities with business logic
- **Event-Driven Architecture**: Domain events for workflow coordination
- **Repository Pattern**: Abstracted data access with file-based storage
- **Dependency Injection**: Service registration and resolution
- **MVC Controllers**: RESTful API endpoints with automatic discovery

## 🏗️ Architecture

```
mario-pizzeria/
├── api/                     # 🌐 API Layer
│   ├── controllers/         # RESTful endpoints
│   └── dtos/               # Data transfer objects
├── application/            # 💼 Application Layer
│   ├── commands/           # Write operations
│   ├── queries/            # Read operations
│   └── handlers/           # Command/Query handlers
├── domain/                 # 🏛️ Domain Layer
│   ├── entities/           # Business entities
│   ├── events/             # Domain events
│   └── repositories/       # Repository interfaces
└── integration/            # 🔌 Integration Layer
    └── repositories/       # File-based implementations
```

## 🚀 Features

### Order Management

- Place new pizza orders with customer information
- Track order status through the complete lifecycle
- Support for multiple pizzas per order
- Automatic pricing calculations

### Kitchen Operations

- View kitchen status and capacity
- Start cooking orders
- Complete orders when ready
- Queue management for busy periods

### Menu System

- Predefined pizza types with base prices
- Configurable toppings with additional costs
- Size variations (small, medium, large)
- Real-time pricing calculations

### Customer Management

- Customer information tracking
- Order history
- Contact details management

## 🏃‍♂️ Quick Start

### 1. Run the Application

```bash
# From the mario-pizzeria directory
python main.py

# Or with custom settings
python main.py --port 8080 --host 0.0.0.0 --data-dir ./custom_data
```

### 2. Access the API

- **Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc

### 3. Sample Requests

#### Place an Order

```bash
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Mario Rossi",
    "customer_phone": "+1-555-0123",
    "customer_address": "123 Pizza Street, Little Italy",
    "pizzas": [
      {
        "name": "Margherita",
        "size": "large",
        "toppings": ["extra cheese"]
      }
    ],
    "payment_method": "credit_card"
  }'
```

#### Get Order Status

```bash
curl "http://localhost:8000/orders/{order_id}"
```

#### View Menu

```bash
curl "http://localhost:8000/menu"
```

#### Check Kitchen Status

```bash
curl "http://localhost:8000/kitchen/status"
```

## 📊 Order Lifecycle

1. **Placed** → Order received and validated
2. **Cooking** → Kitchen starts preparation
3. **Ready** → Pizza is ready for pickup/delivery
4. **Delivered** → Order completed successfully
5. **Cancelled** → Order cancelled (if needed)

## 💾 Data Storage

The application uses file-based storage with JSON serialization:

- **Orders**: `./data/orders/` - Order information and status
- **Menu**: `./data/menu/` - Available pizzas and pricing
- **Customers**: `./data/customers/` - Customer profiles
- **Kitchen**: `./data/kitchen/` - Kitchen status and capacity

## 🔧 Configuration

### Environment Variables

- `PIZZERIA_PORT`: Application port (default: 8000)
- `PIZZERIA_HOST`: Bind address (default: 127.0.0.1)
- `PIZZERIA_DATA_DIR`: Data storage directory (default: ./data)

### Command Line Options

- `--port <port>`: Set the application port
- `--host <host>`: Set the bind address
- `--data-dir <path>`: Set the data storage directory

## 🧪 Testing

```bash
# Run all tests for Mario's Pizzeria
pytest tests/ -k mario_pizzeria -v

# Run specific test categories
pytest tests/unit/mario_pizzeria/ -v      # Unit tests
pytest tests/integration/mario_pizzeria/ -v  # Integration tests
```

## 📝 API Endpoints

### Orders

- `GET /orders` - List all orders
- `POST /orders` - Place a new order
- `GET /orders/{id}` - Get specific order
- `PUT /orders/{id}/status` - Update order status
- `GET /orders/status/{status}` - Get orders by status

### Menu

- `GET /menu` - Get full menu
- `GET /menu/{pizza_name}` - Get specific pizza details

### Kitchen

- `GET /kitchen/status` - Get kitchen status and capacity
- `POST /kitchen/start-cooking/{order_id}` - Start cooking an order
- `POST /kitchen/complete/{order_id}` - Mark order as ready

## 🎨 Domain Model

### Core Entities

#### Order

- **Properties**: ID, Customer, Pizzas, Status, Total, Timestamps
- **Business Logic**: Status transitions, pricing calculations
- **Events**: OrderPlaced, CookingStarted, OrderReady, OrderDelivered

#### Pizza

- **Properties**: Name, Size, Toppings, Price
- **Business Logic**: Price calculation based on size and toppings
- **Validation**: Valid sizes and available toppings

#### Customer

- **Properties**: ID, Name, Phone, Address, Order History
- **Business Logic**: Contact validation, order tracking

#### Kitchen

- **Properties**: Capacity, Current Load, Queue
- **Business Logic**: Capacity management, queue processing

## 🔄 CQRS Implementation

### Commands (Write Operations)

- `PlaceOrderCommand` - Create new orders
- `StartCookingCommand` - Begin order preparation
- `CompleteOrderCommand` - Mark orders as ready

### Queries (Read Operations)

- `GetOrderByIdQuery` - Retrieve specific orders
- `GetMenuQuery` - Get available menu items
- `GetKitchenStatusQuery` - Check kitchen capacity
- `GetOrdersByStatusQuery` - Filter orders by status

## 🎯 Learning Objectives

This sample demonstrates:

1. **Clean Architecture Principles**

   - Layer separation and dependency inversion
   - Domain-driven design patterns
   - Testable and maintainable code structure

2. **CQRS and Mediator Patterns**

   - Command and query separation
   - Handler-based request processing
   - Cross-cutting concerns with behaviors

3. **Domain Events and Event-Driven Architecture**

   - Business event modeling
   - Event handlers for side effects
   - Workflow coordination through events

4. **Repository Pattern and Data Access**

   - Interface-based data access
   - Pluggable storage implementations
   - File-based persistence for simplicity

5. **Dependency Injection and IoC**

   - Service registration and lifetime management
   - Constructor injection patterns
   - Testable service dependencies

6. **RESTful API Design**
   - Resource-based endpoints
   - Proper HTTP status codes
   - Request/response modeling

## 🔗 Related Documentation

- [Getting Started](../../docs/getting-started.md)
- [CQRS & Mediation](../../docs/features/cqrs-mediation.md)
- [MVC Controllers](../../docs/features/mvc-controllers.md)
- [Data Access](../../docs/features/data-access.md)
- [Dependency Injection](../../docs/features/dependency-injection.md)

## 📞 Support

This sample is part of the Neuroglia Python framework. For issues or questions:

- Framework Documentation: [docs/](../../docs/)
- Sample Applications: [samples/](../)
- GitHub Issues: Create an issue in the main repository
