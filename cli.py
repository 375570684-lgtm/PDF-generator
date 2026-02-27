#!/usr/bin/env python3
"""Command-line interface for the PDF generator."""

import argparse
import sys
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from pdf_generator import PDFGenerator
from pdf_generator.templates import list_templates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-generator",
        description="Generate a beautifully formatted one-page PDF from text.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-t", "--template",
        default="simple",
        choices=list_templates(),
        help="Template to use (default: simple).",
    )
    parser.add_argument(
        "-o", "--output",
        default="output.pdf",
        metavar="FILE",
        help="Output PDF file path (default: output.pdf).",
    )
    parser.add_argument(
        "-s", "--page-size",
        default="a4",
        choices=["a4", "letter"],
        metavar="SIZE",
        help="Page size: a4 or letter (default: a4).",
    )
    parser.add_argument("--title", default="", help="Document title.")
    parser.add_argument("--subtitle", default="", help="Subtitle / tagline.")
    parser.add_argument("--author", default="", help="Author name.")
    parser.add_argument("--date", default="", help="Date string.")
    parser.add_argument("--footer", default="", help="Footer text.")
    parser.add_argument(
        "--tags",
        default="",
        metavar="TAG1,TAG2,...",
        help="Comma-separated list of tags.",
    )
    parser.add_argument(
        "--body",
        default="",
        help="Body text.  Use '\\n' for paragraph breaks.",
    )
    parser.add_argument(
        "--body-file",
        default="",
        metavar="FILE",
        help="Read body text from a file instead of --body.",
    )
    parser.add_argument(
        "--config",
        default="",
        metavar="FILE",
        help=(
            "YAML config file.  All fields above can be specified in the file.\n"
            "CLI flags override config file values."
        ),
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available templates and exit.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_templates:
        print("Available templates:")
        for name in list_templates():
            print(f"  {name}")
        return 0

    # Defaults from config file (if given)
    cfg: dict = {}
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: config file not found: {args.config}", file=sys.stderr)
            return 1
        with config_path.open() as fh:
            cfg = yaml.safe_load(fh) or {}

    def _get(key, default=""):
        cli_val = getattr(args, key.replace("-", "_"), None)
        return cli_val if cli_val else cfg.get(key, default)

    title = _get("title")
    subtitle = _get("subtitle")
    author = _get("author")
    date = _get("date")
    footer = _get("footer")
    template = args.template if args.template != "simple" else cfg.get("template", "simple")
    output = args.output if args.output != "output.pdf" else cfg.get("output", "output.pdf")
    page_size = args.page_size if args.page_size != "a4" else cfg.get("page_size", "a4")

    # Body text
    body = args.body.replace("\\n", "\n")
    if not body and args.body_file:
        body_path = Path(args.body_file)
        if not body_path.exists():
            print(f"Error: body file not found: {args.body_file}", file=sys.stderr)
            return 1
        body = body_path.read_text()
    if not body:
        body = cfg.get("body", "")

    # Tags
    raw_tags = args.tags or cfg.get("tags", "")
    if isinstance(raw_tags, list):
        tags = raw_tags
    else:
        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]

    gen = PDFGenerator(template=template, page_size=page_size)
    gen.generate(
        output,
        title=title,
        subtitle=subtitle,
        body=body,
        footer=footer,
        author=author,
        date=date,
        tags=tags,
    )
    print(f"PDF generated: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
