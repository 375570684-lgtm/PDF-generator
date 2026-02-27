"""Core PDF generation engine."""

import io
import os
from pathlib import Path
from typing import Optional, Union

from reportlab.lib.pagesizes import A4, LETTER
from reportlab.pdfgen import canvas as rl_canvas

from .templates import get_template, list_templates
from .templates.base import DocumentContent

PAGE_SIZES = {
    "a4": A4,
    "letter": LETTER,
}


class PDFGenerator:
    """Generate a one-page PDF from text content and a named template.

    Args:
        template: Template name (``"simple"``, ``"business"``, ``"elegant"``,
            ``"newsletter"``).  Defaults to ``"simple"``.
        page_size: ``"a4"`` or ``"letter"``.  Defaults to ``"a4"``.
    """

    def __init__(self, template: str = "simple", page_size: str = "a4") -> None:
        page_size_key = page_size.lower()
        if page_size_key not in PAGE_SIZES:
            raise ValueError(f"Unknown page size '{page_size}'. Use: {', '.join(PAGE_SIZES)}")
        self.template = get_template(template)
        self.page_size = PAGE_SIZES[page_size_key]
        self.width, self.height = self.page_size

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        output: Union[str, Path, io.BytesIO],
        title: str = "",
        subtitle: str = "",
        body: str = "",
        footer: str = "",
        author: str = "",
        date: str = "",
        tags: Optional[list[str]] = None,
    ) -> None:
        """Generate a PDF and write it to *output*.

        Args:
            output: File path (``str`` / ``Path``) or an ``io.BytesIO`` buffer.
            title: Main heading shown prominently in the template.
            subtitle: Secondary heading or tagline.
            body: The main body text.  Newlines create new paragraphs.
            footer: Optional small footer line.
            author: Author name.
            date: Date string (free-form).
            tags: Optional list of tag strings.
        """
        doc_content = DocumentContent(
            title=title,
            subtitle=subtitle,
            body=body,
            footer=footer,
            author=author,
            date=date,
            tags=list(tags) if tags else [],
        )

        if isinstance(output, (str, Path)):
            dest: Union[str, io.BytesIO] = str(output)
        else:
            dest = output

        c = rl_canvas.Canvas(dest, pagesize=self.page_size)
        self.template.render(c, doc_content, self.width, self.height)
        c.showPage()
        c.save()

    def generate_bytes(
        self,
        title: str = "",
        subtitle: str = "",
        body: str = "",
        footer: str = "",
        author: str = "",
        date: str = "",
        tags: Optional[list[str]] = None,
    ) -> bytes:
        """Generate a PDF and return it as a ``bytes`` object."""
        buf = io.BytesIO()
        self.generate(buf, title=title, subtitle=subtitle, body=body,
                      footer=footer, author=author, date=date, tags=tags)
        return buf.getvalue()

    @staticmethod
    def available_templates() -> list[str]:
        """Return names of all built-in templates."""
        return list_templates()
