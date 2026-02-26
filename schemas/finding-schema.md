# Finding JSON Schema

Defines the JSON structure produced by `gsd-reviewer.md` and consumed by `gsd-review-synthesizer.md`.
Every finding flowing through the review pipeline must conform to this schema.

**Version:** v1.0 (Phase 3)

---

## Full Schema Example

```json
{
  "findings": [
    {
      "id": "SEC-001",
      "reviewer": "security-auditor",
      "domain": "security",
      "severity": "high",
      "evidence": "JWT_SECRET | required env var | .env",
      "description": "JWT_SECRET stored in .env with no indication of secret rotation policy or minimum entropy requirement.",
      "suggested_routing": "send_for_rework"
    }
  ]
}
```

---

## Field Reference

| Field | Type | Required | Constraints | Notes |
|-------|------|----------|-------------|-------|
| `id` | string | YES | Format `{ROLE_PREFIX}-{NNN}` (zero-padded 3 digits) | Role prefix = first 3-4 uppercase characters of role name (e.g., `SEC` for security-auditor, `LAW` for rules-lawyer, `PERF` for performance-analyst). Sequential within a reviewer's response. |
| `reviewer` | string | YES | Must match role `name:` field from TEAM.md YAML exactly | Machine-readable role identifier. |
| `domain` | string | YES | Must match role `focus:` field from TEAM.md | Enables synthesizer to detect scope bleed. |
| `severity` | string enum | YES | One of: `critical`, `high`, `medium`, `low`, `info` (exact strings) | Case-sensitive. |
| `evidence` | string | YES | Character-for-character quote from ARTIFACT.md — not a paraphrase | The literal text that grounds the finding. Paraphrase is not valid. |
| `description` | string | YES | Observable issue — no speculation, no "might", "could", "probably" | States what IS wrong, not what MIGHT be wrong. |
| `suggested_routing` | string enum | YES | One of: `block_and_escalate`, `send_for_rework`, `send_to_debugger`, `log_and_continue` | Reviewer suggestion; Phase 4 synthesizer enforces severity-based minimum. |

---

## Severity Rubric

Assign severity based on production impact. Use your role's specific severity thresholds from your role definition to calibrate these general definitions.

**CRITICAL:** Would cause data loss, security breach, or complete system failure in production.
No reasonable person would ship code with this finding unresolved.
Production deploy must halt.

Examples: Hardcoded credentials, SQL injection, auth bypass, data corruption.

---

**HIGH:** Incorrect behavior that would reach users or break core functionality.
Fix required before shipping. Does not warrant halting a deploy if a workaround exists.

Examples: Race condition in payment processing, missing authentication on a route.

---

**MEDIUM:** Deviates from stated requirements or established patterns.
Should fix before next plan executes. Acceptable risk for a hotfix deploy.

Examples: Missing input validation on an API field, wrong HTTP status code returned.

---

**LOW:** Suboptimal but working. Degrades quality without breaking behavior.
Fix before the phase completes. Fine to ship with a tracking issue.

Examples: Missing database index on a queried column, deprecated API in use.

---

**INFO:** Observation worth recording. No action required.
For awareness only.

Examples: Unused env var, style deviation with no behavioral impact.

---

## Tie-Breaking Rule

```
When deciding between two severity levels, choose the LOWER one.

Tie-breaking question: "Would I personally halt a production deploy for this finding?"
  YES → critical or high
  NO  → medium, low, or info

Anti-inflation check: Review each `critical` finding before finalizing.
If you would not personally stop a production deploy for it, downgrade to `high`.
```

---

## Routing Destinations

| Destination | When to use |
|-------------|-------------|
| `block_and_escalate` | Critical finding that must be seen by the user before execution continues. Phase 4 hardcodes this for all `critical` severity findings. |
| `send_for_rework` | Finding indicates the plan output is incorrect — the plan should be re-executed with corrections. |
| `send_to_debugger` | Finding indicates a runtime error or unexpected behavior needing debugging. |
| `log_and_continue` | Finding is worth recording but does not block execution. |

---

## Empty Findings

When a reviewer has no findings in its domain, it returns:

```json
{"findings": []}
```

This is a valid, expected output. An empty findings array means the reviewer found nothing in its domain — not that the reviewer failed. The workflow handles empty arrays by logging "0 findings" and continuing normally.

---

## ID Generation

- **Format:** `{ROLE_PREFIX}-{NNN}` where NNN is zero-padded (001, 002, 003...)
- **Prefix derivation:** First 3-4 uppercase characters of the role's `name:` field from TEAM.md YAML
- **Starter role prefixes:** `SEC` (security-auditor), `LAW` (rules-lawyer), `PERF` (performance-analyst)
- IDs are sequential within a single reviewer's response starting from 001
- In Phase 4 (parallel), each reviewer's unique prefix prevents ID collisions across the findings set
