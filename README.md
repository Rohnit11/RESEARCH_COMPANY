# RESEARCH_COMPANY — Market Signal Research Funnel

A polite, Playwright-based scraping funnel for market-data scanning. Three stages:

```
  Stage 1: EXPLORE   →   Stage 2: SCRAPE   →   Stage 3: RUN / COLLECT
  understand a page      extract records        orchestrate on a safe timer
  (agent/human picks     (row + field           (all targets → CSV + JSON)
   selectors)             selectors)
```

Built to run **locally on a randomized safe timer** so you don't get IP-blocked.

## Setup

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Stage 1 — Explore a page's structure

Before scraping a new source, inspect it. This reports the repeated "record"
containers (your `row` selector), tables, and headings, and saves the full
HTML + a full-page screenshot under `artifacts/`.

```bash
python -m funnel.explore "https://example.com/listings"
python -m funnel.explore "https://example.com/listings" --headed   # watch it
```

## Stage 2/3 — Configure targets, then run

Edit `config/targets.json`. Each target needs a `row` selector (the repeated
record) and `fields` mapping output columns to selectors relative to each row:

```json
{
  "name": "my_source",
  "url": "https://example.com/listings",
  "row": "article.product_pod",
  "fields": {
    "title": "h3 a @title",        // "@attr" pulls an attribute
    "price": ".price_color",       // no @attr = innerText
    "link":  "h3 a @href"          // href/src auto-resolve to absolute URLs
  },
  "next_page": "li.next a @href"   // optional pagination
}
```

Then run:

```bash
python -m funnel.run                 # all enabled targets
python -m funnel.run --only my_source
python -m funnel.run --headed
```

Output lands in `data/scan-<timestamp>.csv` and `.json`; logs in `logs/`.

## The "safe timer" (avoiding IP blocks)

Tune these in `config/targets.json` → `defaults`:

| Key             | Meaning                                          | Default |
|-----------------|--------------------------------------------------|---------|
| `min_delay_sec` | min randomized pause between page loads          | 4.0     |
| `max_delay_sec` | max randomized pause                             | 9.0     |
| `max_pages`     | pagination depth per target                      | 3       |
| `headless`      | run without a visible window                     | true    |

Every navigation (and every source-to-source hop) waits a random interval in
`[min, max]`. The browser also uses a realistic UA/viewport and strips the
obvious `navigator.webdriver` automation flag.

## Scheduling continuous scans (Windows)

Run the funnel on a schedule with Task Scheduler:

```powershell
schtasks /create /tn "MarketScan" /tr "python -m funnel.run" ^
  /sc hourly /mo 6 /st 08:00 /rl LIMITED
```

(Set the task's *Start in* directory to this repo folder.)

## Layout

```
config/targets.json   # what to scrape + safe-timer settings
funnel/browser.py     # Chromium launch w/ polite, block-resistant defaults
funnel/explore.py     # Stage 1: understand page structure
funnel/scraper.py     # Stage 2: extract records + safe timer
funnel/run.py         # Stage 3: orchestrate all targets → data/
data/  logs/  artifacts/   # output (gitignored)
```

## Please scrape responsibly

Respect each site's Terms of Service and `robots.txt`, scrape only public
data, keep the delays generous, and don't collect personal data. The safe
timer is there to be a good citizen, not just to avoid blocks.
