"""Stage 3 - RUN (orchestrator).

Reads config/targets.json, scrapes every enabled target on a safe timer, and
writes timestamped CSV + JSON into data/. Meant to be run on a schedule
(Windows Task Scheduler / cron) for continuous market-signal scanning.

Usage:
    python -m funnel.run                 # all enabled targets
    python -m funnel.run --only demo_books
    python -m funnel.run --headed
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from funnel.browser import browser_context
from funnel.scraper import safe_sleep, scrape_target

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "targets.json"
DATA_DIR = ROOT / "data"
LOG_DIR = ROOT / "logs"


def _setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(name)s  %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_DIR / "funnel.log", encoding="utf-8"),
        ],
    )


def _write_output(rows: list[dict], stamp: str) -> tuple[Path, Path]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DATA_DIR / f"scan-{stamp}.json"
    csv_path = DATA_DIR / f"scan-{stamp}.csv"

    json_path.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if rows:
        # Union of keys preserves every field across heterogeneous sources.
        cols: list[str] = []
        for r in rows:
            for k in r:
                if k not in cols:
                    cols.append(k)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    return json_path, csv_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the market-scan funnel.")
    ap.add_argument("--only", help="run just this target name")
    ap.add_argument("--headed", action="store_true", help="show the browser window")
    args = ap.parse_args()

    _setup_logging()
    log = logging.getLogger("funnel.run")

    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    defaults = cfg.get("defaults", {})
    targets = [
        t for t in cfg.get("targets", [])
        if t.get("enabled", True) and (not args.only or t["name"] == args.only)
    ]
    if not targets:
        log.error("No enabled targets matched. Check config/targets.json.")
        return 1

    headless = defaults.get("headless", True) and not args.headed
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    all_rows: list[dict] = []

    with browser_context(headless=headless,
                         timeout_ms=int(defaults.get("timeout_ms", 30000))) as page:
        for i, target in enumerate(targets):
            log.info("=== target %d/%d: %s ===", i + 1, len(targets), target["name"])
            try:
                rows = scrape_target(page, target, defaults)
                all_rows.extend(rows)
                log.info("[%s] collected %d records", target["name"], len(rows))
            except Exception:  # keep going even if one source breaks
                log.exception("[%s] FAILED — skipping", target["name"])

            # Safe pause between distinct sources too.
            if i < len(targets) - 1:
                safe_sleep(
                    float(defaults.get("min_delay_sec", 4.0)),
                    float(defaults.get("max_delay_sec", 9.0)),
                )

    json_path, csv_path = _write_output(all_rows, stamp)
    log.info("DONE. %d total records", len(all_rows))
    log.info("  JSON -> %s", json_path)
    log.info("  CSV  -> %s", csv_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
