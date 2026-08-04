# Homework Helper — 9th Grade Math & English Teaching Agent

A web app that takes a photo or PDF of a student's homework and walks them
through it with **progressive Socratic hints** instead of handing over the
answer. Covers 9th grade Math (Algebra 1 basics + intro geometry) and
English (writing, reading, grammar, vocabulary, literary analysis).

No LLM/AI API is used — question detection, tutoring logic, and math
solving are all deterministic (regex heuristics + [sympy](https://www.sympy.org/)
for exact math), so it runs fully offline with no API key required.

## How it works

1. **Upload** a PDF or photo of the homework (or paste the text directly).
2. **Extraction** (`teaching_agent/extraction.py`) pulls text out with
   `pdfplumber`; pages that come back mostly empty (i.e. scanned images) are
   rendered and OCR'd with `pytesseract` via PyMuPDF.
3. **Parsing** (`teaching_agent/parsing.py`) splits the text into individual
   numbered questions.
4. **Classification** (`teaching_agent/classify.py`) tags each question as
   Math or English using keyword/symbol heuristics.
5. **Tutoring** (`teaching_agent/math_tutor.py`, `teaching_agent/english_tutor.py`)
   generates an ordered list of hints for that question — general strategy
   first, more specific steps next, and the worked answer last.
6. **Results page** reveals one hint at a time as the student clicks
   "Get a Hint," so they're never shown the answer before they've had a
   chance to try each step themselves.

### Math topics covered

Linear equations & inequalities, quadratic equations (factoring or the
quadratic formula), systems of two equations, slope between two points,
the Pythagorean theorem, exponent rules, evaluating functions, simplifying
expressions, and basic rectangle/triangle/circle area & perimeter. Anything
not recognized falls back to a general problem-solving-strategy sequence
(Polya-style: what's given, what's asked, what formula applies, check your
answer).

### English topics covered

Essay/writing prompts, reading comprehension, grammar (fragments &
run-ons), vocabulary in context, and literary analysis (theme, character,
symbolism). Since there's no language model doing the reading, these are
process/strategy hints (the same questions a tutor would ask) rather than
hints generated from actually understanding the passage's content.

## Running locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Then open http://localhost:5000.

OCR for scanned/photographed homework requires the `tesseract` binary to be
installed on the host (e.g. `apt install tesseract-ocr`). If it's not
installed, image-based OCR silently returns no text — pasting the homework
text directly always works as a fallback.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Limitations

- **In-memory results**: generated hint sessions live in a plain Python
  dict and are lost on server restart — fine for a single-user/demo
  deployment, not meant for production scale.
- **Rule-based, not AI**: math problems are solved exactly via sympy, but
  detection of *which* topic a question is (and extracting the equation
  from surrounding sentence text) is regex-based and works best on clearly
  formatted problems. English hints are strategy-based rather than content-
  aware, since no LLM is used to actually read and understand a passage.
