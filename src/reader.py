"""Read tokens into expressions and expand quote shorthand."""

import re
from lexer import StringToken, tokenize
from values import NIL, SchemeError, Symbol, make_list


def atom(token):
    if isinstance(token, StringToken):
        return token.value
    if token == '#t':
        return True
    if token == '#f':
        return False
    if re.fullmatch(r'[+-]?\d+', token):
        return int(token)
    if re.fullmatch(r'[+-]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][+-]?\d+)?', token):
        return float(token)
    return Symbol(token)


def read_all(source):
    tokens = tokenize(source)
    position = 0

    def read():
        nonlocal position
        if position == len(tokens):
            raise SchemeError('unexpected end of input')
        token = tokens[position]
        position += 1
        if isinstance(token, StringToken):
            return atom(token)
        if token == "'":
            return make_list([Symbol('quote'), read()])
        if token == ')':
            raise SchemeError('unexpected closing parenthesis')
        if token != '(':
            return atom(token)
        items = []
        tail = NIL
        while True:
            if position == len(tokens):
                raise SchemeError('missing closing parenthesis')
            if tokens[position] == ')':
                position += 1
                return make_list(items, tail)
            if tokens[position] == '.':
                if not items:
                    raise SchemeError('dot requires a preceding element')
                position += 1
                tail = read()
                if position == len(tokens) or tokens[position] != ')':
                    raise SchemeError('dotted pair requires one tail')
                position += 1
                return make_list(items, tail)
            items.append(read())

    expressions = []
    while position < len(tokens):
        expressions.append(read())
    return expressions
