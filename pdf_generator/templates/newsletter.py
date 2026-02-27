"""Newsletter template – modern card grid / magazine layout."""

import textwrap

from reportlab.lib import colors
from reportlab.lib.units import mm

from .base import BaseTemplate, DocumentContent

PRIMARY = colors.HexColor("#E63946")
SECONDARY = colors.HexColor("#457B9D")
DARK = colors.HexColor("#1D3557")
LIGHT_BG = colors.HexColor("#F1FAEE")
CARD_BG = colors.HexColor("#A8DADC")


class NewsletterTemplate(BaseTemplate):
    """Modern newsletter / magazine layout with bold header and content card."""

    name = "newsletter"
    description = "Bold magazine header with a content card and accent colours."

    def render(self, canvas, doc_content: DocumentContent, width: float, height: float) -> None:
        canvas.saveState()

        # ── background ─────────────────────────────────────────────────────────
        canvas.setFillColor(LIGHT_BG)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)

        # ── masthead / banner ──────────────────────────────────────────────────
        banner_h = 40 * mm
        canvas.setFillColor(DARK)
        canvas.rect(0, height - banner_h, width, banner_h, fill=1, stroke=0)

        # red accent on left edge
        canvas.setFillColor(PRIMARY)
        canvas.rect(0, height - banner_h, 4 * mm, banner_h, fill=1, stroke=0)

        # issue / date chip
        if doc_content.date:
            chip_w = 32 * mm
            chip_x = width - chip_w - 10 * mm
            canvas.setFillColor(PRIMARY)
            canvas.roundRect(chip_x, height - 16 * mm, chip_w, 8 * mm, 1.5 * mm, fill=1, stroke=0)
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawCentredString(chip_x + chip_w / 2, height - 11 * mm, doc_content.date)

        # title in banner
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 24)
        canvas.drawString(12 * mm, height - banner_h + 16 * mm, doc_content.title or "Newsletter")

        # subtitle
        if doc_content.subtitle:
            canvas.setFillColor(CARD_BG)
            canvas.setFont("Helvetica", 10)
            canvas.drawString(12 * mm, height - banner_h + 7 * mm, doc_content.subtitle)

        # ── author strip ───────────────────────────────────────────────────────
        strip_h = 8 * mm
        strip_y = height - banner_h - strip_h
        canvas.setFillColor(SECONDARY)
        canvas.rect(0, strip_y, width, strip_h, fill=1, stroke=0)
        if doc_content.author:
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(12 * mm, strip_y + 2.5 * mm, f"BY  {doc_content.author.upper()}")

        # ── content card ───────────────────────────────────────────────────────
        card_margin = 12 * mm
        card_y_top = strip_y - 8 * mm
        card_bottom = 22 * mm
        card_h = card_y_top - card_bottom
        canvas.setFillColor(colors.white)
        canvas.setStrokeColor(colors.HexColor("#CBD5E0"))
        canvas.setLineWidth(0.5)
        canvas.roundRect(card_margin, card_bottom, width - 2 * card_margin, card_h,
                         3 * mm, fill=1, stroke=1)

        # left colour bar inside card
        canvas.setFillColor(PRIMARY)
        canvas.roundRect(card_margin, card_bottom, 3 * mm, card_h, 1.5 * mm, fill=1, stroke=0)

        # body text
        text_x = card_margin + 8 * mm
        text_w = width - 2 * card_margin - 12 * mm
        y = card_y_top - 8 * mm
        canvas.setFillColor(DARK)
        canvas.setFont("Helvetica", 10.5)
        line_h = 5.8 * mm
        char_w = int(text_w / (10.5 * 0.55))
        for paragraph in (doc_content.body or "").split("\n"):
            for line in textwrap.wrap(paragraph, width=char_w) or [""]:
                if y < card_bottom + 4 * mm:
                    break
                canvas.drawString(text_x, y, line)
                y -= line_h
            y -= 2 * mm

        # ── tags ───────────────────────────────────────────────────────────────
        if doc_content.tags:
            tx = card_margin + 8 * mm
            ty = card_bottom - 8 * mm
            canvas.setFont("Helvetica", 8)
            for tag in doc_content.tags[:6]:
                canvas.setFillColor(SECONDARY)
                tw = canvas.stringWidth(f" #{tag} ", "Helvetica", 8) + 2
                canvas.roundRect(tx, ty, tw, 5 * mm, 1.2 * mm, fill=1, stroke=0)
                canvas.setFillColor(colors.white)
                canvas.drawString(tx + 1, ty + 1.5 * mm, f" #{tag} ")
                tx += tw + 2 * mm

        # ── footer ─────────────────────────────────────────────────────────────
        canvas.setFillColor(DARK)
        canvas.setFont("Helvetica", 8)
        footer = doc_content.footer or ""
        canvas.drawCentredString(width / 2, 10 * mm, footer)

        # bottom rule
        canvas.setStrokeColor(PRIMARY)
        canvas.setLineWidth(1.5)
        canvas.line(card_margin, 14 * mm, width - card_margin, 14 * mm)

        canvas.restoreState()
