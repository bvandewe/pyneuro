import uuid
from datetime import date, datetime
from multipledispatch import dispatch
from neuroglia.data.abstractions import AggregateRoot, AggregateState, DomainEvent
from neuroglia.mapping.mapper import map_to
from samples.openbank.domain.models import Address
from samples.openbank.integration import PersonGender
from samples.openbank.integration.models import PersonDto
from samples.openbank.application.events.integration import PersonRegisteredIntegrationEvent


@map_to(PersonRegisteredIntegrationEvent)
class PersonRegisteredDomainEventV1(DomainEvent[str]):

    def __init__(self, aggregate_id: str, first_name: str, last_name: str, nationality: str, gender: PersonGender, date_of_birth: date, address: Address):
        super().__init__(aggregate_id)
        self.first_name = first_name
        self.last_name = last_name
        self.nationality = nationality
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.address = address

    first_name: str

    last_name: str

    nationality: str

    gender: PersonGender

    date_of_birth: date

    address: Address


@map_to(PersonDto)
class PersonStateV1(AggregateState[str]):

    def __init__(self):
        super().__init__()

    first_name: str

    last_name: str

    nationality: str

    gender: PersonGender

    date_of_birth: date

    address: Address

    @dispatch(PersonRegisteredDomainEventV1)
    def on(self, e: PersonRegisteredDomainEventV1):
        self.id = e.aggregate_id
        self.created_at = e.created_at
        self.first_name = e.first_name
        self.last_name = e.last_name
        self.nationality = e.nationality
        self.gender = e.gender
        self.date_of_birth = e.date_of_birth
        self.address = e.address

    def __str__(self) -> str: return f"{self.last_name} {self.first_name} ({ self.date_of_birth.strftime('%m/%d/%Y') })"


@map_to(PersonDto)
class Person(AggregateRoot[PersonStateV1, str]):

    def __init__(self, first_name: str, last_name: str, nationality: str, gender: PersonGender, date_of_birth: date, address: Address):
        super().__init__()
        self.state.on(self.register_event(PersonRegisteredDomainEventV1(str(uuid.uuid4()).replace('-', ''), first_name, last_name, nationality, gender, date_of_birth, address)))

    def __str__(self) -> str: return str(self.state)
