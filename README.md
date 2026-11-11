# FLA Assignment 3 – CFG and PDA Case Studies

**Course:** 21CSC301T – Formal Language and Automata (AY 2026–2027, Semester V)
**Programme:** B.Tech. CSE (Artificial Intelligence and Machine Learning), SRM IST Tiruchirappalli
**Student:** `<Name>` · `<Register Number>`
**Repository:** `<paste GitHub URL after creating the repository>`

An interactive application that models three non-regular languages with context-free
grammars and pushdown automata, and shows the real stack moves of each PDA.

| Case study | Language | PDA | Grammar |
|---|---|---|---|
| Balanced parentheses | nested `()`, `[]`, `{}` | deterministic, 2 states | `S → (S)S \| [S]S \| {S}S \| ε` |
| Arithmetic expressions | numbers, `+ - * /`, parentheses | 3 states, built from the grammar | E/T/F precedence grammar |
| Palindromes | binary strings with w = wᴿ | nondeterministic, 3 states | `S → 0S0 \| 1S1 \| 0 \| 1 \| ε` |

## What makes this a real PDA simulation

- δ is stored as explicit rules `δ(q, a, X) ∋ (p, γ)`; nothing else decides acceptance.
- The simulator performs breadth-first search over configurations
  (state, remaining input, stack), so **every nondeterministic branch** is followed.
- Derivations are read from the accepting run of the grammar's own top-down PDA.
- The program checks the two DPDA conditions to report determinism.

## Features

- ACCEPTED / REJECTED with the stuck configuration explained
- Step slider: state, input tape, stack drawn as boxes, move applied
- Complete trace table with push / pop / replace operations
- Leftmost derivations (and a "furthest attempt" explanation for rejected strings)
- Parse tree and value for expressions (shows precedence and associativity)
- Midpoint-guess table for palindromes (one row per nondeterministic branch)
- CFG, PDA 7-tuple, state diagram and transition table for each case
- Analysis: pumping-lemma argument, determinism, ambiguity, revised grammar
- 13–16 test strings per case, executed live

## Project structure

```
app.py                     Streamlit interface
cli.py                     Terminal / Colab demo
pda/
  pda.py                   Generic NPDA, BFS simulator, determinism check, diagrams
  cfg.py                   CFG class, CFG → PDA construction, derivations
  balanced.py              Case study 1
  arithmetic.py            Case study 2 (lexer, grammars, parse tree)
  palindrome.py            Case study 3 (branch table)
  test_cases.py            Accepted / rejected strings
tests/test_pda.py          60 unit tests (exhaustive and randomised cross-checks)
scripts/build_assets.py    Regenerates diagrams/ and the generated docs
docs/CASE_STUDY.md         Case-study report (main written submission)
docs/transition_tables.md  Complete δ of all three PDAs (generated)
docs/worked_examples.md    Stack traces and derivations (generated)
docs/test_results.txt      pytest output
diagrams/                  PDA diagrams and parse trees (.dot and .png)
screenshots/               Demonstration screenshots
```

## Installation and execution

Requires Python 3.11 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

**Without Streamlit / in Google Colab**

```bash
python cli.py balanced "([]{})"
python cli.py arithmetic "2+3*4"
python cli.py palindrome 0110
```

**Tests and regenerated documents**

```bash
pytest -v
python scripts/build_assets.py      # PNG output needs Graphviz installed (optional)
```

## Demonstration plan (oral explanation)

1. **Balanced** – `{[()()]}`: move the Step slider and watch push/pop; then `([)]` to show the stuck configuration. Open **PDA** to show it is deterministic.
2. **Arithmetic** – `2+3*4`: open **Parse tree** (value 14), then `(2+3)*4` (value 20). Open **Analysis** for the two parse trees of the ambiguous grammar and the revised grammar. Try `2+*3`.
3. **Palindromes** – `0110`: the **Midpoint guesses** tab shows 9 branches with one accepting; `0111` shows all branches dying. Open **Analysis** for why the PDA must be nondeterministic.
4. **Comparison & Limitations**.

## Limitations

A PDA has a single stack ({aⁿbⁿcⁿ} is out of reach), checks syntax only (`4/0` is
accepted), and the expression language has no unary minus or identifiers.
See `docs/CASE_STUDY.md` §7.

## Publishing to GitHub

Create an empty repository named `FLA-Assignment-3-CFG-PDA` on github.com, then:

```bash
git init
git add .
git commit -m "FLA Assignment 3: CFG and PDA case studies"
git branch -M main
git remote add origin https://github.com/<your-username>/FLA-Assignment-3-CFG-PDA.git
git push -u origin main
```

## References

Hopcroft, Motwani and Ullman, *Introduction to Automata Theory, Languages, and Computation*, 3rd ed.;
Sipser, *Introduction to the Theory of Computation*, 3rd ed.; Aho, Lam, Sethi and Ullman, *Compilers*, 2nd ed.
Full list in the case-study report.
