# Screenshots

The PNG files here were captured from the application running locally
(`streamlit run app.py`). For your own demonstration evidence, re-capture them on
your machine (Windows: **Win + Shift + S**) and keep the same file names.

| File | What it shows |
|---|---|
| 01_overview.png | Landing page |
| 02_balanced_accepted_stack_trace.png | `{[()()]}` accepted, stack viewer and trace |
| 03_balanced_rejected.png | `([)]` rejected with the stuck configuration |
| 04_balanced_derivation.png | Leftmost derivation |
| 05_balanced_pda.png | PDA 7-tuple, diagram, transition table |
| 06_arithmetic_accepted.png | `(2+3)*4-10/5` accepted |
| 07_arithmetic_parse_tree.png | Parse tree of `2+3*4` and its value |
| 08_arithmetic_rejected.png | `2+*3` rejected with an "expected" message |
| 09_arithmetic_ambiguity.png | Ambiguous grammar, two parse trees, revised grammar |
| 10_arithmetic_pda.png | PDA built from the grammar |
| 11_palindrome_branches_accepted.png | Midpoint guesses for `0110` |
| 12_palindrome_rejected.png | `0111`: every branch dies |
| 13_palindrome_stack_trace.png | Stack trace of the furthest branch |
| 14_palindrome_pda.png | Nondeterministic PDA |
| 15_palindrome_test_cases.png | Live test-case table |
| 16_comparison.png | Comparison and limitations |
