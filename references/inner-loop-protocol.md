# Inner Loop Protocol: Iterative Refinement

## Overview

The inner loop is the automated self-correction mechanism that runs when the hard metric
score falls below the gate threshold. It identifies failing metrics, dispatches the
responsible agent to fix each issue, re-scores, and checks for regressions. The loop
continues until the threshold is met or the maximum iteration count is reached.

### When It Triggers

| Gate | Threshold | Trigger Condition |
|------|-----------|-------------------|
| Gate 2 (Draft) | Hard score >= 85 | Score < 85 after Agent 14 scores the draft |
| Gate 3 (Final) | Hard score >= 90 | Score < 90 after Agent 14 scores the final manuscript |

The inner loop does NOT run at Gates 0a, 0b, or 1 (those gates have no automated scoring).

### Maximum Iterations

**5 iterations per gate invocation.** If the threshold is not met after 5 iterations,
the best-scoring version is presented to the user with a warning.

---

## Step-by-Step Process

### Step 1: SCORE

Agent 14 (Scoring Agent) computes all 10 hard metrics.

- Input: current manuscript artifacts
- Output: `verification/score_card.md` with PASS/FAIL for each metric
- Compute: hard score = (passing metrics / 10) x 100

Record the score in the iteration log:
```
iteration_log[iteration_number] = {
  score: N,
  metrics: { H1: PASS/FAIL, H2: PASS/FAIL, ... },
  version_snapshot: "draft_v{N}"
}
```

### Step 2: IDENTIFY

Find the worst-failing metric. Priority order for dispatch when multiple metrics fail:

1. **H9 (Numbers match)** — highest priority because number errors are the most damaging
2. **H10 (N consistency)** — related to H9, fundamental data integrity
3. **H8 (Retracted refs)** — credibility issue, must fix immediately
4. **H6 (DOI resolve)** — reference integrity
5. **H3 (Checklist completion)** — compliance requirement
6. **H1 (Word count)** — structural issue
7. **H2 (Ref count)** — structural issue
8. **H7 (P-value format)** — formatting issue
9. **H4 (AI words)** — style issue
10. **H5 (Sentence variance)** — style issue

If multiple metrics fail, fix ONE metric per iteration (the highest-priority failing metric).
This prevents cascading changes and makes regression detection possible.

### Step 3: DISPATCH

Load the responsible agent's protocol and dispatch the fix.

#### Metric-to-Agent Dispatch Map

| Metric Failed | Agent Dispatched | Fix Action |
|---|---|---|
| H1 (Word count over limit) | Agent 11 (Editor) | Cut words: remove redundancy, tighten prose, eliminate filler. Preserve all data and claims. |
| H2 (Reference count over limit) | Agent 9 (Reference & Citation) | Remove least-essential references: those cited only once in non-critical contexts. Merge citations where possible. |
| H3 (Checklist incomplete) | Agent 10 (Compliance & Ethics) | Complete missing checklist items: locate existing content and add page numbers, or flag content that must be written. |
| H4 (AI words over limit) | Agent 12 (Humanizer) | Replace each flagged word with a natural alternative. Verify replacements do not introduce new blacklisted words. |
| H5 (Sentence variance too low) | Agent 12 (Humanizer) | Vary sentence lengths: split overlong sentences, combine choppy sequences, introduce periodic long/short constructions. |
| H6 (DOIs unresolved) | Agent 9 (Reference & Citation) | Fix DOIs: correct typos, look up correct DOI via title search on CrossRef, or replace unretrievable references. |
| H7 (P-value format wrong) | Agent 11 (Editor) | Reformat all P-values per journal style YAML: leading zero, case, decimal character, spacing. |
| H8 (Retracted references) | Agent 9 (Reference & Citation) | Replace retracted references with non-retracted alternatives that support the same claim. If no alternative exists, remove the claim or flag for user. |
| H9 (Numbers mismatch) | Agent 5 (Results Writer) | Correct manuscript text to match results_package.json. The package is immutable; only the text is changed. |
| H10 (N inconsistency) | Agent 5 (Results Writer) | Reconcile N values across sections using population_flow.json as the authoritative source. |

#### Dispatch Instruction Format

The orchestrator provides the dispatched agent with:
```
FIX REQUEST — Inner Loop Iteration {N}
Metric: {metric_id} — {metric_name}
Status: FAIL
Current value: {value}
Target: {target}
Details: {fail_output from scoring}
Instruction: Fix this specific issue. Do not modify any other section.
Constraint: Preserve all other metrics. Do not introduce new failures.
```

### Step 4: FIX

The dispatched agent produces a targeted fix. The agent:
- Reads only the relevant section(s)
- Makes the minimum change necessary to pass the metric
- Does NOT rewrite unrelated content
- Preserves the narrative arc and all other metrics

Output: updated section file(s) with changes tracked.

### Step 5: RE-SCORE

Agent 14 re-scores ALL 10 hard metrics on the updated manuscript.

This is a full re-score, not just the fixed metric, because a fix to one metric can
affect others (e.g., cutting words for H1 might break a number reference for H9).

### Step 6: COMPARE

Compare the new score against the previous iteration:

```
For each metric H1-H10:
  if new_status == FAIL and previous_status == PASS:
    REGRESSION DETECTED on {metric_id}
```

#### Decision Logic

| Outcome | Action |
|---------|--------|
| Target metric now PASSES, no regressions | **KEEP** the fix. Record in iteration log. Proceed to Step 7. |
| Target metric now PASSES, but another metric REGRESSED | **REVERT** the fix. Trigger revert protocol (see below). |
| Target metric still FAILS, no regressions | **KEEP** the fix (partial improvement). Proceed to Step 7. |
| Target metric still FAILS, and another metric REGRESSED | **REVERT** the fix. Trigger revert protocol. |

### Step 7: COHERENCE CHECK

After keeping a fix, run `scripts/consistency-checker.py` to verify:

1. **Methods-Results mirror:** Does the Results section structure still mirror the Methods section? (Each method described should have a corresponding result.)
2. **Numbers-Tables-Figures match:** Do numbers in text match corresponding table cells and figure annotations?
3. **Narrative thread:** Is the story arc (from Agent 2's blueprint) still intact? Introduction gap -> Results answer -> Discussion interpretation chain unbroken?
4. **Abstract currency:** Does the Abstract still reflect the current manuscript content? (Abstracts can become stale after section edits.)

If a coherence issue is detected:
- Log the issue
- It becomes a secondary fix target in the next iteration (if the primary metric is resolved)
- Coherence issues do NOT count as hard metric failures but are flagged in the iteration log

### Step 8: REPEAT

Return to Step 1. Continue until a stop condition is met.

---

## Revert Protocol

When a fix causes regression in any metric:

### Immediate Actions
1. **Discard** the fix entirely — restore the previous version of all modified files
2. **Log** the revert: metric targeted, agent dispatched, regression caused, version restored

### Second Attempt
3. **Retry** with a DIFFERENT approach:
   - If Agent 11 was dispatched for H1 and caused H9 regression: re-dispatch Agent 11 with
     explicit instruction "cut words ONLY from Introduction and Discussion, not Results"
   - If Agent 9 was dispatched for H2 and caused H6 regression: re-dispatch Agent 9 with
     "remove references that do not have DOIs rather than those with DOIs"

### Escalation
4. If the same metric causes regression on 2 consecutive attempts:
   - Mark the metric as **STUCK**
   - Flag it for user review at the gate presentation
   - Move to the next-highest-priority failing metric
   - Include in gate warning: "Metric {id} could not be fixed without regressing {other_id}.
     Manual intervention recommended."

---

## Stop Conditions

The inner loop terminates when ANY of these conditions is met:

| Condition | Action |
|-----------|--------|
| Hard score >= threshold (85 or 90) | Present current version at gate. Inner loop SUCCESS. |
| All 10 metrics PASS | Present current version at gate. Perfect score. |
| 5 iterations reached | Present BEST-SCORING version at gate. Inner loop EXHAUSTED. |
| All failing metrics are STUCK | Present best version. All remaining failures require user input. |

### Best Version Selection

When the loop is exhausted, the orchestrator selects the version with the highest hard
score from all iterations (including the initial pre-loop version). If multiple versions
tie, the latest is preferred.

---

## Presentation After Exhaustion

If the inner loop does not reach the threshold after 5 iterations, the gate presentation
includes an additional section:

```markdown
## Inner Loop Report

### Summary
- **Iterations run:** {N}
- **Starting score:** {initial}/10
- **Best score achieved:** {best}/10 (iteration {M})
- **Final score:** {final}/10
- **Threshold required:** {threshold}

### Iteration History
| Iter | Score | Metric Targeted | Agent | Result | Regressions |
|------|-------|-----------------|-------|--------|-------------|
| 1    | 5/10  | H9 (numbers)    | Ag 5  | Fixed  | None        |
| 2    | 6/10  | H8 (retracted)  | Ag 9  | Fixed  | None        |
| ...  | ...   | ...             | ...   | ...    | ...         |

### Unresolved Failures
| Metric | Current Value | Target | Why Unresolved |
|--------|---------------|--------|----------------|
| H4     | 5 AI words    | <= 3   | STUCK — fixes regressed H5 |
| ...    | ...           | ...    | ...            |

### Recommendation
The following metrics require your input: {list}.
```

---

## Constraints and Safeguards

1. **Immutability:** The inner loop NEVER modifies `results_package.json`, `population_flow.json`,
   or approved clean data. Only manuscript text, references, and checklist are mutable.
2. **One fix per iteration:** Only one metric is targeted per iteration to isolate effects.
3. **Full re-score:** All metrics are re-scored after every fix, not just the targeted metric.
4. **No soft metric optimization:** Soft metrics (S1-S4) are never targeted by the inner loop.
5. **Agent protocol adherence:** Dispatched agents follow their full protocol — they are not
   given shortcuts or reduced instructions during the inner loop.
6. **Version control:** Every iteration's manuscript state is preserved so any version can be
   restored. The orchestrator maintains a stack of snapshots.
7. **Transparency:** The complete iteration log is presented to the user at the gate. No
   inner loop activity is hidden.
