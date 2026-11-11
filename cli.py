"""Command-line demo (works in Google Colab or any terminal without Streamlit).

    python cli.py balanced "([]{})"
    python cli.py arithmetic "2+3*4"
    python cli.py palindrome 0110
    python cli.py                      # interactive
"""
import sys

from pda import arithmetic, balanced, palindrome


def run(kind, text):
    if kind == "balanced":
        pda, grammar, sep = balanced.build_pda(), balanced.GRAMMAR, ""
        tokens, error = balanced.tokenize(text)
    elif kind == "arithmetic":
        pda, grammar, sep = arithmetic.build_pda(), arithmetic.GRAMMAR, " "
        tokens, _, error = arithmetic.tokenize(text)
    else:
        pda, grammar, sep = palindrome.build_pda(), palindrome.GRAMMAR, ""
        tokens, error = palindrome.tokenize(text)
    print(f"\n{pda.name}   input = {text!r}")
    if error:
        print("  REJECTED:", error, "\n")
        return
    result = pda.search(tokens)
    index = result.best_index()
    print(f"  {'step':>4}  {'state':<5}  {'remaining input':<22}  {'stack (top first)':<26}  move")
    for i, node in enumerate(result.path(index)):
        rest = sep.join(tokens[node.pos:]) or "ε"
        move = node.rule.formal() if node.rule else "start"
        print(f"  {i:>4}  {node.state:<5}  {rest:<22}  {' '.join(node.stack):<26}  {move}")
    if result.accepted:
        steps, _ = grammar.derive(tokens)
        print("  ACCEPTED")
        print("  derivation:", " ⇒ ".join(" ".join(f) or "ε" for f, _ in steps), "\n")
    else:
        print("  REJECTED:", result.why_stuck(index), "\n")


if __name__ == "__main__":
    kinds = ("balanced", "arithmetic", "palindrome")
    if len(sys.argv) == 3 and sys.argv[1] in kinds:
        run(sys.argv[1], sys.argv[2])
    else:
        while True:
            kind = input("Case study [balanced / arithmetic / palindrome / quit]: ").strip().lower()
            if kind not in kinds:
                break
            run(kind, input("Input string: "))
