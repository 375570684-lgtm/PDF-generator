from teaching_agent.classify import classify_subject


def test_classifies_linear_equation_as_math():
    assert classify_subject("Solve for x: 3x + 5 = 2x + 20") == "math"


def test_classifies_geometry_as_math():
    assert classify_subject("Find the area of a rectangle with length 8 and width 3") == "math"


def test_classifies_essay_prompt_as_english():
    assert classify_subject("Write an essay explaining why recycling matters to your community.") == "english"


def test_classifies_reading_comprehension_as_english():
    assert classify_subject("According to the passage, what was the author's main argument?") == "english"


def test_classifies_grammar_question_as_english():
    assert classify_subject("Identify the sentence fragment in the paragraph below.") == "english"
