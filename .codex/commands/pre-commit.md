---
name: pre-commit
description: Run full pre-commit validation — tests, lint, halachic accuracy, documentation checks
---

# Pre-Commit Alignment Gate

Run this before every commit to verify all changes meet quality standards. This command is READ-ONLY — it reports a verdict but does NOT stage or commit anything.

## Instructions

Before anything else:
1. Re-read `AGENTS.md` fully.
2. Read `docs/status.md` for current state.

### Step 1: Build Pipeline
Run in sequence:
1. `ruff check .` — lint check
2. `pytest --cov=src --cov-report=term-missing` — tests + coverage

Report: PASS/FAIL for each.

### Step 2: Code Review
For every modified file (check `git diff --name-only`):
- `from __future__ import annotations` present
- Full type annotations on all functions
- No `Any` type escape hatches
- No dead code or commented-out blocks
- No magic numbers
- One class per file (OOP rule)

### Step 3: Halachic Accuracy Validation
For any changes to engine code (`src/engine/`):
- Formulas match AGENTS.md Section 5 documentation
- Depression angles come from config, not literals
- Shaah zmanis calculation correct for the opinion
- At least one test validates against a reference source

### Step 4: Documentation
- `docs/status.md` reflects current state
- `docs/versions.md` updated with changes (semver computed from pyproject.toml)

### Step 5: Unified Report
```
=== PRE-COMMIT REPORT ===

Lint:         PASS/FAIL
Tests:        PASS/FAIL (N passed, M failed)
Coverage:     XX% (target: 100%)
Type Safety:  PASS/FAIL
OOP Rule:     PASS/FAIL
Halachic:     PASS/FAIL/N/A
Docs:         Updated: YES/NO

VERDICT: READY TO COMMIT / NOT READY (list blockers)
```

The user will run git commands based on this report.