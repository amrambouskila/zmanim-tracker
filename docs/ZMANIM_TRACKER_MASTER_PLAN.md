# Zmanim Tracker — Master Plan

## 1. Project Vision

A halachic prayer times calculator and tracker that computes accurate zmanim for any location worldwide. Built for a Torah-observant user who relies on these times for daily religious practice — accuracy is non-negotiable.

The project progresses through three phases: a local Streamlit app, a full-stack web application, and a notification/calendar integration platform.

---

## 2. Architecture Overview

```mermaid
graph TD
    subgraph Phase1["Phase 1: Streamlit App"]
        UI[Streamlit UI] --> Engine[ZmanimEngine]
        UI --> Resolver[LocationResolver]
        Resolver --> Nominatim[Nominatim API]
        Resolver --> PGeocode[pgeocode]
        Resolver --> TZFinder[TimezoneFinder]
        Engine --> Astral[astral library]
        Engine --> Models[Data Models]
        UI --> Plotter[ZmanimPlotter]
        UI --> Builder[ZmanimDataBuilder]
        Builder --> Engine
    end

    subgraph Phase2["Phase 2: Full-Stack"]
        React[React Frontend] --> FastAPI[FastAPI Backend]
        FastAPI --> EngineV2[Zmanim Engine v2]
        FastAPI --> DB[(PostgreSQL)]
        FastAPI --> HebrewCal[Hebrew Calendar]
    end

    subgraph Phase3["Phase 3: Notifications"]
        Notif[Notification Service] --> FastAPI
        CalSync[Calendar Sync] --> FastAPI
        PDF[PDF Generator] --> FastAPI
    end

    Phase1 -.->|refactor| Phase2
    Phase2 -.->|extend| Phase3
```

## 3. Calculation Flow

```mermaid
flowchart TD
    Input[/"User Input: Location + Date Range"/] --> Resolve[LocationResolver]
    Resolve --> |lat, lon, tz| Solar[SolarAngleSolver]
    Solar --> |sunrise, sunset| SZ[Compute Shaah Zmanis]
    Solar --> |dawn/dusk at angles| Angles[Angle-Based Zmanim]
    SZ --> |proportional hour| TimeBased[Time-Based Zmanim]

    TimeBased --> Shema["Latest Shema\nsunrise + 3h"]
    TimeBased --> Shacharit["Latest Shacharit\nsunrise + 4h"]
    TimeBased --> MinchaG["Mincha Gedolah\nsunrise + 6.5h"]
    TimeBased --> MinchaK["Mincha Ketana\nsunrise + 9.5h"]
    TimeBased --> Plag["Plag HaMincha\nsunrise + 10.75h"]

    Angles --> Alos["Alos HaShachar\n16.9 / 12.0 deg"]
    Angles --> Misheyakir["Misheyakir\n10.0 deg"]
    Angles --> Tzais["Tzais\n8.5 / 6.0 deg"]

    Solar --> Shabbat{Friday or Saturday?}
    Shabbat --> |Friday| Candle["Candle Lighting\nsunset - 18 min"]
    Shabbat --> |Saturday| Havdalah["Havdalah\ntzais + offset"]

    Solar --> ChatzotN["Chatzot HaLaila\nmidpoint sunset..next sunrise"]

    Shema & Shacharit & MinchaG & MinchaK & Plag & Alos & Misheyakir & Tzais & Candle & Havdalah & ChatzotN --> Row[ZmanimRow]
    Row --> DF[DataFrame]
    DF --> Chart[Plotly Chart]
    DF --> CSV[CSV Export]
    DF --> Table[Streamlit Table]
```

## 4. Phase Roadmap

```mermaid
gantt
    title Zmanim Tracker Development Phases
    dateFormat  YYYY-MM-DD
    axisFormat  %b %Y

    section Phase 1
    Prototype (single file)           :done, p1a, 2025-01-01, 2025-03-09
    OOP Refactor                      :active, p1b, 2026-04-13, 30d
    Docker + CI/CD                    :p1c, after p1b, 14d
    Test Coverage to 100%             :p1d, after p1b, 21d
    MGA Opinion Support               :p1e, after p1d, 7d

    section Phase 2
    FastAPI Backend                    :p2a, after p1e, 30d
    React Frontend                     :p2b, after p2a, 30d
    Hebrew Calendar Integration        :p2c, after p2a, 14d
    PostgreSQL + Saved Locations       :p2d, after p2a, 14d
    Yom Tov Zmanim                    :p2e, after p2c, 14d

    section Phase 3
    Push Notifications                 :p3a, after p2e, 21d
    Calendar Sync                      :p3b, after p2e, 21d
    Shabbat PDF Generation             :p3c, after p2b, 14d
    Multi-Location Comparison          :p3d, after p2b, 14d
```

---

## 5. Phase 1 — Streamlit App

### 5.1 Goals
- Accurate zmanim calculation for any location worldwide
- Multiple location input methods (lat/lon, ZIP, free-text)
- Date range support with tabular and chart output
- CSV export
- Shabbat candle lighting and havdalah times
- Docker containerized
- 100% test coverage

### 5.2 Deliverables
1. OOP-refactored codebase (one class per file)
2. Full test suite validating against reference zmanim sources
3. Docker + docker-compose setup
4. CI/CD pipeline (GitLab)
5. MGA opinion support (in addition to GRA)

### 5.3 Phase 1 Completion Gate
- [ ] All classes in separate files under `src/`
- [ ] `from __future__ import annotations` in every module
- [ ] Full type annotations, ruff clean
- [ ] pytest coverage at 100%
- [ ] At least 3 reference-validated test cases (different locations, seasons)
- [ ] Docker builds and runs cleanly
- [ ] CI pipeline passes (lint, test, coverage, build, docker-build)
- [ ] GRA and MGA opinions both supported
- [ ] `docs/status.md` and `docs/versions.md` current
- [ ] Launcher scripts work on macOS and Windows

---

## 6. Phase 2 — Full-Stack Web Application

### 6.1 Goals
- FastAPI backend serving zmanim via REST
- React + TypeScript frontend with interactive UI
- Hebrew calendar integration for parsha, yom tov awareness
- PostgreSQL for user preferences and saved locations
- Yom tov-aware candle lighting and havdalah

### 6.2 Key Decisions
- Backend reuses the same engine classes from Phase 1
- Frontend uses Chart.js for zmanim visualization (matching charting preferences)
- Hebrew calendar via `hdate` or `jewish-calendar` Python library
- Authentication: session-based (FastAPI + PostgreSQL)

### 6.3 Phase 2 Completion Gate
- [ ] FastAPI serves all zmanim via REST endpoints
- [ ] React frontend renders zmanim with interactive charts
- [ ] Hebrew date displayed alongside Gregorian
- [ ] Yom tov candle lighting and havdalah correct for all major holidays
- [ ] Saved locations persist in PostgreSQL
- [ ] Backend + frontend Docker containers orchestrated
- [ ] API documented via OpenAPI/Swagger

---

## 7. Phase 3 — Notifications & Calendar Integration

### 7.1 Goals
- Push notifications N minutes before configurable zmanim
- Google Calendar / Apple Calendar .ics export
- Weekly Shabbat schedule PDF
- Side-by-side comparison of zmanim at multiple locations

### 7.2 Phase 3 Completion Gate
- [ ] Notifications delivered reliably
- [ ] Calendar events created correctly
- [ ] PDF renders all Shabbat times with correct Hebrew dates
- [ ] Multi-location view functional

---

## 8. Cross-Phase Concerns

### 8.1 Halachic Opinions (Shitot)
The engine must support multiple halachic opinions. Phase 1 implements GRA; Phase 1 extension adds MGA. Future phases may add:
- Rabbeinu Tam (72-minute sunset)
- Yereim (dawn-to-dawn day definition)
- Various community minhagim for candle lighting offsets

Each opinion is a configuration of the calculator, not a separate engine.

### 8.2 Canonical Unit System
- **Angles:** decimal degrees (the `astral` library convention)
- **Time:** Python `datetime` with timezone-aware objects (always `ZoneInfo`)
- **Duration:** Python `timedelta`
- **Coordinates:** decimal degrees (WGS84)

### 8.3 External API Dependencies
| Service | Purpose | Rate Limit |
|---------|---------|------------|
| Nominatim (OpenStreetMap) | Free-text geocoding | 1 req/sec max |
| pgeocode | US ZIP → lat/lon | Local (no network) |
| TimezoneFinder | lat/lon → IANA tz | Local (no network) |
| astral | Solar calculations | Local (no network) |

### 8.4 Data Flow Contracts
- `LocationResolver.resolve(str) -> Location` — never returns None; raises ValueError on failure
- `ZmanimCalculatorAngleBased.compute_for_day(Location, date) -> ZmanimRow` — never returns None; raises on polar regions where sun doesn't set/rise
- `ZmanimDataBuilder.build(Location, date, date) -> pd.DataFrame` — empty DataFrame if end < start (after validation error)

---

## 9. Technology Choices

| Tool | Why |
|------|-----|
| **astral** | Pure Python solar calculations, well-maintained, handles refraction |
| **pgeocode** | Offline ZIP code resolution, no API dependency |
| **TimezoneFinder** | Offline timezone lookup from coordinates |
| **Streamlit** | Rapid UI for Phase 1; replaced by React in Phase 2 |
| **Plotly** | Interactive charts in Streamlit (Phase 1 only) |
| **pandas** | DataFrame output for tabular display and CSV export |
| **requests** | Nominatim geocoding HTTP calls (will migrate to httpx in Phase 2) |
| **ruff** | Lint + format, replaces black/flake8/isort |
| **pytest** | Testing framework with coverage |
| **Docker** | Containerized deployment |
| **uv** | Python package manager |