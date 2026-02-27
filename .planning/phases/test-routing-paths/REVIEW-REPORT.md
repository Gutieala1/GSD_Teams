# Review Report — Phase test-routing-paths

---

## Plan high — 2026-02-25T10:06:00Z

**Reviewers:** security-auditor, rules-lawyer, performance-analyst
**Findings:** 2 | **Deduped:** 1
**Action:** send_for_rework

| ID | Reviewer | Severity | Description | Evidence | Routing |
|----|----------|----------|-------------|----------|---------|
| SYNTH-001 | security-auditor | info | Export endpoint returns PII fields (email, phone, address) with no documented authentication requirement on the route. | Returns full user objects including email, phone, address fields | log_and_continue |
| SYNTH-002 | rules-lawyer, performance-analyst | high | Missing pagination and no record limit on export endpoint. Implementation uses User.query.all() returning complete dataset unconditionally, directly contradicting the stated plan requirement and creating an unbounded database query. | Plan requirement stated: all exports must be paginated and limited to 1000 records per request | send_for_rework |

---

## Plan medium — 2026-02-25T10:07:00Z

**Reviewers:** security-auditor, rules-lawyer, performance-analyst
**Findings:** 2 | **Deduped:** 1
**Action:** send_for_rework

| ID | Reviewer | Severity | Description | Evidence | Routing |
|----|----------|----------|-------------|----------|---------|
| SYNTH-001 | security-auditor, rules-lawyer | medium | The discount_rate parameter accepts values outside the documented 0.0–1.0 range with no validation. Out-of-contract values produce incorrect financial calculations and are accepted silently. | No validation that discount_rate is within 0.0–1.0 range | send_to_debugger |
| SYNTH-002 | rules-lawyer | high | Implementation divides subtotal by discount_rate. When discount_rate=0.0 (the documented no-discount case), this triggers an unhandled ZeroDivisionError at runtime. No exception handling exists for this case. | Divides the subtotal by the discount rate to apply discounts | send_for_rework |

---

## Plan critical — 2026-02-25T10:10:00Z

**Reviewers:** security-auditor, rules-lawyer, performance-analyst
**Findings:** 6 | **Deduped:** 0
**Action:** block_and_escalate

| ID | Reviewer | Severity | Description | Evidence | Routing |
|----|----------|----------|-------------|----------|---------|
| SYNTH-001 | security-auditor | critical | Production secret key is hardcoded as a literal string in src/config.py. The value is committed to the codebase and cannot be rotated without a code change. | `SECRET_KEY` \| `"sk-prod-hardcoded-abc123xyz-do-not-rotate"` \| `src/config.py` | block_and_escalate |
| SYNTH-002 | security-auditor | critical | Database password is hardcoded as a plaintext literal in src/config.py. The credential is exposed in source control. | `DB_PASSWORD` \| `"admin123"` \| `src/config.py` | block_and_escalate |
| SYNTH-003 | security-auditor | medium | No input validation or sanitization documented on the authentication endpoint's username and password fields. | POST `/api/authenticate` accepts `username` and `password` in the request body | send_for_rework |
| SYNTH-004 | security-auditor | low | JWT token validity window of 30 days is an extended exposure period. | Token expiry is set to 30 days | log_and_continue |
| SYNTH-005 | rules-lawyer | low | Only manual test coverage documented. No automated tests added for the authentication endpoint. | Manual test: endpoint returns 200 with valid credentials — No automated tests added | log_and_continue |
| SYNTH-006 | rules-lawyer | info | No error contract defined for malformed or missing request body fields. | POST `/api/authenticate` — body: `{username, password}` → returns `{token, expires_at}` | log_and_continue |

---
