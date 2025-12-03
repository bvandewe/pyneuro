"""
Motor (async) MongoDB Query implementation for Neuroglia.

This module provides async LINQ-style queryable support for Motor repositories,
enabling the same fluent query API available in sync MongoRepository.

Classes:
    MotorQuery: Async queryable wrapper for Motor collections
    MotorQueryProvider: Async query provider implementation
    MotorQueryBuilder: AST visitor for building Motor queries from Python expressions

Example:
    ```python
    from neuroglia.data.infrastructure.mongo import MotorRepository

    # Repository with queryable support
    repo = MotorRepository[Product, str](...)

    # Fluent LINQ-style queries
    products = await repo.query_async() \\
        .where(lambda p: p.price > 10) \\
        .order_by(lambda p: p.name) \\
        .skip(10) \\
        .take(5) \\
        .to_list_async()
    ```

See Also:
    - mongo_repository.py: Sync MongoQuery implementation (reference)
    - MotorRepository: Async repository with queryable support
    - Queryable: Base queryable abstraction
"""

import ast
from ast import NodeVisitor, expr
from typing import Any, Generic, List, Optional

import pymongo
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor

from neuroglia.data.queryable import Queryable, QueryProvider, T
from neuroglia.expressions.javascript_expression_translator import (
    JavaScriptExpressionTranslator,
)


class MotorQuery(Generic[T], Queryable[T]):
    """
    Represents an async Motor MongoDB query.

    This is the async equivalent of MongoQuery, providing LINQ-style
    queryable support for Motor (async MongoDB driver).

    Type Parameters:
        T: The entity type being queried

    Example:
        ```python
        query = await repo.query_async()  # Returns MotorQuery[Product]
        results = await query.where(lambda p: p.price > 10).to_list_async()
        ```
    """

    def __init__(self, query_provider: "MotorQueryProvider", expression: Optional[expr] = None):
        """
        Initialize a Motor query.

        Args:
            query_provider: The Motor query provider
            expression: Optional AST expression for the query
        """
        super().__init__(query_provider, expression)


class MotorQueryBuilder(NodeVisitor):
    """
    Represents the service used to build Motor (async) MongoDB queries from Python AST expressions.

    This is the async equivalent of MongoQueryBuilder, translating LINQ-style
    Python expressions into Motor query operations.

    The builder walks the Python AST tree and translates method calls like
    .where(), .order_by(), .skip(), .take() into corresponding Motor operations.

    Attributes:
        _collection: Motor collection to query
        _translator: JavaScript expression translator
        _order_by_clauses: Sort specifications
        _select_clause: Field projection
        _skip_clause: Documents to skip
        _take_clause: Maximum documents to return
        _where_clauses: Filter conditions

    Example:
        ```python
        # This Python expression:
        query.where(lambda x: x.price > 10).order_by(lambda x: x.name).take(5)

        # Gets translated to Motor operations:
        collection.find({"$where": "this.price > 10"}).sort("name", 1).limit(5)
        ```
    """

    def __init__(self, collection: AsyncIOMotorCollection, translator: JavaScriptExpressionTranslator):
        """
        Initialize the Motor query builder.

        Args:
            collection: Motor async collection to query
            translator: JavaScript expression translator for filter expressions
        """
        self._collection = collection
        self._translator = translator
        self._order_by_clauses: dict[str, int] = {}
        self._select_clause: Optional[list[str]] = None
        self._skip_clause: Optional[int] = None
        self._take_clause: Optional[int] = None
        self._where_clauses: list[str] = []

    def build(self, expression: expr) -> AsyncIOMotorCursor:
        """
        Build a Motor cursor from the Python AST expression.

        Walks the AST tree, collects query parameters, and returns
        a configured Motor cursor ready for async iteration.

        Args:
            expression: Python AST expression representing the query

        Returns:
            Configured Motor cursor with filters, sorts, skip, and limit applied

        Example:
            ```python
            builder = MotorQueryBuilder(collection, translator)
            cursor = builder.build(query_expression)
            async for doc in cursor:
                print(doc)
            ```
        """
        self.visit(expression)

        # Build cursor with projection
        cursor = self._collection.find(projection=self._select_clause)

        # Apply sorting
        if len(self._order_by_clauses) > 0:
            cursor = cursor.sort(list(self._order_by_clauses.items()))

        # Apply where clauses
        if len(self._where_clauses) > 0:
            # Use $where for JavaScript expressions
            cursor = self._collection.find({"$where": " && ".join(self._where_clauses)}, projection=self._select_clause)
            if len(self._order_by_clauses) > 0:
                cursor = cursor.sort(list(self._order_by_clauses.items()))

        # Apply skip
        if self._skip_clause is not None:
            cursor = cursor.skip(self._skip_clause)

        # Apply limit
        if self._take_clause is not None:
            cursor = cursor.limit(self._take_clause)

        return cursor

    def visit_Call(self, node: ast.Call):
        """
        Visit a method call node in the AST.

        Translates LINQ-style method calls (.where, .order_by, etc.)
        into Motor query parameters.

        Args:
            node: AST Call node representing a method invocation
        """
        if not isinstance(node.func, ast.Attribute):
            return

        clause = node.func.attr
        expression = node.args[0] if len(node.args) > 0 else None

        # Recursively visit the receiver (the object being called)
        self.visit(node.func.value)

        if expression is None:
            return

        # Translate lambda expressions to JavaScript
        javascript = self._translator.translate(expression)

        if clause == "distinct_by":
            # Not directly supported in projection, would need aggregation
            pass
        elif clause == "first":
            self._where_clauses.append(javascript)
            self._take_clause = 1
        elif clause == "last":
            self._where_clauses.append(javascript)
            self._take_clause = 1
            # Default sort by created_at descending (could be any field)
            if "created_at" not in self._order_by_clauses:
                self._order_by_clauses["created_at"] = pymongo.DESCENDING
        elif clause == "order_by":
            self._order_by_clauses[javascript.replace("this.", "")] = pymongo.ASCENDING
        elif clause == "order_by_descending":
            self._order_by_clauses[javascript.replace("this.", "")] = pymongo.DESCENDING
        elif clause == "select" and isinstance(expression, ast.Lambda) and isinstance(expression.body, ast.List):
            # Project specific fields
            self._select_clause = [self._translator.translate(elt).replace("this.", "") for elt in expression.body.elts]
        elif clause == "skip" and isinstance(expression, ast.Constant):
            if isinstance(expression.value, int):
                self._skip_clause = expression.value
        elif clause == "take" and isinstance(expression, ast.Constant):
            if isinstance(expression.value, int):
                self._take_clause = expression.value
        elif clause == "where":
            self._where_clauses.append(javascript)


class MotorQueryProvider(QueryProvider):
    """
    Represents the Motor (async) implementation of the QueryProvider.

    This provider creates MotorQuery instances and executes them asynchronously
    against a Motor collection.

    Attributes:
        _collection: Motor async collection to query
        _entity_type: Type of entities in the collection

    Example:
        ```python
        provider = MotorQueryProvider(motor_collection, Product)
        query = provider.create_query(Product, expression)
        results = await provider.execute_async(expression, List[Product])
        ```
    """

    def __init__(self, collection: AsyncIOMotorCollection, entity_type: type):
        """
        Initialize the Motor query provider.

        Args:
            collection: Motor async collection
            entity_type: Type of entities being queried
        """
        self._collection = collection
        self._entity_type = entity_type

    def create_query(self, element_type: type, expression: expr) -> Queryable:
        """
        Create a new queryable instance.

        Args:
            element_type: Type of elements in the query
            expression: AST expression for the query

        Returns:
            New MotorQuery instance
        """
        return MotorQuery(self, expression)

    def execute(self, expression: expr, query_type: type) -> Any:
        """
        Sync execute method (not used, kept for interface compatibility).

        Motor repositories are async-only. Use execute_async() instead.

        Raises:
            NotImplementedError: Always, as Motor is async-only
        """
        raise NotImplementedError("Motor repositories are async-only. Use execute_async() instead.")

    async def execute_async(self, expression: expr, query_type: type) -> Any:
        """
        Execute the query asynchronously using Motor.

        Builds the Motor cursor from the expression and executes it,
        returning either a list or single result based on query_type.

        Args:
            expression: AST expression representing the query
            query_type: Expected return type (List[T] or T)

        Returns:
            Query results (list or single entity)

        Example:
            ```python
            # Returns list
            results = await provider.execute_async(expr, List[Product])

            # Returns single result
            result = await provider.execute_async(expr, Product)
            ```
        """
        # Build Motor cursor from expression
        cursor = MotorQueryBuilder(self._collection, JavaScriptExpressionTranslator()).build(expression)

        # Determine if we're expecting a list or single result
        # Check if query_type is List or list type annotation
        is_list_type = False
        if query_type == List or query_type == list:
            is_list_type = True
        elif hasattr(query_type, "__origin__"):
            # Handle List[T] from typing
            is_list_type = query_type.__origin__ in (list, List)

        if is_list_type:
            # Return list of documents
            return [doc async for doc in cursor]
        else:
            # Return single document
            results = await cursor.to_list(length=1)
            return results[0] if results else None
