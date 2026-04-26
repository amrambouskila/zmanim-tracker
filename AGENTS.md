# AGENTS.md - Zmanim Tracker

---

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

---

## 0. Critical Context

**This is a halachic tool.** Zmanim accuracy matters for actual religious observance — people rely on these times for davening, Shabbat candle lighting, and havdalah. Incorrect calculations are not just bugs; they can cause someone to miss a zman or violate Shabbat. Treat every time computation with the rigor of safety-critical software.

**What this project is:** A Jewish prayer times calculator and tracker that computes halachic zmanim for any location using solar angle calculations. It resolves locations via lat/lon, US ZIP codes, and free-text geocoding, then applies the astronomical primitives to derive all standard zmanim according to accepted shitot (halachic opinions).

**What this project is NOT:**
- Not a calendar app (no yom tov scheduling — Phase 3)
- Not a notification service (Phase 3)
- Not a multi-user web app (Phase 2 adds FastAPI backend)

**Current phase:** Phase 1 — Streamlit single-user app. The prototype exists as a single file (`zmanim_tracker.py`). The immediate priority is OOP refactoring into proper module structure, containerization, and test coverage.

---

## 1. Project Identity

- **Project:** `zmanim-tracker` — halachic prayer times calculator
- **Location:** `zmanim-tracker/`
- **Master plan:** `docs/ZMANIM_TRACKER_MASTER_PLAN.md`
- **Stack:** Python 3.13+, Streamlit, astral, pandas, plotly, requests, pgeocode, timezonefinder, zoneinfo
- **Package manager:** uv
- **Testing:** pytest + pytest-cov (100% coverage target)
- **Lint:** ruff (line-length 120, rules E, F, I, N, UP, ANN)
- **Containerization:** Docker (python:3.13-slim)

---

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

---

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

---

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

---

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

---

## 6. Target Directory Structure (Post-Refactor)

```
zmanim-tracker/
├── AGENTS.md                           # This file
├── README.md                           # Human-facing project description
├── docs/
│   ├── ZMANIM_TRACKER_MASTER_PLAN.md   # Master plan: goals, phases, architecture
│   ├── status.md                       # Current project state
│   └── versions.md                     # Semver changelog
├── .codex/
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
├── .gitlab-ci.yml                      # CI/CD pipeline
└── .env                                # Local env vars (gitignored)
```

**Note:** The current `zmanim_tracker.py` in the root is the Phase 1 prototype. It will be refactored into the `src/` structure above. Until refactoring is complete, both may coexist.

---

## 7. Containerization

### Dockerfile
- Base: `python:3.13-slim` (NOT Alpine — musl breaks scientific Python wheels)
- Install deps from `pyproject.toml` via uv
- Copy source
- Expose port 8501 (Streamlit default)
- CMD: `["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]`

### docker-compose.yml
- Single service: `zmanim-tracker`
- Port: `${ZT_PORT:-8501}:8501`
- Bind mount `./src` for dev hot-reload
- `restart: unless-stopped`

### Launcher Scripts
`run_zmanim_tracker.sh` and `run_zmanim_tracker.bat` implement the standard `[k]/[q]/[v]/[r]` shutdown/restart loop per the global AGENTS.md launcher contract.

---

## 8. CI/CD Pipeline (.gitlab-ci.yml)

**Stages (in order):**
1. **lint** — `ruff check .` — fail on any error
2. **test** — `pytest --cov=src --cov-report=term-missing` — fail on any test failure
3. **coverage** — gated at 100% (enforced in pytest config)
4. **build** — `uv build` — must succeed
5. **docker-build** — `docker build .` — verify container builds

All MRs must pass CI before merging.

---

## 9. Testing Requirements

- **Framework:** pytest + pytest-cov, 100% coverage target
- **Test location:** `tests/` directory, mirroring `src/` structure
- **Every engine method** must have at least one test validating against a known reference value (MyZmanim.com, Chabad.org, or KosherJava)
- **Numerical comparisons:** use appropriate tolerances. Zmanim should match reference sources within 1-2 minutes (solar calculations have inherent precision limits from refraction models)
- **No mocking of solar calculations.** Test against real `astral` computations
- **Mocking is acceptable for:** Nominatim HTTP calls (use `responses` or `httpx` mocking), pgeocode lookups
- **Parametrize tests** for multiple locations and dates using `@pytest.mark.parametrize`
- **Edge cases to test:** polar regions (midnight sun, polar night), equinox, solstice, date line crossing, invalid locations

---

## 10. Hands Off Git

**The user manages all git operations.** No `git add`, `git commit`, `git checkout`, `git merge`, `git push`, or any other state-mutating git command. Read-only git commands (`git status`, `git diff`, `git log`, `git show`, `git blame`) are allowed for inspection.

When finishing a task, report:
1. What files changed and why (one line each)
2. Whether changes are cohesive enough for one commit or should be split
3. A suggested commit message (clearly labeled as suggestion)

---

## 11. Versioning

- **Source of truth:** `version` field in `pyproject.toml`
- **Protocol:** strict semver (MAJOR.MINOR.PATCH)
- Patch: bug fix, docs, refactor with no behavior change
- Minor: new feature, new zman, new location method
- Major: breaking change to data contracts or calculation method — ask first
- Document next version in `docs/versions.md` — do NOT edit `pyproject.toml` version directly
- Only one unreleased version at a time in `docs/versions.md`

---

## 12. Change Policy

1. Re-read this file before any change (mandatory)
2. Re-read `docs/ZMANIM_TRACKER_MASTER_PLAN.md` for architectural decisions
3. Check `docs/status.md` for current state
4. Update `docs/status.md` and `docs/versions.md` after significant changes
5. Run tests after any calculation change
6. Validate against reference zmanim sources when modifying the engine

---

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
9. **Forward-compatibility check** — Work aligns with Phase 2 requirements.
10. **Git state** — Report changed files and suggest commit message.

---

## 14. Reminder

**Before writing any code or making architectural decisions:** re-read this file, then `docs/ZMANIM_TRACKER_MASTER_PLAN.md`, then `docs/status.md`, then `docs/versions.md`, then the source files you plan to modify. Only then implement. Consistency across sessions is non-negotiable.