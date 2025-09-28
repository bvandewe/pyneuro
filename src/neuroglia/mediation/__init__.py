# Import mediator extensions to register the add_mediator method
from neuroglia.extensions.mediator_extensions import add_mediator

from .mediator import *
from .simple import (
    InMemoryRepository,
    SimpleApplicationSettings,
    SimpleCommandHandler,
    SimpleQueryHandler,
    add_simple_mediator,
    create_simple_app,
    register_simple_handler,
    register_simple_handlers,
)
