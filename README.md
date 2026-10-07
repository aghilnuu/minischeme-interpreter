# mini-Scheme interpreter

A modular interpreter written in Python 3 using only the standard library.

## Run

```text
python3 src/main.py program.scm
python3 src/main.py first.scm second.scm
```

With no file arguments, the interpreter reads its program from standard input.
Multiple input files share their global environment. Each result is printed on
its own line; expressions with no result do not add output.

## Structure

- `lexer.py` and `reader.py`: tokens and expressions.
- `values.py`: symbols, pairs, procedures and equality semantics.
- `environment.py`: lexical variable bindings.
- `evaluator.py`: evaluation, closures and function application.
- `primitives.py`: arithmetic, comparisons, lists, predicates and output.
- `printer.py`: Scheme output notation.
- `main.py`: command-line entry point.

## Independent checks

```text
python3 -m unittest discover -s tests -v
```

The tests cover evaluation order, lexical scope, closures, recursion, pairs,
type distinctions, integer division, string escapes and command-line behavior.
