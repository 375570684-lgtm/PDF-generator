"""Tests for the PDF generator."""

import io
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_generator import PDFGenerator
from pdf_generator.templates import get_template, list_templates
from pdf_generator.templates.base import DocumentContent


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

class TestTemplateRegistry:
    def test_list_templates_returns_four(self):
        names = list_templates()
        assert len(names) == 4

    def test_list_templates_includes_all_expected(self):
        names = list_templates()
        for expected in ("simple", "business", "elegant", "newsletter"):
            assert expected in names

    def test_get_template_valid(self):
        for name in list_templates():
            t = get_template(name)
            assert t.name == name

    def test_get_template_case_insensitive(self):
        t = get_template("SIMPLE")
        assert t.name == "simple"

    def test_get_template_invalid_raises(self):
        with pytest.raises(ValueError, match="Unknown template"):
            get_template("nonexistent")


# ---------------------------------------------------------------------------
# DocumentContent
# ---------------------------------------------------------------------------

class TestDocumentContent:
    def test_defaults(self):
        dc = DocumentContent()
        assert dc.title == ""
        assert dc.tags == []

    def test_custom_values(self):
        dc = DocumentContent(title="Hello", tags=["a", "b"])
        assert dc.title == "Hello"
        assert dc.tags == ["a", "b"]


# ---------------------------------------------------------------------------
# PDFGenerator construction
# ---------------------------------------------------------------------------

class TestPDFGeneratorInit:
    def test_default_template_and_size(self):
        gen = PDFGenerator()
        assert gen.template.name == "simple"

    def test_custom_template(self):
        for name in list_templates():
            gen = PDFGenerator(template=name)
            assert gen.template.name == name

    def test_invalid_page_size_raises(self):
        with pytest.raises(ValueError, match="Unknown page size"):
            PDFGenerator(page_size="a3")

    def test_available_templates_static(self):
        assert PDFGenerator.available_templates() == list_templates()


# ---------------------------------------------------------------------------
# PDF generation – output is valid PDF bytes
# ---------------------------------------------------------------------------

PDF_HEADER = b"%PDF-"


def _make_content():
    return dict(
        title="Test Title",
        subtitle="Test Subtitle",
        body="First paragraph.\n\nSecond paragraph.",
        footer="Page 1",
        author="Test Author",
        date="2024-01-01",
        tags=["foo", "bar"],
    )


class TestGenerateBytes:
    @pytest.mark.parametrize("template", ["simple", "business", "elegant", "newsletter"])
    def test_returns_valid_pdf_bytes(self, template):
        gen = PDFGenerator(template=template)
        data = gen.generate_bytes(**_make_content())
        assert data[:5] == PDF_HEADER

    def test_minimal_content(self):
        gen = PDFGenerator()
        data = gen.generate_bytes()
        assert data[:5] == PDF_HEADER

    def test_no_tags(self):
        gen = PDFGenerator()
        data = gen.generate_bytes(title="No Tags", body="Body text.")
        assert data[:5] == PDF_HEADER

    def test_long_title(self):
        gen = PDFGenerator()
        data = gen.generate_bytes(title="A" * 100, body="Body.")
        assert data[:5] == PDF_HEADER

    def test_long_body(self):
        gen = PDFGenerator()
        long_body = ("Lorem ipsum dolor sit amet. " * 30 + "\n") * 5
        data = gen.generate_bytes(title="Long Body Test", body=long_body)
        assert data[:5] == PDF_HEADER


class TestGenerateFile:
    def test_write_to_file(self, tmp_path):
        out = tmp_path / "test.pdf"
        gen = PDFGenerator()
        gen.generate(out, **_make_content())
        assert out.exists()
        assert out.stat().st_size > 100
        assert out.read_bytes()[:5] == PDF_HEADER

    def test_write_to_string_path(self, tmp_path):
        out = str(tmp_path / "test_str.pdf")
        gen = PDFGenerator()
        gen.generate(out, title="String Path")
        assert Path(out).exists()

    def test_write_to_bytesio(self):
        buf = io.BytesIO()
        gen = PDFGenerator()
        gen.generate(buf, **_make_content())
        assert buf.getvalue()[:5] == PDF_HEADER

    @pytest.mark.parametrize("template", ["simple", "business", "elegant", "newsletter"])
    def test_all_templates_produce_files(self, tmp_path, template):
        out = tmp_path / f"{template}.pdf"
        gen = PDFGenerator(template=template)
        gen.generate(out, **_make_content())
        assert out.stat().st_size > 500

    def test_letter_page_size(self, tmp_path):
        out = tmp_path / "letter.pdf"
        gen = PDFGenerator(page_size="letter")
        gen.generate(out, title="Letter Size")
        assert out.exists()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestCLI:
    def test_list_templates(self, capsys):
        from cli import main
        rc = main(["--list-templates"])
        assert rc == 0
        out = capsys.readouterr().out
        for name in list_templates():
            assert name in out

    def test_generate_via_cli(self, tmp_path):
        from cli import main
        out = str(tmp_path / "cli_test.pdf")
        rc = main([
            "--template", "simple",
            "--output", out,
            "--title", "CLI Title",
            "--body", "CLI body text.",
            "--author", "CLI Author",
        ])
        assert rc == 0
        assert Path(out).exists()
        assert Path(out).read_bytes()[:5] == PDF_HEADER

    def test_generate_with_config(self, tmp_path):
        import yaml
        from cli import main
        cfg = {
            "template": "elegant",
            "title": "Config Title",
            "body": "Config body.",
        }
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text(yaml.dump(cfg))
        out = str(tmp_path / "config_test.pdf")
        rc = main(["--config", str(cfg_path), "--output", out])
        assert rc == 0
        assert Path(out).exists()

    def test_missing_config_returns_error(self, tmp_path):
        from cli import main
        rc = main(["--config", str(tmp_path / "nonexistent.yaml"), "--output", "/tmp/x.pdf"])
        assert rc == 1

    def test_body_file(self, tmp_path):
        from cli import main
        body_file = tmp_path / "body.txt"
        body_file.write_text("Body from file.")
        out = str(tmp_path / "body_file_test.pdf")
        rc = main(["--body-file", str(body_file), "--output", out])
        assert rc == 0
        assert Path(out).exists()

    def test_tags_parsed(self, tmp_path):
        from cli import main
        out = str(tmp_path / "tags_test.pdf")
        rc = main(["--tags", "python,pdf,tool", "--output", out])
        assert rc == 0
        assert Path(out).exists()
