"""Classify a homework question as math or English using simple heuristics.

No LLM is used here on purpose: this is a fast, deterministic keyword and
pattern scorer, good enough to route a question to the right tutor module.
"""
from __future__ import annotations

import re

MATH_KEYWORDS = [
    "solve", "equation", "simplify", "factor", "evaluate", "slope",
    "graph", "triangle", "angle", "perimeter", "area", "volume",
    "expression", "inequality", "polynomial", "exponent", "root",
    "function", "variable", "coefficient", "hypotenuse", "circumference",
    "radius", "diameter", "ratio", "proportion", "integer", "fraction",
]

ENGLISH_KEYWORDS = [
    "essay", "paragraph", "sentence", "grammar", "noun", "verb",
    "adjective", "pronoun", "adverb", "thesis", "theme", "character",
    "plot", "metaphor", "simile", "punctuation", "comma", "apostrophe",
    "passage", "summarize", "summary", "main idea", "vocabulary",
    "synonym", "antonym", "context clue", "author", "poem", "story",
    "paraphrase", "narrator", "setting", "conflict", "tone", "mood",
    "fragment", "run-on", "run on",
]

_MATH_SYMBOL_RE = re.compile(r"[=<>]|\^|\d+\s*[+\-*/]\s*\d+")
_PROSE_HINT_RE = re.compile(r'"[^"]{3,}"|\bthe\b.*\bthe\b', re.IGNORECASE)


def classify_subject(text: str) -> str:
    """Return 'math' or 'english' for the given question text."""
    lowered = text.lower()

    math_score = sum(1 for kw in MATH_KEYWORDS if kw in lowered)
    english_score = sum(1 for kw in ENGLISH_KEYWORDS if kw in lowered)

    if _MATH_SYMBOL_RE.search(text):
        math_score += 2
    if _PROSE_HINT_RE.search(text):
        english_score += 1
    if re.search(r"\bf\s*\(\s*x\s*\)", lowered):
        math_score += 2

    return "math" if math_score >= english_score else "english"
