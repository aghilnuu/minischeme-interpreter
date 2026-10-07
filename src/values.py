"""Scheme values, distinct from Python's booleans and strings."""

from dataclasses import dataclass


class SchemeError(Exception):
    """A readable error for invalid Scheme input."""


@dataclass(frozen=True)
class Symbol:
    name: str


class EmptyList:
    pass


NIL = EmptyList()


@dataclass(eq=False)
class Pair:
    first: object
    rest: object


@dataclass(eq=False)
class Builtin:
    name: str
    function: object


@dataclass(eq=False)
class Closure:
    parameters: tuple
    body: tuple
    environment: object


def is_number(value):
    # In Python bool inherits from int; in Scheme they are separate types.
    return type(value) in (int, float)


def is_true(value):
    return value is not False


def make_list(items, tail=NIL):
    for item in reversed(list(items)):
        tail = Pair(item, tail)
    return tail


def to_list(value):
    result = []
    while isinstance(value, Pair):
        result.append(value.first)
        value = value.rest
    if value is not NIL:
        raise SchemeError('expected a proper list')
    return result


def is_list(value):
    while isinstance(value, Pair):
        value = value.rest
    return value is NIL


def eq_value(left, right):
    if is_number(left) and is_number(right):
        return left == right
    if type(left) is bool and type(right) is bool:
        return left == right
    if isinstance(left, Symbol) and isinstance(right, Symbol):
        return left.name == right.name
    # Compound values compare by identity, not dataclass/Python equality.
    return left is right


def equal_value(left, right):
    if isinstance(left, Pair) and isinstance(right, Pair):
        return equal_value(left.first, right.first) and equal_value(left.rest, right.rest)
    if type(left) is str and type(right) is str:
        return left == right
    return eq_value(left, right)
