"""Stage 1 - EXPLORE.

Open a page and report its structure so you (or an agent) can pick selectors
before writing a scraper. Detects repeated "record" containers (the rows you
usually want), tables, and headings, then saves the full HTML + a screenshot.

Usage:
    python -m funnel.explore https://example.com/listings
    python -m funnel.explore https://example.com/listings --headed
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from funnel.browser import browser_context

ART_DIR = Path(__file__).resolve().parent.parent / "artifacts"

# JS that finds groups of sibling elements sharing a class signature — these
# repeated groups are almost always the records worth scraping.
FIND_REPEATS_JS = r"""
() => {
  const groups = {};
  document.querySelectorAll('body *').forEach(el => {
    const parent = el.parentElement;
    if (!parent) return;
    const tag = el.tagName.toLowerCase();
    const cls = (el.getAttribute('class') || '').trim().split(/\s+/).sort().join('.');
    const key = `${parent.tagName.toLowerCase()}>${tag}${cls ? '.' + cls : ''}`;
    (groups[key] = groups[key] || []).push(el);
  });
  return Object.entries(groups)
    .filter(([, els]) => els.length >= 3)
    .map(([key, els]) => {
      const sample = els[0];
      const child = key.split('>')[1];
      const sel = child.replace(/\./g, (m, i) => i === 0 ? ' ' : '.').trim();
      return {
        selector: child.startsWith('.') ? child : child,
        count: els.length,
        sample_text: (sample.innerText || '').trim().slice(0, 120),
      };
    })
    .sort((a, b) => b.count - a.count)
    .slice(0, 15);
}
"""


def explore(url: str, headless: bool = True) -> dict:
    ART_DIR.mkdir(parents=True, exist_ok=True)
    slug = urlparse(url).netloc.replace(":", "_") or "page"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    base = ART_DIR / f"{slug}-{stamp}"

    with browser_context(headless=headless) as page:
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)  # let late content settle

        title = page.title()
        repeats = page.evaluate(FIND_REPEATS_JS)
        table_count = page.locator("table").count()
        headings = page.eval_on_selector_all(
            "h1, h2, h3",
            "els => els.slice(0, 20).map(e => e.innerText.trim()).filter(Boolean)",
        )

        html = page.content()
        base.with_suffix(".html").write_text(html, encoding="utf-8")
        page.screenshot(path=str(base.with_suffix(".png")), full_page=True)

    report = {
        "url": url,
        "title": title,
        "scraped_at": stamp,
        "tables_found": table_count,
        "headings": headings,
        "repeated_record_candidates": repeats,
        "artifacts": {
            "html": str(base.with_suffix(".html")),
            "screenshot": str(base.with_suffix(".png")),
        },
    }
    base.with_suffix(".json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


def _print_report(r: dict) -> None:
    print(f"\n  PAGE: {r['title']}")
    print(f"  URL : {r['url']}")
    print(f"  tables: {r['tables_found']}   headings: {len(r['headings'])}")
    print("\n  Top repeated-record candidates (likely your 'row' selector):")
    for c in r["repeated_record_candidates"]:
        print(f"    [{c['count']:>4}x]  {c['selector']:<30}  e.g. {c['sample_text']!r}")
    print(f"\n  Saved HTML + screenshot + JSON under: {ART_DIR}")
    print("  Next: put the 'row' + field selectors into config/targets.json,")
    print("        then run  python -m funnel.run\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Explore a page's structure.")
    ap.add_argument("url")
    ap.add_argument("--headed", action="store_true", help="show the browser window")
    args = ap.parse_args()
    report = explore(args.url, headless=not args.headed)
    _print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
