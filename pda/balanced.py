"""Case study 1 - balanced brackets over Σ = { ( ) [ ] { } }  (a Dyck language)."""
from .cfg import CFG
from .pda import EPS, PDA, Rule, Z0

OPEN = ["(", "[", "{"]
CLOSE = [")", "]", "}"]
PAIR = dict(zip(OPEN, CLOSE))
SIGMA = OPEN + CLOSE


def build_pda():
    """Deterministic PDA with two states.

    q0 - the stack holds only Z0: everything opened so far is closed (accepting).
    q1 - at least one bracket is still open.
    """
    rules = []
    for o in OPEN:
        rules.append(Rule("q0", o, Z0, "q1", (o, Z0), f"First open bracket {o}: push it"))
    for o in OPEN:
        for x in OPEN:
            rules.append(Rule("q1", o, x, "q1", (o, x), f"Another open bracket {o}: push it"))
    for o in OPEN:
        rules.append(Rule("q1", PAIR[o], o, "q1", (), f"{PAIR[o]} matches the {o} on top: pop it"))
    rules.append(Rule("q1", EPS, Z0, "q0", (Z0,), "Stack is down to Z0: every bracket is closed"))
    info = {"q0": "Start and accepting state. Stack = Z0, so nothing is waiting to be closed.",
            "q1": "At least one open bracket is on the stack, waiting for its partner."}
    return PDA("Balanced-brackets DPDA", ["q0", "q1"], SIGMA, [Z0] + OPEN, rules, "q0", {"q0"}, info)


# Unambiguous grammar used by the application.
GRAMMAR = CFG(
    "G_bal", ["S"], SIGMA,
    [("S", ["(", "S", ")", "S"]), ("S", ["[", "S", "]", "S"]), ("S", ["{", "S", "}", "S"]), ("S", [])],
    "S",
    notes={
        ("S", ("(", "S", ")", "S")): "A balanced string may start with ( … ) around a balanced string, followed by another balanced string.",
        ("S", ("[", "S", "]", "S")): "Same for square brackets.",
        ("S", ("{", "S", "}", "S")): "Same for curly braces.",
        ("S", ()): "The empty string is balanced (this ends the recursion).",
    })

# Ambiguous grammar for the same language - shown only for the ambiguity discussion.
AMBIGUOUS = ["S → S S | ( S ) | [ S ] | { S } | ε"]


def tokenize(text, ignore_other=False):
    """Split into symbols.  Returns (tokens, error message or None)."""
    tokens = []
    for i, ch in enumerate(text, start=1):
        if ch in SIGMA:
            tokens.append(ch)
        elif not ignore_other:
            return tokens, f"Character {i} ('{ch}') is not in Σ = {{ ( ) [ ] {{ }} }}."
    return tokens, None


def explain(result):
    """Plain-language reason for a rejection, read from the stuck configuration."""
    node = result.nodes[result.best_index()]
    top = node.stack[0]
    if node.pos < len(result.tokens):
        sym = result.tokens[node.pos]
        if top == Z0:
            return f"Symbol {node.pos + 1} is '{sym}' but the stack is empty (only Z0): there is no open bracket for it to close."
        return f"Symbol {node.pos + 1} is '{sym}' but the top of the stack is '{top}', which needs '{PAIR[top]}'."
    waiting = " ".join(s for s in node.stack if s != Z0)
    return f"The input ended while the stack still holds: {waiting} (unclosed brackets)."


INFO = {
    "title": "Balanced Parentheses Checker",
    "language": "L_bal = the set of all correctly nested strings over Σ. Formally the smallest set "
                "with ε ∈ L; if x, y ∈ L then (x)y, [x]y, {x}y ∈ L.",
    "alphabet": "Σ = { ( , ) , [ , ] , { , } }",
    "why_not_regular": "Take w = (ⁿ)ⁿ with n larger than the pumping length p. By the pumping lemma "
        "w = xyz with |xy| ≤ p and |y| ≥ 1, so y consists only of '('. Pumping gives x y² z, which "
        "has more '(' than ')' and is not balanced. So L_bal is not regular. Intuitively a DFA with "
        "k states cannot remember more than k different nesting depths, but the depth is unbounded.",
    "determinism": "The PDA is deterministic: for every (state, stack top) there is at most one "
        "move for each input symbol, and the only ε-move (q1, Z0) has no competing input move. "
        "L_bal is therefore a deterministic context-free language.",
    "ambiguity": "The natural grammar S → SS | (S) | [S] | {S} | ε is AMBIGUOUS: the string ()()() "
        "can be grouped as (()())() or ()(()()) by S → SS, giving two different parse trees (and ε "
        "can be inserted in infinitely many ways).",
    "revised": "Revised unambiguous grammar: S → (S)S | [S]S | {S}S | ε. The first symbol of the "
        "remaining input decides the production (an open bracket selects exactly one rule, anything "
        "else selects ε), so every string has exactly one leftmost derivation. The grammar is LL(1).",
}
