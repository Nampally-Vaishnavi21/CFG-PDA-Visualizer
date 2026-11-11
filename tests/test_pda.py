"""Unit tests.  Run with:  pytest -v"""
import itertools
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pda import arithmetic, balanced, palindrome
from pda.test_cases import ARITHMETIC_CASES, BALANCED_CASES, PALINDROME_CASES

BAL, ARI, PAL = balanced.build_pda(), arithmetic.build_pda(), palindrome.build_pda()


def run_balanced(text):
    tokens, err = balanced.tokenize(text)
    return err is None and BAL.accepts(tokens)


def run_arithmetic(text):
    tokens, _, err = arithmetic.tokenize(text)
    return err is None and ARI.accepts(tokens)


def run_palindrome(text):
    tokens, err = palindrome.tokenize(text)
    return err is None and PAL.accepts(tokens)


@pytest.mark.parametrize("text,expected,reason", BALANCED_CASES)
def test_balanced_cases(text, expected, reason):
    assert run_balanced(text) == expected, reason


@pytest.mark.parametrize("text,expected,reason", ARITHMETIC_CASES)
def test_arithmetic_cases(text, expected, reason):
    assert run_arithmetic(text) == expected, reason


@pytest.mark.parametrize("text,expected,reason", PALINDROME_CASES)
def test_palindrome_cases(text, expected, reason):
    assert run_palindrome(text) == expected, reason


@pytest.mark.parametrize("cases", [BALANCED_CASES, ARITHMETIC_CASES, PALINDROME_CASES])
def test_at_least_five_of_each(cases):
    assert sum(1 for c in cases if c[1]) >= 5 and sum(1 for c in cases if not c[1]) >= 5


# ---------------------------------------------------------------- determinism
def test_determinism_claims():
    assert BAL.is_deterministic()            # balanced brackets: DPDA
    assert not PAL.is_deterministic()        # palindromes: genuinely nondeterministic
    assert not ARI.is_deterministic()        # grammar-derived PDA has ε-choices


# ---------------------------------------------------------------- exhaustive checks
def reference_balanced(s):
    """Independent definition: repeatedly delete adjacent pairs until nothing changes."""
    while True:
        t = s.replace("()", "").replace("[]", "").replace("{}", "")
        if t == s:
            return s == ""
        s = t


def test_balanced_pda_on_all_strings_up_to_length_6():
    for n in range(7):
        for w in itertools.product("()[]{}", repeat=n):
            w = "".join(w)
            assert BAL.accepts(list(w)) == reference_balanced(w), w


def test_palindrome_pda_on_all_strings_up_to_length_11():
    for n in range(12):
        for w in itertools.product("01", repeat=n):
            assert PAL.accepts(list(w)) == (w == w[::-1]), w


def test_grammars_agree_with_hand_built_pdas():
    """The CFG (via its own PDA) and the hand-designed PDA must define the same language."""
    for n in range(7):
        for w in itertools.product("()[]{}", repeat=n):
            steps, _ = balanced.GRAMMAR.derive(list(w))
            assert (steps is not None) == BAL.accepts(list(w)), w
    for n in range(10):
        for w in itertools.product("01", repeat=n):
            steps, _ = palindrome.GRAMMAR.derive(list(w))
            assert (steps is not None) == PAL.accepts(list(w)), w


def reference_expression(tokens):
    """Independent recursive-descent recogniser for grammar G2 (iterative form)."""
    pos = 0

    def expr():
        nonlocal pos
        if not term():
            return False
        while pos < len(tokens) and tokens[pos] in "+-":
            pos += 1
            if not term():
                return False
        return True

    def term():
        nonlocal pos
        if not factor():
            return False
        while pos < len(tokens) and tokens[pos] in "*/":
            pos += 1
            if not factor():
                return False
        return True

    def factor():
        nonlocal pos
        if pos < len(tokens) and tokens[pos] == "num":
            pos += 1
            return True
        if pos < len(tokens) and tokens[pos] == "(":
            pos += 1
            if expr() and pos < len(tokens) and tokens[pos] == ")":
                pos += 1
                return True
        return False

    return expr() and pos == len(tokens)


def test_arithmetic_pda_matches_reference_parser():
    rng = random.Random(7)
    accepted = 0
    for _ in range(4000):
        tokens = [rng.choice(arithmetic.TERMINALS + ["num", "num"]) for _ in range(rng.randint(0, 9))]
        expected = reference_expression(tokens)
        assert ARI.accepts(tokens) == expected, tokens
        accepted += expected
    assert accepted > 50


# ---------------------------------------------------------------- derivations and values
def test_derivation_ends_in_the_input():
    for grammar, w in [(balanced.GRAMMAR, list("([]{})")), (palindrome.GRAMMAR, list("10101")),
                       (arithmetic.GRAMMAR, ["num", "+", "num", "*", "num"])]:
        steps, _ = grammar.derive(w)
        assert steps[0][0] == [grammar.start] and steps[-1][0] == w


@pytest.mark.parametrize("text,value", [("2+3*4", 14), ("(2+3)*4", 20), ("8-3-2", 3),
                                        ("16/4/2", 2), ("10/2-3", 2), ("3.5 * (2 + 0.25)", 7.875)])
def test_precedence_and_associativity(text, value):
    tokens, lexemes, _ = arithmetic.tokenize(text)
    result = ARI.search(tokens)
    assert arithmetic.evaluate(arithmetic.parse_tree(result, lexemes)) == pytest.approx(value)


def test_lexer_errors():
    assert arithmetic.tokenize("3.")[2] is not None
    assert arithmetic.tokenize("2 $ 3")[2] is not None
    assert arithmetic.tokenize("12.50+(3)")[0] == ["num", "+", "(", "num", ")"]


def test_stack_trace_of_balanced_run():
    result = BAL.search(list("([])"))
    stacks = [" ".join(n.stack) for n in result.path(result.accepted_index)]
    assert stacks == ["Z0", "( Z0", "[ ( Z0", "( Z0", "Z0", "Z0"]
