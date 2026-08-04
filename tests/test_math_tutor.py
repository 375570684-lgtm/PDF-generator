from teaching_agent.math_tutor import generate_math_hints


def _answer(guidance):
    answers = [s.text for s in guidance.steps if s.is_answer]
    assert len(answers) == 1, "expected exactly one final answer step"
    return answers[0]


def _no_hint_reveals_answer_early(guidance):
    assert all(not s.is_answer for s in guidance.steps[:-1])


def test_linear_equation():
    g = generate_math_hints("Solve for x: 3x + 5 = 2x + 20")
    assert g.topic == "linear_equation"
    assert _answer(g) == "x = 15"
    _no_hint_reveals_answer_early(g)


def test_linear_equation_no_solution():
    g = generate_math_hints("Solve for x: 3x + 5 = 3x + 20")
    assert "no solution" in _answer(g).lower()


def test_linear_equation_infinite_solutions():
    g = generate_math_hints("Solve for x: 3x + 5 = 3x + 5")
    assert "infinitely many" in _answer(g).lower()


def test_quadratic_factorable():
    g = generate_math_hints("Solve: x^2 - 5x + 6 = 0")
    assert g.topic == "quadratic"
    answer = _answer(g)
    assert "x = 2" in answer and "x = 3" in answer


def test_quadratic_via_formula():
    g = generate_math_hints("Solve: x^2 + 4x + 2 = 0")
    assert g.topic == "quadratic"
    assert "sqrt" in _answer(g)


def test_inequality_flips_sign_on_negative_divide():
    g = generate_math_hints("Solve for x: -2x + 4 <= 10")
    assert g.topic == "inequality"
    assert _answer(g) == "x >= -3"


def test_inequality_no_flip():
    g = generate_math_hints("Solve for x: 3x + 5 > 20")
    assert _answer(g) == "x > 5"


def test_slope_between_two_points():
    g = generate_math_hints("Find the slope of the line through (2, 3) and (5, 9)")
    assert g.topic == "slope"
    assert _answer(g) == "m = 2"


def test_slope_vertical_line_is_undefined():
    g = generate_math_hints("Find the slope of the line through (4, 1) and (4, 9)")
    assert "undefined" in _answer(g).lower()


def test_pythagorean_find_hypotenuse():
    g = generate_math_hints("A right triangle has legs of 3 and 4. Find the hypotenuse.")
    assert g.topic == "pythagorean"
    assert "5" in _answer(g)


def test_pythagorean_find_leg():
    g = generate_math_hints("A right triangle has a hypotenuse of 13 and one leg of 5. Find the missing leg.")
    assert "12" in _answer(g)


def test_rectangle_area():
    g = generate_math_hints("Find the area of a rectangle with length 8 and width 3")
    assert _answer(g) == "Area = 24 square units"


def test_rectangle_perimeter():
    g = generate_math_hints("Find the perimeter of a rectangle with length 8 and width 3")
    assert _answer(g) == "Perimeter = 22 units"


def test_triangle_area():
    g = generate_math_hints("Find the area of a triangle with base 6 and height 10")
    assert _answer(g) == "Area = 30 square units"


def test_exponent_product_rule():
    g = generate_math_hints("Simplify: x^3 * x^5")
    assert _answer(g) == "x^8"


def test_exponent_power_rule():
    g = generate_math_hints("Simplify: (x^2)^4")
    assert _answer(g) == "x^8"


def test_exponent_quotient_rule():
    g = generate_math_hints("Simplify: x^7 / x^2")
    assert _answer(g) == "x^5"


def test_evaluate_function():
    g = generate_math_hints("If f(x) = 2x + 3, find f(5)")
    assert g.topic == "evaluate_function"
    assert _answer(g) == "f(5) = 13"


def test_simplify_expression_combines_like_terms():
    g = generate_math_hints("Simplify: 3x + 5 + 2x - 1")
    assert g.topic == "simplify_expression"
    assert _answer(g) == "5x + 4"


def test_system_of_equations():
    g = generate_math_hints("Solve the system: x + y = 5 and x - y = 1")
    assert g.topic == "system_of_equations"
    answer = _answer(g)
    assert "x = 3" in answer and "y = 2" in answer


def test_unrecognized_problem_falls_back_to_generic_strategy():
    g = generate_math_hints("What is the meaning of life?")
    assert g.topic == "generic_math"
    assert len(g.steps) >= 3
