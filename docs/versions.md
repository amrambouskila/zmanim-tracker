# Zmanim Tracker — Version History

## v0.1.0 — Initial Streamlit Prototype

- Single-file implementation (`zmanim_tracker.py`) with all core classes
- Location, SolarPrimitivesUTC, ZmanimRow dataclasses
- SolarAngleSolver wrapping the `astral` library for sunrise/sunset/dawn/dusk
- LocationResolver supporting lat/lon, US ZIP (pgeocode), and free-text (Nominatim)
- ZmanimCalculatorAngleBased computing GRA-based zmanim with configurable depression angles
- ZmanimDataBuilder producing pandas DataFrames
- ZmanimPlotter generating Plotly interactive charts
- Streamlit UI with sidebar inputs, today's zmanim display, data table, chart, CSV export
- Shabbat candle lighting (18 min before sunset) and havdalah (tzais three stars)

## v0.2.0 — Project Infrastructure

- CLAUDE.md with full project conventions and halachic accuracy requirements
- Master plan document with phase roadmap and Mermaid diagrams
- docs/status.md and docs/versions.md
- .claude/ directory with hooks, commands, and skills
- Dockerfile (python:3.13-slim) and docker-compose.yml
- Launcher scripts (run_zmanim_tracker.sh, run_zmanim_tracker.bat)
- pyproject.toml with ruff and pytest configuration
- .gitignore, .gitlab-ci.yml
- README.md with project description and supported zmanim

## v0.2.3

- Container Streamlit port set symmetric to the published host port: the Docker image now serves on `5270` internally (`Dockerfile` `--server.port`/`EXPOSE`) and `docker-compose.yml` maps `${ZT_PORT:-5270}:5270`. Host port and all behavior unchanged. Workspace `PORT_ASSIGNMENTS.md` updated.

### Security hardening
- `sast` job added to `.github/workflows/ci.yml` between `lint` and `test` (`needs: lint`; `test` now `needs: sast`): CodeQL (python), Semgrep (`p/owasp-top-ten`, `p/python`, `p/docker`, SARIF uploaded to Code scanning), gitleaks, `pip-audit`. Trivy (`HIGH,CRITICAL`, exit-code 1) added to `docker-build`.
- **Dependency-audit scope correction.** The `sast` job ran `uvx pip-audit`, which audits pip-audit's own isolated tool environment rather than this project's dependencies -- verified locally: `uvx pip-audit` reports 28 packages, `uv run --with pip-audit pip-audit` reports 77. The job would therefore have passed with a known-vulnerable dependency. Changed to `uv run --with pip-audit pip-audit`.
- ruff `S` (flake8-bandit) rules enabled in `pyproject.toml`; `tests/**` ignores `S101`.
- `LocationResolver.resolve_nominatim`: explicit `timeout=NOMINATIM_TIMEOUT_SECONDS` on the Nominatim `requests.get`.
- `ZmanimDataBuilder.build`: `MAX_RANGE_DAYS = 366` cap; spans at or beyond it raise `ValueError` before iteration.
- New `src/export/neutralize_csv_formulas.py`: prefixes `=`, `+`, `-`, `@`, `\t`, `\r`-leading string cells with `'` before the CSV download (formula-injection defense).
- Tests added for all of the above: 87 passing, 100% coverage.

### Security documentation
- `<security>` section (8a) in `CLAUDE.md`/`AGENTS.md`: SAST stage requirement and tool table, input-boundary inventory with injection classes and defenses, local reproduction commands; Security check added to the completion checklist.
- Master plan: Security section (8.5) and SAST gate lines in every phase completion gate.
- CI provider references corrected from GitLab (`.gitlab-ci.yml`) to GitHub Actions (`.github/workflows/ci.yml`) in `CLAUDE.md`/`AGENTS.md` and `.codex/commands/phase-status.md`.
- `.codex/commands/pre-commit.md`: SAST audit step, security-boundary step, and verdict-table rows; `phase-status.md`: SAST gate lines.