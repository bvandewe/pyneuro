# Neuroglia Python Framework

The framework is a very thin software layer built on top of [FastAPI](https://fastapi.tiangolo.com/) that provides developers with a set of coding features and tools that may be useful for any microservice (regardless of its role and domain/bounded context), such as:

- Implements all guidelines from https://12factor.net
- MVC Web App builder with fundamental abstractions
- Simple Dependency Injection mechanism, including automatic class discovery and instantiation
- Class-based API controller with automatic module discovery
- Modular Command/Query responsibility segregation
- Optional Event-sourcing for event-driven Domain modeling
- Clean layered Code https://levelup.gitconnected.com/clean-architecture-86c4f03e4771
  - Pure Domain models, independent of persistence
  - Application handlers (Command, Queries, Events, Tasks)
  - Repository pattern
  - Independent API controllers, endpoints and models (DTO's) vs Domain models and logic
- Native async Events ingestion, handling, emission (JSON [CloudEvent](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/formats/json-format.md)) using [ReactiveX programming](https://medium.com/@willAmaral/asynchronous-programming-and-rx-anything-479d9cb8daee) with [RxPy](https://rxpy.readthedocs.io/en/latest/)
- Data models mapping between Domain and Integration
- Easy extension for background task scheduling with [apscheduler](https://apscheduler.readthedocs.io/en/3.x/)
- etc...

The code typically includes comments that help understand it.

The `src/main.py` file is the entry point that defines all dependencies, including the sub-folders where to dynamically load the API, Application, Persistence and Domain layers.

In turn, when booting, the web app dynamically discovers, identifies and instantiate dependencies then loads:

- API controllers and define the mapping between each endpoint and its corresponding Application handler
- Application handlers (incl. Commands, Queries, Events, Tasks) and services (any business logic)
- Integration dependencies (any API client service, persistence-layer clients, ) and models (API' DTO for requests and responses)

## Documentation

Temporarily hosted at https://bvandewe.github.io/pyneuro/

## Disclaimer

This project was the opportunity for me (cdavernas) to learn Python while porting some of the concepts and services of the .NET version of the Neuroglia Framework

## Packaging

```sh
# Set `package-mode = true` in pyproject.toml
# Set the version tag in pyproject.toml
# Commit changes
# Create API Token in pypi.org...
# Configure credentials for pypi registry:
poetry config pypi-token.pypi  {pypi-....mytoken}
# Build package locally
poetry build
# Publish package to pypi.org:
poetry publish

```
