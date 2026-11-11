"""Accepted / rejected test strings.  Each entry: (input, expected_accept, reason)."""

BALANCED_CASES = [
    ("", True, "Empty string is balanced"),
    ("()", True, "One pair"),
    ("([]{})", True, "Different brackets nested and in sequence"),
    ("{[()()]}", True, "Three levels of nesting"),
    ("()[]{}", True, "Concatenation"),
    ("((((()))))", True, "Deep nesting"),
    ("{[]}([])", True, "Mixed"),
    ("(", False, "Open bracket never closed"),
    (")", False, "Close bracket with nothing open"),
    ("(]", False, "Wrong type of closing bracket"),
    ("([)]", False, "Brackets cross instead of nesting"),
    ("(()", False, "One bracket left open"),
    ("())", False, "One closing bracket too many"),
    ("{[}]", False, "Crossing"),
]

ARITHMETIC_CASES = [
    ("7", True, "A single number"),
    ("2+3*4", True, "Precedence: * before +"),
    ("(2+3)*4", True, "Parentheses override precedence"),
    ("10/2-3", True, "Left to right"),
    ("8-3-2", True, "Left associativity of -"),
    ("((1+2)*(3-4))/5", True, "Nested parentheses"),
    ("3.5 * (2 + 0.25)", True, "Decimals and spaces"),
    ("2+", False, "Operator without right operand"),
    ("*3", False, "Operator without left operand"),
    ("2++3", False, "Two operators in a row"),
    ("(2+3", False, "Missing closing parenthesis"),
    ("2+3)", False, "Extra closing parenthesis"),
    ("()", False, "Empty parentheses"),
    ("2 3", False, "Two numbers without an operator"),
    ("2+a", False, "Symbol outside the alphabet"),
    ("", False, "Empty input"),
]

PALINDROME_CASES = [
    ("", True, "Empty string"),
    ("0", True, "Single symbol"),
    ("11", True, "Even length"),
    ("010", True, "Odd length"),
    ("0110", True, "Even length"),
    ("10101", True, "Odd length"),
    ("1001001", True, "Odd length"),
    ("01", False, "Not symmetric"),
    ("001", False, "Not symmetric"),
    ("0111", False, "Not symmetric"),
    ("10100", False, "Not symmetric"),
    ("110100", False, "Not symmetric"),
    ("012", False, "Symbol outside Σ"),
]
