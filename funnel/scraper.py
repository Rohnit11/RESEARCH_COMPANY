"""Stage 2 - SCRAPE.

Given a target config (row selector + field selectors), extract records across
pages with a randomized "safe timer" between navigations to avoid IP blocks.

Field selector syntax:
    ".price_color"        -> innerText of the first match inside the row
    "h3 a @title"         -> the 'title' attribute
    "h3 a @href"          -> the 'href' attribute (auto-resolved to absolute URL)
"""
from __future__ import annotations

import logging
import random
import time
from urllib.parse import urljoin

log = logging.getLogger("funnel.scraper")


def _parse_field(spec: str):
    """Return (css_selector, attribute_or_None)."""
    if " @" in spec:
        sel, attr = spec.rsplit(" @", 1)
        return sel.strip(), attr.strip()
    return spec.strip(), None


def _extract_one(row, spec: str, base_url: str):
    sel, attr = _parse_field(spec)
    target = row if sel in ("", ".") else row.query_selector(sel)
    if target is None:
        return None
    if attr:
        val = target.get_attribute(attr)
        if val and attr.lower() in ("href", "src"):
            return urljoin(base_url, val)
        return val
    text = target.inner_text()
    return text.strip() if text else None


def safe_sleep(min_delay: float, max_delay: float) -> float:
    """Sleep a random amount in [min, max]. Returns the delay used."""
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)
    return delay


def scrape_target(page, target: dict, defaults: dict) -> list[dict]:
    """Scrape one target across up to max_pages, politely paced."""
    cfg = {**defaults, **target}
    row_sel = target["row"]
    fields = target["fields"]
    next_sel = target.get("next_page")
    max_pages = int(cfg.get("max_pages", 3))
    min_d = float(cfg.get("min_delay_sec", 4.0))
    max_d = float(cfg.get("max_delay_sec", 9.0))

    url = target["url"]
    rows: list[dict] = []

    for page_num in range(1, max_pages + 1):
        log.info("[%s] page %d/%d -> %s", target["name"], page_num, max_pages, url)
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(800)

        elements = page.query_selector_all(row_sel)
        log.info("[%s] found %d rows", target["name"], len(elements))
        for el in elements:
            record = {"_source": target["name"], "_page_url": url}
            for col, spec in fields.items():
                record[col] = _extract_one(el, spec, url)
            rows.append(record)

        # Follow pagination if configured and present.
        next_url = None
        if next_sel and page_num < max_pages:
            sel, attr = _parse_field(next_sel)
            nxt = page.query_selector(sel)
            if nxt:
                href = nxt.get_attribute(attr or "href")
                if href:
                    next_url = urljoin(url, href)
        if not next_url:
            break
        url = next_url

        # THE SAFE TIMER: randomized pause before hitting the next page.
        waited = safe_sleep(min_d, max_d)
        log.info("[%s] safe-timer slept %.1fs", target["name"], waited)

    return rows
