"""Rule-based Socratic hint generator for 9th grade English.

No LLM: without deep language understanding we can't grade grammar or
literary analysis outright, so instead of guessing at "correct" answers,
each topic gets an honest, process-oriented set of guiding questions a real
tutor would ask — the same strategy questions regardless of the specific
passage, personalized with any quoted word/phrase we can detect.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class HintStep:
    text: str
    is_answer: bool = False


@dataclass
class Guidance:
    topic: str
    topic_label: str
    steps: list[HintStep] = field(default_factory=list)


def _quoted_snippet(text: str) -> str | None:
    match = re.search(r'"([^"]{2,80})"', text)
    return match.group(1) if match else None


def _try_vocabulary_context(text: str) -> Guidance | None:
    lowered = text.lower()
    triggers = ["what does the word", "in this context", "vocabulary", "synonym", "antonym", "context clue", "the word", "means"]
    if not any(t in lowered for t in triggers):
        return None
    word = _quoted_snippet(text)
    word_ref = f'the word "{word}"' if word else "the word in question"

    steps = [
        HintStep(f"Find {word_ref} in the sentence — what other words around it give clues about its meaning? (Those are called context clues.)"),
        HintStep("Try substituting each answer choice back into the sentence. Which one keeps the sentence's meaning logical and natural?"),
        HintStep("Check the word's part of speech (noun, verb, adjective...) — does your chosen answer match that role in the sentence?"),
        HintStep("Now make your best choice, and be ready to explain in one sentence why it fits.", is_answer=True),
    ]
    return Guidance("vocabulary_context", "English · Vocabulary in Context", steps)


def _try_essay_prompt(text: str) -> Guidance | None:
    lowered = text.lower()
    triggers = ["write an essay", "write a paragraph", "in your opinion", "argue", "persuade",
                "explain why", "discuss", "compare and contrast", "write a response"]
    if not any(t in lowered for t in triggers):
        return None

    steps = [
        HintStep("Before writing, restate the prompt in your own words. What exactly is it asking you to do — explain, argue, compare, or describe?"),
        HintStep("Brainstorm 2-3 main points or reasons that answer the prompt. Jot each one down in a few words."),
        HintStep("Turn your main idea into one clear thesis sentence that states your position or main point."),
        HintStep("Plan one paragraph per point: a topic sentence, then an example or evidence, then an explanation of how it supports your point."),
        HintStep("Now write it: an introduction with your thesis, one body paragraph per point, and a conclusion that restates your thesis in new words.", is_answer=True),
    ]
    return Guidance("essay_prompt", "English · Essay / Writing Prompt", steps)


def _try_reading_comprehension(text: str) -> Guidance | None:
    lowered = text.lower()
    triggers = ["the passage", "the author", "main idea", "according to the passage",
                "the text states", "infer", "based on the reading", "the article", "the excerpt"]
    if not any(t in lowered for t in triggers):
        return None

    steps = [
        HintStep("Reread the question first — is it asking for the main idea, a specific detail, an inference, or the author's purpose?"),
        HintStep("Go back to the passage and find the sentence(s) that relate to the question. Underline or note them."),
        HintStep("If it's an inference question, what does the text imply even though it isn't stated directly? What clues point you there?"),
        HintStep("Write your answer using evidence from the passage — quote or paraphrase the specific line that supports it.", is_answer=True),
    ]
    return Guidance("reading_comprehension", "English · Reading Comprehension", steps)


def _try_grammar_fragment_runon(text: str) -> Guidance | None:
    lowered = text.lower()
    triggers = ["sentence fragment", "complete sentence", "run-on", "run on",
                "fix the sentence", "correct the sentence", "identify the error", "subject-verb agreement"]
    if not any(t in lowered for t in triggers):
        return None

    steps = [
        HintStep("Read the sentence aloud. Does it have a subject (who/what) and a verb (the action)?"),
        HintStep("Does it express one complete thought, or does it feel like it's missing something — or like two thoughts crammed together?"),
        HintStep(
            "If it's missing a subject or verb, it's a fragment — what could you add? If it "
            "has two complete thoughts with no proper punctuation between them, it's a "
            "run-on — where could you add a period, a comma + conjunction, or a semicolon?"
        ),
        HintStep("Rewrite the sentence so it expresses one complete, correctly punctuated thought (or split it into two correct sentences).", is_answer=True),
    ]
    return Guidance("grammar_fragment_runon", "English · Grammar (Fragments & Run-ons)", steps)


def _try_literary_analysis(text: str) -> Guidance | None:
    lowered = text.lower()
    triggers = ["theme", "character", "plot", "symbol", "metaphor", "simile",
                "the poem", "the story", "the novel", "protagonist", "narrator", "setting", "tone", "mood"]
    if not any(t in lowered for t in triggers):
        return None

    steps = [
        HintStep("What is the text literally about — who are the people/characters, and what happens?"),
        HintStep("Look for repeated words, images, or ideas. What might the author be emphasizing by repeating them?"),
        HintStep("Connect that pattern to a bigger idea about life. Can you state it in one full sentence (avoid a single word like 'love' — say what the text says ABOUT love)?"),
        HintStep("Support your idea with one specific quote or example from the text.", is_answer=True),
    ]
    return Guidance("literary_analysis", "English · Literary Analysis", steps)


def _generic_fallback(text: str) -> Guidance:
    steps = [
        HintStep("What is this question actually asking you to do?"),
        HintStep("Reread the relevant sentence or passage carefully, more than once if needed."),
        HintStep("Try answering in your own words first, then check that it makes sense in context."),
        HintStep("Write your final answer in a complete sentence.", is_answer=True),
    ]
    return Guidance("generic_english", "English · Problem-Solving Strategy", steps)


_DETECTORS = [
    _try_vocabulary_context,
    _try_grammar_fragment_runon,
    _try_reading_comprehension,
    _try_literary_analysis,
    _try_essay_prompt,
]


def generate_english_hints(question_text: str) -> Guidance:
    for detector in _DETECTORS:
        try:
            result = detector(question_text)
        except Exception:
            result = None
        if result is not None:
            return result
    return _generic_fallback(question_text)
