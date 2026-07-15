"""Shared Chromium launch helpers with polite, block-resistant defaults.

The goal is to look like an ordinary desktop browser and to never hammer a
host: realistic UA/viewport, a persistent-ish context, and (in scraper.py) a
randomized delay between every navigation.
"""
from __future__ import annotations

import random
from contextlib import contextmanager
from playwright.sync_api import sync_playwright

# A small pool of recent, real desktop UAs. Rotated per session (not per
# request — flipping UA mid-session looks *more* suspicious, not less).
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
]


@contextmanager
def browser_context(headless: bool = True, timeout_ms: int = 30000):
    """Yield a ready-to-use Playwright page inside a context manager.

    Usage:
        with browser_context(headless=True) as page:
            page.goto(url)
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport=random.choice(VIEWPORTS),
            locale="en-US",
            timezone_id="America/New_York",
        )
        context.set_default_timeout(timeout_ms)
        # Strip the most obvious automation tell.
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()
