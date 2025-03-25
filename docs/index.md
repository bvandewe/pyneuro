# Neuroglia Python Framework

This Python framework is a lightweight layer built on top of [FastAPI](https://fastapi.tiangolo.com/). It offers developers a set of useful tools and features that can be applied to any microservice, no matter its specific purpose or domain. These features include:

- Adherence to 12-Factor App principles: We've built the framework to follow the best practices outlined in the 12-factor methodology.
- Built-in MVC Web App structure: It provides a foundation for building web applications using the Model-View-Controller pattern, with essential abstractions.
- Simplified Dependency Injection: A straightforward mechanism for managing dependencies, including automatic discovery and instantiation of classes.
- Class-based API Controllers with Automatic Loading: Easily define API controllers using classes, with the framework automatically finding and loading them.
- Modular Command/Query Separation (CQRS): Supports a clear separation of commands (actions that change data) and queries (actions that retrieve data).
- Optional Event-Sourcing: Provides the option to implement event-sourcing for building event-driven domain models.
- Clean, Layered Code: Encourages a clean architecture approach, similar to the principles outlined in [link to clean architecture article].
- Pure Domain Models: Allows you to define domain models that are independent of any specific persistence mechanism.
- Application Handlers: Provides a structure for handling commands, queries, events, and background tasks within your application logic.
- Repository Pattern Implementation: Includes support for the Repository pattern for abstracting data access.
- Separation of API and Domain: Keeps API controllers, endpoints, and data transfer objects (DTOs) separate from your core domain models and business logic.
- Native Asynchronous Event Handling with RxPy: Offers built-in support for handling, emitting, and ingesting asynchronous events (in JSON CloudEvent format) using the ReactiveX programming paradigm with RxPy.
- Data Model Mapping: Provides tools for easily mapping data between your domain models and integration layers.
- Easy Background Task Scheduling: Integrates seamlessly with apscheduler for scheduling background tasks.
- And more...

The codebase is generally well-commented to help you understand its functionality.

The main entry point of your application is typically the `src/main.py` file. This file is where you define all the necessary dependencies and specify the sub-folders where the framework should dynamically load your API, Application, Persistence, and Domain layers.

When the web application starts, it automatically discovers, identifies, and instantiates the necessary dependencies. It then loads:

- API Controllers: Defines the routes and maps each endpoint to its corresponding Application handler.
- Application Handlers and Services: Loads the logic for handling commands, queries, events, tasks, and any other business logic services.
- Integration Dependencies: Loads any external API client services, persistence layer clients, and their associated data models (API DTOs for requests and responses).
