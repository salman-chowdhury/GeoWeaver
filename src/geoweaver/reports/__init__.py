"""Machine-readable and human-readable recommendation reports."""

from geoweaver.reports.json_report import render_json
from geoweaver.reports.markdown_report import render_markdown

__all__ = ["render_json", "render_markdown"]
