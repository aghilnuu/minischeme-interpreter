"""The specified built-in procedures; no hidden host-language evaluation."""

import math
import operator
from environment import Environment
from printer import format_value
from values import (NIL, Builtin, Closure, Pair, SchemeError, Symbol,
                    eq_value, equal_value, is_list, is_number, is_true,
                    make_list, to_list)


def check_count(name, args, minimum, maximum=None):
    if len(args) < minimum or (maximum is not None and len(args) > maximum):
        raise SchemeError(f'{name}: wrong number of arguments')


def numbers(name, args):
    if not all(is_number(value) for value in args):
        raise SchemeError(f'{name}: expected numbers')


def unary(name, function):
    def call(args):
        check_count(name, args, 1, 1)
        return function(args[0])
    return call


def numeric(name, function, minimum=0, maximum=None):
    def call(args):
        check_count(name, args, minimum, maximum)
        numbers(name, args)
        return function(args)
    return call


def subtract(args):
    if len(args) == 1:
        return -args[0]
    result = args[0]
    for value in args[1:]:
        result -= value
    return result


def truncate_division(left, right):
    if right == 0:
        raise SchemeError('division by zero')
    # Avoid float conversion so large integer division stays exact.
    if type(left) is int and type(right) is int:
        magnitude = abs(left) // abs(right)
        return -magnitude if (left < 0) != (right < 0) else magnitude
    return math.trunc(left / right)


def divide(args):
    if len(args) == 1:
        return 1 / args[0]
    result = args[0]
    for value in args[1:]:
        result = truncate_division(result, value) if type(result) is int and type(value) is int else result / value
    return result


def comparison(name, operation):
    def call(args):
        check_count(name, args, 2)
        if all(is_number(value) for value in args):
            values = args
        elif all(isinstance(value, Symbol) for value in args):
            values = [value.name for value in args]
        else:
            raise SchemeError(f'{name}: expected numbers or symbols')
        return all(operation(a, b) for a, b in zip(values, values[1:]))
    return call


def pair_part(value, first):
    if not isinstance(value, Pair):
        raise SchemeError('car/cdr: expected a pair')
    return value.first if first else value.rest


def append(args):
    if not args:
        return NIL
    # Copy all preceding lists and retain the final tail, as in Scheme.
    items = []
    for value in args[:-1]:
        items.extend(to_list(value))
    return make_list(items, args[-1])


def initial_environment(output):
    env = Environment()
    procedures = {
        '+': numeric('+', sum),
        '-': numeric('-', subtract, 1),
        '*': numeric('*', math.prod),
        '/': numeric('/', divide, 1),
        'modulo': numeric('modulo', lambda a: a[0] % a[1], 2, 2),
        'quotient': numeric('quotient', lambda a: truncate_division(*a), 2, 2),
        'expt': numeric('expt', lambda a: a[0] ** a[1], 2, 2),
        'abs': numeric('abs', lambda a: abs(a[0]), 1, 1),
        'not': unary('not', lambda a: not is_true(a)),
        'car': unary('car', lambda a: pair_part(a, True)),
        'cdr': unary('cdr', lambda a: pair_part(a, False)),
        'list': lambda a: make_list(a),
        'length': unary('length', lambda a: len(to_list(a))),
        'append': append,
        'null?': unary('null?', lambda a: a is NIL),
        'pair?': unary('pair?', lambda a: isinstance(a, Pair)),
        'list?': unary('list?', is_list),
        'number?': unary('number?', is_number),
        'boolean?': unary('boolean?', lambda a: type(a) is bool),
        'symbol?': unary('symbol?', lambda a: isinstance(a, Symbol)),
        'string?': unary('string?', lambda a: type(a) is str),
        'procedure?': unary('procedure?', lambda a: isinstance(a, (Builtin, Closure))),
        'zero?': numeric('zero?', lambda a: a[0] == 0, 1, 1),
        'even?': numeric('even?', lambda a: a[0] % 2 == 0, 1, 1),
        'odd?': numeric('odd?', lambda a: a[0] % 2 != 0, 1, 1),
    }
    for name, operation in [('=', operator.eq), ('<', operator.lt), ('>', operator.gt),
                            ('<=', operator.le), ('>=', operator.ge)]:
        procedures[name] = comparison(name, operation)

    def cons(args):
        check_count('cons', args, 2, 2)
        return Pair(*args)

    def equality(name, function):
        def call(args):
            check_count(name, args, 2, 2)
            return function(*args)
        return call

    def display(args):
        check_count('display', args, 1, 1)
        value = args[0]
        output.write(value if type(value) is str else format_value(value))
        return None

    def newline(args):
        check_count('newline', args, 0, 0)
        output.write('\n')
        return None

    procedures.update({'cons': cons, 'eq?': equality('eq?', eq_value),
                       'equal?': equality('equal?', equal_value),
                       'display': display, 'newline': newline})
    for name, function in procedures.items():
        env.define(name, Builtin(name, function))
    return env
