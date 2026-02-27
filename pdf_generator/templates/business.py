"""Business template – professional two-column layout with sidebar."""

import textwrap

from reportlab.lib import colors
from reportlab.lib.units import mm

from .base import BaseTemplate, DocumentContent

NAVY = colors.HexColor("#0D2137")
GOLD = colors.HexColor("#C9963A")
LIGHT_GRAY = colors.HexColor("#F2F4F6")
DARK_GRAY = colors.HexColor("#2D3748")
MID_GRAY = colors.HexColor("#718096")

SIDEBAR_W = 60 * mm


class BusinessTemplate(BaseTemplate):
    """Professional business document with a dark left sidebar."""

    name = "business"
    description = "Professional layout with a dark sidebar and gold accents."

    def render(self, canvas, doc_content: DocumentContent, width: float, height: float) -> None:
        canvas.saveState()

        # ── page background ────────────────────────────────────────────────────
        canvas.setFillColor(colors.white)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)

        # ── left sidebar ───────────────────────────────────────────────────────
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, SIDEBAR_W, height, fill=1, stroke=0)

        # gold accent stripe at top of sidebar
        canvas.setFillColor(GOLD)
        canvas.rect(0, height - 6 * mm, SIDEBAR_W, 6 * mm, fill=1, stroke=0)

        # ── sidebar content ────────────────────────────────────────────────────
        sidebar_x = 8 * mm

        # Author name in sidebar
        if doc_content.author:
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 12)
            for i, word in enumerate(doc_content.author.split()):
                canvas.drawString(sidebar_x, height - 18 * mm - i * 7 * mm, word)

        # date block
        if doc_content.date:
            canvas.setFillColor(GOLD)
            canvas.setFont("Helvetica-Bold", 8)
            date_y = height - 48 * mm
            canvas.drawString(sidebar_x, date_y, "DATE")
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica", 9)
            canvas.drawString(sidebar_x, date_y - 5 * mm, doc_content.date)

        # tags
        if doc_content.tags:
            canvas.setFillColor(GOLD)
            canvas.setFont("Helvetica-Bold", 8)
            tags_y = height - 70 * mm
            canvas.drawString(sidebar_x, tags_y, "TAGS")
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica", 8)
            for i, tag in enumerate(doc_content.tags[:8]):
                canvas.drawString(sidebar_x, tags_y - (i + 1) * 5.5 * mm, f"• {tag}")

        # ── main area header ───────────────────────────────────────────────────
        main_x = SIDEBAR_W + 12 * mm
        main_w = width - SIDEBAR_W - 24 * mm

        # top gold rule
        canvas.setFillColor(GOLD)
        canvas.rect(SIDEBAR_W, height - 6 * mm, width - SIDEBAR_W, 6 * mm, fill=1, stroke=0)

        # Title
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 20)
        title_y = height - 22 * mm
        _draw_wrapped(canvas, doc_content.title or "Untitled", "Helvetica-Bold", 20,
                      main_x, title_y, main_w, NAVY, 9 * mm)

        # Subtitle
        if doc_content.subtitle:
            canvas.setFillColor(GOLD)
            canvas.setFont("Helvetica-Oblique", 11)
            canvas.drawString(main_x, height - 34 * mm, doc_content.subtitle)

        # divider
        canvas.setStrokeColor(LIGHT_GRAY)
        canvas.setLineWidth(1.2)
        divider_y = height - 38 * mm
        canvas.line(main_x, divider_y, width - 12 * mm, divider_y)

        # ── body text ──────────────────────────────────────────────────────────
        y = divider_y - 7 * mm
        canvas.setFillColor(DARK_GRAY)
        canvas.setFont("Helvetica", 10)
        line_h = 5.5 * mm
        char_w = int(main_w / (10 * 0.55))
        for paragraph in (doc_content.body or "").split("\n"):
            for line in textwrap.wrap(paragraph, width=char_w) or [""]:
                if y < 18 * mm:
                    break
                canvas.drawString(main_x, y, line)
                y -= line_h
            y -= 2 * mm

        # ── footer ─────────────────────────────────────────────────────────────
        canvas.setFillColor(MID_GRAY)
        canvas.setFont("Helvetica", 8)
        footer = doc_content.footer or ""
        canvas.drawString(main_x, 10 * mm, footer)

        canvas.restoreState()


def _draw_wrapped(canvas, text, font, size, x, y, max_w, color, line_h):
    char_w = int(max_w / (size * 0.55))
    canvas.setFillColor(color)
    canvas.setFont(font, size)
    for line in textwrap.wrap(text, width=char_w) or [text]:
        canvas.drawString(x, y, line)
        y -= line_h
