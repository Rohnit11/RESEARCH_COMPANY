# Deep-Research Brief Template

Use this whenever a hard figure (e.g. "Swiss Beauty FY24 sales on Nykaa") is
**not directly published**. It hands Claude/Tavily a structured estimation task
instead of a vague question, so the output is a *defensible approximate* — never
a hallucinated number. Copy the template, fill every section, run it, and store
the result in `data/estimates/`.

**Golden rule:** every estimated figure ships with (1) a range, (2) a confidence
level, (3) the assumption chain, and (4) a bold `⚠️ APPROXIMATE` flag.

---

## Template (copy below the line)

---

**METRIC:** <exact thing to estimate — e.g. "Swiss Beauty annual GMV on Amazon.in, FY2024, INR">
**BRAND / PLATFORM / PERIOD:** <brand> · <platform> · <time window>

**1. KNOWN (hard data in hand + source + date)**
- e.g. "Total company revenue FY24 = ₹X cr (ROC filing via Tofler, dated ...)"
- e.g. "Amazon.in listing shows 12,400 ratings on hero SKU (scraped <date>)"

**2. UNKNOWN (the exact figure we want, and why it's not public)**
- e.g. "Per-platform sales split is never disclosed by private brands."

**3. AVAILABLE PROXIES / INDICATORS (what we CAN observe that correlates)**
- Marketplace: rating_count, review_count, bestseller_rank, "bought last month", # of SKUs, in-stock %
- Financial: ROC revenue/profit, funding raised, valuation
- Demand: Google Trends index, Instagram followers/engagement, YouTube views

**4. MISSING INDICATORS (would sharpen the estimate but we lack)**
- e.g. "Conversion rate from rating → units sold; average selling price mix."

**5. ESTIMATION METHOD (the triangulation chain, step by step)**
- State the model explicitly. Example (review-ratio method):
  1. Units ≈ rating_count ÷ review_rate (assume ~1–3% of buyers leave a rating)
  2. GMV ≈ Units × avg_selling_price
  3. Cross-check against total ROC revenue × plausible platform share
- Prefer 2+ independent methods and reconcile (triangulation).

**6. ASSUMPTIONS (each explicit, with rationale + confidence H/M/L)**
- A1: review_rate = 2% [rationale: category norm] [confidence: L]
- A2: avg selling price = ₹___ [rationale: scraped catalogue median] [confidence: M]

**7. OUTPUT REQUIRED**
- Point estimate + **range** (low–high) + **confidence** (H/M/L)
- One-line sensitivity: which assumption moves the number most
- Bold `⚠️ APPROXIMATE — modelled, not reported` flag

**8. SOURCES TO CHECK (point Tavily/Claude here first)**
- ROC/financials: Tofler, Zaubacorp, The Company Check
- Funding/revenue news: Inc42, Entrackr, YourStory, ET Retail, Business Standard
- Marketplace proxies: the platform listings themselves (scraped)
- Public comps: Nykaa investor filings (listed — use as a calibration anchor)

---

## Worked mini-example

**METRIC:** Sugar Cosmetics FY24 GMV on Nykaa, INR
**KNOWN:** Company FY24 revenue ≈ ₹420 cr (news/ROC); Nykaa hero SKUs show ~8k–25k ratings each.
**METHOD:** (units from rating-ratio) × (avg price ₹450) → platform GMV; cross-check vs. "beauty specialist ≈ 30–40% of a masstige brand's online mix."
**OUTPUT:** ₹___–₹___ cr · confidence **L–M** · ⚠️ APPROXIMATE. Most sensitive to review_rate assumption.

> Nykaa is a *listed* company — always use its disclosed numbers as the
> calibration anchor when modelling the private brands around it.
