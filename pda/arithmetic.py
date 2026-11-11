"""Case study 2 - arithmetic expressions with + - * / and parentheses.

Two stages, exactly as in a compiler:
  1. LEXER  (regular / finite-state): characters → tokens.  Every number becomes the
     single terminal `num`.
  2. PARSER (context-free / PDA): checks the token sequence against the grammar.

Three grammars for the same language are discussed:
  G1  E → E+E | E-E | E*E | E/E | (E) | num                 ambiguous
  G2  E → E+T | E-T | T ;  T → T*F | T/F | F ;  F → (E)|num  unambiguous, encodes precedence
  G3  the same as G2 with left recursion removed            used to build the PDA
"""
from .cfg import CFG
from .pda import EPS, Z0

TERMINALS = ["num", "+", "-", "*", "/", "(", ")"]

G1_LINES = ["E → E + E | E - E | E * E | E / E | ( E ) | num"]
G2_LINES = ["E → E + T | E - T | T", "T → T * F | T / F | F", "F → ( E ) | num"]

# G3: left recursion removed  (A → Aα | β   becomes   A → βA',  A' → αA' | ε)
GRAMMAR = CFG(
    "G3", ["E", "E'", "T", "T'", "F"], TERMINALS,
    [("E", ["T", "E'"]),
     ("E'", ["+", "T", "E'"]), ("E'", ["-", "T", "E'"]), ("E'", []),
     ("T", ["F", "T'"]),
     ("T'", ["*", "F", "T'"]), ("T'", ["/", "F", "T'"]), ("T'", []),
     ("F", ["(", "E", ")"]), ("F", ["num"])],
    "E",
    notes={
        ("E", ("T", "E'")): "An expression is a term followed by an optional tail of + or - terms.",
        ("E'", ("+", "T", "E'")): "Tail: add another term.",
        ("E'", ("-", "T", "E'")): "Tail: subtract another term.",
        ("E'", ()): "Tail ends (no more + or -).",
        ("T", ("F", "T'")): "A term is a factor followed by an optional tail of * or / factors.",
        ("T'", ("*", "F", "T'")): "Tail: multiply by another factor.",
        ("T'", ("/", "F", "T'")): "Tail: divide by another factor.",
        ("T'", ()): "Tail ends (no more * or /).",
        ("F", ("(", "E", ")")): "A factor can be a whole expression in parentheses - this gives nesting.",
        ("F", ("num",)): "A factor can be a number.",
    })


def build_pda():
    """The PDA is obtained from G3 by the standard CFG → PDA construction."""
    return GRAMMAR.to_pda()


# ------------------------------------------------------------------ lexer
def tokenize(text):
    """Finite-state scanner.  Returns (tokens, lexemes, error).

    number = digit+ ( '.' digit+ )?      spaces are skipped
    """
    tokens, lexemes = [], []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch in "+-*/()":
            tokens.append(ch)
            lexemes.append(ch)
            i += 1
        elif "0" <= ch <= "9":
            j = i
            while j < n and "0" <= text[j] <= "9":
                j += 1
            if j < n and text[j] == ".":
                k = j + 1
                while k < n and "0" <= text[k] <= "9":
                    k += 1
                if k == j + 1:
                    return tokens, lexemes, f"Lexical error at character {j + 1}: a digit must follow the decimal point."
                j = k
            tokens.append("num")
            lexemes.append(text[i:j])
            i = j
        else:
            return tokens, lexemes, f"Lexical error at character {i + 1}: '{ch}' is not in the alphabet."
    return tokens, lexemes, None


# ------------------------------------------------------------------ messages
def explain(result):
    """'Expected …' message built from every branch that reached the furthest token."""
    furthest = max(result.nodes[i].pos for i in result.leaves())
    expected = set()
    for i in result.leaves():
        node = result.nodes[i]
        if node.pos == furthest and node.stack:
            top = node.stack[0]
            if top in TERMINALS:
                expected.add(top)
            elif top == Z0:
                expected.add("end of input")
    expected = ", ".join(sorted(expected)) or "nothing"
    if furthest < len(result.tokens):
        return f"Syntax error at token {furthest + 1} ('{result.tokens[furthest]}'). Expected: {expected}."
    return f"Unexpected end of input after {furthest} token(s). Expected: {expected}."


# ------------------------------------------------------------------ parse tree
class Tree:
    def __init__(self, symbol):
        self.symbol, self.children, self.lexeme = symbol, [], None


def parse_tree(result, lexemes):
    """Rebuild the parse tree from the accepting run (each expansion adds children)."""
    root = Tree(GRAMMAR.start)
    stack = [root]                      # tree nodes in the same order as the PDA stack
    pos = 0
    for node in result.path(result.accepted_index):
        rule = node.rule
        if rule is None or rule.state != "q1":
            continue
        if rule.read == EPS and rule.top in GRAMMAR.variables:       # expand
            parent = stack.pop(0)
            parent.children = [Tree(s) for s in rule.push]
            stack = parent.children + stack
        elif rule.read != EPS:                                       # match a terminal
            leaf = stack.pop(0)
            leaf.lexeme = lexemes[pos]
            pos += 1
    return root


def tree_dot(root):
    lines = ['digraph T { bgcolor="transparent"; pad=0.2; ranksep=0.35; nodesep=0.25;',
             'node [fontname="Helvetica", fontsize=11, shape=circle, style=filled, fillcolor="#F4F7FB", color="#1F3A5F", width=0.4, fixedsize=false];',
             'edge [color="#5B6B7F", arrowhead=none];']
    counter = [0]

    def walk(t):
        my = counter[0]
        counter[0] += 1
        if t.symbol in GRAMMAR.variables:
            lines.append(f'n{my} [label="{t.symbol}"];')
            if not t.children:
                eps = counter[0]
                counter[0] += 1
                lines.append(f'n{eps} [label="ε", shape=plaintext, fillcolor="transparent"];')
                lines.append(f"n{my} -> n{eps};")
        else:
            label = t.lexeme if t.lexeme is not None else t.symbol
            lines.append(f'n{my} [label="{label}", shape=box, style="rounded,filled", fillcolor="#FFE9A8"];')
        for c in t.children:
            lines.append(f"n{my} -> n{walk(c)};")
        return my

    walk(root)
    lines.append("}")
    return "\n".join(lines)


def evaluate(root):
    """Value of the expression, computed from the parse tree.

    This is SEMANTICS (beyond the PDA).  It is shown only to confirm that the
    grammar groups operators with the usual precedence and left associativity.
    Raises ZeroDivisionError for division by zero.
    """
    def expr(t):                         # E → T E'
        return tail(term(t.children[0]), t.children[1], term)

    def term(t):                         # T → F T'
        return tail(factor(t.children[0]), t.children[1], factor)

    def tail(value, t, operand):         # X' → op Y X' | ε   (left-associative)
        while t.children:
            op, right = t.children[0].symbol, operand(t.children[1])
            if op == "+":
                value += right
            elif op == "-":
                value -= right
            elif op == "*":
                value *= right
            else:
                value /= right
            t = t.children[2]
        return value

    def factor(t):                       # F → ( E ) | num
        if len(t.children) == 3:
            return expr(t.children[1])
        return float(t.children[0].lexeme)

    return expr(root)


# Two different parse trees of  num + num * num  under the ambiguous grammar G1.
AMBIGUITY_TREE_A = '''digraph A { bgcolor="transparent"; label="Tree 1: num + (num * num)"; labelloc=t; fontname="Helvetica"; fontsize=12;
node [fontname="Helvetica", fontsize=11, shape=circle, style=filled, fillcolor="#F4F7FB", color="#1F3A5F"]; edge [arrowhead=none, color="#5B6B7F"];
e0 [label="E"]; e1 [label="E"]; p [label="+", shape=plaintext, fillcolor="transparent"]; e2 [label="E"];
n1 [label="num", shape=box]; e3 [label="E"]; m [label="*", shape=plaintext, fillcolor="transparent"]; e4 [label="E"]; n2 [label="num", shape=box]; n3 [label="num", shape=box];
e0 -> e1; e0 -> p; e0 -> e2; e1 -> n1; e2 -> e3; e2 -> m; e2 -> e4; e3 -> n2; e4 -> n3; }'''
AMBIGUITY_TREE_B = '''digraph B { bgcolor="transparent"; label="Tree 2: (num + num) * num"; labelloc=t; fontname="Helvetica"; fontsize=12;
node [fontname="Helvetica", fontsize=11, shape=circle, style=filled, fillcolor="#F4F7FB", color="#1F3A5F"]; edge [arrowhead=none, color="#5B6B7F"];
e0 [label="E"]; e1 [label="E"]; m [label="*", shape=plaintext, fillcolor="transparent"]; e2 [label="E"];
e3 [label="E"]; p [label="+", shape=plaintext, fillcolor="transparent"]; e4 [label="E"]; n1 [label="num", shape=box]; n2 [label="num", shape=box]; n3 [label="num", shape=box];
e0 -> e1; e0 -> m; e0 -> e2; e1 -> e3; e1 -> p; e1 -> e4; e3 -> n1; e4 -> n2; e2 -> n3; }'''

INFO = {
    "title": "Arithmetic Expression Validator",
    "language": "L_exp = L(G2): well-formed infix expressions built from numbers, the binary "
                "operators + - * / and parentheses.",
    "alphabet": "Character alphabet: digits 0-9, the decimal point, + - * / ( ) and spaces. "
                "Token alphabet used by the grammar and the PDA: Σ = { num, +, -, *, /, (, ) }.",
    "why_not_regular": "Expressions contain nested parentheses. The strings (ⁿ num )ⁿ are in L_exp "
        "for every n, and pumping the block of '(' (exactly as for balanced brackets) produces "
        "unmatched parentheses. Recognising L_exp requires matching each '(' with a later ')' at "
        "unbounded depth, which needs a stack. (Without parentheses the language num (op num)* "
        "would be regular.)",
    "determinism": "As a PDA, the machine built from G3 is nondeterministic: with E' or T' or F on "
        "top of the stack several ε-expansions are possible. But G3 is LL(1) - the next input "
        "token always identifies the single expansion that can succeed - so L_exp is a "
        "deterministic CFL and a real parser never backtracks. The simulator explores all branches "
        "and the wrong ones die after one move.",
    "ambiguity": "G1 is AMBIGUOUS. num + num * num has two leftmost derivations / parse trees: "
        "one groups it as num + (num * num), the other as (num + num) * num. The two trees give "
        "different values (2 + 3 * 4 = 14 or 20), so the grammar does not fix operator precedence. "
        "num - num - num is ambiguous in the same way (associativity).",
    "revised": "Revised grammar G2 introduces one variable per precedence level: E (lowest: + -), "
        "T (* /), F (numbers and parentheses). * and / can only appear inside a T, so they bind "
        "tighter; left recursion (E → E + T) makes operators left-associative. G2 is unambiguous. "
        "G3 removes the left recursion so that a top-down PDA can use it; G2 and G3 generate the "
        "same language.",
    "assumptions": [
        "Numbers are unsigned integers or decimals (12, 3.14). Unary minus such as -5 is not in the language.",
        "Spaces between tokens are ignored by the lexer.",
        "Division by zero is a semantic error; the string 4/0 is syntactically valid.",
    ],
}
