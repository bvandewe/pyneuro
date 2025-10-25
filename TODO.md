# TODO

## Quick Notes

- builder.services.add_scoped(AuthService)
- Use decorator for automatic tracing
  @trace_async()
  async def my_function():
  pass

- automate `set_oas_description(api_app, app_settings)`

- simplify config with passing the abstract repo to the MotorRepository.configure
  MotorRepository.configure(builder, entity_type=Customer, key_type=str, database_name="mario_pizzeria", collection_name="customers")
  builder.services.add_scoped(ICustomerRepository, MongoCustomerRepository)

## In Progress

## Next

- [ ] Clean up and integrate notes into mkdos site
- [ ] Add event on menu' changes
- [ ] Add alerts
- [ ] Protect endpoints
- [ ] Mark new order as delivery or take-away
- [ ] Mark take-away orders as delivered
- [ ] Mark ready_orders as completed after expiration time
- [ ] Add sample ROA app with telemetry
- [ ] Add CLI to bootstrap and manipulate src code
- [ ] Add CI/CD pipeline configuration

## Completed

- [x] Add functional sample_app/mario-pizzeria with DDD/CQRS (no event-sourcing)
  - OAuth 2.0 authentication (as mentioned in the requirements doc)
  - MongoDB repository implementations
  - Event sourcing with domain events
  - Web UI frontend
  - Real-time notifications
  - Advanced reporting and analytics
- [x] Add extensive MkDocs documentation
- [x] Add extensive tests coverage
- [x] Add Telemetry Features and docs
- [x] Integrate enhanced API Client
- [x] Integrate enhanced repositories
- [x] Integrate background scheduler
- [x] Integrate multi-api app
- [x] Fix mapping issues
- [x] Fix mediator issues
- [x] Fix serialization issues
- [x] Add CHANGELOG
