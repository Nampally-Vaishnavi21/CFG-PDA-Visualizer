"""Case study 3 - palindromes over Σ = {0, 1}:  L_pal = { w ∈ {0,1}* : w = wᴿ }."""
from .cfg import CFG
from .pda import EPS, PDA, Rule, Z0

SIGMA = ["0", "1"]


def build_pda():
    """Nondeterministic PDA with three states.

    q0 - PUSH phase: copy the first half onto the stack.
    q1 - POP phase: compare the second half with the stack (which holds the first half reversed).
    q2 - accept.

    The machine cannot see where the middle is, so in q0 it GUESSES at every step:
      (a) keep pushing,
      (b) "the middle is exactly here" (even length)  - ε-move to q1,
      (c) "this symbol is the middle" (odd length)    - read it without pushing, go to q1.
    """
    rules = []
    for x in [Z0] + SIGMA:
        for a in SIGMA:
            rules.append(Rule("q0", a, x, "q0", (a, x), f"Push {a} (still in the first half)"))
    for x in [Z0] + SIGMA:
        for a in SIGMA:
            rules.append(Rule("q0", a, x, "q1", (x,), f"Guess: this {a} is the middle symbol (odd length)"))
    for x in [Z0] + SIGMA:
        rules.append(Rule("q0", EPS, x, "q1", (x,), "Guess: the middle is here (even length)"))
    for a in SIGMA:
        rules.append(Rule("q1", a, a, "q1", (), f"Input {a} equals stack top {a}: pop"))
    rules.append(Rule("q1", EPS, Z0, "q2", (Z0,), "Second half matched the whole stack: accept"))
    info = {"q0": "Push phase - reading the first half.",
            "q1": "Pop phase - matching the second half against the stack.",
            "q2": "Accepting state."}
    return PDA("Palindrome NPDA", ["q0", "q1", "q2"], SIGMA, [Z0] + SIGMA, rules, "q0", {"q2"}, info)


GRAMMAR = CFG(
    "G_pal", ["S"], SIGMA,
    [("S", ["0", "S", "0"]), ("S", ["1", "S", "1"]), ("S", ["0"]), ("S", ["1"]), ("S", [])],
    "S",
    notes={
        ("S", ("0", "S", "0")): "A palindrome may begin and end with 0, with a palindrome in between.",
        ("S", ("1", "S", "1")): "A palindrome may begin and end with 1, with a palindrome in between.",
        ("S", ("0",)): "Middle symbol 0 of an odd-length palindrome.",
        ("S", ("1",)): "Middle symbol 1 of an odd-length palindrome.",
        ("S", ()): "Centre of an even-length palindrome (also the empty string).",
    })


def tokenize(text):
    for i, ch in enumerate(text, start=1):
        if ch not in SIGMA:
            return list(text[:i - 1]), f"Character {i} ('{ch}') is not in Σ = {{0, 1}}."
    return list(text), None


def branches(result):
    """One row per nondeterministic branch: which midpoint was guessed and how it ended."""
    rows = []
    n = len(result.tokens)
    for index in result.leaves():
        path = result.path(index)
        guess = "never guessed (pushed everything)"
        for node in path:
            r = node.rule
            if r is not None and r.state == "q0" and r.new_state == "q1":
                if r.read == EPS:
                    guess = f"even: middle after {node.pos} symbol(s)"
                else:
                    guess = f"odd: symbol {node.pos} ('{r.read}') is the middle"
        last = path[-1]
        if index == result.accepted_index or (last.state == "q2" and last.pos == n):
            outcome = "ACCEPT"
        elif last.state == "q2":
            outcome = f"dies: stack emptied with {n - last.pos} input symbol(s) left"
        elif last.pos < n:
            outcome = (f"dies at symbol {last.pos + 1}: input '{result.tokens[last.pos]}' "
                       f"≠ stack top '{last.stack[0]}'") if last.state == "q1" else "dies"
        elif last.state == "q0":
            outcome = "dies: input ended in the push phase"
        else:
            outcome = f"dies: input ended with {len(last.stack) - 1} unmatched symbol(s) on the stack"
        rows.append({"Midpoint guess": guess, "Moves": last.depth, "Outcome": outcome})
    rows.sort(key=lambda r: (r["Outcome"] != "ACCEPT", r["Midpoint guess"]))
    return rows


def explain(result):
    """Rejection summary taken from the search itself (no string comparison is used)."""
    return (f"All {len(result.leaves())} nondeterministic branches died - no midpoint guess leads "
            f"to the accepting state. The table of branches below shows where each one failed.")


INFO = {
    "title": "Palindrome Checker",
    "language": "L_pal = { w ∈ {0,1}* : w = wᴿ }, the binary strings that read the same in both "
                "directions (even and odd length, including ε).",
    "alphabet": "Σ = {0, 1}",
    "why_not_regular": "Take w = 0ⁿ 1 0ⁿ with n ≥ p (the pumping length). In w = xyz with |xy| ≤ p "
        "the part y lies inside the first block of 0s. Pumping to x y² z gives 0ⁿ⁺ᵏ 1 0ⁿ, which is "
        "not a palindrome. So L_pal is not regular: a DFA would have to remember the whole first "
        "half, which is unbounded.",
    "determinism": "The PDA is NONDETERMINISTIC. In state q0, for the same input symbol and stack "
        "top, three moves are possible (push / guess odd middle / guess even middle). This cannot "
        "be removed: L_pal is context-free but not a deterministic CFL, because a machine reading "
        "left to right has no marker telling it where the middle is. (With a centre marker, "
        "{ w c wᴿ }, a deterministic PDA exists.) The simulator therefore explores every branch; the "
        "input is accepted if at least one branch accepts.",
    "ambiguity": "The grammar is UNAMBIGUOUS even though the PDA is nondeterministic: the first and "
        "last symbols of a palindrome fix the outer production, and the remaining middle is again a "
        "palindrome, so each palindrome has exactly one parse tree. Ambiguity (a property of the "
        "grammar) and nondeterminism (a property of the machine) are different things.",
    "revised": "No revision is required because no ambiguity is present.",
}
