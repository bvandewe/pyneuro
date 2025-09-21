"""Resource controller implementation for reconciliation patterns.

This module provides the base controller implementation for resource
reconciliation following Kubernetes controller patterns.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Generic, Optional

from neuroglia.dependency_injection import ServiceProviderBase
from neuroglia.eventing.cloud_events.cloud_event import CloudEvent
from neuroglia.eventing.cloud_events.infrastructure.cloud_event_publisher import CloudEventPublisher

from .abstractions import Resource, ResourceController, TResourceSpec, TResourceStatus

log = logging.getLogger(__name__)


class ReconciliationStatus(Enum):
    """Status of a reconciliation operation."""
    SUCCESS = "Success"
    FAILED = "Failed"
    REQUEUE = "Requeue"
    REQUEUE_AFTER = "RequeueAfter"


@dataclass
class ReconciliationResult:
    """Result of a resource reconciliation operation."""
    
    status: ReconciliationStatus
    message: Optional[str] = None
    delay: Optional[timedelta] = None
    error: Optional[Exception] = None
    
    @classmethod
    def success(cls, message: Optional[str] = None) -> 'ReconciliationResult':
        """Create a successful reconciliation result."""
        return cls(ReconciliationStatus.SUCCESS, message)
    
    @classmethod
    def failed(cls, error: Exception, message: Optional[str] = None) -> 'ReconciliationResult':
        """Create a failed reconciliation result."""
        return cls(ReconciliationStatus.FAILED, message, error=error)
    
    @classmethod
    def requeue(cls, message: Optional[str] = None) -> 'ReconciliationResult':
        """Create a requeue reconciliation result."""
        return cls(ReconciliationStatus.REQUEUE, message)
    
    @classmethod
    def requeue_after(cls, delay: timedelta, message: Optional[str] = None) -> 'ReconciliationResult':
        """Create a requeue after delay reconciliation result."""
        return cls(ReconciliationStatus.REQUEUE_AFTER, message, delay=delay)


class ResourceControllerBase(Generic[TResourceSpec, TResourceStatus],
                             ResourceController[TResourceSpec, TResourceStatus],
                             ABC):
    """Base implementation for resource controllers with reconciliation logic."""
    
    def __init__(self,
                 service_provider: ServiceProviderBase,
                 event_publisher: Optional[CloudEventPublisher] = None):
        self.service_provider = service_provider
        self.event_publisher = event_publisher
        self._reconciliation_timeout = timedelta(minutes=5)
        self._max_retry_attempts = 3
    
    async def reconcile(self, resource: Resource[TResourceSpec, TResourceStatus]) -> None:
        """Main reconciliation entry point with error handling and events."""
        
        start_time = datetime.now()
        resource_name = resource.metadata.name
        resource_namespace = resource.metadata.namespace
        
        try:
            log.info(f"Starting reconciliation for {resource_namespace}/{resource_name}")
            
            # Check if resource needs reconciliation
            if not resource.needs_reconciliation():
                log.debug(f"Resource {resource_namespace}/{resource_name} does not need reconciliation")
                return
            
            # Execute reconciliation with timeout
            result = await asyncio.wait_for(
                self._do_reconcile(resource),
                timeout=self._reconciliation_timeout.total_seconds()
            )
            
            # Handle reconciliation result
            await self._handle_reconciliation_result(resource, result, start_time)
            
        except asyncio.TimeoutError:
            error_msg = f"Reconciliation timeout after {self._reconciliation_timeout}"
            log.error(f"Reconciliation timeout for {resource_namespace}/{resource_name}: {error_msg}")
            await self._handle_reconciliation_error(resource, TimeoutError(error_msg), start_time)
            
        except Exception as e:
            log.error(f"Reconciliation failed for {resource_namespace}/{resource_name}: {e}")
            await self._handle_reconciliation_error(resource, e, start_time)
    
    @abstractmethod
    async def _do_reconcile(self, resource: Resource[TResourceSpec, TResourceStatus]) -> ReconciliationResult:
        """Implement the actual reconciliation logic for the resource type."""
        raise NotImplementedError()
    
    async def finalize(self, resource: Resource[TResourceSpec, TResourceStatus]) -> bool:
        """Default finalization implementation. Override for custom cleanup."""
        
        resource_name = resource.metadata.name
        resource_namespace = resource.metadata.namespace
        
        try:
            log.info(f"Starting finalization for {resource_namespace}/{resource_name}")
            
            cleanup_complete = await self._do_finalize(resource)
            
            if cleanup_complete:
                log.info(f"Finalization completed for {resource_namespace}/{resource_name}")
                await self._publish_finalized_event(resource)
            else:
                log.info(f"Finalization in progress for {resource_namespace}/{resource_name}")
            
            return cleanup_complete
            
        except Exception as e:
            log.error(f"Finalization failed for {resource_namespace}/{resource_name}: {e}")
            await self._publish_finalization_failed_event(resource, e)
            return False
    
    async def _do_finalize(self, resource: Resource[TResourceSpec, TResourceStatus]) -> bool:
        """Override this method to implement custom finalization logic."""
        # Default implementation - no cleanup needed
        return True
    
    async def _handle_reconciliation_result(self, 
                                          resource: Resource[TResourceSpec, TResourceStatus],
                                          result: ReconciliationResult,
                                          start_time: datetime) -> None:
        """Handle the result of a reconciliation operation."""
        
        duration = datetime.now() - start_time
        resource_name = f"{resource.metadata.namespace}/{resource.metadata.name}"
        
        if result.status == ReconciliationStatus.SUCCESS:
            log.info(f"Reconciliation successful for {resource_name} in {duration}")
            await self._publish_reconciled_event(resource, result)
            
        elif result.status == ReconciliationStatus.FAILED:
            log.error(f"Reconciliation failed for {resource_name}: {result.message}")
            await self._publish_reconciliation_failed_event(resource, result)
            
        elif result.status in [ReconciliationStatus.REQUEUE, ReconciliationStatus.REQUEUE_AFTER]:
            requeue_msg = f"Reconciliation requeued for {resource_name}"
            if result.delay:
                requeue_msg += f" after {result.delay}"
            log.info(requeue_msg)
            await self._publish_reconciliation_requeued_event(resource, result)
    
    async def _handle_reconciliation_error(self,
                                         resource: Resource[TResourceSpec, TResourceStatus],
                                         error: Exception,
                                         start_time: datetime) -> None:
        """Handle reconciliation errors and emit appropriate events."""
        
        duration = datetime.now() - start_time
        resource_name = f"{resource.metadata.namespace}/{resource.metadata.name}"
        
        log.error(f"Reconciliation error for {resource_name} after {duration}: {error}")
        
        result = ReconciliationResult.failed(error, str(error))
        await self._publish_reconciliation_failed_event(resource, result)
    
    # Event publishing methods
    async def _publish_reconciled_event(self, 
                                       resource: Resource[TResourceSpec, TResourceStatus],
                                       result: ReconciliationResult) -> None:
        """Publish event when resource is successfully reconciled."""
        if not self.event_publisher:
            return
        
        event = CloudEvent(
            source=f"controller/{resource.kind.lower()}",
            type=f"{resource.kind.lower()}.reconciled",
            subject=f"{resource.metadata.namespace}/{resource.metadata.name}",
            data={
                "resourceUid": resource.id,
                "apiVersion": resource.api_version,
                "kind": resource.kind,
                "namespace": resource.metadata.namespace,
                "name": resource.metadata.name,
                "generation": resource.metadata.generation,
                "observedGeneration": resource.status.observed_generation if resource.status else 0,
                "message": result.message
            }
        )
        
        await self.event_publisher.on_publish_cloud_event_async(event)
    
    async def _publish_reconciliation_failed_event(self,
                                                  resource: Resource[TResourceSpec, TResourceStatus],
                                                  result: ReconciliationResult) -> None:
        """Publish event when reconciliation fails."""
        if not self.event_publisher:
            return
        
        event = CloudEvent(
            source=f"controller/{resource.kind.lower()}",
            type=f"{resource.kind.lower()}.reconciliation.failed",
            subject=f"{resource.metadata.namespace}/{resource.metadata.name}",
            data={
                "resourceUid": resource.id,
                "apiVersion": resource.api_version,
                "kind": resource.kind,
                "namespace": resource.metadata.namespace,
                "name": resource.metadata.name,
                "error": str(result.error) if result.error else "Unknown error",
                "message": result.message
            }
        )
        
        await self.event_publisher.on_publish_cloud_event_async(event)
    
    async def _publish_reconciliation_requeued_event(self,
                                                    resource: Resource[TResourceSpec, TResourceStatus],
                                                    result: ReconciliationResult) -> None:
        """Publish event when reconciliation is requeued."""
        if not self.event_publisher:
            return
        
        event = CloudEvent(
            source=f"controller/{resource.kind.lower()}",
            type=f"{resource.kind.lower()}.reconciliation.requeued",
            subject=f"{resource.metadata.namespace}/{resource.metadata.name}",
            data={
                "resourceUid": resource.id,
                "apiVersion": resource.api_version,
                "kind": resource.kind,
                "namespace": resource.metadata.namespace,
                "name": resource.metadata.name,
                "requeueAfter": result.delay.total_seconds() if result.delay else None,
                "message": result.message
            }
        )
        
        await self.event_publisher.on_publish_cloud_event_async(event)
    
    async def _publish_finalized_event(self, resource: Resource[TResourceSpec, TResourceStatus]) -> None:
        """Publish event when resource finalization completes."""
        if not self.event_publisher:
            return
        
        event = CloudEvent(
            source=f"controller/{resource.kind.lower()}",
            type=f"{resource.kind.lower()}.finalized",
            subject=f"{resource.metadata.namespace}/{resource.metadata.name}",
            data={
                "resourceUid": resource.id,
                "apiVersion": resource.api_version,
                "kind": resource.kind,
                "namespace": resource.metadata.namespace,
                "name": resource.metadata.name
            }
        )
        
        await self.event_publisher.on_publish_cloud_event_async(event)
    
    async def _publish_finalization_failed_event(self,
                                                resource: Resource[TResourceSpec, TResourceStatus],
                                                error: Exception) -> None:
        """Publish event when resource finalization fails."""
        if not self.event_publisher:
            return
        
        event = CloudEvent(
            source=f"controller/{resource.kind.lower()}",
            type=f"{resource.kind.lower()}.finalization.failed",
            subject=f"{resource.metadata.namespace}/{resource.metadata.name}",
            data={
                "resourceUid": resource.id,
                "apiVersion": resource.api_version,
                "kind": resource.kind,
                "namespace": resource.metadata.namespace,
                "name": resource.metadata.name,
                "error": str(error)
            }
        )
        
        await self.event_publisher.on_publish_cloud_event_async(event)
