# Hard and Soft Metrics Specification

## Overview

The scoring system uses two classes of metrics:

- **Hard metrics (H1-H10):** Objectively computable. Binary PASS/FAIL. Trigger the inner
  loop when they fail. Computed by Agent 14 (Scoring Agent) using scripts and pattern matching.
- **Soft metrics (S1-S4):** Require LLM assessment. Advisory only. Presented to the user at
  gates but do NOT trigger automated refinement (avoids the circularity of LLMs grading
  their own work).

### Composite Score Calculation

```
Hard Score = (number of hard metrics PASSING / 10) x 100
```

Examples:
- 10/10 passing = 100
- 9/10 passing = 90
- 8/10 passing = 80

### Threshold Definitions

| Gate | Required Hard Score | Meaning |
|------|---------------------|---------|
| Gate 2 (Draft) | >= 85 | At least 8.5/10 hard metrics must pass (in practice, 9/10 since metrics are binary) |
| Gate 3 (Final) | >= 90 | At least 9/10 hard metrics must pass |

Note: Since each metric is binary (PASS or FAIL), the effective thresholds are:
- Gate 2: 9/10 metrics must pass (85 rounds up to requiring 9)
- Gate 3: 9/10 metrics must pass (90 requires exactly 9)
- A perfect score of 10/10 (100) exceeds both thresholds

---

## Hard Metrics (H1-H10)

### H1: Word Count Within Limit

| Field | Value |
|-------|-------|
| **Metric ID** | H1 |
| **Name** | Word count within journal limit |
| **Responsible Agent** | Agent 11 (Editor) |
| **Computation** | Count words in manuscript body sections (Introduction + Methods + Results + Discussion). Exclude abstract, references, figure legends, tables, declarations. |
| **Target** | <= word limit from active journal style YAML (`word_limits.{manuscript_type}`) |
| **Tool** | `scripts/word-counter.py` or Unix `wc -w` on concatenated sections |
| **Pass Condition** | Word count <= journal word limit |
| **Fail Output** | "FAIL — {actual} words, limit is {target}. Over by {difference}." |
| **Inner Loop Fix** | Agent 11 (Editor) cuts words, tightens prose, removes redundancy |

### H2: Reference Count Within Limit

| Field | Value |
|-------|-------|
| **Metric ID** | H2 |
| **Name** | Reference count within journal limit |
| **Responsible Agent** | Agent 9 (Reference & Citation) |
| **Computation** | Count unique references in `references.bib` or reference list |
| **Target** | <= reference limit from active journal style YAML (`reference_limit`) |
| **Pass Condition** | Reference count <= journal reference limit |
| **Fail Output** | "FAIL — {actual} references, limit is {target}. Over by {difference}." |
| **Inner Loop Fix** | Agent 9 removes least-essential references (those cited only once in non-critical contexts) |

### H3: Reporting Checklist Completion

| Field | Value |
|-------|-------|
| **Metric ID** | H3 |
| **Name** | Reporting checklist completion rate |
| **Responsible Agent** | Agent 10 (Compliance & Ethics) |
| **Computation** | Parse `reporting_checklist.md`. Count items marked as complete (have page number or "N/A" with justification) / total items in the guideline. |
| **Target** | >= 90% of checklist items completed |
| **Tool** | Pattern matching on checklist markdown |
| **Pass Condition** | (completed items / total items) >= 0.90 |
| **Fail Output** | "FAIL — {completed}/{total} items ({percentage}%). Missing: {list of incomplete item numbers}." |
| **Inner Loop Fix** | Agent 10 completes missing checklist items by locating or adding the required content |

### H4: AI-Flagged Word Count

| Field | Value |
|-------|-------|
| **Metric ID** | H4 |
| **Name** | AI-flagged word count |
| **Responsible Agent** | Agent 12 (Humanizer) |
| **Computation** | Scan full manuscript text for words appearing in the `ai_word_blacklist` from the active journal style YAML. Count total occurrences. |
| **Target** | <= 3 total occurrences across the entire manuscript |
| **Tool** | `scripts/ai-word-scanner.py` or regex matching against blacklist |
| **Pass Condition** | Total blacklisted word occurrences <= 3 |
| **Fail Output** | "FAIL — {count} AI-flagged words found: {word} x{n} at line {line}, ..." |
| **Inner Loop Fix** | Agent 12 replaces each flagged word with a natural alternative |

### H5: Sentence Length Standard Deviation

| Field | Value |
|-------|-------|
| **Metric ID** | H5 |
| **Name** | Sentence length standard deviation |
| **Responsible Agent** | Agent 12 (Humanizer) |
| **Computation** | Split manuscript prose into sentences. Count words per sentence. Compute standard deviation (sigma) of word counts. Exclude tables, figure legends, reference list. |
| **Target** | sigma >= 5.0 (indicates natural variation in sentence length) |
| **Tool** | `scripts/sentence-variance.py` |
| **Pass Condition** | Standard deviation of sentence word counts >= 5.0 |
| **Fail Output** | "FAIL — sentence length sigma = {value}. Too uniform. Target >= 5.0." |
| **Inner Loop Fix** | Agent 12 varies sentence lengths: splits long sentences, combines short ones, adds periodic long or short sentences |

### H6: References Resolve via DOI

| Field | Value |
|-------|-------|
| **Metric ID** | H6 |
| **Name** | All references resolve via DOI |
| **Responsible Agent** | Agent 9 (Reference & Citation) |
| **Computation** | For each reference with a DOI, query CrossRef API (`https://api.crossref.org/works/{DOI}`). For references with PMID, query PubMed. Verify HTTP 200 response and metadata match (title, authors, year). |
| **Target** | 100% of references resolve successfully |
| **Tool** | `scripts/retraction-checker.py` (DOI resolution module) |
| **Pass Condition** | All references return valid metadata from CrossRef or PubMed |
| **Fail Output** | "FAIL — {n} references unresolved: ref {id} (DOI: {doi}), ..." |
| **Inner Loop Fix** | Agent 9 corrects DOIs, finds correct DOIs for mistyped references, or replaces unretrievable references with verified alternatives |

### H7: P-Values Correctly Formatted

| Field | Value |
|-------|-------|
| **Metric ID** | H7 |
| **Name** | P-value formatting compliance |
| **Responsible Agent** | Agent 11 (Editor) |
| **Computation** | Extract all P-value strings from manuscript using regex. Check each against the active journal style YAML rules: leading zero (yes/no), case (lowercase p), decimal type (midline dot for Lancet, baseline for others), spacing. |
| **Target** | 100% of P-values correctly formatted |
| **Tool** | Regex pattern matching against journal-specific rules |
| **Pass Condition** | Every P-value in the manuscript matches the journal format |
| **Fail Output** | "FAIL — {n} incorrectly formatted P-values: line {n}: '{found}' should be '{expected}', ..." |
| **Inner Loop Fix** | Agent 11 reformats all P-values per journal style |

### H8: No Retracted References

| Field | Value |
|-------|-------|
| **Metric ID** | H8 |
| **Name** | No retracted references |
| **Responsible Agent** | Agent 9 (Reference & Citation) |
| **Computation** | For each reference, query CrossRef for "update-to" entries of type "retraction". Query Retraction Watch database if available. Check PubMed for retraction notices. |
| **Target** | 0 retracted references |
| **Tool** | `scripts/retraction-checker.py` (retraction module) |
| **Pass Condition** | No reference in the manuscript has been retracted |
| **Fail Output** | "FAIL — {n} retracted reference(s): ref {id} '{title}' retracted {date}." |
| **Inner Loop Fix** | Agent 9 replaces retracted references with non-retracted alternatives that support the same claim |

### H9: Numbers Match results_package.json

| Field | Value |
|-------|-------|
| **Metric ID** | H9 |
| **Name** | Manuscript numbers match results_package.json |
| **Responsible Agent** | Agent 5 (Results Writer) |
| **Computation** | Extract all numerical claims from the manuscript (effect estimates, CIs, P-values, percentages, counts). Cross-reference each against `results_package.json`. Flag any mismatch. |
| **Target** | 100% match between manuscript numbers and results_package.json |
| **Tool** | `scripts/consistency-checker.py` |
| **Pass Condition** | Every number in the manuscript that corresponds to an entry in results_package.json matches exactly |
| **Fail Output** | "FAIL — {n} mismatches: line {n}: manuscript says '{found}', results_package says '{expected}', ..." |
| **Inner Loop Fix** | Agent 5 corrects the manuscript text to match results_package.json (the package is immutable; the text is corrected) |

### H10: Internal N Consistency

| Field | Value |
|-------|-------|
| **Metric ID** | H10 |
| **Name** | Internal N consistency across sections |
| **Responsible Agent** | Agent 14 (Scoring Agent — flags), Agent 5 (Results Writer — fixes) |
| **Computation** | Extract the stated N (sample size / population count) from: Methods section, Results section (first paragraph), Table 1 header, CONSORT/flow diagram, Abstract. All must be identical for the same population. |
| **Target** | All N values match for each defined population |
| **Tool** | `scripts/consistency-checker.py` (N-consistency module) |
| **Pass Condition** | Methods N = Results N = Table 1 N = CONSORT N = Abstract N for each population |
| **Fail Output** | "FAIL — N mismatch: Methods={n1}, Results={n2}, Table 1={n3}, CONSORT={n4}." |
| **Inner Loop Fix** | Agent 5 reconciles N values, using population_flow.json as the source of truth |

---

## Soft Metrics (S1-S4)

Soft metrics are assessed by Agent 14 using LLM judgment. They are presented at gates
as advisory text. They do NOT trigger the inner loop and do NOT contribute to the hard
score. The user considers them alongside the hard metrics when deciding whether to approve.

### S1: Narrative Coherence

| Field | Value |
|-------|-------|
| **Metric ID** | S1 |
| **Name** | Narrative coherence |
| **Assessment Method** | Agent 14 reads Introduction and Discussion as a pair |
| **Evaluation Criteria** | (1) Does Introduction build logically from known evidence to the gap? (2) Does Discussion open with the key finding (not a restatement of background)? (3) Is the story arc from Agent 2's blueprint preserved? (4) Does the Abstract reflect the current narrative? |
| **Rubric** | **Strong:** Clear arc from evidence to gap to finding to implication. **Adequate:** Arc present but some sections feel disconnected. **Weak:** No clear arc; Discussion opens with background; gap statement is buried. |
| **Output Format** | 2-3 sentence assessment with specific suggestions |

### S2: Gap Statement Specificity

| Field | Value |
|-------|-------|
| **Metric ID** | S2 |
| **Name** | Gap statement specificity |
| **Assessment Method** | Agent 14 extracts the gap statement from the Introduction |
| **Evaluation Criteria** | (1) Does the gap name a specific clinical unknown? (2) Is it more specific than "remains unclear" or "is not well understood"? (3) Does it logically follow from the evidence presented? (4) Does the study directly address this gap? |
| **Rubric** | **Strong:** "No randomised trial has compared drug X with drug Y in patients with HFrEF and CKD stage 3b." **Adequate:** "The comparative effectiveness of drug X vs drug Y is uncertain." **Weak:** "The role of drug X remains unclear." |
| **Output Format** | Assessment of gap statement quality with the exact gap statement quoted |

### S3: Discussion Balance

| Field | Value |
|-------|-------|
| **Metric ID** | S3 |
| **Name** | Discussion balance |
| **Assessment Method** | Agent 14 reads the Discussion section |
| **Evaluation Criteria** | (1) Are limitations honest and specific (not generic)? (2) Are limitations not self-defeating (don't undermine the entire study)? (3) Is interpretation proportionate to the evidence (no overclaiming)? (4) For null results: is there spin? (5) Are strengths mentioned without being promotional? |
| **Rubric** | **Strong:** Specific limitations acknowledged; interpretation is measured; no spin. **Adequate:** Limitations present but somewhat generic; interpretation slightly strong. **Weak:** Limitations are self-defeating OR absent; interpretation overclaims; spin detected. |
| **Output Format** | Assessment with specific examples of balance or imbalance |

### S4: Clinical Implication Clarity

| Field | Value |
|-------|-------|
| **Metric ID** | S4 |
| **Name** | Clinical implication clarity |
| **Assessment Method** | Agent 14 reads the final paragraph of the Discussion and the Abstract conclusion |
| **Evaluation Criteria** | (1) Does the paper state what clinicians should do differently based on these findings? (2) Is the implication specific to a patient population and clinical context? (3) Is it proportionate to the evidence level? (4) For null results: does it state what clinicians should NOT do? |
| **Rubric** | **Strong:** "These findings support initiating SGLT2 inhibitors in patients with HFrEF regardless of diabetes status, with NNT of 21 over 2 years." **Adequate:** "SGLT2 inhibitors may benefit patients with HFrEF." **Weak:** "Further research is needed." (alone, with no actionable statement) |
| **Output Format** | Assessment with the exact implication statement quoted |

---

## Score Card Format

See SKILL.md section 7 for the complete score card template. The score card includes:

1. Header: Gate name, draft version number, date
2. Hard metrics table: all 10 metrics with value, target, PASS/FAIL
3. Hard score: N/10 PASS, with threshold status (PASS/INNER LOOP TRIGGERED)
4. Soft metrics table: all 4 metrics with LLM assessment text
5. Inner loop history (if applicable): iteration count, fixes applied, score trajectory
6. Comparison with previous gate score (at Gate 3, compare with Gate 2)

---

## Metric Evolution Across Gates

| Metric | Gate 2 (Draft) Expectation | Gate 3 (Final) Expectation |
|--------|----------------------------|----------------------------|
| H1 | May be slightly over; Editor has not polished yet | Must be within limit after editing |
| H2 | May be over; Reference agent has not pruned yet | Must be within limit after pruning |
| H3 | May be incomplete; Compliance has not finished | Must be >= 90% after compliance pass |
| H4 | Expect some AI words before Humanizer's final pass | Must be <= 3 after Humanizer |
| H5 | Expect moderate variance before Humanizer | Must be >= 5.0 after Humanizer |
| H6 | All should resolve; early catch of bad DOIs | Must be 100% after Reference agent |
| H7 | Should be correct from writing phase | Must be 100% after Editor |
| H8 | Should be 0; early catch of retractions | Must be 0 |
| H9 | Must match; immutable chain from Phase 0 | Must match; no excuse for drift |
| H10 | Must match; flow numbers locked since Gate 0a | Must match; absolute requirement |
