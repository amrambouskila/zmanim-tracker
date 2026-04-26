---
name: validation-protocol
description: Proactively applied when writing or modifying tests; enforces real assertions, reference values, and no-mocking rules
---

# Validation Protocol

## When to Apply
- When writing or modifying any file in `tests/`
- When modifying any calculation in `src/engine/`

## Rules

### Reference Validation Required
Every engine method must have at least one test that validates against a known external reference:
- **MyZmanim.com** — enter the same location and date, compare times
- **Chabad.org/calendar** — zmanim section for a specific date and location
- **KosherJava ZmanimCalendar** — open-source Java reference (GitHub)

Document the reference source and expected values in the test docstring.

### Numerical Tolerances
Use appropriate tolerances for time comparisons:
```python
# Compare datetimes within N minutes
assert abs((actual - expected).total_seconds()) < tolerance_seconds
```

Acceptable tolerances:
- Sunrise/sunset: 60 seconds (1 minute)
- Angle-based zmanim: 120 seconds (2 minutes)
- Time-based zmanim: 120 seconds (2 minutes)
- Candle lighting: 60 seconds (simple arithmetic from sunset)

### No Mocking of Solar Calculations
- Never mock the `astral` library in engine tests
- Never mock `SolarAngleSolver` when testing `ZmanimCalculatorAngleBased`
- Test against real solar computations to catch actual calculation errors

### Mocking IS Acceptable For
- HTTP calls to Nominatim (use `responses` library)
- pgeocode lookups (mock the Nominatim class from pgeocode)
- Streamlit UI components

### Parametrize Across Conditions
Use `@pytest.mark.parametrize` for:
- Multiple locations (New York, Jerusalem, London, Sydney)
- Multiple dates (equinoxes, solstices, regular days)
- Multiple opinions (GRA, MGA when implemented)
- Edge cases (high latitude, southern hemisphere)

### Test Structure
```python
def test_<zman>_<location>_<condition>():
    """Validate <zman> for <location> on <date>.

    Reference: <source> accessed <date>
    Expected: <HH:MM timezone>
    Tolerance: <N> seconds
    """
```