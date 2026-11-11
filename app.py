"""CFG and PDA case studies - Streamlit interface.

Run with:   streamlit run app.py

All formal models live in the `pda` package; this file only draws the UI.
"""
import html

import pandas as pd
import streamlit as st

from pda import Z0, arithmetic, balanced, palindrome
from pda.test_cases import ARITHMETIC_CASES, BALANCED_CASES, PALINDROME_CASES

st.set_page_config(page_title="CFG & PDA Case Studies", page_icon="📚", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2.2rem; max-width: 1200px;}
h1, h2, h3 {color: #1F3A5F; letter-spacing: -0.01em;}
.banner {padding: 14px 18px; border-radius: 10px; font-weight: 700; font-size: 1.15rem;
         margin: 6px 0 14px 0; border-left: 8px solid;}
.banner small {display: block; font-weight: 400; font-size: 0.9rem; margin-top: 2px;}
.accept {background: #E8F6EE; color: #14532D; border-color: #2E9E5B;}
.reject {background: #FDECEA; color: #7F1D1D; border-color: #D64545;}
.card {background: #F4F7FB; border: 1px solid #DCE4EE; border-radius: 10px; padding: 16px 18px; height: 100%;}
.card h4 {margin: 0 0 6px 0; color: #1F3A5F;}
.formal {background: #F4F7FB; border-left: 4px solid #1F3A5F; padding: 10px 14px;
         border-radius: 6px; font-family: "Cambria Math", Georgia, serif; margin-bottom: 10px;}
.stack {display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 8px 0;}
.cell {min-width: 74px; text-align: center; padding: 7px 10px; border-radius: 6px; font-family: monospace;
       font-size: 1rem; background: #DCE8F7; border: 1.5px solid #1F3A5F; color: #1B2430;}
.cell.top {background: #FFE9A8; border-color: #D4860B; font-weight: 700;}
.cell.bottom {background: #E6E9EE; border-color: #8894A5; color: #55606E;}
.stacklabel {font-size: 0.8rem; color: #5B6B7F;}
.tape {font-family: monospace; font-size: 1.05rem; line-height: 2.2; overflow-wrap: anywhere;}
.tok {display: inline-block; padding: 1px 8px; margin: 0 2px; border-radius: 5px; border: 1px solid #C9D3E0;}
.tok.done {background: #E6E9EE; color: #8894A5; text-decoration: line-through;}
.tok.next {background: #FFE9A8; border-color: #D4860B; font-weight: 700;}
.kv {font-size: 0.95rem; margin-bottom: 6px;}
.kv b {color: #1F3A5F;}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_pdas():
    return balanced.build_pda(), arithmetic.build_pda(), palindrome.build_pda()


BAL, ARI, PAL = load_pdas()


# ------------------------------------------------------------------ helpers
def _stretch(widget, *args, **kwargs):
    """Draw a widget at full width on both new and old Streamlit versions."""
    try:
        return widget(*args, width="stretch", **kwargs)
    except TypeError:
        return widget(*args, use_container_width=True, **kwargs)


def table(rows, **kwargs):
    return _stretch(st.dataframe, pd.DataFrame(rows), hide_index=True, **kwargs)


def graph(dot, stretch=True):
    if stretch:
        return _stretch(st.graphviz_chart, dot)
    return st.graphviz_chart(dot)            # natural size (used for trees)


def banner(accepted, detail):
    cls, word = ("accept", "ACCEPTED") if accepted else ("reject", "REJECTED")
    st.markdown(f'<div class="banner {cls}">{word}<small>{html.escape(detail)}</small></div>',
                unsafe_allow_html=True)


def formal(text):
    st.markdown(f'<div class="formal">{html.escape(text)}</div>', unsafe_allow_html=True)


def stack_html(stack):
    """The stack drawn as a column of boxes, top of stack at the top."""
    cells = []
    for i, sym in enumerate(stack):
        cls = "cell top" if i == 0 else ("cell bottom" if sym == Z0 else "cell")
        cells.append(f'<div class="{cls}">{html.escape(sym)}</div>')
    body = "".join(cells) if cells else '<div class="stacklabel">(empty)</div>'
    return f'<div class="stack"><div class="stacklabel">top</div>{body}<div class="stacklabel">bottom</div></div>'


def tape_html(shown, pos):
    """Input tokens: consumed ones struck out, the next one highlighted."""
    if not shown:
        return '<div class="tape"><span class="tok">ε</span></div>'
    parts = []
    for i, tok in enumerate(shown):
        cls = "tok done" if i < pos else ("tok next" if i == pos else "tok")
        parts.append(f'<span class="{cls}">{html.escape(tok)}</span>')
    return '<div class="tape">' + "".join(parts) + "</div>"


def trace_rows(result, path, sep):
    rows = []
    for i, node in enumerate(path):
        rows.append({
            "Step": i,
            "State": node.state,
            "Remaining input": sep.join(result.tokens[node.pos:]) or "ε",
            "Stack (top → bottom)": " ".join(node.stack),
            "Move applied": node.rule.formal() if node.rule else "start configuration",
            "Stack operation": node.rule.operation() if node.rule else "—",
        })
    return rows


def stack_trace_tab(pda, result, shown, sep, key):
    """Step-through viewer + full table for the accepting (or furthest failing) branch."""
    index = result.best_index()
    path = result.path(index)
    if result.accepted:
        st.caption(f"Accepting computation: {len(path) - 1} moves. "
                   f"Configurations explored by the simulator: {len(result.nodes)}.")
    else:
        st.caption(f"No branch accepts. Showing the branch that consumed the most input "
                   f"({len(path) - 1} moves). Configurations explored: {len(result.nodes)}.")
    step = st.slider("Step", 0, len(path) - 1, len(path) - 1, key=key + "_step") if len(path) > 1 else 0
    node = path[step]
    left, mid, right = st.columns([5, 2, 5])
    with left:
        st.markdown("**Configuration**")
        st.markdown(f'<div class="kv"><b>State:</b> {node.state}</div>', unsafe_allow_html=True)
        st.markdown('<div class="kv"><b>Input</b> (struck out = already read)</div>' +
                    tape_html(shown, node.pos), unsafe_allow_html=True)
        if node.rule:
            st.markdown(f'<div class="kv"><b>Move applied:</b> {html.escape(node.rule.formal())}</div>'
                        f'<div class="kv"><b>Stack operation:</b> {html.escape(node.rule.operation())}</div>'
                        f'<div class="kv"><b>Purpose:</b> {html.escape(node.rule.note)}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="kv">Start configuration (q0, w, Z0).</div>', unsafe_allow_html=True)
        if step == len(path) - 1 and not result.accepted:
            st.error(result.why_stuck(index))
    with mid:
        st.markdown("**Stack**")
        st.markdown(stack_html(node.stack), unsafe_allow_html=True)
    with right:
        st.markdown("**Current state**")
        graph(pda.to_dot(current=node.state, labels=False), stretch=False)
    st.markdown("**Complete trace**")
    table(trace_rows(result, path, sep))
    if result.truncated:
        st.warning("The search hit its safety limit before exploring every branch.")


def derivation_tab(grammar, tokens):
    steps, result = grammar.derive(tokens)
    st.code("\n".join(grammar.grouped()), language=None)
    if steps is not None:
        st.success(f"Leftmost derivation found ({len(steps) - 1} steps).")
        table([{"Step": i, "Production applied": prod, "Sentential form": " ".join(form) or "ε"}
               for i, (form, prod) in enumerate(steps)])
        chain = " ⇒ ".join(" ".join(f) or "ε" for f, _ in steps)
        st.markdown("**In one line**")
        st.code(chain, language=None)
    else:
        form, pos, why = grammar.failed_derivation(result)
        st.error("No derivation exists: the string is not in L(G).")
        st.markdown(f"The furthest leftmost-derivation attempt matched **{pos}** of "
                    f"**{len(tokens)}** input symbol(s) and reached the sentential form")
        st.code(" ".join(form) or "ε", language=None)
        st.markdown(why)


def cfg_tab(grammar, info, extra=None):
    st.markdown("**Target language**")
    formal(info["language"])
    st.markdown("**Alphabet**")
    formal(info["alphabet"])
    if info.get("assumptions"):
        st.markdown("**Assumptions**")
        for a in info["assumptions"]:
            st.markdown(f"- {a}")
    st.markdown(f"**Context-free grammar** {grammar.name} = (V, T, P, S)")
    formal(f"V = {{{', '.join(grammar.variables)}}},  T = {{{', '.join(grammar.terminals)}}},  "
           f"S = {grammar.start},  P:")
    st.code("\n".join(grammar.grouped()), language=None)
    if extra:
        extra()
    st.markdown("**Meaning of every production**")
    table(grammar.production_rows())


def pda_tab(pda):
    st.markdown("**Pushdown automaton** P = (Q, Σ, Γ, δ, q0, Z0, F), acceptance by final state")
    formal(f"Q = {{{', '.join(pda.states)}}},  Σ = {{{', '.join(pda.input_alphabet)}}},  "
           f"Γ = {{{', '.join(pda.stack_alphabet)}}},  q0 = {pda.start},  "
           f"F = {{{', '.join(sorted(pda.finals))}}}")
    kind = "deterministic (DPDA)" if pda.is_deterministic() else "nondeterministic (NPDA)"
    st.markdown(f"Checked by the program: this PDA is **{kind}**, with {len(pda.rules)} transitions.")
    st.markdown("**State diagram** — edge label: `input, pop → push`")
    graph(pda.to_dot())
    st.markdown("**States**")
    table([{"State": q, "Role": pda.state_info.get(q, "")} for q in pda.states])
    st.markdown("**Transition table**")
    table(pda.transition_rows(), height=420)


def analysis_tab(info, extra=None):
    st.markdown("**Why a finite automaton is not enough**")
    st.write(info["why_not_regular"])
    st.markdown("**Determinism**")
    st.write(info["determinism"])
    st.markdown("**Ambiguity**")
    st.write(info["ambiguity"])
    if extra:
        extra()
    st.markdown("**Revised grammar**")
    st.write(info["revised"])


def test_tab(cases, runner):
    rows = []
    for text, expected, reason in cases:
        actual = runner(text)                      # run the real PDA, live
        rows.append({"Input": text if text else "ε (empty)",
                     "Expected": "ACCEPT" if expected else "REJECT",
                     "PDA result": "ACCEPT" if actual else "REJECT",
                     "Match": "✔" if actual == expected else "✘", "Why": reason})
    acc = sum(c[1] for c in cases)
    a, b, c = st.columns(3)
    a.metric("Accepted strings", acc)
    b.metric("Rejected strings", len(cases) - acc)
    c.metric("PDA agrees with expected", f"{sum(r['Match'] == '✔' for r in rows)} / {len(rows)}")
    table(rows)
    st.caption("Results are computed by the PDA simulator each time the page loads.")


def input_row(label, cases, key, default):
    """Sample dropdown + text box.  Returns the string to analyse."""
    options = ["— type your own —"] + [f"{t or 'ε (empty)'}   [{'accept' if e else 'reject'}]" for t, e, _ in cases]
    left, right = st.columns([2, 3])
    choice = left.selectbox("Load a sample", options, key=key + "_sample")
    value = default if choice == options[0] else cases[options.index(choice) - 1][0]
    return right.text_input(label, value=value, key=f"{key}_text_{choice}")


# ------------------------------------------------------------------ pages
def page_overview():
    st.title("Context-Free Grammars and Pushdown Automata")
    st.caption("21CSC301T Formal Language and Automata · Assignment 3 · Case Study-Based Analysis and Design using PDA and CFG")
    st.write("Three languages that a finite automaton cannot recognise, each modelled by a "
             "context-free grammar and a pushdown automaton whose stack moves are simulated step by step.")
    cols = st.columns(3)
    cards = [("Balanced Parentheses", "( ) [ ] { } correctly nested.", "Deterministic PDA · 2 states"),
             ("Arithmetic Expressions", "Numbers, + - * /, parentheses, with precedence.", "PDA built from the grammar · 3 states"),
             ("Palindromes", "Binary strings equal to their reverse.", "Nondeterministic PDA · 3 states")]
    for col, (t, d, s) in zip(cols, cards):
        col.markdown(f'<div class="card"><h4>{t}</h4>{d}<br><br><b>{s}</b></div>', unsafe_allow_html=True)
    st.subheader("Models used")
    formal("CFG  G = (V, T, P, S).   PDA  P = (Q, Σ, Γ, δ, q0, Z0, F) with "
           "δ : Q × (Σ ∪ {ε}) × Γ → finite subsets of Q × Γ*.   Acceptance by final state.")
    st.markdown("Each case-study page takes one input and shows: the **stack trace** of the PDA, "
                "the **leftmost derivation** in the grammar, the **CFG**, the **PDA** (diagram and "
                "transition table), the **analysis** (non-regularity, determinism, ambiguity) and the "
                "**test cases**.")
    st.info("The simulator never checks the input with ordinary string functions. It applies the "
            "transitions of δ to configurations (state, remaining input, stack) and explores every "
            "nondeterministic branch.")


def page_balanced():
    st.title("Balanced Parentheses Checker")
    text = input_row("Bracket string", BALANCED_CASES, "bal", "{[()()]}")
    ignore = st.checkbox("Ignore characters that are not brackets (pre-filter, e.g. for a line of code)")
    tokens, error = balanced.tokenize(text, ignore_other=ignore)
    result = None
    if error:
        banner(False, error)
    else:
        result = BAL.search(tokens)
        if result.accepted:
            banner(True, "The PDA consumed the whole input and stopped in accepting state q0 with only Z0 on the stack.")
        else:
            banner(False, balanced.explain(result))
    tabs = st.tabs(["Stack trace", "Derivation", "CFG", "PDA", "Analysis", "Test cases"])
    with tabs[0]:
        if result:
            stack_trace_tab(BAL, result, tokens, "", "bal")
        else:
            st.write("The input contains a symbol outside Σ, so the PDA has no move for it.")
    with tabs[1]:
        if result:
            derivation_tab(balanced.GRAMMAR, tokens)
    with tabs[2]:
        cfg_tab(balanced.GRAMMAR, balanced.INFO)
    with tabs[3]:
        pda_tab(BAL)
    with tabs[4]:
        def amb():
            st.code("Ambiguous:   " + balanced.AMBIGUOUS[0] + "\nRevised:     " +
                    "\n             ".join(balanced.GRAMMAR.grouped()), language=None)
        analysis_tab(balanced.INFO, amb)
    with tabs[5]:
        test_tab(BALANCED_CASES, lambda s: balanced.tokenize(s)[1] is None and BAL.accepts(balanced.tokenize(s)[0]))


def page_arithmetic():
    st.title("Arithmetic Expression Validator")
    text = input_row("Expression", ARITHMETIC_CASES, "ari", "(2+3)*4-10/5")
    tokens, lexemes, error = arithmetic.tokenize(text)
    result = None
    if error:
        banner(False, error)
    else:
        result = ARI.search(tokens)
        if result.accepted:
            banner(True, "The token sequence is derivable from the grammar; the PDA reached accepting state q2.")
        else:
            banner(False, arithmetic.explain(result))
    if tokens:
        st.markdown("**Tokens from the lexer:** " +
                    " ".join(f"`{lx}`→{tk}" if tk == "num" else f"`{tk}`" for tk, lx in zip(tokens, lexemes)))
    tabs = st.tabs(["Stack trace", "Derivation", "Parse tree", "CFG", "PDA", "Analysis", "Test cases"])
    with tabs[0]:
        if result:
            stack_trace_tab(ARI, result, lexemes, " ", "ari")
        else:
            st.write("The lexer rejected the input, so no token sequence reaches the PDA.")
    with tabs[1]:
        if result:
            derivation_tab(arithmetic.GRAMMAR, tokens)
    with tabs[2]:
        if result and result.accepted:
            tree = arithmetic.parse_tree(result, lexemes)
            graph(arithmetic.tree_dot(tree), stretch=False)
            try:
                value = arithmetic.evaluate(tree)
                st.markdown(f"**Value read from the tree:** `{value:g}`")
                st.caption("Evaluation is a semantic step outside the PDA. It is shown to confirm "
                           "that * and / are grouped before + and -, and that operators associate to the left.")
            except ZeroDivisionError:
                st.warning("The expression is syntactically valid but divides by zero. Detecting "
                           "this is a semantic check that the grammar and the PDA cannot perform.")
        else:
            st.write("A parse tree exists only for accepted expressions.")
    with tabs[3]:
        def grammars():
            st.caption("G3 is G2 with left recursion removed (A → Aα | β becomes A → βA′, A′ → αA′ | ε), "
                       "so that a top-down PDA can use it. Both generate the same language.")
            st.code("G2 (precedence grammar):\n  " + "\n  ".join(arithmetic.G2_LINES), language=None)
        cfg_tab(arithmetic.GRAMMAR, arithmetic.INFO, grammars)
    with tabs[4]:
        st.caption("This PDA is produced from G3 by the standard CFG → PDA construction: "
                   "expand a variable on top of the stack, or match a terminal with the input.")
        pda_tab(ARI)
    with tabs[5]:
        def amb():
            st.code("G1 (ambiguous):\n  " + arithmetic.G1_LINES[0], language=None)
            st.markdown("Two parse trees of `num + num * num` under G1:")
            a, b = st.columns(2)
            with a:
                graph(arithmetic.AMBIGUITY_TREE_A, stretch=False)
            with b:
                graph(arithmetic.AMBIGUITY_TREE_B, stretch=False)
            st.code("Leftmost derivation 1:  E ⇒ E + E ⇒ num + E ⇒ num + E * E ⇒ num + num * E ⇒ num + num * num\n"
                    "Leftmost derivation 2:  E ⇒ E * E ⇒ E + E * E ⇒ num + E * E ⇒ num + num * E ⇒ num + num * num",
                    language=None)
            st.code("G2 (revised, unambiguous):\n  " + "\n  ".join(arithmetic.G2_LINES), language=None)
        analysis_tab(arithmetic.INFO, amb)
    with tabs[6]:
        test_tab(ARITHMETIC_CASES, lambda s: arithmetic.tokenize(s)[2] is None and ARI.accepts(arithmetic.tokenize(s)[0]))


def page_palindrome():
    st.title("Palindrome Checker")
    text = input_row("Binary string", PALINDROME_CASES, "pal", "0110")
    tokens, error = palindrome.tokenize(text)
    result = None
    if error:
        banner(False, error)
    else:
        result = PAL.search(tokens)
        if result.accepted:
            banner(True, "At least one nondeterministic branch guessed the midpoint correctly and reached accepting state q2.")
        else:
            banner(False, palindrome.explain(result))
    tabs = st.tabs(["Midpoint guesses", "Stack trace", "Derivation", "CFG", "PDA", "Analysis", "Test cases"])
    with tabs[0]:
        if result:
            rows = palindrome.branches(result)
            good = sum(r["Outcome"] == "ACCEPT" for r in rows)
            a, b, c = st.columns(3)
            a.metric("Branches explored", len(rows))
            b.metric("Accepting branches", good)
            c.metric("Dead branches", len(rows) - good)
            st.write("The PDA cannot see where the middle of the input is, so it tries every "
                     "possibility. Each row is one complete computation.")
            table(rows)
            st.caption("A nondeterministic PDA accepts when at least one branch accepts.")
    with tabs[1]:
        if result:
            stack_trace_tab(PAL, result, tokens, "", "pal")
    with tabs[2]:
        if result:
            derivation_tab(palindrome.GRAMMAR, tokens)
    with tabs[3]:
        cfg_tab(palindrome.GRAMMAR, palindrome.INFO)
    with tabs[4]:
        pda_tab(PAL)
    with tabs[5]:
        analysis_tab(palindrome.INFO)
    with tabs[6]:
        test_tab(PALINDROME_CASES, lambda s: palindrome.tokenize(s)[1] is None and PAL.accepts(palindrome.tokenize(s)[0]))


def page_summary():
    st.title("Comparison and Limitations")
    table([
        {"Case study": "Balanced brackets", "Regular?": "No", "Language class": "Deterministic CFL",
         "PDA": "DPDA, 2 states", "Natural grammar ambiguous?": "Yes (S → SS …)",
         "Revised grammar": "S → (S)S | [S]S | {S}S | ε"},
        {"Case study": "Arithmetic expressions", "Regular?": "No", "Language class": "Deterministic CFL (LL(1) grammar)",
         "PDA": "From grammar, 3 states", "Natural grammar ambiguous?": "Yes (E → E+E …)",
         "Revised grammar": "E/T/F precedence grammar"},
        {"Case study": "Binary palindromes", "Regular?": "No", "Language class": "CFL, not deterministic",
         "PDA": "NPDA, 3 states", "Natural grammar ambiguous?": "No",
         "Revised grammar": "Not needed"},
    ])
    st.subheader("Finite automaton versus pushdown automaton")
    table([
        {"": "Memory", "Finite automaton": "Current state only (bounded)", "Pushdown automaton": "State + one unbounded stack (last-in, first-out)"},
        {"": "Languages", "Finite automaton": "Regular", "Pushdown automaton": "Context-free"},
        {"": "Grammar", "Finite automaton": "Regular (right-linear) grammar", "Pushdown automaton": "Context-free grammar"},
        {"": "Nondeterminism", "Finite automaton": "Adds no power (NFA = DFA)", "Pushdown automaton": "Adds power (NPDA > DPDA)"},
        {"": "Typical use", "Finite automaton": "Lexer: tokens, formats", "Pushdown automaton": "Parser: nesting, expressions"},
    ])
    st.subheader("Limitations of the PDA model")
    st.markdown(
        "- **One stack only.** { aⁿbⁿcⁿ } and { ww } are not context-free; they need a second "
        "stack or a tape (Turing machine).\n"
        "- **Syntax only.** The expression PDA accepts `4/0`; type errors, undeclared variables and "
        "division by zero are semantic checks done after parsing.\n"
        "- **Nondeterminism is costly to simulate.** The palindrome simulator explores about 2n+1 "
        "branches for an input of length n. Practical parsers therefore use deterministic grammars "
        "(LL, LR).\n"
        "- **Ambiguity cannot be tested automatically in general.** Whether an arbitrary CFG is "
        "ambiguous is undecidable; the revisions shown here were designed by hand.")


PAGES = {"Overview": page_overview, "Balanced Parentheses": page_balanced,
         "Arithmetic Expressions": page_arithmetic, "Palindromes": page_palindrome,
         "Comparison & Limitations": page_summary}

with st.sidebar:
    st.markdown("### CFG & PDA\nAssignment 3")
    page = st.radio("Section", list(PAGES), label_visibility="collapsed")
    st.divider()
    st.caption("Stack notation: the leftmost symbol is the top of the stack. Z0 marks the bottom.")

PAGES[page]()
