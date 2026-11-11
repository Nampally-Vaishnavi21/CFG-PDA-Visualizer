"""Context-free grammar and the standard CFG → PDA construction.

A CFG is the 4-tuple  G = (V, T, P, S):
    V - variables (non-terminals)     T - terminals
    P - productions  A → α            S - start variable

Top-down construction (Hopcroft-Motwani-Ullman, Theorem 6.13 idea):
    q0 --ε, Z0 → S Z0-->  q1                      put the start variable on the stack
    q1 --ε, A → α-->      q1   for every A → α    EXPAND a variable (a derivation step)
    q1 --a, a → ε-->      q1   for every a ∈ T    MATCH a terminal with the input
    q1 --ε, Z0 → Z0-->    q2                      stack is back to Z0: accept

Every accepting run of this PDA spells out a LEFTMOST derivation of the input,
which is how `derive` produces derivations.
"""
from .pda import EPS, PDA, Rule, Z0


class CFG:
    def __init__(self, name, variables, terminals, productions, start, notes=None):
        self.name = name
        self.variables = list(variables)
        self.terminals = list(terminals)
        self.productions = [(head, tuple(body)) for head, body in productions]
        self.start = start
        self.notes = notes or {}         # (head, body) -> explanation
        for head, body in self.productions:
            assert head in self.variables
            assert all(s in self.variables or s in self.terminals for s in body), (head, body)

    @staticmethod
    def show(head, body):
        return f"{head} → {' '.join(body) or 'ε'}"

    def production_rows(self):
        return [{"Production": self.show(h, b), "Meaning": self.notes.get((h, b), "")}
                for h, b in self.productions]

    def grouped(self):
        """Productions in the compact form  A → α | β | …"""
        lines = []
        for v in self.variables:
            bodies = [" ".join(b) or "ε" for h, b in self.productions if h == v]
            if bodies:
                lines.append(f"{v} → " + " | ".join(bodies))
        return lines

    def to_pda(self):
        rules = [Rule("q0", EPS, Z0, "q1", (self.start, Z0), "Place the start variable on the stack")]
        for head, body in self.productions:
            rules.append(Rule("q1", EPS, head, "q1", body, f"Expand using {self.show(head, body)}"))
        for a in self.terminals:
            rules.append(Rule("q1", a, a, "q1", (), f"Match terminal {a} with the input"))
        rules.append(Rule("q1", EPS, Z0, "q2", (Z0,), "Whole derivation matched: accept"))
        info = {"q0": "Start: only pushes the start variable.",
                "q1": "Working state: expand variables and match terminals.",
                "q2": "Accepting state."}
        return PDA(f"PDA of {self.name}", ["q0", "q1", "q2"], self.terminals,
                   [Z0] + self.variables + self.terminals, rules, "q0", {"q2"}, info)

    def derive(self, tokens):
        """Leftmost derivation of `tokens`, read off an accepting run of the PDA.

        Returns (steps, result).  `steps` is a list of (sentential form, production
        used) when the string is in L(G), otherwise None.
        """
        tokens = list(tokens)
        result = self.to_pda().search(tokens)
        if not result.accepted:
            return None, result
        steps = [([self.start], "start")]
        for node in result.path(result.accepted_index):
            rule = node.rule
            if rule is not None and rule.state == "q1" and rule.read == EPS and rule.top in self.variables:
                # sentential form = input consumed so far + stack (without Z0)
                form = tokens[:node.pos] + [s for s in node.stack if s != Z0]
                steps.append((form, self.show(rule.top, rule.push)))
        return steps, result

    def failed_derivation(self, result):
        """Describe the furthest a leftmost derivation attempt got before failing.

        Returns (sentential form, symbols matched, reason).
        """
        tokens = result.tokens
        furthest = max(n.pos for n in result.nodes)
        # First configuration (in search order) that has matched `furthest` symbols.
        node = next(n for n in result.nodes if n.pos == furthest)
        rest = [s for s in node.stack if s != Z0]
        form = tokens[:furthest] + rest
        if furthest < len(tokens):
            why = (f"The next input symbol is '{tokens[furthest]}', and no choice of productions "
                   f"for the remaining part ( {' '.join(rest) or 'ε'} ) can produce it at this position.")
        else:
            needed = [s for s in rest if s in self.terminals]
            why = ("The input has ended, but the sentential form still requires: "
                   f"{' '.join(needed) or ' '.join(rest)}.")
        return form, furthest, why
