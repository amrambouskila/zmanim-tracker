---
name: data-driven-check
description: Proactively applied when writing any engine or calculation code; flags hard-coded domain values that should come from config or data
---

# Data-Driven Check Protocol

## When to Apply
- When writing or modifying any file in `src/engine/`
- When writing or modifying any file in `src/models/`
- When adding new zmanim calculations

## What to Check

### Hard-Coded Values That MUST Be Configurable
- Depression angles (alos, misheyakir, tzais) — must come from `ZmanimCalculatorAngleBased` constructor parameters
- Candle lighting offset (default 18 min) — must be a constructor parameter
- Havdalah offset — must be a constructor parameter
- Shaah zmanis multipliers (3, 4, 6.5, 9.5, 10.75) — these are halachic constants from the GRA opinion and ARE acceptable as literals in the GRA implementation, but must be clearly documented

### Acceptable Literals
- Mathematical constants (0, 1, 2, 12 for hours in a day)
- Halachic constants that are definitional (3 shaos for shema, 4 for shacharit, etc.) — document the source
- Day-of-week checks (4 for Friday, 5 for Saturday in Python's weekday())
- Coordinate bounds (-90 to 90 latitude, -180 to 180 longitude)

### NOT Acceptable as Literals
- Depression angles — always from config
- Time offsets (candle lighting minutes, havdalah minutes) — always from config
- Nominatim throttle delay — should be a constant or config value
- API URLs — should be constants

## Action
If a hard-coded value is found that should be configurable, flag it immediately. Do not proceed until it is moved to config.