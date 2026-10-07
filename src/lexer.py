"""Split source into tokens without treating string contents as syntax."""

from dataclasses import dataclass
from values import SchemeError


@dataclass(frozen=True)
class StringToken:
    value: str


def tokenize(source):
    tokens = []
    i = 0
    escapes = {'n': '\n', 't': '\t', '"': '"', '\\': '\\'}
    while i < len(source):
        char = source[i]
        if char.isspace():
            i += 1
        elif char == ';':
            end = source.find('\n', i)
            i = len(source) if end < 0 else end + 1
        elif char in "()'":
            tokens.append(char)
            i += 1
        elif char == '"':
            i += 1
            text = []
            while i < len(source) and source[i] != '"':
                if source[i] == '\\':
                    i += 1
                    if i == len(source) or source[i] not in escapes:
                        raise SchemeError('invalid string escape')
                    text.append(escapes[source[i]])
                else:
                    text.append(source[i])
                i += 1
            if i == len(source):
                raise SchemeError('unterminated string')
            tokens.append(StringToken(''.join(text)))
            i += 1
        else:
            start = i
            while i < len(source) and not source[i].isspace() and source[i] not in "()';\"":
                i += 1
            tokens.append(source[start:i])
    return tokens
