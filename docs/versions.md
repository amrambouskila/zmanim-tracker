# Zmanim Tracker — Version History

## v0.2.3 — 2026-08-24 (unreleased)

### CI hardening + dependency remediation (2026-08-24)

- **Semgrep invocation corrected.** The job used `semgrep ci` with `--severity` and `--error`, which that subcommand does not accept — it exits 2 with a usage error before scanning. Switched to `semgrep scan`, which supports both.
- **Release workflow hardened against script injection.** `${{ inputs.bump }}` and `${{ steps.bump.outputs.new_version }}` were interpolated directly into `run:` blocks, where the value becomes shell code. Both now pass through `env:` and are read as quoted shell variables. The input is `type: choice`, so this was not exploitable today — it is the pattern that breaks the moment the input type changes.
- **Base-image security patches in the Dockerfile.** The Debian slim bases ship a `util-linux` that Trivy flags HIGH (CVE-2026-53612..53615, fixed upstream in 2.41.5). Measured directly: `python:3.13-slim` carries 38 fixable HIGH/CRITICAL, `3.12-slim` 36, `3.11-slim` 38, while `nginx:alpine` is clean. These come from the base layer, so an `apt-get upgrade` step is required even where nothing else installs them.
- **`.trivyignore` added** for two findings with no in-image remediation: `CVE-2025-47273` (setuptools 70.3.0) and `GHSA-6v7p-g79w-8964` (msgpack 1.1.2). Both come from pip's vendored manifest in the base image, not from project dependencies — and setuptools 70.3.0 is not even installed (`find` finds nothing; the image ships 84.x). Upgrading pip does not rewrite that manifest. Each entry carries its justification inline.
- **Dockerfile `missing-user` suppressed with written justification**, per global CLAUDE.md section 9 (non-root is not required for personal local-dev containers). The nginx images additionally cannot run as non-root without the unprivileged image and a port change. Revisit before any deployment beyond localhost.
- **Nominatim SSRF and response-size hardening.** `resolve_nominatim` now passes `allow_redirects=False` (the URL is a module constant, so a redirect can only move the request off-host; a non-200 raises instead of being followed) and streams the body with a `NOMINATIM_MAX_RESPONSE_BYTES` (1 MB) cap enforced before `json.loads`. The `<security>` boundary table had claimed redirect rejection that no code implemented. Two tests cover both defenses; the suite stays at 89 tests / 100% coverage.

---

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