# Project Research Summary

**Project:** GSD Review Team Extension — Agent Studio v2.0
**Domain:** Claude Code extension — agent lifecycle management and multi-trigger orchestration
**Researched:** 2026-02-26
**Confidence:** HIGH

## Executive Summary

GSD Agent Studio v2.0 evolves a proven v1.0 post-execution review pipeline into a full agent lifecycle platform. The v1.0 foundation — TEAM.md role definitions, isolated Task() subagents, review-sanitize-synthesize-route pipeline, and Python-based idempotent install.sh patches — is solid and must not be replaced. Every v2.0 addition extends rather than replaces: new YAML fields in TEAM.md are additive and backward compatible; new trigger hooks in GSD core workflows are separate named steps that do not touch existing steps; the new agent dispatcher routes advisory post-plan roles to the unchanged v1.0 review pipeline. The recommended approach is a strictly layered build order: schema first, then dispatcher, then management UI, then lifecycle hooks, then agent creation workflow, then new-project integration.

The core v2.0 differentiator is lifecycle-spanning trigger coverage: agents that advise before plans execute (pre-plan), review after each plan (post-plan, already working), and act autonomously after a full phase completes (post-phase). Three new GSD core workflow patches (plan-phase.md, execute-phase.md, new-project.md) plus a central agent-dispatcher.md that routes by trigger type and mode achieve this without modifying existing functionality. The advisory-to-planner feedback loop — pre-plan agent output injected into the planner's Task() context — is the hardest single implementation task and the key capability that makes v2.0 meaningful.

The top risks are over-generalization (building abstract agent infrastructure before concrete features work), patch idempotency breaks during v1-to-v2 upgrades, and autonomous mode boundary confusion. All three are avoidable: keep every component describable in terms of a user-facing capability, write a versioned patch manifest to track which extension version applied which patch, and scope autonomous mode per trigger type rather than as a global boolean. The review pipeline must never run on agent definition artifacts — add an artifact type bypass before any agent-creation phase.

---

## Key Findings

### Recommended Stack

All v2.0 work runs on the existing stack with zero new runtime dependencies. GSD workflow markdown (XML step blocks and `@`-reference loading) handles all new workflows. YAML frontmatter in TEAM.md is extended with `mode`, `trigger`, `tools`, `output_type`, and `commit` fields. The `config.json` workflow section gets a new `agent_studio` subsection with `lifecycle_hooks` and `autonomous_mode` boolean flags. Python 3 patch scripts (already proven for execute-plan.md and settings.md) handle the three new GSD core patches. YAML parsing in TEAM.md is done by Claude reading the file via the Read tool — not via bash YAML parsing, which jq cannot handle.

**Core technologies:**
- GSD workflow markdown (XML step blocks): All new workflows — consistent with the full extension; Claude Code loads .md files natively via `@` references; no new runtime needed
- YAML frontmatter in TEAM.md: Agent configuration — keeps all agent config in the one file users already manage; new fields are optional with documented defaults
- `config.json` `workflow.agent_studio` subsection: Feature flags — mirrors the existing `workflow.review_team` pattern; jq-readable without gsd-tools changes
- Python 3 patch scripts: Three new GSD core patches — same idempotent anchor-based insertion pattern proven in patch-execute-plan.py
- bash + jq: Config reads in patched workflow steps — reads `workflow.agent_studio.*` flags using the same pattern as the existing `REVIEW_TEAM_ENABLED` check

**Critical version note:** TEAM.md must carry a `version: 2` sentinel so the dispatcher applies the full v2 parsing path. Absent or `version: 1` triggers the v1 compatibility shim — all v1 roles default to `mode: advisory`, `trigger: post-plan`, no tools, no commit.

### Expected Features

**Must have (table stakes) — v2.0 launch:**
- TEAM.md v2 schema (mode, trigger, tools, output_type, commit fields) — foundation everything else depends on; must be designed first
- Agent mode toggle (advisory vs autonomous) — binary, not a spectrum; set per agent, not globally
- Configurable trigger points (pre-plan, post-plan, post-phase, on-demand) — per-agent, not global; post-plan already works via review_team_gate
- Lifecycle-spanning trigger wiring — patches to plan-phase.md (pre-plan) and execute-phase.md (post-phase)
- Advisory output surfaced to planner — pre-plan advisory agent output injected into planner's Task() prompt; this is the hardest feature and the core v2.0 differentiator
- /gsd:new-agent creation workflow — extends new-reviewer.md; captures purpose, mode, triggers, scope, output_type via guided AskUserQuestion
- Config toggle for agent_studio — `workflow.agent_studio` in config.json with /gsd:settings toggle
- Agent roster command (/gsd:team) — formatted table of agents with mode, trigger, status; supports add, edit, disable, on-demand invoke

**Should have — v2.x (after P1 features validated):**
- Agent history per-agent log — aggregate TEAM-HISTORY.md; add once trigger/activation pattern is stable and generating real data
- Project-aware agent initialization — /gsd:new-project proposes agents tailored to project type; requires /gsd:new-agent to exist first
- Autonomous agent artifact output — full autonomous action with defined scope and commit integration; requires advisory mode to be stable first

**Defer to v3+:**
- On-demand agent invocation via /gsd:team invoke — automatic triggers handle the main use case; on-demand is most valuable after they are proven
- Starter agent templates for v2 schema
- Agent performance metrics

**Hard anti-features (do not build):**
- Auto-generating agents from project context without user confirmation
- Agent-to-agent messaging or shared memory — destroys isolation
- Visual dashboard — /gsd:team formatted roster is sufficient
- Autonomous agents with unconstrained tool access

### Architecture Approach

The architecture uses a single central dispatcher (agent-dispatcher.md) as the routing layer between GSD core workflow trigger points and the three execution paths: the unchanged v1 review pipeline, advisory agents, and autonomous agents. Each GSD core workflow patch calls the dispatcher with a trigger type; the dispatcher reads and normalizes TEAM.md once, filters roles by trigger type, then routes advisory post-plan roles to review-team.md (unchanged) and all other roles to their mode-specific Task() invocation. This single dispatch entry point means each GSD core workflow patch is thin — it only needs to check one config flag and call one workflow.

**Major components:**
1. TEAM.md v2 schema — agent roster with additive fields; version sentinel enables compatibility shim; Claude parses YAML via Read tool
2. agent-dispatcher.md — reads TEAM.md, applies version defaults, filters by trigger, routes to review pipeline or autonomous execution path
3. team-studio.md + /gsd:team command — roster display plus add/edit/disable/on-demand invoke; AskUserQuestion loop
4. new-agent.md — GSD-native agent creation via plan+execute cycle; produces auditable, committable agent definition files
5. gsd-agent-builder.md — dedicated subagent for writing GSD-compliant agent files from spec; separate from inline generation for quality
6. Three new GSD core patches: plan-phase.md (pre_plan_agent_gate), execute-phase.md (post_phase_agent_gate), new-project.md (agent_team_hook)
7. gsd-tools.cjs commit used by autonomous agents — agents commit their own artifacts; dispatcher does not commit on their behalf

**Key patterns to follow:**
- Trigger-scoped filtering: dispatcher reads TEAM.md once and filters by current trigger context; prevents N separate patch steps
- Version shim before processing: apply version-appropriate defaults before any routing logic; no scattered `if version == 1` branches downstream
- Autonomous agent commit isolation: each agent commits its own output; dispatcher does not; commit logic lives inside the agent definition
- Advisory passthrough unchanged: advisory post-plan roles route to existing review-team.md with no modifications to the pipeline

### Critical Pitfalls

1. **Frameworkitis — building generic agent infrastructure before any concrete feature works** — Write every component's purpose in terms of what a user can do with it. If a component only makes sense in terms of what other components it connects to, it is infrastructure — defer it. Ship TEAM.md v2 schema + dispatcher + one working trigger before any abstraction layer.

2. **Patch idempotency breaks on v1-to-v2 upgrade** — Never modify an existing named patch block in place; always add a new named step. Maintain a versioned `.patch-state.json` in the extension that records which extension version applied which patch to which GSD file. Test every install.sh run on a system already patched with v1.

3. **Pre-plan agent gate becomes a blocking tax** — Pre-plan agents must be advisory-only by default; the only blocking path is a hardcoded critical condition explicitly declared in TEAM.md. Pre-plan agent scope must not overlap with gsd-plan-checker. Set a 60-second timeout that fails open (advisory, not block).

4. **Review pipeline fires on agent-creation artifacts (meta-problem)** — Agent definition files (.md prompts) will be near-empty after sanitization; code-oriented reviewers produce hallucinated findings. Add artifact type awareness to the pipeline before the agent creation phase. The agent creation phase plan must explicitly state that review_team is disabled or uses a non-code reviewer for those plans.

5. **Autonomous mode boundary confusion** — A single `mode: autonomous` boolean grants autonomy across all trigger types, which users did not intend. Scope autonomous mode per trigger type in TEAM.md. Every autonomous action writes a pre-action log entry before the action. Autonomous agents may not modify GSD core files, install.sh, or other agents' definition files.

6. **new-project integration breaks 60-second onboarding** — The new-project integration adds exactly one question ("set up agent team now or later?"). If "later," the outcome is identical to v1. Agent configuration is never inlined into the new-project flow — it delegates to /gsd:team.

---

## Implications for Roadmap

Based on the combined research, the build order is dictated by strict architectural dependencies: the schema must precede the dispatcher; the dispatcher must precede all trigger hooks and the management UI; agent creation must precede new-project integration. Suggested 7-phase structure:

### Phase 1: TEAM.md v2 Schema and Config Foundation
**Rationale:** Every other v2 feature depends on the schema. The schema must be finalized and backward compatibility validated before any dispatcher logic, any trigger hook, or any agent creation workflow is written. This is the only phase with no upstream dependencies.
**Delivers:** Updated TEAM.md schema with version sentinel, additive fields (mode, trigger, tools, output_type, commit), version shim defaults, and `workflow.agent_studio` subsection in config.json with /gsd:settings toggle.
**Addresses:** TEAM.md v2 schema (P1), Config toggle for agent_studio (P1)
**Avoids:** Schema changes after downstream code is written; breaking v1.0 TEAM.md files (test v1 TEAM.md through new parser to confirm zero-modification backward compatibility)
**Research flag:** No deeper research needed — schema design is fully specified in ARCHITECTURE.md with field definitions and compatibility rules.

### Phase 2: Agent Dispatcher
**Rationale:** The dispatcher is the central routing layer. Once it exists and routes post-plan advisory roles to the unchanged review pipeline, every subsequent phase has a testable integration point. The post-plan path is immediately verifiable because it connects to existing review-team.md.
**Delivers:** agent-dispatcher.md that reads TEAM.md, applies version defaults, filters by trigger type, routes advisory post-plan roles to review-team.md, and handles autonomous role execution via Task(). Post-plan path is fully wired and testable.
**Uses:** TEAM.md v2 schema (Phase 1), existing review-team.md (unchanged), gsd-tools.cjs commit for autonomous agent output
**Implements:** Central dispatch pattern; trigger-scoped filtering; version shim before processing; autonomous agent commit isolation
**Avoids:** Anti-pattern of routing autonomous agents through the review pipeline; anti-pattern of adding per-agent-type config flags
**Research flag:** No deeper research needed — dispatcher data flow is fully specified in ARCHITECTURE.md.

### Phase 3: Team Roster Command (/gsd:team)
**Rationale:** /gsd:team is the management UI for everything that follows. Having it available before lifecycle triggers are wired means users can inspect and modify their TEAM.md through a structured interface rather than hand-editing. On-demand trigger (via /gsd:team) is the only trigger type that requires no GSD core patch — it is fully contained in the extension.
**Delivers:** team-studio.md workflow with roster display, add/edit/disable/on-demand invoke options; commands/gsd/team.md entry point. On-demand trigger path (fourth trigger type) works immediately.
**Uses:** agent-dispatcher.md (Phase 2) for on-demand dispatch; TEAM.md v2 schema (Phase 1)
**Implements:** team-studio.md step sequence; /gsd:team command entry
**Avoids:** Users hand-editing TEAM.md and introducing schema errors; anti-pattern of read-only roster with no management capability
**Research flag:** No deeper research needed — roster display format and step sequence fully specified in ARCHITECTURE.md.

### Phase 4: Pre-Plan and Post-Phase Lifecycle Trigger Hooks
**Rationale:** These are the two new GSD core patches (plan-phase.md and execute-phase.md). They are grouped together because both follow the same pattern: check `workflow.agent_studio` flag, call agent-dispatcher.md with the appropriate trigger type. Grouping them in one phase reduces the number of install.sh changes and allows idempotency to be tested once for both patches.
**Delivers:** pre_plan_agent_gate step in plan-phase.md (fires after plan-checker, before offer_next); post_phase_agent_gate step in execute-phase.md (fires after aggregate_results, before verify_phase_goal); patch-plan-phase.py and updated patch-execute-phase.py scripts; extended install.sh with new patch sections.
**Uses:** agent-dispatcher.md (Phase 2); versioned .patch-state.json to track applied patches
**Implements:** Pre-plan trigger (advisory only; non-blocking by default; 60s timeout); post-phase trigger (advisory and autonomous paths)
**Avoids:** Pre-plan agent overlapping gsd-plan-checker scope; blocking pre-plan gate; install.sh idempotency breaks on v1-to-v2 upgrade (critical — test on v1-patched system)
**Research flag:** May need verification of exact anchor locations in plan-phase.md and execute-phase.md before writing patch scripts. ARCHITECTURE.md provides step names but implementation should confirm current file state.

### Phase 5: Advisory Output Surfaced to Planner
**Rationale:** This is the hardest feature and the core v2.0 differentiator — pre-plan advisory output injected into the planner's Task() prompt creates the genuine planning loop. It is separated from Phase 4 (which wires the trigger) because the injection mechanism requires changes to how the planner's Task() prompt is constructed, which is a distinct implementation concern from the trigger hook itself.
**Delivers:** Advisory agent output from pre-plan trigger collected and injected into the GSD planner's Task() context. Agents that fire at pre-plan now genuinely inform what gets planned.
**Uses:** pre-plan trigger (Phase 4); agent-dispatcher.md advisory output format
**Implements:** Advisory output injection into planner Task() prompt; "Society of Mind / critic-then-revise" pattern adapted to GSD's Task() isolation model
**Avoids:** Contaminating planner context with other agents' reasoning biases; the isolation guarantee that is the v1.0 foundation
**Research flag:** This phase needs deeper research during planning. The injection mechanism — how advisory output reaches the planner's Task() prompt without violating Task() isolation — has no direct GSD precedent. Plan for one research step in the phase plan.

### Phase 6: GSD-Native Agent Creation Workflow (/gsd:new-agent)
**Rationale:** Agent creation via plan+execute is the "studio" part of Agent Studio. It depends on /gsd:team (Phase 3) for the management context and TEAM.md v2 schema (Phase 1) for correct output format. It is built before new-project integration (Phase 7) because the initialization wizard can only propose agents if it knows how to create them.
**Delivers:** new-agent.md workflow (7-step guided: gather intent, classify mode, gather details, plan agent definition, execute agent definition, validate, activate or iterate); gsd-agent-builder.md subagent; commands/gsd/new-agent.md entry point. The review pipeline is explicitly bypassed or uses a non-code reviewer for all agent-creation plans in this phase.
**Uses:** TEAM.md v2 schema (Phase 1); team-studio.md (Phase 3); GSD plan+execute internal model
**Implements:** Plan+execute pattern applied internally to build agent definitions; gsd-agent-builder.md for GSD-compliant agent file generation
**Avoids:** Meta-problem (review pipeline firing on agent definition artifacts) — this is a required design decision for this phase; artifact type bypass must be specified before the first agent-creation plan is executed
**Research flag:** No deeper research needed for the workflow structure — ARCHITECTURE.md specifies the step sequence in full. The artifact type bypass mechanism may need a short research step.

### Phase 7: New-Project Integration
**Rationale:** Last phase because it depends on /gsd:team (Phase 3) and /gsd:new-agent (Phase 6) being fully functional. The integration is intentionally minimal: one question at the end of new-project, delegating to /gsd:team if the user says "now." This phase is the easiest to describe but the most dangerous to scope-creep — the pitfall of adding agent configuration questions to the new-project flow is addressed by keeping this phase's scope to a single binary prompt.
**Delivers:** agent_team_hook step in new-project.md (inserts after Step 5 config write); patch-new-project.py script; one AskUserQuestion at project init offering to launch /gsd:team or skip; project-goal-based agent proposals as suggestions (not auto-created).
**Uses:** /gsd:team (Phase 3); /gsd:new-agent (Phase 6); SUMMARY.md research output (reads project goals for agent proposals)
**Implements:** New-project integration that adds under 10 seconds to onboarding
**Avoids:** Onboarding breaking (exactly one question; "later" produces identical outcome to v1); auto-activation of any agent without explicit user confirmation; inlining agent configuration questions into new-project flow
**Research flag:** No deeper research needed — ARCHITECTURE.md and PITFALLS.md fully specify the correct integration pattern.

### Phase Ordering Rationale

- Phases 1-2 are non-negotiable first because every other phase depends on schema and dispatcher being correct. Skipping ahead creates rework.
- Phase 3 before Phase 4-5 because /gsd:team gives users a way to inspect and manage the team before any automatic triggers fire. This reduces confusion when triggers start activating during Phase 4-5 testing.
- Phase 4 before Phase 5 because the trigger hook must exist before the advisory output injection can be built. They cannot be developed in the same phase — the hook's output contract must be stable before the injection mechanism consumes it.
- Phase 5 isolated because it is the highest-risk implementation. Isolating it means a failure here does not block Phases 6 and 7, which are independent of the advisory injection mechanism.
- Phase 6 before Phase 7 because new-project integration requires /gsd:new-agent to be callable.
- Phase 7 is last because it is the lowest-risk integration — one patch, one question — and depends on all upstream work being stable.

### Research Flags

Phases likely needing a research step during plan-phase:
- **Phase 4:** Confirm current anchor locations in plan-phase.md and execute-phase.md before writing patch scripts. ARCHITECTURE.md names the anchors but the implementation should verify exact step names against the current GSD install.
- **Phase 5:** How advisory output reaches the planner's Task() context without violating Task() isolation has no GSD precedent and is the single highest-risk design question in the project. Plan for one dedicated research step.

Phases with standard, well-documented patterns (skip research-phase):
- **Phase 1:** Schema design fully specified in ARCHITECTURE.md; backward compatibility rules are explicit.
- **Phase 2:** Dispatcher data flow fully specified; no novel integration points.
- **Phase 3:** Roster display and team-studio step sequence fully specified in ARCHITECTURE.md.
- **Phase 6:** new-agent.md step sequence fully specified; plan+execute pattern is the GSD native model.
- **Phase 7:** Integration scope is fully specified; the pitfall to avoid (scope creep) is more dangerous than any implementation ambiguity.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All findings verified directly from GSD source files; zero new runtime dependencies; Python patch pattern is proven in v1.0 |
| Features | HIGH | MVP feature set verified against Claude Code subagent docs (February 2026) and v1.0 codebase; feature priorities consistent across FEATURES.md and ARCHITECTURE.md build order |
| Architecture | HIGH | All component boundaries, anchor points, and data flows verified directly from installed GSD workflow source files; no WebSearch needed for architecture analysis |
| Pitfalls | HIGH | All pitfalls grounded in v1.0 codebase analysis, verified GSD extension architecture, and current ecosystem patterns (OWASP LLM Top 10, Claude Code docs) |

**Overall confidence:** HIGH

### Gaps to Address

- **TEAM.md YAML parsing in bash:** Reading `triggers:` and `mode:` from TEAM.md cannot use jq (jq parses JSON, not YAML). All TEAM.md parsing must use Claude's Read tool with in-context YAML interpretation. This is a workflow design constraint, not a bug — document it explicitly in agent-dispatcher.md's design notes so no implementer reaches for a bash YAML parser.
- **new-project.md patch anchor stability:** The `## 7. Define Requirements` heading is a markdown heading, not an XML step tag. It is more fragile across GSD version bumps than an XML anchor. The patch-new-project.py script must verify the anchor exists and warn (not fail) if it is missing. Treat this as a known fragility during Phase 7.
- **Advisory output injection mechanism:** How pre-plan advisory output reaches the planner's Task() context is not specified in the research files. This is the most significant remaining design question. Flag for a dedicated research step in Phase 5.
- **Autonomous agent tool isolation boundary:** `tools:` frontmatter in Claude Code agent files limits tool access but is a trust boundary, not a hard sandbox. Document clearly in new-agent.md that `autonomous_tools:` in TEAM.md is a declaration of intent and a declaration to the agent, not a security guarantee. Users with high-trust autonomous agents should understand this limitation.

---

## Sources

### Primary (HIGH confidence)
- `C:/Users/gutie/.claude/get-shit-done/workflows/execute-plan.md` — review_team_gate step location and body; trigger extension point
- `C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md` — step sequence; pre-plan hook anchor (after Step 13 present_final_status)
- `C:/Users/gutie/.claude/get-shit-done/workflows/execute-phase.md` — aggregate_results and verify_phase_goal step names; post-phase hook anchor
- `C:/Users/gutie/.claude/get-shit-done/workflows/new-project.md` — Step 5 config write location; agent_team_hook insertion point
- `C:/Users/gutie/.claude/get-shit-done/workflows/settings.md` — AskUserQuestion pattern for new config toggles
- `D:/GSDteams/.planning/TEAM.md` — v1.0 schema; YAML frontmatter format; role block structure
- `D:/GSDteams/install.sh` — Python patch script pattern; idempotency check approach
- `D:/GSDteams/scripts/patch-execute-plan.py` — anchor-based insertion implementation; proven idempotency model
- `D:/GSDteams/commands/gsd/new-reviewer.md` — command entry format for /gsd:team and /gsd:new-agent
- `D:/GSDteams/.planning/research/GSD-EXTENSION-ARCH.md` — patch mechanism; config.json schema; @ reference pattern
- `D:/GSDteams/.planning/research/GSD-AGENT-PATTERNS.md` — Task() isolation; tool grants; structured return conventions
- [Claude Code Subagent Documentation](https://code.claude.com/docs/en/sub-agents) — February 2026 — trigger model, background/foreground, permissionMode, tools field, persistent memory

### Secondary (MEDIUM confidence)
- [GitHub Agentic Workflows Technical Preview](https://github.blog/changelog/2026-02-13-github-agentic-workflows-are-now-in-technical-preview/) — February 2026 — advisory vs autonomous distinction as industry standard
- [OpenAI Agents SDK Hooks](https://medium.com/@abdulkabirlive1/customize-ai-agent-behavior-with-hooks-in-openai-agents-sdk-05270e590cbe) — pre/post hook patterns
- [AGENTS.md Configuration Standard](https://skywork.ai/blog/agent/agents-md-configuration-standardizing-ai-agent-instructions-across-teams/) — GSD's TEAM.md approach aligns with emerging standard
- OWASP LLM Top 10 2025 (LLM01 prompt injection, LLM06 excessive agency) — autonomous agent security constraints
- [Arslan.io — Idempotent Bash Scripts](https://arslan.io/2019/07/03/how-to-write-idempotent-bash-scripts/) — install.sh patch idempotency patterns

### Tertiary (LOW confidence)
- ACL 2025: "Inefficiencies of Meta Agents for Agent Design" — meta-agent self-reference pitfalls (confirms Pitfall 4 risk profile)
- [Google Cloud Blog: Lessons from 2025 on agents and trust](https://cloud.google.com/transform/ai-grew-up-and-got-a-job-lessons-from-2025-on-agents-and-trust) — production agent governance; pre-action logging pattern

---
*Research completed: 2026-02-26*
*Ready for roadmap: yes*
