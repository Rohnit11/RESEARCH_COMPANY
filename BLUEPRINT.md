# Swiss Beauty Competitive Intelligence — Build Blueprint

**Status:** design locked (this session). **Next:** build in a separate session.
**Golden rule:** production system — real data & defensible outputs only. Where a
figure isn't obtainable, flag it or leave it unbuilt. Never stub/mock/invent. See
`research/deep_research_brief.md` for the estimation-brief method.

---

## 1. Objective
Rank Swiss Beauty vs a 16-brand competitive set in Indian color cosmetics, and
answer two headline questions daily:
- 🏆 **Market Position Leaderboard** — brands ranked by estimated sales & share (of the tracked set).
- 📣 **Share-of-Voice & Momentum Leaderboard** — who owns attention and who's climbing.

Geography: pan-India. Cadence: daily (snapshot + accumulating history for trends).

## 2. Brand set
16 brands defined in `config/brands.json` (Swiss Beauty = target; 15 competitors).
**Extensibility requirement:** adding a brand = appending ONE object to that file
(`name, role, tier, search_term, d2c, instagram`). The whole pipeline iterates the
config; a brand must pass the Verify step (real URLs/handles confirmed) before it
enters scoring.

## 3. Measurement: 4-pillar Competitive Position Scorecard
| Pillar | Measures | Signals |
|--------|----------|---------|
| 1. Market presence | Shelf ownership | SKU counts, category coverage, bestseller-list presence per platform |
| 2. Commercial pull → **sales** | Who's selling now | daily Δreviews/ratings, "bought last month", rank, price |
| 3. Price positioning | Value vs premium | price bands, discount depth, price-per-shade |
| 4. Brand momentum | Mindshare & trajectory | IG engagement, YouTube, Google Trends, X, sentiment |

## 4. Data sources — division of labor (Hybrid posture)
| Source | Method | Confidence |
|--------|--------|-----------|
| Swiss Beauty, Sugar (Shopify) | Playwright → open `/products.json` feed | 🟢 hard |
| Nykaa, Purplle, Myntra, Tira | Playwright scrape (safe timer, listing + top SKUs) | 🟡 |
| Amazon.in, Flipkart | Tavily extract/research + light scrape where reachable; use "bought last month" when visible | 🟡–🔴 |
| Instagram | Tavily/research for follower counts; sampled engagement (flagged) | 🔴 soft |
| YouTube | YouTube Data API (free tier) | 🟢 |
| Google Trends | `pytrends` (free) | 🟢 |
| Financials (ROC) | Tavily research → Tofler/Zaubacorp/TheCompanyCheck | 🟡 |
| Funding / market size / offline / sentiment | Tavily deep-research briefs | 🟡–🔴 flagged |
| Nykaa (listed) financials | Tavily research → investor filings — **calibration anchor** | 🟢 |

Rule: Playwright does the easy/moderate wins; Tavily + free APIs cover blocked or
login-walled sources. Do not pretend to daily-scrape Amazon/IG at volume.

## 5. Sales estimation model (the spine)
Per brand × platform, tracking **top ~50 bestseller SKUs**:

1. **Velocity:** capture cumulative `review_count` per SKU daily → `ΔR = R(t) − R(t−1)` (current sales-rate signal, not lifetime).
2. **Calibrate the review-rate ρ from real data:** where Amazon shows `B` = "bought in past month" and we have ~30-day Δreviews, `ρ = ΔR(30d) / B`. Aggregate ρ across SKUs that expose B → calibrated `ρ̂` (with a low–high range). No blind guessing.
3. **Units/day:** `U_s = ΔR_s / ρ̂`.
4. **GMV/day:** `G_s = U_s × current_price_s`; brand-platform GMV = `Σ G_s`.
5. **Long-tail coverage factor:** scale up for SKUs beyond top-50 using the observed rank/sales distribution (flagged range).
6. **Cross-check / anchor:** `Σ platforms = total online`. ROC annual revenue = all-channel ceiling — if online > ROC total, the model is wrong → flag. `offline ≈ ROC_total − online` (residual), sanity-checked vs Nykaa's disclosed online:offline mix + a research brief. Offline is the **softest** number — always low-confidence flagged.
7. **Market share (of set):** `brand_sales / Σ all 16 brands`.

Every estimate ships: point value + **low–high range** + **confidence H/M/L** +
bold `⚠️ APPROXIMATE`. Insufficient data → labelled "insufficient data", never invented.

## 6. Share of Voice model (engagement-led)
Per platform, compute each brand's share of total set engagement:
- **Instagram:** engagement (likes+comments) weighted above raw followers.
- **YouTube:** views/mentions on brand content (API).
- **Google Trends:** normalized search-interest index across the set.
- **X:** mentions/engagement.

Normalize each platform metric to a brand-share, then **engagement-weighted blend**
→ single SoV score. **Momentum** = day-over-day / week-over-week change in SoV and
pillar scores (accrues as history builds — not available day 1).

## 7. Sentiment (momentum pillar) — blended
Base = avg star-rating + review-text signal (hard, scraped) → enriched with
news/social tone from Tavily/Claude research briefs. Multi-angle, flagged where interpretive.

## 8. Outputs
- **Excel workbook** (openpyxl): ranked tables + bar/line charts per pillar & the two leaderboards; one sheet per view; confidence/flags visible.
- **Interactive HTML dashboard**: self-contained, sortable tables + charts.
- **Time-series store**: append each daily snapshot (brand × platform × signal × date) so trends build from day one.

## 9. Pipeline stages
1. **Explore/Verify** (per brand): confirm D2C, per-marketplace brand pages, social handles; discover selectors. Real-data gate before scoring.
2. **Scrape** (daily): Shopify feeds, marketplace top-50 proxies, social counts, Trends.
3. **Research briefs** (Tavily/Claude): financials, offline, market size, sentiment, gaps — via `deep_research_brief.md`.
4. **Estimate**: run sales + SoV models with calibration & triangulation → ranges + confidence + flags.
5. **Store**: append to time-series.
6. **Dashboards**: build Excel + HTML.

## 10. Phasing
- **Phase 1 (pilot):** Swiss Beauty, Sugar, Nykaa Cosmetics — online sales model + SoV, snapshot; prove the chain end-to-end.
- **Phase 2:** all 16 + offline triangulation + trend lines + full dashboards.

## 11. Anti-block & ethics
Safe randomized timers, realistic browser profile, low volume, respect ToS/robots,
public + non-personal data only. Prefer official APIs/feeds over fragile scraping.

## 12. Locked decisions (this session)
Framework = 4 pillars · Headlines = Market Position + SoV/Momentum · Time = snapshot
+ daily history · Share base = tracked set · Rank = est. sales/GMV · SoV = engagement-led
· Sales spine = velocity + "bought last month" calibration · SKU coverage = top ~50 ·
Offline = triangulate (flagged) · Acquisition = hybrid · Sentiment = blended · Research
tool = Tavily (connected).
