"""CLI entry: evaluate files in order, or read a program from standard input."""

import sys
from pathlib import Path
from evaluator import evaluate
from primitives import initial_environment
from printer import format_value
from reader import read_all
from values import SchemeError


def run_source(source, environment, output):
    for expression in read_all(source):
        result = evaluate(expression, environment)
        if result is not None:
            output.write(format_value(result) + '\n')


def main():
    # Keep output UTF-8 with LF newlines on Windows as well as Linux.
    sys.stdout.reconfigure(encoding='utf-8', newline='\n')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')
    sys.setrecursionlimit(10000)
    environment = initial_environment(sys.stdout)
    try:
        if sys.argv[1:]:
            for filename in sys.argv[1:]:
                run_source(Path(filename).read_text(encoding='utf-8-sig'), environment, sys.stdout)
        else:
            run_source(sys.stdin.read(), environment, sys.stdout)
    except (SchemeError, OSError, ArithmeticError, RecursionError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
