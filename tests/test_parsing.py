from teaching_agent.parsing import split_questions


def test_splits_numbered_list():
    text = "1. Solve for x: 3x + 5 = 20\n2. What is the theme of the story?"
    questions = split_questions(text)
    assert len(questions) == 2
    assert questions[0] == "Solve for x: 3x + 5 = 20"
    assert questions[1] == "What is the theme of the story?"


def test_splits_parenthesized_numbering():
    text = "1) Simplify: 2x + 3x\n2) Define the word resilient."
    questions = split_questions(text)
    assert len(questions) == 2


def test_single_question_no_numbering():
    text = "Write an essay about your summer vacation."
    questions = split_questions(text)
    assert questions == [text]


def test_empty_text():
    assert split_questions("") == []
    assert split_questions("   ") == []
