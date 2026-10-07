"""Independent specification checks, including CLI and lexical scope edges."""

import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from main import run_source
from primitives import initial_environment
from values import SchemeError


CASES = [
    ('arithmetic_identity', '(+) (*)', '0\n1\n'),
    ('unary_subtraction', '(- -8)', '8\n'),
    ('division_signs', '(/ -7 2) (/ 7 -2) (/ -7 -2)', '-3\n-3\n3\n'),
    ('large_division', '(/ 1000000000000000000000000000001 3)', '333333333333333333333333333333\n'),
    ('division_chain', '(/ 40 3 2) (/ 2)', '6\n0.5\n'),
    ('quotient_signs', '(quotient -7 2) (quotient 7 -2)', '-3\n-3\n'),
    ('modulo_signs', '(modulo -7 3) (modulo 7 -3)', '2\n-2\n'),
    ('expt_abs', '(expt 2 10) (abs -8)', '1024\n8\n'),
    ('all_comparisons', '(= 2 2 2) (< 1 2 3) (> 3 2 1) (<= 1 1 2) (>= 2 2 1)', '#t\n#t\n#t\n#t\n#t\n'),
    ('symbol_comparisons', "(< 'a 'b 'c) (= 'same 'same) (> 'a 'b)", '#t\n#t\n#f\n'),
    ('only_false_is_false', "(if 0 1 2) (if '() 3 4) (if \"\" 5 6) (not 0) (not #f)", '1\n3\n5\n#f\n#t\n'),
    ('empty_and_or', '(and) (or)', '#t\n#f\n'),
    ('and_or_return_values', '(and 1 2 3) (or #f 0 4)', '3\n0\n'),
    ('short_circuit', '(and #f (/ 1 0)) (or 7 (/ 1 0)) (if #t 9 (/ 1 0))', '#f\n7\n9\n'),
    ('if_missing_branch', '(if #f 3) 4', '4\n'),
    ('cond_no_match', '(cond (#f 2)) 3', '3\n'),
    ('cond_test_value', '(cond ((+ 1 2)) (else 9))', '3\n'),
    ('cond_body_sequence', '(cond (#f 0) (#t (display "ok") 7 8))', 'ok8\n'),
    ('begin_no_value', '(begin) (begin (display "x") (newline))', 'x\n'),
    ('define_return_name', '(define x 5) (+ x 2)', 'x\n7\n'),
    ('function_body_sequence', '(define (f x) (define y (+ x 1)) (* y 2)) (f 3)', 'f\n8\n'),
    ('anonymous_call', '((lambda (x) (* x 3)) 4)', '12\n'),
    ('recursive_factorial', '(define (f n) (if (= n 0) 1 (* n (f (- n 1))))) (f 8)', 'f\n40320\n'),
    ('lexical_scope', '(define x 10) (define (f y) (+ x y)) (let ((x 100)) (f 1))', 'x\nf\n11\n'),
    ('closure_escape', '(define (make x) (lambda (y) (+ x y))) (define f (make 7)) (let ((x 100)) (f 2))', 'make\nf\n9\n'),
    ('parallel_let', '(define x 9) (let ((x 1) (y x)) (+ x y)) x', 'x\n10\n9\n'),
    ('nested_let', '(let ((a 1)) (let ((b (+ a 1))) (* a b)))', '2\n'),
    ('empty_let', '(let () 1 2)', '2\n'),
    ('quote_symbol_and_empty', "'name '() '(1 (2 3) #f)", 'name\n()\n(1 (2 3) #f)\n'),
    ('quote_no_execution', "'(/ 1 0)", '(/ 1 0)\n'),
    ('pair_operations', "(car (cons 1 2)) (cdr (cons 1 2)) (cons 1 '(2 3))", '1\n2\n(1 2 3)\n'),
    ('list_operations', "(length '()) (append) (append '(1) '() '(2 3)) (list)", '0\n()\n(1 2 3)\n()\n'),
    ('proper_list_predicates', "(null? '()) (pair? '()) (pair? (cons 1 2)) (list? (cons 1 2)) (list? '(1 2))", '#t\n#f\n#t\n#f\n#t\n'),
    ('all_type_predicates', "(number? 1) (boolean? #f) (symbol? 'x) (string? \"x\") (procedure? car) (procedure? (lambda () 1))", '#t\n#t\n#t\n#t\n#t\n#t\n'),
    ('predicate_type_separation', "(number? #t) (boolean? 1) (symbol? \"x\") (string? 'x) (procedure? 1)", '#f\n#f\n#f\n#f\n#f\n'),
    ('numeric_predicates', '(zero? 0) (even? -8) (odd? -3)', '#t\n#t\n#t\n'),
    ('equality_type_separation', "(equal? #t 1) (equal? 'a \"a\") (eq? #f 0)", '#f\n#f\n#f\n'),
    ('identity_vs_structure', "(eq? '(1) '(1)) (equal? '(1 (2)) (list 1 (list 2))) (eq? '() '())", '#f\n#t\n#t\n'),
    ('shared_pair_identity', '(define xs (list 1 2)) (eq? xs xs) (eq? (cdr xs) (cdr xs))', 'xs\n#t\n#t\n'),
    ('dotted_pair_print', '(cons 1 (cons 2 3))', '(1 2 . 3)\n'),
    ('higher_order_map_filter', "(define (map f xs) (if (null? xs) '() (cons (f (car xs)) (map f (cdr xs))))) (define (filter p xs) (cond ((null? xs) '()) ((p (car xs)) (cons (car xs) (filter p (cdr xs)))) (else (filter p (cdr xs))))) (map (lambda (x) (* x x)) '(1 2 3)) (filter odd? '(1 2 3 4 5))", 'map\nfilter\n(1 4 9)\n(1 3 5)\n'),
    ('display_values', '(display "hi") (display #t) (display 3) (newline) "hi"', 'hi#t3\n"hi"\n'),
    ('string_escapes', '"a\\nb\\t\\\"c\\\\d"', '"a\\nb\\t\\\"c\\\\d"\n'),
    ('display_string_escapes', '(display "a\\nb\\t")', 'a\nb\t'),
    ('string_delimiters', '(display "(;quote\'inside)") ; ignored\n(+ 1 2)', "(;quote'inside)3\n"),
    ('case_sensitive_symbols', '(define x 1) (define X 2) (+ x X)', 'x\nX\n3\n'),
    ('comments_whitespace', '; first\n( +\t1 ;middle\n2) ;end', '3\n'),
]


class SpecificationTests(unittest.TestCase):
    pass


def create_test(program, expected):
    def test(self):
        output = io.StringIO()
        run_source(program, initial_environment(output), output)
        self.assertEqual(output.getvalue(), expected)
    return test


for name, program, expected in CASES:
    setattr(SpecificationTests, 'test_' + name, create_test(program, expected))


class CommandLineTests(unittest.TestCase):
    def test_standard_input_unicode_and_lf(self):
        result = subprocess.run([sys.executable, str(ROOT / 'src/main.py')],
                                input='(display "你好") (newline) (+ 1 2)'.encode(),
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '你好\n3\n'.encode())

    def test_multiple_files_share_bindings(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / 'first.scm'
            second = Path(directory) / 'second.scm'
            first.write_text('(define n 7)', encoding='utf-8')
            second.write_text('(+ n 2)', encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'src/main.py'), str(first), str(second)],
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, b'n\n9\n')

    def test_errors_do_not_contaminate_stdout(self):
        result = subprocess.run([sys.executable, str(ROOT / 'src/main.py')],
                                input=b'(car 3)', capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'Error:', result.stderr)


class InvalidInputTests(unittest.TestCase):
    def test_reject_malformed_or_invalid_programs(self):
        for source in ['(+ 1', ')', '"unfinished', 'missing-name', '(car 1)',
                       '(+ #t 1)', '((lambda (x) x) 1 2)', '(lambda (x x) x)']:
            with self.subTest(source=source):
                output = io.StringIO()
                with self.assertRaises(SchemeError):
                    run_source(source, initial_environment(output), output)


if __name__ == '__main__':
    unittest.main()
