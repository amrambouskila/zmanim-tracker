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

## CI

### Verified state (2026-08-28)

The pipeline had been red since 2026-08-23, failing in `sast` on the dependency audit. Fixed by
regenerating a `uv.lock` that had gone stale since v0.2.0, and by making every job install from that
lock instead of re-resolving `pyproject.toml` ranges on each run. Every job was reproduced locally
against the current tree:

| Job | Command run locally | Result |
|-----|--------------------|--------|
| lint | `uv sync --locked --all-extras && uv run ruff check .` | clean (ruff 0.16.5) |
| sast — Semgrep | CI flags via `semgrep/semgrep` image | 0 findings, exit 0 (186 rules / 52 files) |
| sast — gitleaks | `gitleaks detect --redact` (git mode, 19 commits) | no leaks |
| sast — audit | `uv export --locked … \| uvx pip-audit --strict -r` | no known vulnerabilities |
| test | `uv run pytest --cov-report=xml --junitxml=…` | 89 passed, 100% coverage, JUnit written |
| build | `uv build` | sdist + wheel |
| docker-build | `docker build` + `trivy image --severity HIGH,CRITICAL --exit-code 1` | 0 HIGH/CRITICAL |

CodeQL is the one step that cannot be reproduced locally; its configuration is unchanged apart from
the v3→v4 action bump.

## Security

### Verified state (2026-08-24)

- **Semgrep: clean.** Verified locally by running this repo's own CI command against the working tree (0 findings). The invocation itself was broken before today — `semgrep ci` rejects `--severity`/`--error` and exited 2 without scanning.
- **Container scan: base-image CVEs patched** via an `apt-get upgrade` layer, with the two unremediable pip-vendored findings carried in `.trivyignore` with justification.

- Not run locally: gitleaks and Trivy are not part of any project toolchain here; both were exercised through their official images during verification, and CI runs them on every pipeline.
- Requirements documented in `CLAUDE.md`/`AGENTS.md` section 8a `<security>` (SAST stage, input-boundary inventory, injection defenses) and master plan 8.5; SAST gate lines in every phase gate.
- Wired: `sast` CI job (CodeQL, Semgrep, gitleaks, `pip-audit` over `uv export --locked --all-extras --no-emit-project`, so it audits the locked tree rather than an installed environment — the earlier `uv run --with pip-audit pip-audit` form audited pip-audit's own dependencies alongside the project's and did not prune a stale venv) between `lint` and `test`; Trivy in `docker-build`; ruff `S` rules; Nominatim `timeout=`; `MAX_RANGE_DAYS = 366` date-range cap; CSV formula neutralization (`src/export/neutralize_csv_formulas.py`). 89 tests, 100% coverage.
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