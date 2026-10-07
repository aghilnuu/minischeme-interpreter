"""Evaluate expressions in lexical environments, respecting short circuits."""

from environment import Environment
from values import Builtin, Closure, Pair, SchemeError, Symbol, is_true, to_list


def require(args, minimum, maximum=None):
    if len(args) < minimum or (maximum is not None and len(args) > maximum):
        raise SchemeError('wrong number of operands in special form')


def symbol_name(value):
    if not isinstance(value, Symbol):
        raise SchemeError('expected a symbol')
    return value.name


def make_closure(parameters, body, env):
    names = tuple(symbol_name(item) for item in to_list(parameters))
    if len(set(names)) != len(names):
        raise SchemeError('duplicate parameter')
    require(body, 1)
    return Closure(names, tuple(body), env)


def evaluate_sequence(expressions, env):
    result = None
    for expr in expressions:
        result = evaluate(expr, env)
    return result


def apply(procedure, arguments):
    if isinstance(procedure, Builtin):
        return procedure.function(arguments)
    if isinstance(procedure, Closure):
        if len(arguments) != len(procedure.parameters):
            raise SchemeError('wrong number of function arguments')
        local = Environment(procedure.environment)
        for name, value in zip(procedure.parameters, arguments):
            local.define(name, value)
        return evaluate_sequence(procedure.body, local)
    raise SchemeError('attempted to call a non-procedure')


def evaluate(expr, env):
    if isinstance(expr, Symbol):
        return env.lookup(expr.name)
    if not isinstance(expr, Pair):
        return expr
    parts = to_list(expr)
    operator, args = parts[0], parts[1:]
    keyword = operator.name if isinstance(operator, Symbol) else None

    if keyword == 'quote':
        require(args, 1, 1)
        return args[0]
    if keyword == 'if':
        require(args, 2, 3)
        if is_true(evaluate(args[0], env)):
            return evaluate(args[1], env)
        return evaluate(args[2], env) if len(args) == 3 else None
    if keyword == 'cond':
        for index, clause in enumerate(args):
            entries = to_list(clause)
            require(entries, 1)
            test = entries[0]
            if isinstance(test, Symbol) and test.name == 'else':
                if index != len(args)-1:
                    raise SchemeError('else must be the final cond clause')
                return evaluate_sequence(entries[1:], env)
            value = evaluate(test, env)
            if is_true(value):
                return evaluate_sequence(entries[1:], env) if len(entries) > 1 else value
        return None
    if keyword in ('and', 'or'):
        value = keyword == 'and'
        for argument in args:
            value = evaluate(argument, env)
            if (keyword == 'and' and not is_true(value)) or (keyword == 'or' and is_true(value)):
                return value
        return value
    if keyword == 'define':
        require(args, 2)
        target = args[0]
        if isinstance(target, Pair):
            name = symbol_name(target.first)
            value = make_closure(target.rest, args[1:], env)
        else:
            require(args, 2, 2)
            name = symbol_name(target)
            value = evaluate(args[1], env)
        # A closure retains the environment object, enabling recursion.
        env.define(name, value)
        return Symbol(name)
    if keyword == 'lambda':
        require(args, 2)
        return make_closure(args[0], args[1:], env)
    if keyword == 'let':
        require(args, 2)
        bindings = []
        for binding in to_list(args[0]):
            entry = to_list(binding)
            require(entry, 2, 2)
            bindings.append((symbol_name(entry[0]), evaluate(entry[1], env)))
        # All right-hand sides see the outer environment, not earlier bindings.
        local = Environment(env)
        for name, value in bindings:
            local.define(name, value)
        return evaluate_sequence(args[1:], local)
    if keyword == 'begin':
        return evaluate_sequence(args, env)

    procedure = evaluate(operator, env)
    arguments = [evaluate(argument, env) for argument in args]
    return apply(procedure, arguments)
