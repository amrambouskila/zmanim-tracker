---
name: scaffold
description: Scaffold a new module or refactor the project into the target OOP directory structure
---

# Scaffold Module or Directory Structure

## Instructions

Before anything else:
1. Re-read `AGENTS.md` fully.
2. Re-read `docs/ZMANIM_TRACKER_MASTER_PLAN.md`.
3. Confirm the task scope with the user.

### For OOP Refactor (splitting zmanim_tracker.py)

1. Create the `src/` directory structure per AGENTS.md Section 6.
2. Extract each class into its own file:
   - `src/models/location.py` — Location dataclass
   - `src/models/solar_primitives_utc.py` — SolarPrimitivesUTC dataclass
   - `src/models/zmanim_row.py` — ZmanimRow dataclass
   - `src/engine/solar_angle_solver.py` — SolarAngleSolver
   - `src/engine/zmanim_calculator.py` — ZmanimCalculatorAngleBased
   - `src/engine/zmanim_data_builder.py` — ZmanimDataBuilder
   - `src/location/location_resolver.py` — LocationResolver
   - `src/visualization/zmanim_plotter.py` — ZmanimPlotter
   - `src/app.py` — ZmanimApp (Streamlit UI)
3. Every file gets `from __future__ import annotations` at the top.
4. Every file gets full type annotations.
5. Create `__init__.py` for each package with appropriate re-exports.
6. Do NOT implement new logic — only extract existing code.
7. Create matching test files in `tests/` (signatures and docstrings only during scaffold).
8. Update `Dockerfile` CMD to point to `src/app.py`.

### For a New Module

1. Create the module file in the appropriate `src/` subdirectory.
2. Add `from __future__ import annotations`.
3. Write the class/function signature with type annotations and docstring.
4. Create the matching test file in `tests/`.
5. Do NOT implement logic during scaffold — signatures only.

### Report
List all files created with one-line descriptions.