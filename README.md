# PDF Generator

A tool to automatically generate a beautifully formatted **one-page PDF** from text input.
Provide your title, body text, and choose a template — the layout is handled for you.

---

## Features

- 📄 **One-page PDF output** — A4 or Letter size
- 🎨 **4 built-in templates** — Simple, Business, Elegant, Newsletter
- 🏷️ **Tag support** — display keyword tags on the page
- ⚙️ **YAML config files** — store your document settings as reusable templates
- 🖥️ **CLI interface** — generate PDFs from the command line in one step
- 🐍 **Python API** — integrate into your own scripts

---

## Templates

| Name | Description |
|------|-------------|
| `simple` | Clean minimal design with a solid indigo header bar |
| `business` | Professional layout with a dark sidebar and gold accents |
| `elegant` | Centred typographic layout with decorative rules and warm tones |
| `newsletter` | Bold magazine header with a content card and accent colours |

---

## Installation

```bash
pip install -r requirements.txt
```

**Requirements:** Python 3.10+, `reportlab`, `Pillow`, `PyYAML`

---

## Quick Start

### Command Line

```bash
# Generate a PDF with the simple template
python cli.py --title "My Document" --body "Hello, world!" --output my_doc.pdf

# Use the elegant template
python cli.py --template elegant \
              --title "The Art of Simplicity" \
              --subtitle "A reflection on design" \
              --author "Jane Doe" \
              --date "March 2024" \
              --body "Your body text goes here..." \
              --tags "essay,design,philosophy" \
              --output elegant.pdf

# Read body from a file
python cli.py --template business --body-file article.txt --output report.pdf

# Use a YAML config file (see sample_templates/)
python cli.py --config sample_templates/newsletter.yaml --output newsletter.pdf

# List available templates
python cli.py --list-templates
```

### YAML Config File

Create a `.yaml` file (see `sample_templates/` for examples):

```yaml
template: business
output: report.pdf
page_size: a4

title: "Quarterly Report"
subtitle: "Q4 2024 Financial Summary"
author: "John Smith"
date: "2024-12-31"
footer: "Internal Use Only"
tags:
  - finance
  - quarterly
body: |
  This report covers Q4 performance...

  Revenue grew by 12% year-over-year...
```

Then run:

```bash
python cli.py --config report.yaml
```

### Python API

```python
from pdf_generator import PDFGenerator

gen = PDFGenerator(template="elegant", page_size="a4")

# Write to a file
gen.generate(
    "output.pdf",
    title="Hello World",
    subtitle="Generated with PDF Generator",
    body="Your content here.\n\nSecond paragraph.",
    author="Alice",
    date="2024-01-15",
    tags=["python", "pdf"],
    footer="Page 1",
)

# Or get raw bytes (e.g. for a web API)
pdf_bytes = gen.generate_bytes(title="My PDF", body="Content...")
```

---

## CLI Reference

| Flag | Description | Default |
|------|-------------|---------|
| `-t, --template` | Template name | `simple` |
| `-o, --output` | Output file path | `output.pdf` |
| `-s, --page-size` | `a4` or `letter` | `a4` |
| `--title` | Document title | |
| `--subtitle` | Subtitle / tagline | |
| `--author` | Author name | |
| `--date` | Date string | |
| `--body` | Body text (`\n` for paragraphs) | |
| `--body-file` | Read body from a text file | |
| `--footer` | Footer text | |
| `--tags` | Comma-separated tags | |
| `--config` | YAML config file | |
| `--list-templates` | List templates and exit | |

---

## Project Structure

```
PDF-generator/
├── cli.py                    # Command-line interface
├── pdf_generator/
│   ├── __init__.py
│   ├── generator.py          # Core PDFGenerator class
│   └── templates/
│       ├── __init__.py       # Template registry
│       ├── base.py           # BaseTemplate + DocumentContent
│       ├── simple.py         # Simple / Minimal template
│       ├── business.py       # Business / Sidebar template
│       ├── elegant.py        # Elegant / Centred template
│       └── newsletter.py     # Newsletter / Magazine template
├── sample_templates/         # Example YAML config files
│   ├── simple.yaml
│   ├── business.yaml
│   ├── elegant.yaml
│   └── newsletter.yaml
├── tests/
│   └── test_pdf_generator.py
├── requirements.txt
└── pyproject.toml
```

---

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Adding a Custom Template

1. Create `pdf_generator/templates/my_template.py` subclassing `BaseTemplate`
2. Implement the `render(canvas, doc_content, width, height)` method
3. Register it in `pdf_generator/templates/__init__.py`

```python
from .my_template import MyTemplate

TEMPLATES = {
    ...,
    "my_template": MyTemplate,
}
```
