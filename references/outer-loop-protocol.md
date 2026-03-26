# Outer Loop Protocol: Skill Self-Improvement

## Overview

The outer loop is the meta-learning mechanism by which the multi-agent system improves its
own protocols over time. It is executed by Agent 15 (Meta-Evaluator) and analyses the
performance of all agents across the pipeline to identify systematic weaknesses, recurring
failures, and opportunities for protocol improvement.

Unlike the inner loop (which fixes a specific manuscript), the outer loop fixes the system
itself — making future manuscripts better by updating agent instructions.

---

## When It Runs

The outer loop activates in two scenarios:

### Scenario 1: Post-Completion

After a paper is complete (user approves Gate 3), Agent 15 runs as Step 13 in the pipeline.
This is the standard post-mortem analysis.

**Trigger:** Gate 3 approval.
**Timing:** After the submission package is delivered, before the pipeline session closes.

### Scenario 2: User Feedback

If the user provides explicit feedback about agent performance at any point (e.g., "the
Humanizer keeps missing AI words", "the gap statements are always too generic"), the
orchestrator can dispatch Agent 15 for a targeted analysis.

**Trigger:** User feedback referencing systematic agent issues (not one-off manuscript fixes).
**Timing:** Can run between papers or during a pipeline session.

---

## What It Analyses

Agent 15 examines the complete execution record of the pipeline. The orchestrator provides
Agent 15 with the following data sources:

### 1. Score Trajectory

The hard metric scores at each scoring event across the pipeline:

```
Gate 2 initial score:     {N}/10
Gate 2 post-inner-loop:   {N}/10 (after {M} iterations)
Gate 3 initial score:     {N}/10
Gate 3 post-inner-loop:   {N}/10 (after {M} iterations)
```

**What to look for:**
- Metrics that fail at Gate 2 AND Gate 3 (not fixed by intermediate agents)
- Metrics that pass at Gate 2 but fail at Gate 3 (broken by later agents)
- Metrics that never reach PASS even after inner loop

### 2. Agent Dispatch Frequency

How often each agent was dispatched by the inner loop for fixes:

```
Agent 12 (Humanizer):      dispatched 4 times (H4 x3, H5 x1)
Agent 9  (Reference):      dispatched 2 times (H6 x1, H8 x1)
Agent 5  (Results Writer): dispatched 1 time  (H9 x1)
...
```

**What to look for:**
- Agents dispatched 3+ times across both gates → their initial protocol is too weak
- Agents that are never dispatched → their protocol is effective (or their metrics are easy)

### 3. Recurring Failures

Metrics that failed across multiple papers (if multiple papers have been written):

```
H4 (AI words): failed in 3/4 papers at Gate 2
H5 (sentence variance): failed in 2/4 papers at Gate 2
H3 (checklist): failed in 1/4 papers at Gate 3
```

**What to look for:**
- Any metric that fails in >50% of papers → systemic issue with the responsible agent
- Patterns in which phase the failures originate

### 4. User Feedback at Gates

What the user changed, rejected, or commented on at each gate:

```
Gate 0b: User requested additional sensitivity analysis (competing risks)
Gate 1:  User changed target journal from Lancet to NEJM
Gate 2:  User said "Discussion is too long" and "gap statement is vague"
Gate 3:  User said "cover letter needs to mention the subgroup finding"
```

**What to look for:**
- Repeated themes across papers (e.g., Discussion always too long → Agent 7 or 11 issue)
- User overrides of agent decisions (indicates agent was wrong)
- Content the user consistently adds that agents miss

### 5. Time-to-Convergence

How many inner loop iterations each gate needed:

```
Gate 2: 3 iterations to reach threshold
Gate 3: 1 iteration to reach threshold
```

**What to look for:**
- Gates that consistently need 4-5 iterations → agents upstream are producing low-quality output
- Gates that need 0 iterations → pipeline is well-tuned for this gate

---

## Diagnosis Format

Agent 15 produces a structured diagnosis document. Each finding follows this format:

```markdown
### Finding {N}: {Short Title}

**Pattern observed:** {What the data shows}
**Root cause:** {Why this is happening — which agent, which protocol gap}
**Evidence:**
- {Specific data point 1}
- {Specific data point 2}
- {Specific data point 3}
**Severity:** CRITICAL / MODERATE / LOW
  - CRITICAL: Caused threshold failure in >50% of inner loop invocations
  - MODERATE: Caused 1-2 additional inner loop iterations
  - LOW: Advisory; did not directly cause threshold failure
**Proposed fix:** {Specific protocol change — see next section}
```

### Example Diagnosis

```markdown
### Finding 1: Humanizer Consistently Fails AI Word Check

**Pattern observed:** H4 (AI-flagged words) failed at Gate 2 in 4 out of 5 papers.
Agent 12 was dispatched 3-4 times per paper in the inner loop to fix AI words.
**Root cause:** Agent 12's protocol applies AI word removal as a post-processing step.
Words are introduced by Agent 7 (Narrative Writer) and Agent 11 (Editor) faster than
Agent 12 removes them. Agent 12 needs to prevent AI words, not just remove them.
**Evidence:**
- Paper 1: 12 AI words at Gate 2, needed 3 iterations to reach 3
- Paper 2: 9 AI words at Gate 2, needed 2 iterations
- Paper 3: 15 AI words at Gate 2, needed 4 iterations, still had 5 at exhaustion
**Severity:** CRITICAL
**Proposed fix:** Add to agent-12-humanizer.md: "Before writing ANY sentence, mentally
check against the blacklist. Pre-filter during composition, do not rely solely on
post-fix scanning."
```

---

## Protocol Update Proposal Format

Each proposed update follows this structure:

```markdown
## Proposed Update {N}

**Target file:** `agents/{agent-protocol-file}.md`
**Finding reference:** Finding {N}
**Change type:** ADD_RULE / MODIFY_RULE / ADD_EXAMPLE / RESTRUCTURE
**Current text (if modifying):**
> {Exact current text in the protocol, or "N/A — new addition"}

**Proposed new text:**
> {Exact text to add or replace}

**Expected impact:**
- Metric {H_id} failure rate should decrease from ~{X}% to ~{Y}%
- Inner loop dispatch of Agent {N} should decrease from ~{X} times to ~{Y} times

**Risk assessment:**
- Could this change cause regressions in other metrics? {YES/NO — explain}
- Does this change conflict with any other agent's protocol? {YES/NO — explain}
```

---

## User Approval Requirement

**All protocol updates require explicit user approval.** This is non-negotiable.

The user is the "meta-programmer" — they decide how agents work, not the agents themselves.
Agent 15 proposes; the user disposes.

### Approval Flow

1. Agent 15 produces the diagnosis and proposed updates
2. The orchestrator presents the full report to the user
3. For each proposed update, the user can:
   - **Approve:** The update is applied to the agent protocol file
   - **Modify:** The user edits the proposed text before it is applied
   - **Reject:** The update is discarded with the user's reason logged
   - **Defer:** The update is saved for later consideration

### Presentation Format

```markdown
## META-EVALUATION REPORT — {Paper Title} — {Date}

### Executive Summary
- Papers analysed: {N}
- Findings: {N} (CRITICAL: {N}, MODERATE: {N}, LOW: {N})
- Proposed updates: {N}

### Findings
{All findings in diagnosis format}

### Proposed Protocol Updates
{All proposals in update format}

### Your Decision Required
For each proposed update, please indicate: APPROVE / MODIFY / REJECT / DEFER
```

---

## How Updates Are Persisted

### File Modification

When the user approves an update:

1. The orchestrator reads the target agent protocol file (e.g., `agents/agent-12-humanizer.md`)
2. The specific change is applied:
   - **ADD_RULE:** New rule inserted at the appropriate location in the protocol
   - **MODIFY_RULE:** Existing text replaced with new text
   - **ADD_EXAMPLE:** Examples appended to the relevant section
   - **RESTRUCTURE:** Section reorganised as specified
3. The file is saved with the change

### Change Log

Every approved update is logged in `references/protocol-changelog.md`:

```markdown
## Protocol Change Log

### {Date} — Post "{Paper Title}" Meta-Evaluation

| # | Agent | File | Change Type | Summary | Finding |
|---|-------|------|-------------|---------|---------|
| 1 | 12 (Humanizer) | agent-12-humanizer.md | ADD_RULE | Pre-filter AI words during composition | Finding 1 |
| 2 | 05 (Results Writer) | agent-05-results-writer.md | ADD_RULE | Verify N from CONSORT flow in first sentence | Finding 2 |
| 3 | 07 (Narrative Writer) | agent-07-narrative-writer.md | ADD_EXAMPLE | 5 strong gap statement examples | Finding 3 |
```

### Version Control

Protocol files should be committed to version control after each meta-evaluation session.
This allows:
- Tracking protocol evolution over time
- Rolling back changes if a protocol update causes problems in a future paper
- Comparing agent performance before and after protocol changes

---

## Cumulative Learning

Over multiple papers, the outer loop builds an increasingly detailed picture of system
performance:

### Cross-Paper Analysis (when 3+ papers completed)

Agent 15 performs additional analyses:

1. **Trend analysis:** Is each metric's failure rate decreasing over time? (Protocol updates are working?)
2. **Agent performance ranking:** Which agents consistently produce the highest-quality output?
3. **Journal-specific patterns:** Do certain metrics fail more often for certain journals? (e.g., H4 fails more for Lancet because British English triggers different AI word patterns)
4. **Manuscript-type patterns:** Do RCTs have different failure profiles than cohort studies?

### Persistent Memory

The following data persists across papers:

| Data | Storage | Purpose |
|------|---------|---------|
| Iteration logs | `references/iteration-history/` | Inner loop performance data |
| Protocol changelog | `references/protocol-changelog.md` | What changed and why |
| Score history | `references/score-history.json` | Per-paper, per-gate scores |
| User feedback log | `references/user-feedback-log.md` | What the user said at each gate |
| Dispatch frequency | `references/dispatch-frequency.json` | How often each agent was dispatched |

---

## Constraints and Safeguards

1. **User authority:** No protocol change is applied without explicit user approval. Ever.
2. **No self-modification during a paper:** Protocol changes take effect on the NEXT paper,
   not the current one. The current paper uses the protocols that were active at session start.
3. **Rollback capability:** Every change is logged. Previous protocol versions can be restored.
4. **No metric modification:** The outer loop cannot change metric definitions or thresholds.
   H1-H10 and S1-S4 are fixed. Only agent protocols (instructions) are mutable.
5. **Transparency:** The user sees the full diagnosis, evidence, and proposed changes. No
   silent modifications.
6. **Conservative changes:** Each proposed update targets one specific behaviour of one agent.
   Broad rewrites of agent protocols are discouraged — they risk unintended side effects.
7. **Evidence threshold:** Agent 15 must cite specific data (scores, dispatch counts, user
   feedback) for every finding. Speculation without evidence is not permitted.
