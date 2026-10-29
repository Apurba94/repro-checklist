"""Reproducibility checklist with automatic project detection and a Markdown report."""
from .core import CHECKLIST, auto_detect, score, render_report

__version__ = "0.1.0"
__all__ = ["CHECKLIST", "auto_detect", "score", "render_report"]
