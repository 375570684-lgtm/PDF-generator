"""Template base class and built-in template definitions."""

from .base import BaseTemplate
from .simple import SimpleTemplate
from .business import BusinessTemplate
from .elegant import ElegantTemplate
from .newsletter import NewsletterTemplate

TEMPLATES = {
    "simple": SimpleTemplate,
    "business": BusinessTemplate,
    "elegant": ElegantTemplate,
    "newsletter": NewsletterTemplate,
}


def get_template(name: str) -> BaseTemplate:
    """Return a template instance by name."""
    name = name.lower()
    if name not in TEMPLATES:
        available = ", ".join(TEMPLATES.keys())
        raise ValueError(f"Unknown template '{name}'. Available: {available}")
    return TEMPLATES[name]()


def list_templates() -> list[str]:
    """Return a list of available template names."""
    return list(TEMPLATES.keys())
