# Zmanim Tracker — Current Status

**Phase:** 1 (Streamlit App)
**State:** Prototype complete, infrastructure scaffolding in progress

## What Exists
- Single-file prototype (`zmanim_tracker.py`, ~520 lines) with all classes
- Working Streamlit UI: location input, date range, zmanim table, plotly chart, CSV export
- GRA opinion implemented for all standard zmanim
- Location resolution via lat/lon, US ZIP (pgeocode), free-text (Nominatim)
- Shabbat candle lighting (18 min before sunset) and havdalah (tzais three stars)

## What Was Just Built
- Project infrastructure: CLAUDE.md, docs/, .claude/, Docker files, launcher scripts, CI/CD, pyproject.toml
- All scaffolding files created per the standard project skeleton

## What's Next
1. OOP refactor: split `zmanim_tracker.py` into `src/` module structure (one class per file)
2. Write test suite with reference-validated cases
3. Achieve 100% test coverage
4. Add MGA opinion support
5. Validate zmanim accuracy against MyZmanim.com and Chabad.org for multiple locations/dates

## Recent Decisions
- Using `astral` library for solar calculations (pure Python, handles atmospheric refraction)
- GRA opinion as default; MGA as configurable alternative
- Default depression angles: alos 16.9 deg, nautical 12.0 deg, misheyakir 10.0 deg, tzais 8.5 deg, civil 6.0 deg
- Candle lighting 18 min before sunset (standard minhag, configurable)