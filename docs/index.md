# 🧠 Neuroglia Python Framework

A lightweight, opinionated Python framework built on [FastAPI](https://fastapi.tiangolo.com/) that enforces clean architecture principles and provides comprehensive tooling for building production-ready microservices.

## 🚀 What's Included

### 🏗️ **Framework Core**

Clean architecture patterns with dependency injection, CQRS, event-driven design, and comprehensive testing utilities.

### 🍕 **Real-World Samples**

Complete production examples like [Mario's Pizzeria](mario-pizzeria.md) demonstrating every framework feature in realistic business scenarios.

### ⚙️ **CLI Tooling**

PyNeuroctl command-line interface for managing, testing, and deploying your applications with zero configuration.

## ✨ Key Features

- **🎯 CQRS & Mediation**: Built-in Command Query Responsibility Segregation with mediator pattern
- **💉 Dependency Injection**: Lightweight container with automatic service discovery
- **🔌 MVC Controllers**: Class-based controllers with automatic OpenAPI generation
- **📡 Event-Driven**: Native CloudEvents support and domain event handling
- **🗄️ Data Access**: Repository pattern with file-based, MongoDB, and event sourcing support
- **🧪 Testing Utilities**: Comprehensive testing patterns for all architectural layers

## 🚀 Quick Start

Get started with Neuroglia in minutes:

```bash
# Install the framework
pip install neuroglia

# Create your first app
pyneuroctl new myapp --template pizzeria
cd myapp

# Run the application
python main.py
```

Visit `http://localhost:8000/docs` to explore the auto-generated API documentation.

## 📚 Learn More

- **[Getting Started](getting-started.md)** - Step-by-step tutorial building your first application
- **[Mario's Pizzeria](mario-pizzeria.md)** - Complete bounded context with visual architecture diagrams
- **[Patterns](patterns.md)** - Software design patterns and best practices
- **[Features](features/)** - Deep dive into framework capabilities
- **[Guides](guides/)** - How-to procedures and troubleshooting

## 🎯 Perfect For

- **Microservices**: Clean architecture for scalable service development
- **Event-Driven Systems**: Built-in CloudEvents and domain event support
- **API Development**: FastAPI-based with automatic OpenAPI documentation
- **Domain-Driven Design**: Enforce DDD patterns and bounded contexts
- **Clean Code**: Opinionated structure that promotes maintainable code

## 🔧 Architecture Overview

Neuroglia enforces a four-layer clean architecture:

```
📁 Your Application
├── 🌐 api/          # Controllers, DTOs, Routes
├── 💼 application/  # Commands, Queries, Handlers
├── 🏛️ domain/       # Entities, Business Rules
└── 🔌 integration/ # Repositories, External APIs
```

**Dependency Rule**: Dependencies only flow inward (API → Application → Domain ← Integration)

## 🚀 Next Steps

1. **Start Learning**: Follow the [Getting Started Guide](getting-started.md)
2. **See It In Action**: Explore [Mario's Pizzeria](mario-pizzeria.md) sample
3. **Understand Patterns**: Review [common patterns](patterns.md) used throughout
4. **Deep Dive**: Explore specific [framework features](features/)

---

_Neuroglia Python Framework - Building better software through better architecture_ 🧠✨
