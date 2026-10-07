"""Print values using Scheme notation and exact string escaping."""

from values import NIL, Builtin, Closure, Pair, Symbol


def format_value(value):
    if value is True:
        return '#t'
    if value is False:
        return '#f'
    if value is NIL:
        return '()'
    if isinstance(value, Symbol):
        return value.name
    if type(value) is str:
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        escaped = escaped.replace('\n', '\\n').replace('\t', '\\t')
        return '"' + escaped + '"'
    if isinstance(value, Pair):
        parts = []
        current = value
        while isinstance(current, Pair):
            parts.append(format_value(current.first))
            current = current.rest
        if current is not NIL:
            parts.extend(['.', format_value(current)])
        return '(' + ' '.join(parts) + ')'
    if isinstance(value, (Builtin, Closure)):
        return '#<procedure>'
    return str(value)
