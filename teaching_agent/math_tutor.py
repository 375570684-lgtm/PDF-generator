"""Rule-based Socratic hint generator for 9th grade math.

No LLM: each problem type is detected with regex/keyword heuristics, solved
exactly with sympy, and narrated as a sequence of progressively-revealing
hints (never handing over the final answer first). Unrecognized problems
fall back to a generic problem-solving-strategy hint sequence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import sympy
from sympy import Symbol, sympify
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

x = Symbol("x")
y = Symbol("y")

_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)


@dataclass
class HintStep:
    text: str
    is_answer: bool = False


@dataclass
class Guidance:
    topic: str
    topic_label: str
    steps: list[HintStep] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_EQ_CHARS = r"[\-+]?[\dxyXY\.\+\-\*/\^\(\)²³\s]+=[\-+]?[\dxyXY\.\+\-\*/\^\(\)²³\s]+"


def _normalize(expr_str: str) -> str:
    s = expr_str.strip()
    s = s.replace("²", "**2").replace("³", "**3")
    s = s.replace("^", "**")
    return s


def _parse(expr_str: str, local_dict=None):
    local_dict = local_dict or {"x": x, "y": y}
    return parse_expr(_normalize(expr_str), transformations=_TRANSFORMATIONS, local_dict=local_dict)


def _extract_equation(text: str) -> str | None:
    for candidate in reversed(re.split(r"[:\n]", text)):
        match = re.search(_EQ_CHARS, candidate)
        if match and re.search(r"\d", match.group(0)):
            eq = match.group(0).strip()
            if eq.count("=") == 1:
                return eq
    return None


def _extract_all_equations(text: str) -> list[str]:
    found = []
    for match in re.finditer(_EQ_CHARS, text):
        eq = match.group(0).strip()
        if re.search(r"\d", eq) and eq.count("=") == 1:
            found.append(eq)
    return found


def _fmt(val) -> str:
    """Pretty-print a sympy value, preferring fractions over long decimals."""
    val = sympy.nsimplify(val, rational=True) if val.is_number else val
    s = str(sympy.simplify(val))
    # Drop the implicit-multiplication '*' (but keep '**' for exponents),
    # e.g. "5*x + 4" -> "5x + 4".
    return re.sub(r"(?<!\*)\*(?!\*)", "", s)


def _fmt_linear(a, b, var="x") -> str:
    """Format a*var + b as a readable string, e.g. '3x + 5' or '-2x - 4'."""
    parts = []
    if a != 0:
        if a == 1:
            parts.append(var)
        elif a == -1:
            parts.append(f"-{var}")
        else:
            parts.append(f"{_fmt(a)}{var}")
    if b != 0 or not parts:
        sign = " + " if (b >= 0 and parts) else (" - " if parts else "")
        parts.append(f"{sign}{_fmt(abs(b)) if parts else _fmt(b)}")
    return "".join(parts) if parts else "0"


# ---------------------------------------------------------------------------
# Topic detectors + solvers
# ---------------------------------------------------------------------------

def _try_system_of_equations(text: str) -> Guidance | None:
    eqs = _extract_all_equations(text)
    xy_eqs = [e for e in eqs if re.search(r"[xX]", e) and re.search(r"[yY]", e)]
    if len(xy_eqs) < 2:
        return None
    eq1, eq2 = xy_eqs[0], xy_eqs[1]
    try:
        lhs1, rhs1 = (_parse(s) for s in eq1.split("=", 1))
        lhs2, rhs2 = (_parse(s) for s in eq2.split("=", 1))
    except Exception:
        return None

    steps = [
        HintStep(
            "You have two equations with two unknowns (x and y). One reliable "
            "strategy is elimination: if you add or subtract the two equations, "
            "can you make one of the variables cancel out?"
        ),
        HintStep(f"Your system is:\n  {eq1.strip()}\n  {eq2.strip()}\nLook at the x and y coefficients in each — are any equal or opposite?"),
    ]

    try:
        solution = sympy.linsolve([sympy.Eq(lhs1, rhs1), sympy.Eq(lhs2, rhs2)], [x, y])
    except Exception:
        solution = None

    if solution and len(solution):
        sol = list(solution)[0]
        steps.append(HintStep(
            "Once you cancel one variable, solve the remaining one-variable "
            "equation, then substitute that value back into either original "
            "equation to find the other variable."
        ))
        steps.append(HintStep(f"x = {_fmt(sol[0])}, y = {_fmt(sol[1])}", is_answer=True))
    else:
        steps.append(HintStep(
            "Solve for one variable in terms of the other, substitute it into "
            "the second equation, and solve.", is_answer=True
        ))

    return Guidance("system_of_equations", "Math · System of Equations", steps)


def _try_slope(text: str) -> Guidance | None:
    if "slope" not in text.lower():
        return None
    points = re.findall(r"\(\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)", text)
    if len(points) < 2:
        return None
    (x1, y1), (x2, y2) = points[0], points[1]
    x1, y1, x2, y2 = (sympy.Rational(v) for v in (x1, y1, x2, y2))

    steps = [
        HintStep(
            "Remember the slope formula: m = (y₂ − y₁) / (x₂ − x₁). "
            "Which point will you call (x₁, y₁) and which (x₂, y₂)?"
        ),
        HintStep(f"Substitute the coordinates: m = ({_fmt(y2)} − {_fmt(y1)}) / ({_fmt(x2)} − {_fmt(x1)})"),
    ]

    if x2 == x1:
        steps.append(HintStep(
            "The x-coordinates are the same, so the denominator is 0 — "
            "the line is vertical, and its slope is undefined.", is_answer=True
        ))
    else:
        m = (y2 - y1) / (x2 - x1)
        steps.append(HintStep(f"m = {_fmt(m)}", is_answer=True))

    return Guidance("slope", "Math · Slope", steps)


def _try_pythagorean(text: str) -> Guidance | None:
    lowered = text.lower()
    if not ("hypotenuse" in lowered or "right triangle" in lowered):
        return None
    numbers = [sympy.Rational(n) for n in re.findall(r"\d+\.?\d*", text)]
    if len(numbers) < 2:
        return None

    steps = [HintStep(
        "This is a right triangle, so the Pythagorean theorem applies: "
        "a² + b² = c², where c is the hypotenuse (the side opposite the "
        "right angle). Which side is missing here?"
    )]

    hyp_match = re.search(r"hypotenuse[^\d]{0,20}(\d+\.?\d*)", lowered)
    if hyp_match:
        hyp = sympy.Rational(hyp_match.group(1))
        others = [n for n in numbers if n != hyp]
        leg = others[0] if others else numbers[0]
        steps.append(HintStep(f"You know the hypotenuse (c = {_fmt(hyp)}) and one leg (a = {_fmt(leg)}). Rearrange the formula to solve for the missing leg: b = √(c² − a²)."))
        value = sympy.sqrt(hyp**2 - leg**2)
        steps.append(HintStep(f"missing leg = √({_fmt(hyp)}² − {_fmt(leg)}²) = {_fmt(sympy.nsimplify(value))} ≈ {float(value):.2f}", is_answer=True))
    else:
        a, b = numbers[0], numbers[1]
        steps.append(HintStep(f"You know both legs: a = {_fmt(a)}, b = {_fmt(b)}. Plug them into a² + b² = c² and solve for c."))
        c = sympy.sqrt(a**2 + b**2)
        steps.append(HintStep(f"c = √({_fmt(a)}² + {_fmt(b)}²) = {_fmt(sympy.nsimplify(c))} ≈ {float(c):.2f}", is_answer=True))

    return Guidance("pythagorean", "Math · Pythagorean Theorem", steps)


def _try_geometry_area_perimeter(text: str) -> Guidance | None:
    lowered = text.lower()
    wants_area = "area" in lowered
    wants_perimeter = "perimeter" in lowered or "circumference" in lowered
    if not (wants_area or wants_perimeter):
        return None
    if "=" in text or re.search(r"\bx\b", lowered):
        return None  # let algebraic detectors handle it

    numbers = [sympy.Rational(n) for n in re.findall(r"\d+\.?\d*", text)]
    if not numbers:
        return None

    if "circle" in lowered:
        r = numbers[0]
        if "diameter" in lowered:
            r = r / 2
        if wants_area:
            steps = [
                HintStep("For a circle, area = πr². What is the radius here? (If you were given the diameter, remember radius = diameter ÷ 2.)"),
                HintStep(f"Substitute r = {_fmt(r)}: Area = π × {_fmt(r)}²"),
                HintStep(f"Area = {_fmt(r**2)}π ≈ {float(sympy.pi * r**2):.2f} square units", is_answer=True),
            ]
        else:
            steps = [
                HintStep("For a circle, circumference = 2πr. What is the radius here?"),
                HintStep(f"Substitute r = {_fmt(r)}: C = 2π × {_fmt(r)}"),
                HintStep(f"C = {_fmt(2*r)}π ≈ {float(2*sympy.pi*r):.2f} units", is_answer=True),
            ]
        return Guidance("geometry", "Math · Circle", steps)

    if "triangle" in lowered and wants_area and len(numbers) >= 2:
        base, height = numbers[0], numbers[1]
        steps = [
            HintStep("For a triangle, area = ½ × base × height. Which given number is the base, and which is the height?"),
            HintStep(f"Substitute: Area = ½ × {_fmt(base)} × {_fmt(height)}"),
            HintStep(f"Area = {_fmt(sympy.Rational(1,2)*base*height)} square units", is_answer=True),
        ]
        return Guidance("geometry", "Math · Triangle", steps)

    if len(numbers) >= 2:
        length, width = numbers[0], numbers[1]
        if wants_area:
            steps = [
                HintStep("For a rectangle, area = length × width. What are the two given side lengths?"),
                HintStep(f"Substitute: Area = {_fmt(length)} × {_fmt(width)}"),
                HintStep(f"Area = {_fmt(length*width)} square units", is_answer=True),
            ]
        else:
            steps = [
                HintStep("For a rectangle, perimeter = 2 × (length + width). What are the two given side lengths?"),
                HintStep(f"Substitute: Perimeter = 2 × ({_fmt(length)} + {_fmt(width)})"),
                HintStep(f"Perimeter = {_fmt(2*(length+width))} units", is_answer=True),
            ]
        return Guidance("geometry", "Math · Rectangle", steps)

    return None


def _try_quadratic(text: str) -> Guidance | None:
    eq_str = _extract_equation(text)
    if not eq_str:
        return None
    try:
        lhs, rhs = (_parse(s) for s in eq_str.split("=", 1))
        expr = sympy.expand(lhs - rhs)
        poly = sympy.Poly(expr, x)
    except Exception:
        return None
    if poly.degree() != 2:
        return None

    a, b, c = (poly.coeff_monomial(x**2), poly.coeff_monomial(x), poly.coeff_monomial(1))
    standard_form = f"{_fmt(a)}x² {'+' if b >= 0 else '-'} {_fmt(abs(b))}x {'+' if c >= 0 else '-'} {_fmt(abs(c))} = 0"

    steps = [
        HintStep(
            "Notice the x² term — this is a quadratic equation. First, get "
            "everything on one side so it's in standard form: ax² + bx + c = 0. "
            "What do you get when you move all terms to one side?"
        ),
        HintStep(f"Standard form: {standard_form}"),
    ]

    factored = sympy.factor(expr)
    is_nicely_factored = factored.is_Mul and all(
        (not f.free_symbols) or (sympy.Poly(f, x).degree() <= 1 if f.free_symbols else True)
        for f in factored.args
    )

    solutions = sympy.solve(sympy.Eq(lhs, rhs), x)

    if is_nicely_factored and factored != expr:
        steps.append(HintStep(
            f"This factors as {_fmt(factored)} = 0. Using the zero product property, "
            "if two things multiply to zero, at least one of them must be zero. "
            "What value of x makes each factor equal 0?"
        ))
    else:
        disc = b**2 - 4*a*c
        steps.append(HintStep(
            "This doesn't factor neatly with whole numbers, so use the quadratic "
            f"formula: x = (−b ± √(b² − 4ac)) / 2a, with a = {_fmt(a)}, "
            f"b = {_fmt(b)}, c = {_fmt(c)}. What do you get for the discriminant, "
            "b² − 4ac?"
        ))
        steps.append(HintStep(f"Discriminant = {_fmt(disc)}"))

    sol_text = ", ".join(f"x = {_fmt(s)}" for s in solutions) if solutions else "no real solutions"
    steps.append(HintStep(sol_text, is_answer=True))

    return Guidance("quadratic", "Math · Quadratic Equation", steps)


_EXPONENT_PRODUCT_RE = re.compile(r"\bx\s*\^\s*(\d+)\s*\*\s*x\s*\^\s*(\d+)", re.IGNORECASE)
_EXPONENT_POWER_RE = re.compile(r"\(\s*x\s*\^\s*(\d+)\s*\)\s*\^\s*(\d+)", re.IGNORECASE)
_EXPONENT_QUOTIENT_RE = re.compile(r"\bx\s*\^\s*(\d+)\s*/\s*x\s*\^\s*(\d+)", re.IGNORECASE)


def _try_exponents(text: str) -> Guidance | None:
    if "=" in text:
        return None
    lowered = text.lower()

    m = _EXPONENT_PRODUCT_RE.search(text)
    if m:
        p, q = int(m.group(1)), int(m.group(2))
        steps = [
            HintStep("When you multiply powers with the same base, the Product of Powers rule applies: xᵃ × xᵇ = x⁽ᵃ⁺ᵇ⁾. What do you get if you add the exponents?"),
            HintStep(f"x^{p} × x^{q} = x^({p}+{q})"),
            HintStep(f"x^{p+q}", is_answer=True),
        ]
        return Guidance("exponents", "Math · Exponent Rules", steps)

    m = _EXPONENT_POWER_RE.search(text)
    if m:
        p, q = int(m.group(1)), int(m.group(2))
        steps = [
            HintStep("This is a power raised to another power, so the Power of a Power rule applies: (xᵃ)ᵇ = x⁽ᵃˣᵇ⁾. What do you get if you multiply the exponents?"),
            HintStep(f"(x^{p})^{q} = x^({p}×{q})"),
            HintStep(f"x^{p*q}", is_answer=True),
        ]
        return Guidance("exponents", "Math · Exponent Rules", steps)

    m = _EXPONENT_QUOTIENT_RE.search(text)
    if m:
        p, q = int(m.group(1)), int(m.group(2))
        steps = [
            HintStep("When you divide powers with the same base, the Quotient of Powers rule applies: xᵃ ÷ xᵇ = x⁽ᵃ⁻ᵇ⁾. What do you get if you subtract the exponents?"),
            HintStep(f"x^{p} / x^{q} = x^({p}-{q})"),
            HintStep(f"x^{p-q}" if p != q else "1", is_answer=True),
        ]
        return Guidance("exponents", "Math · Exponent Rules", steps)

    if "simplify" not in lowered:
        return None
    return None


def _try_evaluate_function(text: str) -> Guidance | None:
    def_match = re.search(r"f\s*\(\s*x\s*\)\s*=\s*([^\n\.;,]+)", text, re.IGNORECASE)
    call_match = re.search(r"f\s*\(\s*(-?\d+\.?\d*)\s*\)", text, re.IGNORECASE)
    if not def_match or not call_match:
        return None
    try:
        expr = _parse(def_match.group(1))
        value = sympy.Rational(call_match.group(1))
    except Exception:
        return None

    steps = [
        HintStep(f"To evaluate f({_fmt(value)}), substitute x = {_fmt(value)} everywhere x appears in f(x) = {_fmt(expr)}."),
        HintStep(f"f({_fmt(value)}) = {_fmt(expr.subs(x, value))}"),
        HintStep(f"f({_fmt(value)}) = {_fmt(sympy.simplify(expr.subs(x, value)))}", is_answer=True),
    ]
    return Guidance("evaluate_function", "Math · Evaluating a Function", steps)


def _linear_coeffs(text: str):
    eq_str = _extract_equation(text)
    if not eq_str or "x" not in eq_str.lower():
        return None
    try:
        lhs, rhs = (_parse(s) for s in eq_str.split("=", 1))
        expr = sympy.expand(lhs - rhs)
        poly = sympy.Poly(expr, x)
    except Exception:
        return None
    # degree <= 0 means the x-terms fully cancelled (no-solution / all-reals case)
    if poly.degree() > 1:
        return None
    a = poly.coeff_monomial(x)
    b = poly.coeff_monomial(1)
    return eq_str, lhs, rhs, a, b


def _try_inequality(text: str) -> Guidance | None:
    op_match = re.search(r"(<=|>=|<|>)", text)
    if not op_match:
        return None
    op = op_match.group(1)
    parts = re.split(r"<=|>=|<|>", text, maxsplit=1)
    if len(parts) != 2:
        return None
    left_text = re.split(r"[:\n]", parts[0])[-1]
    left_match = re.search(r"[\-+]?[\dxX\.\+\-\*/\^\(\)\s]+$", left_text)
    right_match = re.search(r"^[\-+]?[\dxX\.\+\-\*/\^\(\)\s]+", parts[1])
    if not left_match or not right_match:
        return None
    left_str, right_str = left_match.group(0).strip(), right_match.group(0).strip()
    if "x" not in (left_str + right_str).lower() or not re.search(r"\d", left_str + right_str):
        return None
    try:
        lhs, rhs = _parse(left_str), _parse(right_str)
        expr = sympy.expand(lhs - rhs)
        poly = sympy.Poly(expr, x)
    except Exception:
        return None
    if poly.degree() != 1:
        return None

    a, b = poly.coeff_monomial(x), poly.coeff_monomial(1)
    if a == 0:
        return None

    steps = [
        HintStep(f"This is an inequality: {left_str} {op} {right_str}. Just like an equation, combine like terms and move the variable to one side. What do you get?"),
        HintStep(f"{_fmt_linear(a, b)} {op} 0  →  {_fmt(a)}x {op} {_fmt(-b)}"),
    ]

    final_op = op
    if a < 0:
        flip = {"<": ">", ">": "<", "<=": ">=", ">=": "<="}
        final_op = flip[op]
        steps.append(HintStep(f"Now divide both sides by {_fmt(a)}. Since that's negative, remember to flip the inequality sign!"))
    else:
        steps.append(HintStep(f"Now divide both sides by {_fmt(a)}."))

    solution_val = _fmt(-b / a)
    steps.append(HintStep(f"x {final_op} {solution_val}", is_answer=True))

    return Guidance("inequality", "Math · Inequality", steps)


def _try_simplify_expression(text: str) -> Guidance | None:
    lowered = text.lower()
    if "simplify" not in lowered and "combine like terms" not in lowered:
        return None
    if "=" in text:
        return None
    match = re.search(r"[\-+]?[\dxX\.\+\-\*/\^\(\)\s]{3,}", text)
    if not match:
        return None
    expr_str = match.group(0).strip()
    if not re.search(r"\d", expr_str):
        return None
    # Need at least two x-terms (or a product to distribute) for there to be
    # anything worth combining.
    x_tokens = re.findall(r"\d*\.?\d*x\b", expr_str, re.IGNORECASE)
    has_product_to_distribute = "(" in expr_str
    if len(x_tokens) < 2 and not has_product_to_distribute:
        return None
    try:
        expr = _parse(expr_str)
        result = sympy.expand(expr)
    except Exception:
        return None

    steps = [
        HintStep(f"Group the x-terms together and the constant (plain number) terms together in {expr_str}. What do the x-terms add up to? What do the constants add up to?"),
        HintStep(f"Combine each group separately, then write the simplified expression."),
        HintStep(_fmt(result), is_answer=True),
    ]
    return Guidance("simplify_expression", "Math · Simplifying Expressions", steps)


def _try_linear_equation(text: str) -> Guidance | None:
    coeffs = _linear_coeffs(text)
    if not coeffs:
        return None
    eq_str, lhs, rhs, a, b = coeffs

    steps = [HintStep(
        f"This is a linear equation: {eq_str}. Your goal is to get x alone on "
        "one side. First, combine any like terms on each side if needed — "
        "what does each side look like simplified?"
    )]

    if a == 0:
        if b == 0:
            steps.append(HintStep("Every x-term cancels out and the equation is always true — there are infinitely many solutions.", is_answer=True))
        else:
            steps.append(HintStep("Every x-term cancels out but the constants don't match — this equation has no solution.", is_answer=True))
        return Guidance("linear_equation", "Math · Linear Equation", steps)

    steps.append(HintStep(f"Move the x-terms to one side and the constants to the other. You should end up with: {_fmt(a)}x = {_fmt(-b)}"))
    steps.append(HintStep(f"Now divide both sides by {_fmt(a)} to isolate x."))
    steps.append(HintStep(f"x = {_fmt(-b/a)}", is_answer=True))

    return Guidance("linear_equation", "Math · Linear Equation", steps)


def _generic_fallback(text: str) -> Guidance:
    numbers = re.findall(r"\d+\.?\d*", text)
    hint2 = (
        f"You have these numbers to work with: {', '.join(numbers)}. What do you "
        "already know, and what are you being asked to find?"
        if numbers else
        "What information does the problem give you, and what is it asking you to find?"
    )
    steps = [
        HintStep("Start by rereading the problem carefully. What is it actually asking you to find or calculate?"),
        HintStep(hint2),
        HintStep("What formula, rule, or operation connects what you know to what you need to find? Try writing that relationship down."),
        HintStep("Work through it one step at a time, then check your answer by plugging it back into the original problem — does it make sense?", is_answer=True),
    ]
    return Guidance("generic_math", "Math · Problem-Solving Strategy", steps)


_DETECTORS = [
    _try_system_of_equations,
    _try_slope,
    _try_pythagorean,
    _try_geometry_area_perimeter,
    _try_quadratic,
    _try_exponents,
    _try_evaluate_function,
    _try_inequality,
    _try_linear_equation,
    _try_simplify_expression,
]


def generate_math_hints(question_text: str) -> Guidance:
    for detector in _DETECTORS:
        try:
            result = detector(question_text)
        except Exception:
            result = None
        if result is not None:
            return result
    return _generic_fallback(question_text)
