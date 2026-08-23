# CLAUDE.md - Zmanim Tracker

---

<mandatory_workflow>

> **MANDATORY WORKFLOW: READ THIS ENTIRE FILE BEFORE EVERY CHANGE.** Every time. No skimming, no assuming prior-session context carries over — it does not.
>
> **Why:** This project spans multiple sessions and months of development. Skipping the re-read produces decisions that contradict the architecture, duplicate existing patterns, break data contracts, or introduce tech debt that compounds.
>
> **The workflow, every time:**
> 1. Read this entire file in full.
> 2. Read the master plan document: `docs/ZMANIM_TRACKER_MASTER_PLAN.md`.
> 3. Read `docs/status.md` — current state / what was just built.
> 4. Read `docs/versions.md` — recent version history.
> 5. Read the source files you plan to modify — understand existing patterns first.
> 6. Then implement, following the rules and contracts defined here.

</mandatory_workflow>

---

<critical_context>

## 0. Critical Context

**This is a halachic tool.** Zmanim accuracy matters for actual religious observance — people rely on these times for davening, Shabbat candle lighting, and havdalah. Incorrect calculations are not just bugs; they can cause someone to miss a zman or violate Shabbat. Treat every time computation with the rigor of safety-critical software.

**What this project is:** A Jewish prayer times calculator and tracker that computes halachic zmanim for any location using solar angle calculations. It resolves locations via lat/lon, US ZIP codes, and free-text geocoding, then applies the astronomical primitives to derive all standard zmanim according to accepted shitot (halachic opinions).

**What this project is NOT:**
- Not a calendar app (no yom tov scheduling — Phase 3)
- Not a notification service (Phase 3)
- Not a multi-user web app (Phase 2 adds FastAPI backend)

**Current phase:** Phase 1 — Streamlit single-user app. The prototype exists as a single file (`zmanim_tracker.py`). The immediate priority is OOP refactoring into proper module structure, containerization, and test coverage.

</critical_context>

---

<project_identity>

## 1. Project Identity

- **Project:** `zmanim-tracker` — halachic prayer times calculator
- **Location:** `zmanim-tracker/`
- **Master plan:** `docs/ZMANIM_TRACKER_MASTER_PLAN.md`
- **Stack:** Python 3.13+, Streamlit, astral, pandas, plotly, requests, pgeocode, timezonefinder, zoneinfo
- **Package manager:** uv
- **Testing:** pytest + pytest-cov (100% coverage target)
- **Lint:** ruff (line-length 120, rules E, F, I, N, UP, ANN, S)
- **Containerization:** Docker (python:3.13-slim)

</project_identity>

---

<phase_constraints>

## 2. Phase Constraints

### Phase 1 — Streamlit App (current)
- Single-user Streamlit frontend
- All computation local (astral library for solar angles)
- Location resolution via lat/lon, ZIP (pgeocode), free-text (Nominatim)
- Export to CSV
- Plotly visualization of zmanim over date ranges
- Docker containerized
- **Do NOT** add FastAPI endpoints — Phase 2
- **Do NOT** add user accounts or authentication — Phase 2
- **Do NOT** add Hebrew calendar integration — Phase 2
- **Do NOT** add push notifications or calendar sync — Phase 3

### Phase 2 — FastAPI + React Frontend
- FastAPI backend serving zmanim via REST API
- React frontend replacing Streamlit
- Hebrew calendar integration (jewish-calendar or hdate library)
- Yom tov and special day zmanim
- Saved locations per user
- SQLAlchemy + PostgreSQL for user preferences and saved locations

### Phase 3 — Notifications & Calendar
- Push notifications for upcoming zmanim
- Google Calendar / Apple Calendar integration
- Shabbat schedule PDF generation
- Multi-location comparison

</phase_constraints>

---

<architecture>

## 3. Architecture & Code Rules

### OOP File Isolation (mandatory)
Every class, dataclass, and standalone utility function lives in its own file. The current single-file structure (`zmanim_tracker.py`) **must be refactored** into the target directory structure below.

### Type Annotations
- `from __future__ import annotations` at the top of every module
- Full type annotations on every function signature
- No `Any` unless explicitly approved
- ruff `ANN` rules enforce this

### Code Standards
- No dead code, no commented-out blocks
- No magic numbers — solar angle constants go in a config dataclass or constants module
- No `# TODO` without a linked task
- Domain-standard variable names: `lat`, `lon`, `tz`, `dt` are acceptable
- Document units on every physical quantity (degrees, minutes, radians)

### Error Handling
- Validate at boundaries: user input (location strings, date ranges), external API responses (Nominatim, pgeocode)
- Trust types internally — do not defensively validate between engine methods
- No bare `except:` — always catch specific exception types
- Nominatim rate limiting: enforce a minimum delay between requests (currently 0.8s)

</architecture>

---

<data_contracts>

## 4. Domain Model & Data Contracts

### Location
```python
@dataclass(frozen=True)
class Location:
    label: str          # Human-readable name (e.g., "New York, NY" or "40.7128, -74.0060")
    latitude: float     # Decimal degrees, -90 to 90
    longitude: float    # Decimal degrees, -180 to 180
    timezone: str       # IANA timezone string (e.g., "America/New_York")
```

### SolarPrimitivesUTC
```python
@dataclass(frozen=True)
class SolarPrimitivesUTC:
    sunrise: datetime       # UTC
    sunset: datetime        # UTC
    solar_noon: datetime    # UTC
    civil_twilight_begin: datetime       # Sun at -6 degrees, UTC
    civil_twilight_end: datetime         # Sun at -6 degrees, UTC
    nautical_twilight_begin: datetime    # Sun at -12 degrees, UTC
    nautical_twilight_end: datetime      # Sun at -12 degrees, UTC
    astronomical_twilight_begin: datetime # Sun at -18 degrees, UTC
    astronomical_twilight_end: datetime   # Sun at -18 degrees, UTC
```

### ZmanimRow
```python
@dataclass(frozen=True)
class ZmanimRow:
    day: date
    location_label: str
    timezone: str

    # Solar primitives (local time)
    sunrise: datetime
    sunset: datetime
    solar_noon: datetime
    chatzos: datetime           # = solar_noon
    shaah_zmanis: timedelta     # (sunset - sunrise) / 12

    # Dawn / dusk angle-based
    alos_astronomical_edge: datetime   # Dawn at configured depression (default 16.9 deg)
    alos_nautical_edge: datetime       # Dawn at 12 deg
    misheyakir: datetime               # Dawn at 10 deg (earliest tallit/tefillin)
    tzais_three_stars: datetime        # Dusk at 8.5 deg
    tzais_civil_end: datetime          # Dusk at 6 deg

    # Time-based zmanim (GRA opinion)
    latest_shema: datetime      # sunrise + 3 * shaah_zmanis
    latest_shacharit: datetime  # sunrise + 4 * shaah_zmanis

    # Mincha
    earliest_mincha: datetime   # Mincha Gedolah: sunrise + 6.5 * shaah_zmanis
    mincha_ketana: datetime     # sunrise + 9.5 * shaah_zmanis
    plag_hamincha: datetime     # sunrise + 10.75 * shaah_zmanis

    # Night
    chatzot_halaila: datetime   # Midpoint between sunset and next sunrise

    # Shabbat (None on non-Shabbat days)
    candle_lighting: datetime | None    # Friday: sunset - 18 min
    shabbat_ends: datetime | None       # Saturday: tzais_three_stars (+ optional offset)
```

### ZmanimCalculatorAngleBased
The main computation engine. Configurable via constructor parameters:

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `alos_astronomical_edge_deg` | 16.9 | Depression angle for earliest alos |
| `alos_nautical_edge_deg` | 12.0 | Depression angle for nautical alos |
| `misheyakir_deg` | 10.0 | Depression angle for misheyakir (earliest tallit/tefillin) |
| `tzais_three_stars_deg` | 8.5 | Depression angle for three-star nightfall |
| `tzais_civil_end_deg` | 6.0 | Depression angle for civil twilight end |
| `candle_lighting_offset_min` | 18 | Minutes before sunset for candle lighting |
| `shabbat_end_offset_min` | 0 | Additional minutes after tzais for Shabbat end |
| `shabbat_end_basis` | `"tzais_three_stars"` | Which dusk time to use as havdalah base |

</data_contracts>

---

<domain_model>

## 5. Required Calculations & Halachic Notes

### Shaah Zmanis (Proportional Hour)
**GRA opinion (default):** `shaah_zmanis = (sunset - sunrise) / 12`

The proportional hour divides the daylight period into 12 equal parts. All time-based zmanim (shema, shacharit, mincha, plag) are expressed in terms of shaos zmanios from sunrise.

**MGA opinion (future):** `shaah_zmanis_mga = (sunset_72 - sunrise_72) / 12` where sunrise_72 = sunrise - 72 min, sunset_72 = sunset + 72 min. This uses a longer "day" that includes 72 minutes before sunrise and after sunset. Phase 2 will add MGA as an alternative.

### Time-Based Zmanim (GRA)
| Zman | Formula | Halachic Basis |
|------|---------|----------------|
| Latest Shema | `sunrise + 3 * shaah_zmanis` | End of 3rd hour of the day |
| Latest Shacharit | `sunrise + 4 * shaah_zmanis` | End of 4th hour |
| Chatzos | `solar_noon` (= `sunrise + 6 * shaah_zmanis`) | Midday |
| Mincha Gedolah | `sunrise + 6.5 * shaah_zmanis` | Half hour after chatzos |
| Mincha Ketana | `sunrise + 9.5 * shaah_zmanis` | 9.5 hours into the day |
| Plag HaMincha | `sunrise + 10.75 * shaah_zmanis` | 1.25 hours before sunset |

### Angle-Based Zmanim
These use the sun's depression angle below the horizon:

| Zman | Depression | Meaning |
|------|-----------|---------|
| Alos (astronomical) | 16.9 deg | Earliest alos hashachar |
| Alos (nautical) | 12.0 deg | Standard alos |
| Misheyakir | 10.0 deg | Earliest time for tallit and tefillin |
| Tzais (three stars) | 8.5 deg | Nightfall — three medium stars visible |
| Tzais (civil) | 6.0 deg | Civil twilight end |

### Shabbat Times
- **Candle lighting:** `sunset - 18 minutes` (Friday). 18 minutes is the standard minhag; Jerusalem uses 40 minutes. The offset is configurable.
- **Havdalah:** `tzais_three_stars + shabbat_end_offset_min` (Saturday). Some communities use 72 minutes after sunset (Rabbeinu Tam) instead of the angle-based three stars — this is a future enhancement.

### Chatzot HaLaila (Halachic Midnight)
`chatzot_halaila = sunset + (next_sunrise - sunset) / 2`

This is the midpoint of the night, computed as halfway between sunset and the following morning's sunrise.

### Validation Reference
All zmanim should be validated against known sources:
- **MyZmanim.com** — well-established online zmanim calculator
- **Chabad.org zmanim** — widely trusted
- **KosherJava ZmanimCalendar** — open-source Java reference implementation
- For a specific validation: New York (40.7128, -74.0060) on 2024-03-20 (vernal equinox) — sunrise ~7:02 EDT, sunset ~7:13 EDT, shaah zmanis ~60.9 min

</domain_model>

---

<file_structure>

## 6. Target Directory Structure (Post-Refactor)

```
zmanim-tracker/
├── CLAUDE.md                           # This file
├── README.md                           # Human-facing project description
├── docs/
│   ├── ZMANIM_TRACKER_MASTER_PLAN.md   # Master plan: goals, phases, architecture
│   ├── status.md                       # Current project state
│   └── versions.md                     # Semver changelog
├── .claude/
│   ├── settings.json                   # Hooks and permissions
│   ├── commands/                       # Slash commands
│   │   ├── scaffold.md
│   │   ├── review.md
│   │   ├── pre-commit.md
│   │   ├── validate.md
│   │   └── phase-status.md
│   └── skills/                         # Proactive protocol skills
│       ├── phase-awareness/SKILL.md
│       ├── data-driven-check/SKILL.md
│       └── validation-protocol/SKILL.md
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── location.py                 # Location dataclass
│   │   ├── solar_primitives_utc.py     # SolarPrimitivesUTC dataclass
│   │   └── zmanim_row.py              # ZmanimRow dataclass
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── solar_angle_solver.py       # SolarAngleSolver (wraps astral)
│   │   ├── zmanim_calculator.py        # ZmanimCalculatorAngleBased
│   │   └── zmanim_data_builder.py      # ZmanimDataBuilder (DataFrame output)
│   ├── location/
│   │   ├── __init__.py
│   │   └── location_resolver.py        # LocationResolver (lat/lon, ZIP, Nominatim)
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── zmanim_plotter.py           # ZmanimPlotter (Plotly charts)
│   └── app.py                          # Streamlit UI (ZmanimApp class)
├── tests/
│   ├── __init__.py
│   ├── test_location.py                # Location dataclass tests
│   ├── test_solar_angle_solver.py      # SolarAngleSolver tests
│   ├── test_zmanim_calculator.py       # ZmanimCalculatorAngleBased tests
│   ├── test_zmanim_data_builder.py     # ZmanimDataBuilder tests
│   ├── test_location_resolver.py       # LocationResolver tests
│   └── test_zmanim_plotter.py          # ZmanimPlotter tests
├── pyproject.toml                      # Project metadata, ruff, pytest config
├── Dockerfile                          # python:3.13-slim + Streamlit
├── docker-compose.yml                  # Single service, env var ports
├── .dockerignore                       # Docker build exclusions
├── run_zmanim_tracker.sh               # macOS/Linux launcher
├── run_zmanim_tracker.bat              # Windows launcher
├── .gitignore                          # Python + Docker + Claude + IDE
├── .github/
│   └── workflows/
│       ├── ci.yml                      # CI pipeline (lint, sast, test, build, docker-build)
│       └── release.yml                 # Manual release / version-bump pipeline
└── .env                                # Local env vars (gitignored)
```

**Note:** The current `zmanim_tracker.py` in the root is the Phase 1 prototype. It will be refactored into the `src/` structure above. Until refactoring is complete, both may coexist.

</file_structure>

---

<containerization>

## 7. Containerization

### Dockerfile
- Base: `python:3.13-slim` (NOT Alpine — musl breaks scientific Python wheels)
- Install deps from `pyproject.toml` via uv
- Copy source
- Expose port 5270 (container port set symmetric to the host port)
- CMD: `["streamlit", "run", "src/app.py", "--server.port=5270", "--server.address=0.0.0.0", "--server.headless=true"]`

### docker-compose.yml
- Single service: `zmanim-tracker`
- Port: `${ZT_PORT:-5270}:5270`
- Bind mount `./src` for dev hot-reload
- `restart: unless-stopped`

### Launcher Scripts
`run_zmanim_tracker.sh` and `run_zmanim_tracker.bat` implement the standard `[k]/[q]/[v]/[r]` shutdown/restart loop per the global CLAUDE.md launcher contract.

</containerization>

---

<ci_cd>

## 8. CI/CD Pipeline (GitHub Actions — `.github/workflows/ci.yml`)

**Stages (in order):**
1. **lint** — `ruff check .` — fail on any error (includes ruff `S` security rules)
2. **sast** — Semgrep + CodeQL + `pip-audit` + gitleaks — fail on any HIGH/CRITICAL finding (see section 8a)
3. **test** — `pytest --cov=src --cov-report=term-missing` — fail on any test failure
4. **coverage** — gated at 100% (enforced in pytest config)
5. **build** — `uv build` — must succeed
6. **docker-build** — `docker build .` — verify container builds; Trivy scan of the image, fail on HIGH/CRITICAL

All PRs must pass CI before merging.

</ci_cd>

---

<security>

## 8a. Security — SAST Scanning & Injection Safety (Non-Negotiable)

Per global section 19 `<security>`. Security is part of the Definition of Done for every task, not a later phase.

### SAST scanning
The CI pipeline (`.github/workflows/ci.yml`, GitHub Actions — this project is public) **MUST** have a `sast` job between `lint` and `test` (`needs: lint`; `test` gains `needs: sast`) that **fails on any HIGH/CRITICAL finding**. MEDIUM findings are triaged: fixed, or suppressed inline with a written justification. `continue-on-error: true` on any security job is non-compliant. The `sast` job is wired (CodeQL, Semgrep with SARIF upload, gitleaks, `pip-audit`) and Trivy runs in `docker-build`.

Tool set for this repo (Python-only in Phase 1; the TypeScript rows activate when the Phase 2 React frontend is created):

| Layer | Tool | Where |
|-------|------|-------|
| Lint-time security rules | ruff `S` family (flake8-bandit) — `select = ["E", "F", "I", "N", "UP", "ANN", "S"]` in `pyproject.toml`; `tests/**` additionally ignores `S101` | `lint` |
| Primary SAST | Semgrep (`semgrep scan`, rulesets `p/default`, `p/owasp-top-ten`, `p/python`, `p/docker`; `p/typescript` + `p/react` from Phase 2) uploading SARIF via `github/codeql-action/upload-sarif` | `sast` |
| SAST (GitHub-native) | `github/codeql-action` init → analyze, language `python` (+ `javascript-typescript` from Phase 2) | `sast` |
| Dependency audit | `uv run pip-audit` (Phase 2 frontend: `pnpm audit --audit-level=high`) | `sast` |
| Secret scanning | `gitleaks/gitleaks-action` (`gitleaks detect --no-git --redact` locally) | `sast` |
| Container scanning | `aquasecurity/trivy-action`, `--severity HIGH,CRITICAL --exit-code 1` against the freshly built image | `docker-build` |
| Frontend lint (Phase 2) | `eslint-plugin-security` + `eslint-plugin-no-unsanitized` | `lint` |

Jobs that upload SARIF need `security-events: write`. Findings render under Security → Code scanning.

**Local reproduction** (same set the pipeline runs; `/pre-commit` runs it and reports in its verdict table):
```bash
uv run ruff check .
semgrep scan --config auto --error
uv run pip-audit
gitleaks detect --no-git --redact
docker build -t zmanim-tracker . && trivy image --severity HIGH,CRITICAL --exit-code 1 zmanim-tracker
```

### Injection safety — input boundary inventory
Every boundary below treats its input as hostile until it has crossed typed validation. All paths verified against `src/` at the time of writing.

| Boundary | Where | Injection classes | Required defense |
|----------|-------|-------------------|------------------|
| Free-text location input | `src/app.py` `st.text_input` → `LocationResolver.resolve` (`src/location/location_resolver.py`) | Header/log injection, resource exhaustion, SSRF (query is forwarded to a third party) | Input is matched against anchored regexes (`latitude_longitude_regex`, `zipcode_regex`) before any parsing; lat/lon range-checked (`-90..90`, `-180..180`) and rejected with `ValueError`. Free text reaches Nominatim only as a URL-encoded `params={"q": ...}` value via `requests` — never string-concatenated into the URL; the host is the constant `NOMINATIM_URL`, never derived from input. Never echo raw input into log lines or headers without stripping `\r\n`. Cap input length before dispatch. |
| Date range inputs | `src/app.py` `st.date_input` → `ZmanimDataBuilder.build` | Resource exhaustion | Builder validates `end >= start` and rejects spans of `MAX_RANGE_DAYS` (366) or more with `ValueError` before iterating, so a hostile range cannot pin the process. |
| Nominatim HTTP response | `LocationResolver.resolve_nominatim` (`requests.get`, `resp.json()`) | Unsafe deserialization, SSRF via redirects, resource exhaustion, header injection (`display_name` becomes `Location.label`) | `resp.json()` only (never `pickle`/`eval`); `lat`/`lon` cast with `float()` and range-validated before building `Location`; `display_name` treated as untrusted text — rendered only through Streamlit's escaped widgets (`st.write`, `st.dataframe`, `st.metric`), never `unsafe_allow_html=True`; the call passes `timeout=NOMINATIM_TIMEOUT_SECONDS`, `allow_redirects=False` (the URL is a constant, so a redirect can only point off-host — a non-200 raises rather than being followed), and streams the body with a `NOMINATIM_MAX_RESPONSE_BYTES` (1 MB) cap enforced before `json.loads`. Both are covered by tests in `tests/test_location_resolver.py`. Throttle (`NOMINATIM_THROTTLE_SECONDS`) stays. |
| pgeocode ZIP lookup | `LocationResolver.resolve_zip` | Path traversal (pgeocode downloads/caches a GeoNames dataset on first use), resource exhaustion | `zip_code` comes only from the anchored `\d{5}` regex group; the dataset cache directory is pgeocode's default, never input-derived. |
| `ZoneInfo(tz_name)` | `LocationResolver.require_iana_timezone` | Path traversal (IANA key resolves to a file under the tzdata root) | `tz_name` comes only from `TimezoneFinder`, never from user input; `ZoneInfo` raises on unknown keys. Do not accept a timezone string from the UI or an API without validating it against `zoneinfo.available_timezones()`. |
| CSV export | `src/app.py` `df.to_csv` → `st.download_button` | CSV/formula injection (`location_label` originates from Nominatim `display_name`) | `src/export/neutralize_csv_formulas.py` prefixes cells beginning with `=`, `+`, `-`, `@`, `\t`, `\r` in string columns with `'` before `df.to_csv` feeds the download button. |
| Environment variables | `ZT_PORT` in `docker-compose.yml`, launcher scripts | Command injection (shell interpolation in `run_zmanim_tracker.{sh,bat}`) | Only `${VAR:-default}` substitution; port values are integers and never passed through `eval`. |
| Container / image | `Dockerfile`, `docker-compose.yml` | Vulnerable base image, leaked secrets in layers | Trivy in `docker-build`; `.dockerignore` excludes `.env*`; no secrets baked into layers. |

Out of scope in Phase 1 (no code exists): SQL (no database), XSS/CSP (no React frontend — Streamlit renders escaped widgets; `unsafe_allow_html=True` is banned), template injection, authentication, prompt injection (no LLM calls). When Phase 2 adds FastAPI + SQLAlchemy + React these classes become mandatory entries here: SQLAlchemy bound parameters only, no `text()` with f-strings; Pydantic models on every request; CSP headers in `nginx.conf`; no `dangerouslySetInnerHTML`; `requests` migrates to `httpx` with an explicit host allowlist for outbound calls.

### Project-specific additions
- **Halachic integrity is a security property.** A tampered dependency (`astral`, `timezonefinder`, pgeocode's GeoNames download) silently corrupts zmanim. `pip-audit` in `sast`, pinned `uv.lock`, and the reference-value tests in `tests/` are the controls — never bypass the lockfile in CI or the Dockerfile.
- **Nominatim usage policy.** One request per second max, identifying `User-Agent`, no bulk geocoding. Exceeding it gets the app's IP banned, which is a denial of service on the location boundary.
- Every new input boundary (Phase 2 endpoints, Phase 3 calendar/push integrations) adds a row to the table above before its code merges.

The task-completion checklist in section 13 includes a **Security check** item.

</security>

---

<testing>

## 9. Testing Requirements

- **Framework:** pytest + pytest-cov, 100% coverage target
- **Test location:** `tests/` directory, mirroring `src/` structure
- **Every engine method** must have at least one test validating against a known reference value (MyZmanim.com, Chabad.org, or KosherJava)
- **Numerical comparisons:** use appropriate tolerances. Zmanim should match reference sources within 1-2 minutes (solar calculations have inherent precision limits from refraction models)
- **No mocking of solar calculations.** Test against real `astral` computations
- **Mocking is acceptable for:** Nominatim HTTP calls (use `responses` or `httpx` mocking), pgeocode lookups
- **Parametrize tests** for multiple locations and dates using `@pytest.mark.parametrize`
- **Edge cases to test:** polar regions (midnight sun, polar night), equinox, solstice, date line crossing, invalid locations

</testing>

---

<git_policy>

## 10. Hands Off Git

**The user manages all git operations.** No `git add`, `git commit`, `git checkout`, `git merge`, `git push`, or any other state-mutating git command. Read-only git commands (`git status`, `git diff`, `git log`, `git show`, `git blame`) are allowed for inspection.

When finishing a task, report:
1. What files changed and why (one line each)
2. Whether changes are cohesive enough for one commit or should be split
3. A suggested commit message (clearly labeled as suggestion)

</git_policy>

---

<versioning>

## 11. Versioning

- **Source of truth:** `version` field in `pyproject.toml`
- **Protocol:** strict semver (MAJOR.MINOR.PATCH)
- Patch: bug fix, docs, refactor with no behavior change
- Minor: new feature, new zman, new location method
- Major: breaking change to data contracts or calculation method — ask first
- Document next version in `docs/versions.md` — do NOT edit `pyproject.toml` version directly
- Only one unreleased version at a time in `docs/versions.md`

</versioning>

---

<change_policy>

## 12. Change Policy

1. Re-read this file before any change (mandatory)
2. Re-read `docs/ZMANIM_TRACKER_MASTER_PLAN.md` for architectural decisions
3. Check `docs/status.md` for current state
4. Update `docs/status.md` and `docs/versions.md` after significant changes
5. Run tests after any calculation change
6. Validate against reference zmanim sources when modifying the engine

</change_policy>

---

<definition_of_done>

## 13. Output & Completion Expectations

At the end of every non-trivial task, run through this checklist:

1. **Summary** — One or two sentences: what changed and why.
2. **Reuse check** — Searched for existing utilities before writing new ones.
3. **Tech-debt check** — No shortcuts, no `Any`, no dead code, no duplicated logic, no `TODO` without linked tasks.
4. **File-organization check** — One concept per file.
5. **Data-contract check** — No model changes without architectural approval.
6. **Halachic-accuracy check** — Any calculation change validated against reference sources. State which source and what tolerance.
7. **Docs check** — `status.md` and `versions.md` updated.
8. **Test check** — Tests added or updated for any logic change.
9. **Security check** — Local SAST clean (ruff `S`, Semgrep, pip-audit, gitleaks); every touched input boundary names its injection class(es) and defense; `<security>` section updated if a boundary was added.
10. **Forward-compatibility check** — Work aligns with Phase 2 requirements.
11. **Git state** — Report changed files and suggest commit message.

</definition_of_done>

---

<closing_reminder>

## 14. Reminder

**Before writing any code or making architectural decisions:** re-read this file, then `docs/ZMANIM_TRACKER_MASTER_PLAN.md`, then `docs/status.md`, then `docs/versions.md`, then the source files you plan to modify. Only then implement. Consistency across sessions is non-negotiable.


</closing_reminder>