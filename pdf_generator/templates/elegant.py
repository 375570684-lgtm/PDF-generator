"""Elegant template – centred typographic poster style."""

import textwrap

from reportlab.lib import colors
from reportlab.lib.units import mm

from .base import BaseTemplate, DocumentContent

BG = colors.HexColor("#FDFAF6")
DARK = colors.HexColor("#1C1C1C")
ACCENT = colors.HexColor("#8B6914")
RULE = colors.HexColor("#C8A951")
LIGHT = colors.HexColor("#A09070")


class ElegantTemplate(BaseTemplate):
    """Centred typographic layout with decorative rules – elegant poster style."""

    name = "elegant"
    description = "Centred typographic layout with decorative rules and warm tones."

    def render(self, canvas, doc_content: DocumentContent, width: float, height: float) -> None:
        canvas.saveState()

        # ── background ─────────────────────────────────────────────────────────
        canvas.setFillColor(BG)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)

        # outer border
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(1.2)
        canvas.rect(10 * mm, 10 * mm, width - 20 * mm, height - 20 * mm, stroke=1, fill=0)

        # inner border
        canvas.setLineWidth(0.4)
        canvas.rect(12 * mm, 12 * mm, width - 24 * mm, height - 24 * mm, stroke=1, fill=0)

        cx = width / 2

        # ── top decorative rule ────────────────────────────────────────────────
        rule_y = height - 32 * mm
        _h_rule(canvas, cx, rule_y, 80 * mm, RULE, 0.8)

        # ── title ──────────────────────────────────────────────────────────────
        title = (doc_content.title or "Untitled").upper()
        font_size = max(14, min(28, int(140 / max(len(title), 1)) + 10))
        canvas.setFillColor(DARK)
        canvas.setFont("Helvetica-Bold", font_size)
        title_y = height - 44 * mm
        canvas.drawCentredString(cx, title_y, title)

        # ── subtitle ───────────────────────────────────────────────────────────
        sub_y = title_y - 9 * mm
        if doc_content.subtitle:
            canvas.setFillColor(ACCENT)
            canvas.setFont("Helvetica-Oblique", 12)
            canvas.drawCentredString(cx, sub_y, doc_content.subtitle)
            sub_y -= 7 * mm

        # ── decorative divider ─────────────────────────────────────────────────
        _h_rule(canvas, cx, sub_y - 3 * mm, 50 * mm, RULE, 0.8)
        _diamond(canvas, cx, sub_y - 3 * mm, RULE)

        # ── author / date ──────────────────────────────────────────────────────
        meta_y = sub_y - 9 * mm
        meta_parts = []
        if doc_content.author:
            meta_parts.append(doc_content.author)
        if doc_content.date:
            meta_parts.append(doc_content.date)
        if meta_parts:
            canvas.setFillColor(LIGHT)
            canvas.setFont("Helvetica", 9)
            canvas.drawCentredString(cx, meta_y, "  ·  ".join(meta_parts))
            meta_y -= 8 * mm

        # ── body text (justified-ish via centring) ─────────────────────────────
        body_y = meta_y - 4 * mm
        canvas.setFillColor(DARK)
        canvas.setFont("Helvetica", 10.5)
        line_h = 6 * mm
        body_w = width - 50 * mm
        char_w = int(body_w / (10.5 * 0.55))
        for paragraph in (doc_content.body or "").split("\n"):
            for line in textwrap.wrap(paragraph, width=char_w) or [""]:
                if body_y < 26 * mm:
                    break
                canvas.drawCentredString(cx, body_y, line)
                body_y -= line_h
            body_y -= 2 * mm

        # ── tags ───────────────────────────────────────────────────────────────
        if doc_content.tags:
            tag_y = 26 * mm
            tag_text = "  ·  ".join(f"#{t}" for t in doc_content.tags)
            canvas.setFillColor(LIGHT)
            canvas.setFont("Helvetica-Oblique", 8)
            canvas.drawCentredString(cx, tag_y, tag_text)

        # ── footer ─────────────────────────────────────────────────────────────
        _h_rule(canvas, cx, 19 * mm, 80 * mm, RULE, 0.8)
        if doc_content.footer:
            canvas.setFillColor(LIGHT)
            canvas.setFont("Helvetica", 8)
            canvas.drawCentredString(cx, 14 * mm, doc_content.footer)

        canvas.restoreState()


def _h_rule(canvas, cx, y, half_w, color, lw):
    canvas.setStrokeColor(color)
    canvas.setLineWidth(lw)
    canvas.line(cx - half_w, y, cx + half_w, y)


def _diamond(canvas, cx, y, color):
    """Draw a small rotated square (diamond) centred at (cx, y)."""
    d = 2 * mm
    canvas.setFillColor(color)
    p = canvas.beginPath()
    p.moveTo(cx, y + d)
    p.lineTo(cx + d, y)
    p.lineTo(cx, y - d)
    p.lineTo(cx - d, y)
    p.close()
    canvas.drawPath(p, fill=1, stroke=0)
