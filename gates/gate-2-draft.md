# Gate 2: Draft Gate

## Position in Pipeline

**Follows:** Steps 4-7 — Agent 5 (Results Writer) || Agent 6 (Figure Engine), Agent 7 (Narrative Writer), Agent 8 (Abstract & Summary), Agent 14 (Scoring) || Agent 16 (Claim Verifier)
**Precedes:** Step 8 — Agent 9 (Reference) || Agent 10 (Compliance)
**Gate Type:** Automated Threshold + User Approval
**Threshold:** Hard score >= 85 (at least 8.5 out of 10 hard metrics passing)

---

## Purpose

Evaluate the first complete manuscript draft for scientific accuracy, structural integrity,
and journal compliance. The automated scoring system identifies computable deficiencies
and triggers the inner loop for self-correction before presenting to the user. The user
then reviews the draft holistically for narrative quality, clinical relevance, and strategic
positioning.

---

## Required Artifacts

The orchestrator MUST verify that ALL of the following artifacts exist and are non-empty
before scoring and presenting Gate 2.

| # | Artifact | Path | Description |
|---|----------|------|-------------|
| 1 | Results Section | `draft/results.md` | Complete results text, all numbers from results_package.json |
| 2 | Introduction | `draft/introduction.md` | Background, evidence summary, gap statement |
| 3 | Discussion | `draft/discussion.md` | Key findings, comparison with literature, limitations, implications |
| 4 | Abstract | `draft/abstract.md` | Journal-formatted abstract with required headings |
| 5 | Methods | `draft/methods.md` | Updated methods section (from Gate 1, refined) |
| 6 | Figures & Tables | `figures/` | All figures and tables (publication-quality, journal-styled) |
| 7 | Score Card | `verification/score_card.md` | 10 hard metrics + 4 soft metrics from Agent 14 |
| 8 | Claim Verification Report | `verification/claim_verification_report.md` | Reference status + claim alignment from Agent 16 |

### Journal-Specific Artifacts (if applicable)

| Artifact | Path | When Required |
|----------|------|---------------|
| Research in Context panel | `draft/research_in_context.md` | Lancet |
| Key Points | `draft/key_points.md` | JAMA |
| What This Study Adds | `draft/what_this_adds.md` | BMJ |
| Clinical Perspective | `draft/clinical_perspective.md` | Circulation |

---

## Automated Scoring (Inner Loop Trigger)

### Threshold

**Hard score >= 85** means at least 8.5 out of 10 hard metrics must PASS.

The score is calculated as: (number of hard metrics passing / 10) x 100.

For the precise definition of each hard metric and its pass/fail criteria, see
`references/hard-soft-metrics-spec.md`.

### Inner Loop Activation

If the hard score is BELOW 85 after Agent 14 scores the draft:

1. The inner loop is triggered automatically (see `references/inner-loop-protocol.md`)
2. The inner loop runs for up to 5 iterations
3. After each iteration, the score is recomputed
4. The loop stops when: score >= 85, OR 5 iterations exhausted, OR all metrics pass

If the score reaches >= 85, the draft proceeds to gate presentation.

If 5 iterations are exhausted without reaching 85, the BEST-SCORING version is presented
to the user with a clear warning:

```
WARNING: Automated refinement did not reach the target threshold.
Best score achieved: [N]/10 after [M] iterations.
Remaining failures: [list of failing metrics with details].
Your review and direction are needed.
```

### Score Card Presentation

The full score card is presented to the user in the format defined in SKILL.md section 7,
including:

- All 10 hard metrics with values, targets, and PASS/FAIL status
- All 4 soft metrics with LLM assessment text
- Composite hard score: N/10
- Inner loop history (if triggered): score at each iteration, fixes applied, reverts

---

## What to Present to the User

### Full Manuscript Draft
- All sections assembled in reading order: Abstract, Introduction, Methods, Results, Discussion
- Journal-specific panels (Research in Context, Key Points, etc.)
- All figures and tables in position

### Score Card
- Hard metrics summary: N/10 passing
- Each metric with value, target, status
- Soft metrics with assessment text
- Inner loop summary (iterations, fixes, final state)

### Claim Verification Report
- Total claims extracted: N
- Verified (source supports claim): N
- Plausible (source related, claim interpretive): N
- Unsupported (source does not support): N
- Contradicted (source says opposite): N
- References checked: N/N resolved via DOI
- Retracted references found: N
- Expressions of concern: N

### Key Warnings (if any)
- Failing hard metrics that were not resolved by inner loop
- Unsupported or contradicted claims
- Retracted references
- Spin detected (if null result)

---

## User Actions at Gate 2

| Action | What Happens |
|--------|--------------|
| **Approve** | Draft is accepted. Pipeline proceeds to Step 8 (Agent 9 References + Agent 10 Compliance). Writing phase is considered complete. |
| **Request rewrites** | User specifies sections to rewrite and direction (e.g., "Discussion needs stronger clinical implications", "shorten Introduction by 200 words"). Orchestrator dispatches appropriate agents. Rescored by Agent 14. Gate 2 re-presents. |
| **Add content** | User requests additions (e.g., "add a sensitivity analysis table", "include a comparison with the PARADIGM-HF trial"). Orchestrator dispatches appropriate agents. Gate 2 re-presents. |
| **Redirect narrative** | User wants to change framing (e.g., "lead Discussion with safety finding instead"). Agent 2 (Story Architect) revises blueprint; Agent 7 (Narrative Writer) rewrites. Gate 2 re-presents. |
| **Override metric failure** | User explicitly accepts a failing metric (e.g., "4 AI words is fine, don't fix"). Metric is marked as user-overridden; inner loop skips it in future. |

---

## Immutability Rules at Gate 2

- `results_package.json` remains immutable (locked at Gate 0b)
- Numbers in manuscript MUST match results_package.json (H9 enforces this)
- Population N MUST match across sections (H10 enforces this)
- Agent 5 (Results Writer) may only be dispatched to CORRECT numbers, never to compute new ones
- No new statistical analyses at this stage — only Agent 18 (Data Analyst) can produce numbers, and that requires rolling back to Gate 0b

---

## Orchestrator Checklist

Before presenting Gate 2, the orchestrator verifies:

- [ ] All required artifacts exist and are non-empty
- [ ] Journal-specific panels are present (based on loaded style profile)
- [ ] Agent 14 has scored the draft and score_card.md is complete
- [ ] Agent 16 has verified claims and claim_verification_report.md is complete
- [ ] If hard score < 85: inner loop has been executed (up to 5 iterations)
- [ ] Best-scoring version of the draft is presented
- [ ] Clean data hash matches Gate 0a approved hash
- [ ] results_package.json hash matches Gate 0b approved hash
- [ ] No unresolved agent conflicts (orchestrator has applied conflict resolution hierarchy)
