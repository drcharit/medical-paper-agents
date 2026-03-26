# Gate 1: Plan Gate

## Position in Pipeline

**Follows:** Steps 0.5 through 3 — Agent 0.5 (Triage), Agent 1 (Literature), Agent 2 (Story Architect) || Agent 3 (Study Design), Agent 4 (Statistician verification)
**Precedes:** Step 4 — Agent 5 (Results Writer) || Agent 6 (Figure Engine)
**Gate Type:** User Approval (no automated scoring threshold)

---

## Purpose

Ensure that the strategic plan for the paper is sound before any writing begins. This gate
validates journal targeting, narrative framing, evidence positioning, methods structure,
and statistical approach. Changing direction after writing begins is expensive — this gate
is the last efficient point to pivot.

---

## Required Artifacts

The orchestrator MUST verify that ALL of the following artifacts exist and are non-empty
before presenting Gate 1 to the user.

| # | Artifact | Path | Description |
|---|----------|------|-------------|
| 1 | Triage Report | `plan/triage-report.md` | Per-journal fit scores, recommended target journal, rationale |
| 2 | Paper Plan | `plan/paper-plan.md` | Assembled plan document: scope, contribution, structure |
| 3 | Narrative Blueprint | `plan/narrative-blueprint.md` | Story arc: hook, tension, gap, resolution, punchline |
| 4 | Literature Matrix | `plan/literature-matrix.md` | Evidence summary table, gap statement, reference library |
| 5 | Methods Draft | `draft/methods.md` | Draft methods section with reporting guideline selection |
| 6 | Statistical Plan | `analysis/statistical_plan.md` | Verified SAP — confirmed by Agent 4 as matching executed analysis |

### Loaded Configuration

| Item | Source | Description |
|------|--------|-------------|
| Style Profile | `styles/{journal}.yaml` | Loaded by orchestrator based on triage recommendation |

---

## What to Present to the User

The orchestrator summarises the following in a structured gate review panel:

### Journal Recommendation
- **Recommended journal:** Name (from triage-report.md)
- **Fit score:** N/10 (from triage-report.md)
- **Rationale:** 2-3 sentence summary of why this journal
- **Alternative journals:** Ranked list with scores
- **Key journal constraints:** Word limit, reference limit, figure/table limit, special panels required
- **Style profile loaded:** Confirm which YAML is active

### Narrative Arc
- **Hook:** Opening statement that captures attention (from narrative-blueprint.md)
- **Tension:** The clinical problem and its significance
- **Gap:** The specific unknown this study addresses
- **Resolution:** What this study found (linked to results_package.json)
- **Punchline:** The "so what" for clinical practice
- **Null result mode:** Active / Inactive

### Evidence Positioning
- **Key prior studies:** Top 5 from literature matrix with findings
- **Gap statement:** The exact gap statement to be used in the Introduction
- **Novelty claim:** How this study differs from prior work
- **Systematic search summary:** Databases searched, N results, N included

### Methods Outline
- **Study design:** RCT / Cohort / Case-Control / Cross-Sectional / etc.
- **Reporting guideline:** CONSORT / STROBE / PRISMA / CARE / etc. (with item count)
- **Population:** Inclusion/exclusion criteria summary
- **Primary endpoint:** Definition and analysis method
- **Key secondary endpoints:** List
- **Statistical approach:** Primary model, handling of missing data, sensitivity analyses
- **Statistician verification:** Agent 4's confirmation that methods text matches executed analysis

---

## Scoring

**There is no automated scoring threshold at Gate 1.** The plan does not produce a score
card. The quality of strategic decisions (journal choice, narrative framing, gap positioning)
requires human judgment that cannot be reduced to computable metrics.

---

## User Actions at Gate 1

| Action | What Happens |
|--------|--------------|
| **Approve** | Plan is locked. Orchestrator proceeds to Step 4 (writing phase). Journal style profile is confirmed. Narrative blueprint guides all writing agents. |
| **Change journal** | User selects a different target journal. Orchestrator loads the new style YAML. Agent 0.5 updates triage report. Agents 2 and 3 update outputs for new journal constraints (word limits, special panels). Gate 1 re-presents. |
| **Redirect narrative** | User provides new framing direction (e.g., "lead with the safety finding, not efficacy"). Agent 2 rewrites narrative blueprint. Gate 1 re-presents. |
| **Modify methods** | User changes methods approach (e.g., "add a propensity score analysis", "use Fine-Gray instead of Cox"). Agent 3 updates methods; Agent 4 verifies feasibility against existing results. Gate 1 re-presents. |
| **Request more literature** | User wants additional searches (e.g., "search for studies in paediatric populations too"). Agent 1 expands search. Literature matrix and gap statement updated. Gate 1 re-presents. |

---

## Key Validation Checks

The orchestrator performs these checks before presenting the gate:

### Consistency Checks
- [ ] Methods describe the same statistical approach that was executed and approved at Gate 0b
- [ ] Population described in methods matches population_flow.json from Gate 0a
- [ ] Narrative blueprint references the actual primary result from results_package.json
- [ ] Gap statement is consistent with literature matrix (the gap is real, not already filled)
- [ ] Journal word limit is feasible given the study complexity (warning if tight)

### Completeness Checks
- [ ] All 6 required artifacts exist and are non-empty
- [ ] Triage report includes at least 3 journals scored
- [ ] Literature matrix includes at least 10 relevant prior studies
- [ ] Narrative blueprint covers all 5 arc elements (hook, tension, gap, resolution, punchline)
- [ ] Methods section covers: design, population, intervention/exposure, outcomes, statistical analysis
- [ ] Reporting guideline is selected and all required items are mapped to planned sections

### Coherence Checks
- [ ] Story arc is appropriate for result direction (positive result vs null result)
- [ ] Gap statement names a specific clinical unknown (not generic "remains unclear")
- [ ] Methods and narrative are aligned (methods supports the story being told)

---

## Impact of Plan Decisions

Decisions made at Gate 1 cascade through the entire writing phase:

| Decision | Downstream Impact |
|----------|-------------------|
| Journal choice | Style profile governs: spelling, formatting, abstract structure, special panels, word/ref limits, tone |
| Narrative arc | Guides Agent 7 (Narrative Writer) for Introduction and Discussion structure |
| Gap statement | Becomes the pivot point of the Introduction — all prior evidence leads to this gap |
| Methods structure | Defines the reporting checklist items that Agent 10 (Compliance) must complete |
| Statistical plan | Agent 5 (Results Writer) structures results to mirror the methods |

---

## Orchestrator Checklist

Before presenting Gate 1, the orchestrator verifies:

- [ ] All 6 required artifacts are present and non-empty
- [ ] Style YAML is loaded and active for the recommended journal
- [ ] All consistency checks pass
- [ ] All completeness checks pass
- [ ] All coherence checks pass
- [ ] Null result mode is correctly set based on Gate 0b results
- [ ] No unresolved conflicts between agents (Agent 2 vs Agent 3 outputs are compatible)
