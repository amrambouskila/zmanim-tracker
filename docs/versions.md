# Zmanim Tracker — Version History

## v0.2.3 — 2026-08-24 (unreleased)

### CI pipeline restored to green end-to-end (2026-08-28)

The `sast` job had been failing on its "Dependency audit" step: `pip-audit` reported 46 advisories
across 5 packages (`gitpython` 3.1.47, `idna` 3.13, `pillow` 12.2.0, `tornado` 6.5.5, `urllib3` 2.6.3).

- **Root cause: a stale `uv.lock`.** The lockfile had not been regenerated since v0.2.0 and pinned
  every one of those versions. `uv lock --upgrade` resolves them all: `idna` → 3.19, `pillow` → 12.3.0,
  `urllib3` → 2.7.0, and `streamlit` 1.56.0 → 1.62.0, which drops `gitpython` and `tornado` from the
  tree entirely (it moved to `starlette`/`uvicorn`). Also bumped: `pandas` 3.0.5, `plotly` 7.0.0,
  `numpy` 2.5.2, `pyarrow` 25.0.1, `ruff` 0.16.5, `pytest` 9.1.1, `timezonefinder` 8.3.0.
  Verified on the upgraded set: `ruff check` clean, 89 tests passing at 100% coverage, `uv build` clean.
- **Dependency-audit scope corrected again.** `uv run --with pip-audit pip-audit` audits the *installed
  environment*, which means (a) pip-audit's own dependency tree is audited alongside the project's,
  (b) `uv run` silently re-locks on drift rather than failing, and (c) `uv run` does not prune
  extraneous packages, so a stale venv is audited as if it were the lock. Measured locally: with the
  refreshed lock in place, that command still reported `gitpython`/`tornado` because both were left
  behind in `.venv`. Replaced with `uv export --locked --all-extras --no-emit-project --no-hashes`
  into `uvx pip-audit --strict -r`, which audits exactly the locked tree. `--locked` turns lock drift
  into a pipeline failure (verified: exit 2 on an edited `pyproject.toml`); `--no-emit-project` removes
  the unauditable `zmanim-tracker` self-reference, which lets `--strict` gate on skipped packages.
- **Every job now installs from the lockfile.** `lint`, `test` and `build` used
  `uv pip install --system -r pyproject.toml`, resolving the dependency ranges fresh on each run —
  so CI tested one set of versions while the audit gated a different one, and an upstream release
  could turn the pipeline red with no commit. All three now use `uv sync --locked --all-extras`.
  This is what `CLAUDE.md` 8a already required ("never bypass the lockfile in CI or the Dockerfile").
- **Dockerfile installs from the lockfile** via `uv export --locked` rather than `-r pyproject.toml`,
  for the same reason: the image previously shipped whatever resolved at build time, which is not
  the set `pip-audit` gates.
- **The Semgrep gate ignores `nosemgrep`-suppressed results.** Semgrep 1.175 records inline-suppressed
  findings in its SARIF output with `"suppressions": [{"kind": "inSource"}]` while omitting them from
  its console count — so the Dockerfile's justified `missing-user` suppression appeared as a SARIF
  result and failed the gate, even though the scan reported `Findings: 0 (0 blocking)`. The gate now
  counts only results with an empty `suppressions` array, and reports the suppressed count separately.
  (Semgrep 1.174, which the `semgrep/semgrep` container ships, drops them from SARIF entirely — the
  version skew between that image and the `uvx semgrep` the pipeline runs is why local verification
  passed while CI failed. Verified against a clean clone at the CI commit using `uvx`.)
- **Semgrep no longer conflates a crash with a finding.** `--error` plus
  `|| echo "SEMGREP_FAILED=1" >> $GITHUB_ENV` mapped *any* nonzero exit — network failure, bad
  ruleset, registry outage — onto "security finding", and if Semgrep died before writing the SARIF
  the following `upload-sarif` step failed on a missing file. `--error` is dropped so a crash fails
  its own step, findings are counted out of the SARIF, and the upload is guarded by `hashFiles`.
  Verified: `semgrep scan` with the CI flags returns 0 findings, exit 0 (186 rules, 52 files).
- **Trivy's ignore file is now passed explicitly** (`trivyignores: .trivyignore`). Measured: without
  it the scan exits 1 on the two documented pip-vendored findings. The job had never actually proven
  the default lookup, because no run has reached `docker-build` since `.trivyignore` was added.
- **`dorny/test-reporter` is skipped on forked-PR runs**, where the read-only token makes its check-run
  creation fail and take the `test` job down with it.
- **`aquasecurity/trivy-action@0.28.0` was an unresolvable ref**, so `docker-build` would have died at
  "Set up job" — with the misleading message `unable to find version 0.28.0` — the moment the pipeline
  got past `sast`. That repository publishes `v`-prefixed tags only (`git ls-remote … refs/tags/0.28.0`
  is empty; the sole bare tag in its entire history is `0.35.0`), and the bare form was copied from an
  old README. Never caught because no run has reached `docker-build` since the Trivy step was added on
  2026-08-23. Now `@v0.36.0`.
- **Actions moved off the Node 20 runtime**, which the runner now force-migrates and warns on every
  run: `checkout` v4→v7, `setup-python` v5→v7, `upload-artifact` v4→v7, `codeql-action` v3→v4
  (v3 is EOL December 2026), `gitleaks-action` v2→v3, `test-reporter` v1→v3, `setup-buildx-action`
  v3→v4, `build-push-action` v6→v7. Each of those majors is a runtime bump with no change to the
  inputs used here. `astral-sh/setup-uv@v10.0.1` replaces `pip install uv` for a pinned, cached uv —
  pinned to the exact tag because that project stops publishing moving major tags at `v7`, so `@v10`
  does not resolve even though `v10.0.1` is the current release.
- **Every `uses:` ref in both workflows is now checked with `git ls-remote`** rather than inferred from
  `releases/latest`. The two bugs above are the same mistake — a release *name* is not necessarily a
  usable *ref*.

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