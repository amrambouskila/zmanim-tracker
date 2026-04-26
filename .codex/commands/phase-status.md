---
name: phase-status
description: Assess the project's progress across its phase roadmap
---

# Phase Status Assessment

Check current phase completion and overall project progress.

## Instructions

Before anything else:
1. Re-read `AGENTS.md` fully.
2. Re-read `docs/ZMANIM_TRACKER_MASTER_PLAN.md` for phase gates.
3. Read `docs/status.md` for current state.
4. Read `docs/versions.md` for recent changes.

### Phase 1 Completion Gate
Verify each item by reading source files or running commands:

- [ ] All classes in separate files under `src/` (OOP refactor complete)
- [ ] `from __future__ import annotations` in every module
- [ ] Full type annotations, ruff clean (`ruff check .`)
- [ ] pytest coverage at 100% (`pytest --cov=src`)
- [ ] At least 3 reference-validated test cases (different locations, seasons)
- [ ] Docker builds and runs cleanly (`docker build .`)
- [ ] CI pipeline defined (`.gitlab-ci.yml` exists and is valid)
- [ ] GRA opinion implemented
- [ ] MGA opinion implemented
- [ ] `docs/status.md` and `docs/versions.md` current
- [ ] Launcher scripts exist and implement [k]/[q]/[v]/[r] loop
- [ ] README.md describes the project and how to run it

### Report Format
```
=== PHASE STATUS ===

Current Phase: 1 (Streamlit App)

COMPLETED:
- [x] Item (verified by: how)

INCOMPLETE:
- [ ] Item (blocker: what's missing)

PROGRESS: N/M items complete
NEXT ACTIONS: (ordered list of what to do next)
VERDICT: PHASE COMPLETE / N blockers remain
```