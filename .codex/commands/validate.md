---
name: validate
description: Validate zmanim calculations against reference sources for accuracy
---

# Zmanim Validation

Validate the engine's calculations against known reference sources to ensure halachic accuracy.

## Instructions

Before anything else:
1. Re-read `AGENTS.md` Sections 4-5 (domain model, calculations).
2. Re-read `docs/ZMANIM_TRACKER_MASTER_PLAN.md` Section 8 (cross-phase concerns).

### Step 1: Reference Source Comparison
For each of these test locations and dates, compute zmanim and compare against reference:

**Test cases:**
1. New York (40.7128, -74.0060) — 2024-03-20 (vernal equinox)
2. Jerusalem (31.7683, 35.2137) — 2024-06-21 (summer solstice)
3. Los Angeles (34.0522, -118.2437) — 2024-12-21 (winter solstice)
4. London (51.5074, -0.1278) — 2024-09-22 (autumnal equinox)

**Reference sources:**
- MyZmanim.com
- Chabad.org/calendar
- KosherJava ZmanimCalendar (if available)

### Step 2: Tolerance Check
For each zman, verify the engine output is within acceptable tolerance of the reference:
- Sunrise/sunset: within 1 minute
- Angle-based zmanim (alos, tzais, misheyakir): within 2 minutes
- Time-based zmanim (shema, shacharit, mincha, plag): within 2 minutes
- Candle lighting: within 1 minute (it's a simple subtraction from sunset)
- Chatzot halaila: within 2 minutes

### Step 3: Edge Case Validation
- High latitude (e.g., Helsinki 60.1699, 24.9384) — summer/winter extremes
- Southern hemisphere (e.g., Sydney -33.8688, 151.2093) — reversed seasons
- Friday candle lighting — verify it only appears on Friday
- Saturday havdalah — verify it only appears on Saturday

### Step 4: Report
```
=== ZMANIM VALIDATION REPORT ===

Location: [name] ([lat], [lon])
Date: [YYYY-MM-DD]
Reference: [source]

| Zman | Engine | Reference | Delta | Status |
|------|--------|-----------|-------|--------|
| ... | HH:MM | HH:MM | Xm | PASS/FAIL |

Overall: N/M zmanim within tolerance
Edge cases: PASS/FAIL

VERDICT: VALIDATED / ISSUES FOUND (list specifics)
```