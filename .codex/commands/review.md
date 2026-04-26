---
name: review
description: Review changed code against Zmanim Tracker standards and halachic accuracy requirements
---

# Code Review

Deep review of changes against Zmanim Tracker standards.

## Instructions

Before anything else:
1. Re-read `AGENTS.md` fully (especially Sections 3-5 on architecture, domain model, and calculations).
2. Run `git diff` to see all changes.
3. Read every changed file in full.

### For Calculation/Engine Changes
1. **Halachic accuracy**: Are formulas correct per the documented opinion (GRA/MGA)?
2. **Depression angles**: Do they come from config, not magic numbers?
3. **Shaah zmanis**: Correct formula for the opinion being used?
4. **Time-based zmanim**: Correct number of shaos from sunrise?
5. **Shabbat logic**: Friday candle lighting and Saturday havdalah handled correctly?
6. **Timezone**: All datetimes timezone-aware via ZoneInfo?
7. **Reference validation**: Has the change been validated against MyZmanim.com or Chabad.org?

### For All Changes
1. **Type annotations**: Full annotations on every function signature?
2. **`from __future__ import annotations`**: Present in every module?
3. **OOP rule**: One class per file?
4. **No dead code**: No commented-out blocks, unused imports, unused functions?
5. **No magic numbers**: All constants named or from config?
6. **No `Any`**: No type escape hatches?
7. **Tests**: Matching test file exists with reference-validated cases?
8. **Docs**: `status.md` and `versions.md` updated?

### Report Format
```
=== REVIEW REPORT ===

CRITICAL (must fix):
- [file:line] Issue description

SHOULD-FIX:
- [file:line] Issue description

MINOR:
- [file:line] Issue description

POSITIVE PATTERNS:
- What was done well

VERDICT: APPROVED / CHANGES REQUESTED
```