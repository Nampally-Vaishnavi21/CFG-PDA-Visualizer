"""Generic nondeterministic pushdown automaton (NPDA) and its simulator.

A PDA is the 7-tuple  P = (Q, Σ, Γ, δ, q0, Z0, F):
    Q  - finite set of states            Σ  - input alphabet
    Γ  - stack alphabet                  δ  - transition function
    q0 - start state                     Z0 - initial stack symbol
    F  - set of accepting states

    δ : Q × (Σ ∪ {ε}) × Γ  →  finite subsets of  Q × Γ*

A move  δ(q, a, X) ∋ (p, γ)  means: in state q, reading a (or nothing if a = ε),
with X on top of the stack, go to state p and REPLACE X by the string γ
(the leftmost symbol of γ becomes the new top).
        γ = ε      → X is popped
        γ = X      → stack unchanged
        γ = Y X    → Y is pushed on top of X

A configuration (instantaneous description) is (state, remaining input, stack).
The PDA accepts by FINAL STATE: some sequence of moves must consume the whole
input and end in a state of F.

Because a PDA may have several legal moves, the simulator explores ALL of them
with breadth-first search over configurations.  Nothing here inspects the input
string directly - acceptance is decided only by the moves of δ.
"""
from dataclasses import dataclass

EPS = ""          # the empty string ε (used for ε-moves)
Z0 = "Z0"         # bottom-of-stack marker


@dataclass(frozen=True)
class Rule:
    """One element of δ:  δ(state, read, top) ∋ (new_state, push)."""
    state: str
    read: str        # an input symbol, or EPS for an ε-move
    top: str         # stack symbol that must be on top (it is popped)
    new_state: str
    push: tuple      # symbols that replace `top`; push[0] becomes the new top
    note: str = ""   # human explanation, shown in tables

    def operation(self):
        """Describe the effect on the stack in words."""
        if self.push == (self.top,):
            return "no change"
        if len(self.push) == 2 and self.push[1] == self.top:
            return f"push {self.push[0]}"
        if self.push == ():
            return f"pop {self.top}"
        return f"replace {self.top} by {' '.join(self.push)}"

    def formal(self):
        read = self.read or "ε"
        push = " ".join(self.push) or "ε"
        return f"δ({self.state}, {read}, {self.top}) ∋ ({self.new_state}, {push})"


@dataclass
class Node:
    """A configuration reached during the search, with a link to how we got here."""
    state: str
    pos: int             # number of input symbols consumed so far
    stack: tuple         # stack contents, top first
    parent: int          # index of the previous configuration (-1 for the start)
    rule: object         # the Rule that produced this configuration (None for the start)
    depth: int = 0
    children: int = 0


class SearchResult:
    def __init__(self, pda, tokens, nodes, accepted_index, truncated):
        self.pda, self.tokens, self.nodes = pda, tokens, nodes
        self.accepted_index = accepted_index
        self.accepted = accepted_index is not None
        self.truncated = truncated          # True if the safety limit stopped the search

    def path(self, index):
        """All configurations from the start up to node `index`."""
        chain = []
        while index != -1:
            chain.append(self.nodes[index])
            index = self.nodes[index].parent
        return chain[::-1]

    def leaves(self):
        """Indices of configurations with no further move (ends of branches)."""
        return [i for i, n in enumerate(self.nodes) if n.children == 0]

    def best_index(self):
        """The accepting branch, or the rejected branch that got furthest in the input."""
        if self.accepted:
            return self.accepted_index
        return max(self.leaves(), key=lambda i: (self.nodes[i].pos, -self.nodes[i].depth))

    def why_stuck(self, index):
        """Reason a non-accepting branch cannot continue."""
        node = self.nodes[index]
        top = node.stack[0] if node.stack else "(empty stack)"
        if node.pos < len(self.tokens):
            nxt = self.tokens[node.pos]
            return (f"No move is defined for state {node.state} with next input '{nxt}' "
                    f"and stack top {top}.")
        return (f"The input is finished but {node.state} is not an accepting state "
                f"(stack top {top}), and no ε-move is available.")


class PDA:
    def __init__(self, name, states, input_alphabet, stack_alphabet, rules,
                 start, finals, state_info=None):
        self.name = name
        self.states = list(states)
        self.input_alphabet = list(input_alphabet)
        self.stack_alphabet = list(stack_alphabet)
        self.rules = list(rules)
        self.start = start
        self.finals = set(finals)
        self.state_info = state_info or {}
        # Index δ by (state, read, top) for fast lookup.
        self.delta = {}
        for r in self.rules:
            assert r.state in self.states and r.new_state in self.states
            assert r.read == EPS or r.read in self.input_alphabet, r
            assert r.top in self.stack_alphabet and all(s in self.stack_alphabet for s in r.push), r
            self.delta.setdefault((r.state, r.read, r.top), []).append(r)

    # ------------------------------------------------------------ properties
    def is_deterministic(self):
        """DPDA conditions: (1) at most one move per (q, a, X);
        (2) if an ε-move exists for (q, X) then no input move exists for (q, X)."""
        for (state, read, top), moves in self.delta.items():
            if len(moves) > 1:
                return False
            if read == EPS and any((state, a, top) in self.delta for a in self.input_alphabet):
                return False
        return True

    # ------------------------------------------------------------ simulation
    def search(self, tokens, max_nodes=100000):
        """Breadth-first exploration of every computation of the PDA on `tokens`."""
        tokens = list(tokens)
        nodes = [Node(self.start, 0, (Z0,), -1, None)]
        seen = {(self.start, 0, (Z0,))}
        accepted = None
        i = 0
        while i < len(nodes) and len(nodes) < max_nodes:
            node = nodes[i]
            # Acceptance by final state: all input consumed and state ∈ F.
            if accepted is None and node.pos == len(tokens) and node.state in self.finals:
                accepted = i
            if node.stack:
                top = node.stack[0]
                moves = list(self.delta.get((node.state, EPS, top), []))        # ε-moves
                if node.pos < len(tokens):                                      # input moves
                    moves += self.delta.get((node.state, tokens[node.pos], top), [])
                for rule in moves:
                    new = (rule.new_state,
                           node.pos + (1 if rule.read else 0),
                           rule.push + node.stack[1:])     # pop `top`, push rule.push
                    if new not in seen:
                        seen.add(new)
                        node.children += 1
                        nodes.append(Node(*new, parent=i, rule=rule, depth=node.depth + 1))
            i += 1
        return SearchResult(self, tokens, nodes, accepted, truncated=i < len(nodes))

    def accepts(self, tokens):
        return self.search(tokens).accepted

    # ------------------------------------------------------------ display
    def transition_rows(self):
        return [{"Transition": r.formal(), "Stack operation": r.operation(), "Purpose": r.note}
                for r in self.rules]

    def to_dot(self, current=None, rankdir="LR", labels=True):
        """Graphviz DOT.  Edge label format:  input, pop → push
        (labels=False draws only states and arrows - used for the small live view)."""
        lines = [
            "digraph PDA {",
            f'  rankdir={rankdir}; bgcolor="transparent"; pad=0.2; nodesep=0.6; ranksep=0.9;',
            '  node [fontname="Helvetica", fontsize=12, style=filled, fillcolor="#F4F7FB", color="#1F3A5F", penwidth=1.3];',
            '  edge [fontname="Helvetica", fontsize=10, color="#5B6B7F", arrowsize=0.7];',
            '  __start [shape=point, width=0.12, color="#1F3A5F"];',
        ]
        for q in self.states:
            shape = "doublecircle" if q in self.finals else "circle"
            fill = "#FFE9A8" if q == current else "#F4F7FB"
            lines.append(f'  "{q}" [shape={shape}, fillcolor="{fill}"];')
        lines.append(f'  __start -> "{self.start}";')
        merged = {}
        for r in self.rules:
            label = f"{r.read or 'ε'}, {r.top} → {' '.join(r.push) or 'ε'}"
            merged.setdefault((r.state, r.new_state), []).append(label)
        for (a, b) in merged:
            text = ("\\l".join(merged[(a, b)]) + "\\l") if labels else ""
            lines.append(f'  "{a}" -> "{b}" [label="{text}"];')
        lines.append("}")
        return "\n".join(lines)
