import asyncio
import http.client
from dataclasses import dataclass
import logging
from neuroglia.eventing.cloud_events.cloud_event import CloudEvent
from neuroglia.eventing.cloud_events.infrastructure.cloud_event_bus import CloudEventBus
from neuroglia.hosting.abstractions import ApplicationBuilderBase, HostedService
from neuroglia.reactive.rx_async import AsyncRx
from rx.core.typing import Disposable
from urllib.parse import urlparse, urlunparse


@dataclass
class CloudEventPublishingOptions:
    ''' Represents the service used to configure the way Cloud Events should be published by the application '''

    sink_uri : str
    ''' Gets the URI to publish cloud events to '''
    
    source: str
    ''' Gets the value of the 'source' context attribute for all cloud events produced by the application '''
    
    retry_attempts : int = 5
    ''' Gets/sets the maximum amount of retries before giving up '''

    retry_delay : float = 1
    ''' Gets/sets the delay, in seconds, to wait after each retry attempt. Configured value is multiplied by the amount of retries that have been performed '''


class CloudEventPublisher(HostedService):
    ''' Represents the service used to publish the application's outgoing cloud events '''
    
    def __init__(self, options : CloudEventPublishingOptions, cloud_event_bus : CloudEventBus):
        self._options = options
        self._cloud_event_bus = cloud_event_bus
        
    _options : CloudEventPublishingOptions
    ''' Gets the current CloudEventPublishingOptions '''

    _cloud_event_bus: CloudEventBus
    ''' Gets the service used to manage the cloud events produced and consumed by the application '''
    
    _subscription : Disposable

    async def start_async(self):
        self._subscription = AsyncRx.subscribe(self._cloud_event_bus.output_stream, lambda e: asyncio.run(self.on_publish_cloud_event_async(e)))
        
    async def stop_async(self):
        self._subscription.dispose()

    async def on_publish_cloud_event_async(self, e : CloudEvent):
        uri = urlparse(self._options.sink_uri)
        connection = http.client.HTTPSConnection(uri.hostname, uri.port)
        path_and_query = urlunparse(("", "", uri.path, uri.params, uri.query, ""))
        published = False
        for retries in range(self._options.retry_attempts):
            try:
                connection.request("POST", path_and_query)
                response = connection.getresponse()
                if 200 <= response.status < 300: 
                    published = True
                    break
            except Exception as ex:
                logging.warning(f"An error occured while publishing the cloud event with id '{e.id}' [attempt {retries}/{self._options.retry_attempts}]: {ex}")
            await asyncio.sleep(self._options.retry_delay * retries)
        if not published: 
            raise Exception(f"Failed to publish cloud events to the specified sink '{self._options.sink_uri}' after '{self._options.retry_attempts}' attempts")
        
    def configure(builder : ApplicationBuilderBase) -> ApplicationBuilderBase:
        ''' Registers and configures a cloud event publisher to the specified service collection.
            
            Args:
                services (ServiceCollection): the service collection to configure
        '''
        options = CloudEventPublishingOptions(builder.settings.cloud_event_sink, builder.settings.cloud_event_source, builder.settings.cloud_event_retry_attempts, builder.settings.cloud_event_retry_delay)
        builder.services.try_add_singleton(CloudEventBus)
        builder.services.add_singleton(CloudEventPublishingOptions, singleton=options)
        builder.services.add_singleton(HostedService, CloudEventPublisher)
        return builder