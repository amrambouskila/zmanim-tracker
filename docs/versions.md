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