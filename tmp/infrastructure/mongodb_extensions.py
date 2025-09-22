import logging
import inspect
import traceback
import re
from typing import TypeVar, Generic, List, Type, Dict, Callable, Any, Optional, get_type_hints
from functools import wraps

from neuroglia.data.queryable import Queryable
from neuroglia.data.infrastructure.mongo.mongo_repository import MongoQuery
from neuroglia.data.abstractions import Entity

log = logging.getLogger(__name__)

T = TypeVar("T")


class TypedMongoQuery(Generic[T]):
    """
    A wrapper for MongoQuery that ensures proper type conversion when fetching results.
    """

    def __init__(self, query: MongoQuery, entity_type: Type[T]):
        """
        Initialize the typed mongo query.

        Args:
            query: The original MongoQuery instance
            entity_type: The entity type to convert results to
        """
        self._query = query
        self._entity_type = entity_type
        log.info(f"TypedMongoQuery from {type(query).__name__} created with entity_type: {entity_type.__name__}")
        # log.info(f"Original query object: {type(query).__name__}")

    def where(self, predicate: Callable):
        """
        Apply a where filter with multiple field conditions.

        Args:
            predicate: The predicate to filter by

        Returns:
            A new TypedMongoQuery with the filter applied
        """
        # log.info(f"TypedMongoQuery.where called with predicate: {predicate}")

        # Extract field value from closure for common patterns
        try:
            predicate_src = inspect.getsource(predicate)
            # log.info(f"Predicate source: {predicate_src}")

            # Check if we have the necessary provider and collection
            if hasattr(self._query, "provider") and hasattr(self._query.provider, "_collection"):
                collection = self._query.provider._collection
                mongo_filter = {}
                closure_vars = inspect.getclosurevars(predicate)

                # Handle multiple field conditions (e.g., x.field1 == value1 and x.field2 == value2)
                # Find all field comparisons in the predicate
                field_conditions = re.findall(r"x\.(\w+)\s*==\s*(\w+)", predicate_src)

                if field_conditions:
                    # Process each condition
                    for field_name, var_name in field_conditions:
                        if var_name in closure_vars.nonlocals:
                            field_value = closure_vars.nonlocals[var_name]
                            # Add this condition to the MongoDB filter
                            mongo_filter[field_name] = field_value

                # If we found valid conditions, execute a direct MongoDB query
                if mongo_filter:
                    log.info(f"Using direct MongoDB filter with multiple conditions: {mongo_filter}")
                    cursor = collection.find(mongo_filter)
                    self._direct_cursor = cursor
                    return self

        except Exception as e:
            log.error(f"Error parsing predicate: {e}")
            log.error(traceback.format_exc())

        # Fall back to the default behavior
        filtered_query = self._query.where(predicate)
        log.info(f"where() returned: {type(filtered_query).__name__}")
        return TypedMongoQuery(filtered_query, self._entity_type)

    def order_by(self, selector):
        """
        Order results by a field.

        Args:
            selector: The field selector function

        Returns:
            A new TypedMongoQuery with ordering applied
        """
        ordered_query = self._query.order_by(selector)
        return TypedMongoQuery(ordered_query, self._entity_type)

    def order_by_descending(self, selector):
        """
        Order results by a field in descending order.

        Args:
            selector: The field selector function

        Returns:
            A new TypedMongoQuery with ordering applied
        """
        ordered_query = self._query.order_by_descending(selector)
        return TypedMongoQuery(ordered_query, self._entity_type)

    def take(self, count: int):
        """
        Limit the number of results.

        Args:
            count: The maximum number of results to return

        Returns:
            A new TypedMongoQuery with limit applied
        """
        limited_query = self._query.take(count)
        return TypedMongoQuery(limited_query, self._entity_type)

    def skip(self, count: int):
        """
        Skip a number of results.

        Args:
            count: The number of results to skip

        Returns:
            A new TypedMongoQuery with skip applied
        """
        skipped_query = self._query.skip(count)
        return TypedMongoQuery(skipped_query, self._entity_type)

    def to_list(self) -> List[T]:
        """
        Execute the query and return properly typed entities.

        Returns:
            A list of properly instantiated entity objects
        """
        log.info(f"TypedMongoQuery.to_list called for entity_type: {self._entity_type.__name__}")

        # Get raw results from MongoDB (either from direct cursor or original query)
        raw_results = self._get_raw_results()
        if not raw_results:
            return []

        # Convert dictionaries to proper entity objects
        result_objects = []
        for item in raw_results:
            try:
                if isinstance(item, dict):
                    entity_obj = self._create_entity_from_dict(item)
                    result_objects.append(entity_obj)
                elif isinstance(item, self._entity_type):
                    # Already the correct type
                    # log.info(f"Item is already a {self._entity_type.__name__} instance")
                    result_objects.append(item)
                else:
                    log.warning(f"Unexpected item type: {type(item)}, expected {self._entity_type.__name__}")
                    result_objects.append(item)
            except Exception as e:
                log.error(f"Error processing item: {e}")
                log.error(traceback.format_exc())
                # Include the original item as fallback
                result_objects.append(item)

        log.info(f"TypedMongoQuery.to_list returning {len(result_objects)} processed items")
        return result_objects

    def _get_raw_results(self) -> List[Dict]:
        """Get raw results from MongoDB, either from direct cursor or original query"""
        if hasattr(self, "_direct_cursor"):
            # log.info("Using direct MongoDB cursor")
            try:
                raw_results = list(self._direct_cursor)
                # log.info(f"Raw results from direct cursor: {len(raw_results)} items")
                # if raw_results and len(raw_results) > 0:
                #     log.info(f"First item type: {type(raw_results[0]).__name__}")
                #     log.info(f"First item: {str(raw_results[0])[:100]}...")
                return raw_results
            except Exception as e:
                log.error(f"Error fetching results from direct cursor: {e}")
                log.error(traceback.format_exc())
                return []
        else:
            # Get the raw results from MongoDB using the original query
            try:
                # log.info("Calling to_list() on original query")
                raw_results = self._query.to_list()
                # log.info(f"Raw results type: {type(raw_results).__name__}")
                # log.info(f"Retrieved {len(raw_results)} raw items")

                # if raw_results and len(raw_results) > 0:
                #     log.info(f"First item type: {type(raw_results[0]).__name__}")
                #     log.info(f"First item content: {str(raw_results[0])[:100]}...")

                return raw_results
            except Exception as e:
                log.error(f"Error executing original to_list(): {e}")
                log.error(traceback.format_exc())
                return []

    def _create_entity_from_dict(self, item: Dict) -> T:
        """Create an entity instance from a dictionary"""
        # log.info(f"Converting dictionary to {self._entity_type.__name__}: {str(item)[:100]}...")

        # Clean up MongoDB specific fields
        if "_id" in item:
            item_copy = dict(item)
            del item_copy["_id"]
        else:
            item_copy = item

        # Analyze the entity's constructor to determine required parameters
        try:
            # Get constructor signature
            entity_init = self._entity_type.__init__
            sig = inspect.signature(entity_init)

            # Find required parameters (those without defaults and not self)
            required_params = {name: param for name, param in sig.parameters.items() if param.default is param.empty and name != "self"}

            # log.info(f"Required parameters for {self._entity_type.__name__}: {list(required_params.keys())}")

            # Prepare constructor arguments for required parameters only
            constructor_args = {}
            kwargs = {}

            # Handle special cases for 'id' which may cause conflicts
            if "id" in item_copy and "id" not in required_params:
                stored_id = item_copy["id"]
                # Remove id from the input to avoid passing it to constructor
                item_copy_without_id = dict(item_copy)
                if "id" in item_copy_without_id:
                    del item_copy_without_id["id"]
            else:
                stored_id = None
                item_copy_without_id = item_copy

            # Process enum fields for required parameters
            for param_name in required_params:
                if param_name == "kwargs":  # Special handling for **kwargs parameter
                    continue

                if param_name in item_copy_without_id:
                    param_value = item_copy_without_id[param_name]
                    param_type = self._get_parameter_type(param_name)

                    # If parameter is an enum type and we have a string value, convert it
                    if param_type and hasattr(param_type, "__members__") and isinstance(param_value, str):
                        # log.info(f"Converting string '{param_value}' to enum {param_type.__name__}")
                        constructor_args[param_name] = param_type(param_value)
                    else:
                        constructor_args[param_name] = param_value

            # Add non-required values to kwargs
            for k, v in item_copy_without_id.items():
                if k not in required_params and k != "id":  # Skip id and required params
                    kwargs[k] = v

            # Add kwargs to constructor_args if the constructor accepts it
            if "kwargs" in required_params:
                constructor_args["kwargs"] = kwargs
            elif "**" in str(sig):  # Check if it accepts **kwargs
                constructor_args.update(kwargs)

            # log.info(f"Creating entity with args: {list(constructor_args.keys())}")
            # Create the entity
            entity = self._entity_type(**constructor_args)

            # If we stored an ID and the entity is derived from Entity base class
            if stored_id is not None and hasattr(entity, "id"):
                current_id = getattr(entity, "id")
                if current_id != stored_id:
                    # log.info(f"Updating id from {current_id} to {stored_id}")
                    setattr(entity, "id", stored_id)

            # log.info(f"Successfully created {self._entity_type.__name__} object")
            return entity

        except Exception as e:
            log.error(f"Error creating entity using constructor analysis: {e}")
            log.error(traceback.format_exc())

            # Try creating with special handling for Comment type
            try:
                if self._entity_type.__name__ == "Comment":
                    log.info("Trying Comment-specific creation approach")
                    from integration.enums.comment_types import CommentType

                    # Convert string to enum
                    subject_type_str = item_copy.get("subject_type", "CONTENT")
                    subject_type = CommentType(subject_type_str)

                    # Create with required parameters only
                    entity = self._entity_type(submitter=item_copy.get("submitter", ""), subject_type=subject_type, subject_id=item_copy.get("subject_id", ""), body=item_copy.get("body", ""))

                    # Set additional attributes if they exist
                    if "created_at" in item_copy:
                        setattr(entity, "created_at", item_copy["created_at"])
                    if "data" in item_copy:
                        setattr(entity, "data", item_copy["data"])

                    # Update ID if needed
                    if "id" in item_copy and hasattr(entity, "id"):
                        setattr(entity, "id", item_copy["id"])

                    log.info("Successfully created Comment using special approach")
                    return entity
            except Exception as e2:
                log.error(f"Special Comment creation also failed: {e2}")
                log.error(traceback.format_exc())

            # Return the original dictionary as a last resort
            log.warning(f"All creation methods failed, returning original dictionary")
            return item

    def _get_parameter_type(self, param_name: str) -> Optional[Type]:
        """Get the type annotation for a parameter"""
        try:
            # Try to get type hints from the class
            type_hints = get_type_hints(self._entity_type)
            if param_name in type_hints:
                return type_hints[param_name]

            # Look for type annotations in parent classes
            for base in self._entity_type.__mro__[1:]:  # Skip the class itself
                if hasattr(base, "__annotations__"):
                    base_annotations = base.__annotations__
                    if param_name in base_annotations:
                        return base_annotations[param_name]
        except Exception as e:
            log.error(f"Error getting parameter type for {param_name}: {e}")

        return None


def with_typed_mongo_query(repository_method):
    """
    Decorator to wrap MongoQuery results with TypedMongoQuery.

    Args:
        repository_method: The repository method to decorate

    Returns:
        Wrapped method that returns TypedMongoQuery instead of MongoQuery
    """

    @wraps(repository_method)
    async def wrapper(self, *args, **kwargs):
        # Call the original method which returns a MongoQuery
        result = await repository_method(self, *args, **kwargs)

        # Get the entity type from the repository's generic type parameter
        entity_type = self._get_entity_type()

        # Wrap the MongoQuery with our TypedMongoQuery
        if isinstance(result, MongoQuery):
            return TypedMongoQuery(result, entity_type)

        return result

    return wrapper
