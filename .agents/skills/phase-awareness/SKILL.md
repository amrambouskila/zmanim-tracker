---
name: phase-awareness
description: Proactively applied at session start and before any implementation work; orients Codex to the current phase and its explicit scope constraints
---

# Phase Awareness Protocol

## When to Apply
- At the start of every session
- Before implementing any new feature or architectural change

## Protocol

1. **Identify current phase** by reading `docs/status.md`.
2. **Load phase constraints** from `AGENTS.md` Section 2:
   - Phase 1: Streamlit only. No FastAPI, no React, no auth, no Hebrew calendar, no notifications.
   - Phase 2: FastAPI + React. No notifications, no calendar sync.
   - Phase 3: Full feature set.
3. **Before any implementation**, verify the proposed work is in scope for the current phase.
4. **If work belongs to a later phase**, stop and flag it. Do not implement.
5. **If work spans phases**, implement only the current-phase portion and document the future-phase remainder in `docs/status.md`.

## Phase 1 Scope Boundaries
- Streamlit UI only — no FastAPI endpoints
- Local computation only — no database persistence
- GRA and MGA opinions — no Rabbeinu Tam or other future opinions
- requests library for HTTP — not httpx (Phase 2 migration)
- plotly for charts — not Chart.js (Phase 2 with React)
- Single user — no auth, no saved preferences