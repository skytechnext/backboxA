"""Typed website actions used by the site stage agents (stdlib only)."""
from __future__ import annotations

import html


class SiteBuild:
    """Mutable state shared across the website pipeline stages."""

    def __init__(self):
        self.sources: list[dict] = []        # resolved input sources
        self.facts: dict[str, dict] = {}     # fact -> {"value":..., "source":...}
        self.pages: dict[str, dict] = {}     # id -> {title, description, sections, links}
        self.copy: dict[str, str] = {}       # "page#section" -> text
        self.build: dict[str, str] = {}      # route -> rendered html
        self.deployment: dict | None = None


def render_page(page: dict, copy: dict[str, str]) -> str:
    title = html.escape(page["title"])
    desc = html.escape(page.get("description", ""))
    body = []
    for sec in page.get("sections", []):
        text = html.escape(copy.get(f"{page['id']}#{sec}", ""))
        body.append(f"    <section id='{sec}'><p>{text}</p></section>")
    links = "".join(f"<a href='/{l}'>{l}</a> " for l in page.get("links", []))
    return (
        "<!DOCTYPE html>\n<html lang='en'><head>"
        f"<meta charset='utf-8'><title>{title}</title>"
        f"<meta name='description' content='{desc}'>"
        "</head><body>\n"
        f"  <h1>{title}</h1>\n" + "\n".join(body) + f"\n  <nav>{links}</nav>\n"
        "</body></html>\n"
    )


def route_for(page_id: str) -> str:
    return "/" if page_id == "home" else f"/{page_id}"


def broken_links(pages: dict[str, dict]) -> list[str]:
    ids = set(pages.keys())
    broken = []
    for pid, page in pages.items():
        for target in page.get("links", []):
            if target not in ids:
                broken.append(f"{pid} → {target}")
    return broken
