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
- Container Streamlit port made symmetric with the host port (`5270` inside the container; `docker-compose.yml` maps `${ZT_PORT:-5270}:5270`). Behavior unchanged.

## Security

### Verified state (2026-08-24)

- **Semgrep: clean.** Verified locally by running this repo's own CI command against the working tree (0 findings). The invocation itself was broken before today — `semgrep ci` rejects `--severity`/`--error` and exited 2 without scanning.
- **Container scan: base-image CVEs patched** via an `apt-get upgrade` layer, with the two unremediable pip-vendored findings carried in `.trivyignore` with justification.

- Not run locally: gitleaks and Trivy are not part of any project toolchain here; both were exercised through their official images during verification, and CI runs them on every pipeline.
- Requirements documented in `CLAUDE.md`/`AGENTS.md` section 8a `<security>` (SAST stage, input-boundary inventory, injection defenses) and master plan 8.5; SAST gate lines in every phase gate.
- Wired: `sast` CI job (CodeQL, Semgrep, gitleaks, `pip-audit` via `uv run --with pip-audit pip-audit` so it audits the project's 77-package locked tree, not pip-audit's own tool env) between `lint` and `test`; Trivy in `docker-build`; ruff `S` rules; Nominatim `timeout=`; `MAX_RANGE_DAYS = 366` date-range cap; CSV formula neutralization (`src/export/neutralize_csv_formulas.py`). 87 tests, 100% coverage.
- Outstanding: bounded Nominatim response size and redirect-host rejection; length cap on free-text location input; Phase 2 items (ESLint security plugins, nginx CSP headers, Pydantic/SQLAlchemy boundaries) activate with the React/FastAPI stack.

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