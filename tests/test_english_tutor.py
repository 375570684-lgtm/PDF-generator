from teaching_agent.english_tutor import generate_english_hints


def test_essay_prompt():
    g = generate_english_hints("Write an essay explaining why community service should be required.")
    assert g.topic == "essay_prompt"
    assert g.steps[-1].is_answer


def test_reading_comprehension():
    g = generate_english_hints("According to the passage, what was the main cause of the conflict?")
    assert g.topic == "reading_comprehension"


def test_grammar_fragment():
    g = generate_english_hints('Is this a sentence fragment or a complete sentence: "Running through the park."')
    assert g.topic == "grammar_fragment_runon"


def test_literary_analysis():
    g = generate_english_hints('What is the theme of the poem "The Road Not Taken"?')
    assert g.topic == "literary_analysis"


def test_vocabulary_in_context():
    g = generate_english_hints('What does the word "resilient" mean in this context: "She remained resilient."')
    assert g.topic == "vocabulary_context"
    assert "resilient" in g.steps[0].text


def test_unrecognized_question_falls_back_to_generic_strategy():
    g = generate_english_hints("Name the capital of France.")
    assert g.topic == "generic_english"


def test_all_hint_sequences_end_with_exactly_one_answer():
    prompts = [
        "Write an essay about your favorite season.",
        "According to the passage, what is the author's purpose?",
        "Correct the run-on sentence below.",
        "Describe the symbol used in the story.",
        'What does "ambiguous" mean in this sentence?',
        "Random unrelated question.",
    ]
    for prompt in prompts:
        g = generate_english_hints(prompt)
        answers = [s for s in g.steps if s.is_answer]
        assert len(answers) == 1
        assert g.steps[-1].is_answer
