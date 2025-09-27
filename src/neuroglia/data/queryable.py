import ast
import inspect
import os
from abc import ABC, abstractclassmethod
from ast import Attribute, Name, NodeTransformer, expr
from collections.abc import Callable
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")
""" Represents the type of data associated to a queryable """


class QueryProvider(ABC):
    """
    Defines the abstraction for services that create and execute queries against data sources.

    This abstraction enables the implementation of LINQ-style query operations that can be
    translated to various data store query languages (SQL, MongoDB, etc.) while maintaining
    a consistent Python interface.

    Examples:
        ```python
        class MongoQueryProvider(QueryProvider):
            def create_query(self, element_type: Type, expression: expr) -> Queryable:
                return MongoQueryable(self, element_type, expression)

            def execute(self, expression: expr, query_type: Type) -> Any:
                mongo_query = self.translate_to_mongodb(expression)
                return self.collection.find(mongo_query)
        ```

    See Also:
        - Data Access Patterns: https://bvandewe.github.io/pyneuro/features/data-access/
        - Repository Pattern Guide: https://bvandewe.github.io/pyneuro/patterns/
    """

    @abstractclassmethod
    def create_query(self, element_type: type, expression: expr) -> "Queryable":
        """Creates a new queryable based on the specified expression"""
        raise NotImplementedError()

    @abstractclassmethod
    def execute(self, expression: expr, query_type: type) -> Any:
        """Executes the specified query expression"""
        raise NotImplementedError()


class Queryable(Generic[T]):
    """
    Provides LINQ-style query functionality for evaluating expressions against data sources.

    This abstraction enables fluent, composable queries that can be translated to various
    data store query languages while maintaining type safety and IntelliSense support.

    Type Parameters:
        T: The type of elements in the queryable sequence

    Attributes:
        provider (QueryProvider): The service that translates and executes queries
        expression (expr): The AST expression representing the current query

    Examples:
        ```python
        # Fluent query operations
        products = repository.query(Product) \\
            .where(lambda p: p.category == "Electronics") \\
            .order_by(lambda p: p.price) \\
            .take(10) \\
            .to_list()

        # Complex filtering and projection
        expensive_items = repository.query(OrderItem) \\
            .where(lambda i: i.unit_price > 100.0) \\
            .select(lambda i: [i.product_name, i.unit_price]) \\
            .to_list()
        ```

    See Also:
        - Data Access Patterns: https://bvandewe.github.io/pyneuro/features/data-access/
        - Repository Pattern Guide: https://bvandewe.github.io/pyneuro/patterns/
    """

    def __init__(self, provider: QueryProvider, expression: Optional[expr] = None):
        self.provider = provider
        self.expression = ast.Name(id="__query") if expression is None else expression

    expression: expr
    """ Gets the expression that is associated with the queryable """

    provider: QueryProvider
    """ Gets the service used to create and execute queries associated with the data source """

    def get_element_type(self) -> type:
        """Gets the type of elements to query against"""
        return self.__orig_class__.__args__[0]

    def first_or_default(self, predicate: Callable[[T], bool] = None) -> T:
        """Gets the first element in the sequence that matches the specified predicate, if any"""
        frame = inspect.currentframe().f_back
        frame_info = inspect.getframeinfo(frame)
        variables = {**frame.f_locals}
        lambda_src = self._get_lambda_source_code(predicate, frame_info.positions.end_col_offset)
        lambda_tree = ast.parse(lambda_src)
        lambda_expression = lambda_tree.body[0].value
        expression = VariableExpressionReplacer(variables).visit(
            ast.Call(
                func=ast.Attribute(value=self.expression, attr="first", ctx=ast.Load()),
                args=[lambda_expression],
                keywords=[],
            )
        )
        query = self.provider.create_query(self.get_element_type(), expression)
        return self.provider.execute(query.expression, T)

    def first(self, predicate: Callable[[T], bool] = None) -> T:
        """Gets the first element in the sequence that matches the specified predicate, if any"""
        result = self.first_or_default(predicate)
        if result is None and T != None:
            raise Exception("No match")
        return result

    def last_or_default(self, predicate: Callable[[T], bool] = None) -> T:
        """Gets the last element in the sequence that matches the specified predicate, if any"""
        frame = inspect.currentframe().f_back
        frame_info = inspect.getframeinfo(frame)
        variables = {**frame.f_locals}
        lambda_src = self._get_lambda_source_code(predicate, frame_info.positions.end_col_offset)
        lambda_tree = ast.parse(lambda_src)
        lambda_expression = lambda_tree.body[0].value
        expression = VariableExpressionReplacer(variables).visit(
            ast.Call(
                func=ast.Attribute(value=self.expression, attr="last", ctx=ast.Load()),
                args=[lambda_expression],
                keywords=[],
            )
        )
        query = self.provider.create_query(self.get_element_type(), expression)
        return self.provider.execute(query.expression, T)

    def last(self, predicate: Callable[[T], bool] = None) -> T:
        """Gets the last element in the sequence that matches the specified predicate, if any"""
        result = self.last_or_default(predicate)
        if result is None and T != None:
            raise Exception("No match")
        return result

    def order_by(self, selector: Callable[[T], Any]):
        """Orders the sequence using the specified attribute"""
        selector_source = self._get_lambda_source_code(selector)
        selector_tree = ast.parse(selector_source)
        selector_lambda_expression = selector_tree.body[0].value
        if not isinstance(selector_lambda_expression.body, Attribute):
            raise Exception("The specified expression must be of type Attribute")
        expression = ast.Call(
            func=ast.Attribute(value=self.expression, attr="order_by", ctx=ast.Load()),
            args=[selector_lambda_expression],
            keywords=[],
        )
        return self.provider.create_query(self.get_element_type(), expression)

    def order_by_descending(self, selector: Callable[[T], Any]):
        """Orders the sequence in a descending fashion using the specified attribute"""
        selector_source = self._get_lambda_source_code(selector)
        selector_tree = ast.parse(selector_source)
        selector_lambda_expression = selector_tree.body[0].value
        if not isinstance(selector_lambda_expression.body, Attribute):
            raise Exception("The specified expression must be of type Attribute")
        expression = ast.Call(
            func=ast.Attribute(value=self.expression, attr="order_by_descending", ctx=ast.Load()),
            args=[selector_lambda_expression],
            keywords=[],
        )
        return self.provider.create_query(self.get_element_type(), expression)

    def select(self, selector: Callable[[T], Any]):
        """Projects each element of a sequence into a new form"""
        frame = inspect.currentframe().f_back
        variables = {**frame.f_locals}
        selector_source = self._get_lambda_source_code(selector)
        selector_tree = ast.parse(selector_source)
        selector_lambda_expression = selector_tree.body[0].value
        if not isinstance(selector_lambda_expression.body, Attribute) and not isinstance(selector_lambda_expression.body, ast.List):
            raise Exception("The specified expression must be of type Attribute or List[Attribute]")
        expression = VariableExpressionReplacer(variables).visit(
            ast.Call(
                func=ast.Attribute(value=self.expression, attr="select", ctx=ast.Load()),
                args=[selector_lambda_expression],
                keywords=[],
            )
        )
        return self.provider.create_query(self.get_element_type(), expression)

    def skip(self, amount: int):
        """Bypasses a specified number of elements in a sequence and then returns the remaining elements."""
        expression = ast.Call(
            func=ast.Attribute(value=self.expression, attr="skip", ctx=ast.Load()),
            args=[ast.Constant(value=amount)],
            keywords=[],
        )
        return self.provider.create_query(self.get_element_type(), expression)

    def take(self, amount: int):
        """Selects a specified amount of contiguous elements from the start of a sequence"""
        expression = ast.Call(
            func=ast.Attribute(value=self.expression, attr="take", ctx=ast.Load()),
            args=[ast.Constant(value=amount)],
            keywords=[],
        )
        return self.provider.create_query(self.get_element_type(), expression)

    def where(self, predicate: Callable[[T], bool]) -> "Queryable[T]":
        """Filters a sequence of values based on a predicate."""
        frame = inspect.currentframe().f_back
        frame_info = inspect.getframeinfo(frame)
        variables = {**frame.f_locals}
        lambda_src = self._get_lambda_source_code(predicate, frame_info.positions.end_col_offset)
        lambda_tree = ast.parse(lambda_src)
        lambda_expression = lambda_tree.body[0].value
        expression = VariableExpressionReplacer(variables).visit(
            ast.Call(
                func=ast.Attribute(value=self.expression, attr="where", ctx=ast.Load()),
                args=[lambda_expression],
                keywords=[],
            )
        )
        return self.provider.create_query(self.get_element_type(), expression)

    def to_list(self) -> list[T]:
        """Executes the queryable"""
        return self.provider.execute(self.expression, List)

    def __str__(self) -> str:
        return ast.unparse(self.expression)

    def _get_lambda_source_code(self, function: Callable, max_col_offset: int):
        """Gets the source code of the specified lambda

        Args:
            function (Callable): The lambda to get the source code of
            max_col_offset (int): The maximum column offset to walk the AST tree for the target lamba

        Notes:
            Credits to https://gist.github.com/Xion/617c1496ff45f3673a5692c3b0e3f75a
        """
        source_lines, _ = inspect.getsourcelines(function)
        if len(source_lines) != 1:
            return None
        source_text = os.linesep.join(source_lines).strip()
        source_ast = ast.parse(source_text)
        lambda_node = next(
            (node for node in ast.walk(source_ast) if isinstance(node, ast.Lambda) and node.col_offset <= max_col_offset),
            None,
        )
        if lambda_node is None:
            return None
        lambda_text = source_text[lambda_node.col_offset : lambda_node.end_col_offset]
        return lambda_text


class VariableExpressionReplacer(NodeTransformer):
    """
    AST node transformer that replaces variable references with their literal values.

    This utility class is used internally by the queryable system to substitute variable
    values into lambda expressions during query translation, enabling proper query
    parameterization across different data store backends.

    Attributes:
        variables (Dict[str, Any]): Mapping of variable names to their values

    Examples:
        ```python
        # Internal usage during query translation
        variables = {"category": "Electronics", "min_price": 100.0}
        replacer = VariableExpressionReplacer(variables)

        # Transforms: lambda p: p.category == category and p.price > min_price
        # Into: lambda p: p.category == "Electronics" and p.price > 100.0
        ```

    See Also:
        - Data Access Patterns: https://bvandewe.github.io/pyneuro/features/data-access/
    """

    def __init__(self, variables: dict[str, Any]):
        super().__init__()
        self.variables = variables

    variables: dict[str, Any] = dict[str, Any]()

    def visit_Name(self, node: Name) -> Any:
        if node.id not in self.variables.keys():
            return node
        value = self.variables[node.id]
        return ast.Constant(value)
