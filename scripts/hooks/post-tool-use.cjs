const { emit, getToolFilePath, readHookPayload, toPosixPath } = require("./hookUtils.cjs");

const RULES = [
  {
    test: (p) =>
      p.includes("/engine/") || p.includes("calculator") || p.includes("solar") || p.includes("zmanim_calculator"),
    context:
      "ZMANIM ENGINE CODE EDITED. Verify: (1) all depression angles come from config, not magic numbers, (2) shaah zmanis formula correct for the opinion (GRA vs MGA), (3) time-based zmanim use the correct number of shaos, (4) candle lighting / havdalah handles Friday/Saturday correctly, (5) all datetimes are timezone-aware (ZoneInfo), (6) validate against a reference zmanim source.",
  },
  {
    test: (p) => p.includes("/models/"),
    context:
      "DATA MODEL EDITED. Data models are contracts. Verify: (1) all fields have type annotations, (2) units documented (degrees, minutes, etc.), (3) frozen dataclass if immutable, (4) no changes that break ZmanimRow or Location contracts.",
  },
  {
    test: (p) => p.includes("/location/"),
    context:
      "LOCATION CODE EDITED. Verify: (1) Nominatim rate limiting enforced (min 0.8s between requests), (2) ValueError raised on unresolvable input, (3) IANA timezone string validated via ZoneInfo.",
  },
];

async function main() {
  const payload = await readHookPayload();
  const f = toPosixPath(getToolFilePath(payload));
  if (!f) return;
  const m = RULES.find((r) => r.test(f));
  if (m) emit({ hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: m.context } });
}

main().catch((e) => {
  process.stderr.write(`[hook] post-tool-use failed: ${e.message}\n`);
  process.exitCode = 0;
});
