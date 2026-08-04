"""Split raw homework text into individual questions."""
from __future__ import annotations

import re

_NUMBERED_RE = re.compile(
    r"(?m)^[ \t]*(?:\(?\d{1,2}[\.\)]|Q(?:uestion)?\s*\d{1,2}[\.:\)])[ \t]+"
)


def split_questions(text: str) -> list[str]:
    """Break homework text into a list of individual question strings.

    Falls back to treating the whole text as a single question when fewer
    than two numbered items are found (e.g. a single essay prompt).
    """
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []

    matches = list(_NUMBERED_RE.finditer(text))
    if len(matches) < 2:
        return [text]

    questions = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if chunk:
            questions.append(chunk)
    return questions or [text]
