"""Simple / Minimal template – clean white page with a coloured header bar."""

import textwrap

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .base import BaseTemplate, DocumentContent

# Accent colour: deep indigo
ACCENT = colors.HexColor("#3B4CCA")
TEXT_DARK = colors.HexColor("#1A1A2E")
TEXT_MID = colors.HexColor("#4A4A6A")
TEXT_LIGHT = colors.HexColor("#8888AA")
BG_LIGHT = colors.HexColor("#F5F5FF")


class SimpleTemplate(BaseTemplate):
    """Clean minimal template with a solid header band."""

    name = "simple"
    description = "Clean minimal design with a solid header bar and clear typography."

    def render(self, canvas, doc_content: DocumentContent, width: float, height: float) -> None:
        canvas.saveState()

        # ── background ─────────────────────────────────────────────────────────
        canvas.setFillColor(colors.white)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)

        # ── header band ────────────────────────────────────────────────────────
        header_h = 28 * mm
        canvas.setFillColor(ACCENT)
        canvas.rect(0, height - header_h, width, header_h, fill=1, stroke=0)

        # Title inside header
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 22)
        title = doc_content.title or "Untitled"
        canvas.drawString(18 * mm, height - header_h + 10 * mm, title)

        # Author + date on right side of header
        meta = []
        if doc_content.author:
            meta.append(doc_content.author)
        if doc_content.date:
            meta.append(doc_content.date)
        if meta:
            canvas.setFont("Helvetica", 9)
            canvas.drawRightString(width - 18 * mm, height - header_h + 10 * mm, "  ·  ".join(meta))

        # ── subtitle ───────────────────────────────────────────────────────────
        y = height - header_h - 12 * mm
        if doc_content.subtitle:
            canvas.setFillColor(ACCENT)
            canvas.setFont("Helvetica-Oblique", 13)
            canvas.drawString(18 * mm, y, doc_content.subtitle)
            y -= 8 * mm

        # thin divider
        canvas.setStrokeColor(ACCENT)
        canvas.setLineWidth(0.8)
        canvas.line(18 * mm, y, width - 18 * mm, y)
        y -= 7 * mm

        # ── body text ──────────────────────────────────────────────────────────
        canvas.setFillColor(TEXT_DARK)
        canvas.setFont("Helvetica", 10.5)
        line_height = 5.8 * mm
        max_width_chars = int((width - 36 * mm) / (10.5 * 0.55))
        for paragraph in (doc_content.body or "").split("\n"):
            for line in textwrap.wrap(paragraph, width=max_width_chars) or [""]:
                if y < 22 * mm:
                    break
                canvas.drawString(18 * mm, y, line)
                y -= line_height
            y -= 2 * mm

        # ── tags ───────────────────────────────────────────────────────────────
        if doc_content.tags:
            tag_y = 22 * mm
            x_cursor = 18 * mm
            canvas.setFont("Helvetica", 8)
            for tag in doc_content.tags:
                tag_text = f"  #{tag}  "
                tag_w = canvas.stringWidth(tag_text, "Helvetica", 8) + 2
                canvas.setFillColor(BG_LIGHT)
                canvas.roundRect(x_cursor, tag_y - 1 * mm, tag_w, 5 * mm, 1.5 * mm, fill=1, stroke=0)
                canvas.setFillColor(ACCENT)
                canvas.drawString(x_cursor + 1, tag_y + 1 * mm, tag_text)
                x_cursor += tag_w + 2 * mm

        # ── footer ─────────────────────────────────────────────────────────────
        footer_text = doc_content.footer or ""
        canvas.setFillColor(TEXT_LIGHT)
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(width / 2, 10 * mm, footer_text)

        # thin bottom rule
        canvas.setStrokeColor(ACCENT)
        canvas.setLineWidth(0.4)
        canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)

        canvas.restoreState()
