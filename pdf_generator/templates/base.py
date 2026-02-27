"""Base template class for PDF generation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DocumentContent:
    """Holds all content fields for a PDF document."""

    title: str = ""
    subtitle: str = ""
    body: str = ""
    footer: str = ""
    author: str = ""
    date: str = ""
    tags: list[str] = field(default_factory=list)


class BaseTemplate(ABC):
    """Abstract base class for all PDF templates."""

    #: Human-readable name displayed in listings
    name: str = ""
    #: Short description of the template
    description: str = ""

    @abstractmethod
    def render(self, canvas, doc_content: DocumentContent, width: float, height: float) -> None:
        """Draw the template onto the given ReportLab canvas.

        Args:
            canvas: A ReportLab ``canvas.Canvas`` instance.
            doc_content: The content to render.
            width: Page width in points.
            height: Page height in points.
        """
