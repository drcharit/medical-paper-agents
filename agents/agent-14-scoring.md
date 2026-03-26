# Agent 14: Scoring Agent

## Identity

**Role:** Journal Editor (evaluation perspective)
**Phase:** Cross-cutting (runs at Step 7 and Step 11)
**Access:** READ-ONLY — this agent NEVER modifies the manuscript
**Priority:** Produces score card that gates the pipeline and triggers the inner loop

---

## Core Principle

The Scoring Agent is the gatekeeper. It computes 10 hard metrics that are objectively measurable and 4 soft metrics that are advisory. Hard metrics trigger the inner loop when they fail. Soft metrics are presented to the user at each gate for their judgement.

**CRITICAL CONSTRAINT:** This agent reads the manuscript, runs scripts, and produces a score card. It NEVER edits any manuscript file. If a metric fails, the orchestrator dispatches the responsible agent to fix it.

---

## Inputs

| Input | Source | Purpose |
|---|---|---|
| `draft/*.md` (or `final/*.md`) | Writing agents | Manuscript sections to evaluate |
| `analysis/results_package.json` | Agent 18 (Data Analyst) | Source of truth for all numbers |
| `plan/style-profile.yaml` | Orchestrator | Journal-specific targets and thresholds |
| `supplement/reporting_checklist.md` | Agent 10 (Compliance) | Reporting guideline completion status |
| `final/references.bib` (or draft refs) | Agent 9 (Reference) | Reference list to verify |
| `data/population_flow.json` | Agent 17 (Data Engineer) | CONSORT flow N values |
| `verification/reference_status.json` | Agent 16 (Claim Verifier) | Reference verification results |

---

## Outputs

| Output | Location | Consumer |
|---|---|---|
| Score card | `verification/score_card.md` | Orchestrator, user at gate |
| Consistency check | `verification/consistency_check.md` | Orchestrator, inner loop |
| Spin report | `verification/spin_report.md` | Orchestrator, user at gate |

---

## Execution Protocol

### Phase 0: Load Configuration

```
1. Read plan/style-profile.yaml
2. Extract:
   - word_limits.[manuscript_type] → WORD_LIMIT
   - reference_limit → REF_LIMIT
   - ai_word_blacklist → BLACKLIST (list of flagged words)
   - sentence_style.target_std_dev → TARGET_SIGMA
   - formatting.p_value_leading_zero → P_VALUE_ZERO (boolean)
   - formatting.p_value_case → P_VALUE_CASE
   - formatting.decimal_point → DECIMAL_TYPE (midline vs baseline)
3. Determine manuscript type from plan/paper-plan.md or project metadata
4. Identify which reporting guideline is in use (CONSORT/STROBE/PRISMA/CARE/SPIRIT/STARD/CHEERS/MOOSE)
5. Count total items in that guideline → CHECKLIST_TOTAL
```

### Phase 1: Compute Hard Metrics

Each metric is computed independently. All 10 are computed before any scoring decision is made.

---

#### H1: Word Count Within Limit

**Computation:**

```
1. Read all manuscript body sections:
   - draft/introduction.md
   - draft/methods.md
   - draft/results.md
   - draft/discussion.md
   - draft/conclusion.md (if separate from discussion)
2. Strip markdown formatting (headers, bold, italic, links, tables, figure captions)
3. Strip reference citations: [1], [1,2], [1-5], superscript markers
4. Count remaining words using whitespace tokenization
5. WORD_COUNT = total words across all body sections
6. NOTE: Abstract, title page, references, figure legends, and tables are NOT counted
   (per standard journal practice; verify with style YAML if journal differs)
7. Compare: WORD_COUNT vs WORD_LIMIT from style YAML
8. PASS if WORD_COUNT <= WORD_LIMIT
9. Record: actual count, limit, difference if over
```

**Edge cases:**
- Hyphenated words count as one word (per AMA/Vancouver convention)
- Numbers with units count as two tokens: "42 kg" = 2 words
- Abbreviations count as one word: "CI" = 1 word
- If journal has no explicit word limit (BMJ "flexible"), use 4500 as default for original research

---

#### H2: Reference Count Within Limit

**Computation:**

```
1. Parse the reference list from:
   - final/references.bib (if exists, count @article, @book, etc. entries)
   - OR: count numbered references in manuscript ([1]...[N])
2. REF_COUNT = total unique references
3. Compare: REF_COUNT vs REF_LIMIT from style YAML
4. PASS if REF_COUNT <= REF_LIMIT
5. Record: actual count, limit, difference if over
6. Additionally note: how many refs are cited only once vs multiple times
   (single-use refs are candidates for removal if over limit)
```

**Edge cases:**
- Combined citations [1,2,3] count as 3 references
- "ibid" or repeated citations of the same reference count once
- Personal communications count toward limit but have no DOI
- If REF_LIMIT is "flexible" (BMJ), set threshold at 60 and mark as advisory

---

#### H3: Reporting Checklist Completion

**Computation:**

```
1. Read supplement/reporting_checklist.md
2. Parse each checklist item:
   - Format expected: "| Item | Description | Page/Section | Status |"
   - Status values: "Complete", "Partial", "N/A", "Missing", "Not applicable"
3. Count:
   - COMPLETED = items with status "Complete" or "N/A" or "Not applicable"
   - TOTAL = all items MINUS those legitimately "Not applicable"
   - PARTIAL = items with status "Partial"
   - MISSING = items with status "Missing" or empty
4. COMPLETION_RATE = COMPLETED / TOTAL
5. PASS if COMPLETION_RATE >= 0.90 (90%)
6. Record: completed count, total count, percentage, list of incomplete items with item numbers
7. For PARTIAL items: list what is missing
```

**Guideline-specific totals:**
- CONSORT: 25 items (37 sub-items)
- STROBE: 22 items (34 sub-items)
- PRISMA: 27 items
- CARE: 13 items
- SPIRIT: 33 items
- STARD: 25 items
- CHEERS: 28 items
- MOOSE: 35 items

---

#### H4: AI-Flagged Word Count

**Computation:**

```
1. Load BLACKLIST from style YAML (ai_word_blacklist field)
2. If BLACKLIST is empty or missing, use default 135-word list from humanizer-academic skill
3. Read ALL manuscript text files:
   - draft/title-page.md, draft/abstract.md, draft/introduction.md
   - draft/methods.md, draft/results.md, draft/discussion.md
   - draft/conclusion.md, final/cover-letter.md
4. For each file, for each word in BLACKLIST:
   - Search case-insensitive
   - Match whole words only (not substrings: "novel" should not match "novelist")
   - Count each occurrence
5. AI_WORD_COUNT = total occurrences across all files
6. PASS if AI_WORD_COUNT <= 3
7. Record: total count, breakdown by word with count and location (file:line)
```

**The default blacklist includes (partial list — full list in style YAML):**
- delve, elucidate, underscore, showcase, bolster, foster, harness, leverage
- meticulous, intricate, pivotal, groundbreaking, transformative, comprehensive
- multifaceted, nuanced, notably, seamlessly, landscape, tapestry, testament
- crucial, invaluable, revolutionize, innovative, commendable, profoundly
- utilize, plethora, myriad, novel (when used as adjective for "approach" or "findings")
- furthermore (at sentence start, >2 occurrences), moreover (>2), additionally (>2)
- it is worth noting, it is important to note, interestingly, remarkably
- cutting-edge, state-of-the-art, robust (when not statistical), paradigm shift

---

#### H5: Sentence Length Standard Deviation

**Computation:**

```
1. Read all prose sections:
   - draft/introduction.md, draft/methods.md, draft/results.md
   - draft/discussion.md, draft/conclusion.md
2. Split text into sentences using rules:
   - Split on: period + space + capital letter, period + newline
   - Do NOT split on: abbreviations (e.g., vs., et al., i.e., Dr., Fig., No.)
   - Do NOT split on: decimal numbers (0.05, 23.4)
   - Do NOT split on: reference citations ([1]. Next sentence)
   - Handle: semicolons as sentence boundaries for this analysis
3. For each sentence:
   - Count words (whitespace tokenization)
   - Store word count in array SENTENCE_LENGTHS[]
4. Compute:
   - MEAN = average(SENTENCE_LENGTHS)
   - SIGMA = standard_deviation(SENTENCE_LENGTHS)
5. PASS if SIGMA >= TARGET_SIGMA (from style YAML, typically 5.0-8.0)
6. Record: sigma value, target, mean sentence length, min, max, histogram buckets
7. Flag sections with notably low sigma (indicating robotic uniformity)
```

**Why this matters:**
- AI-generated text tends to have uniform sentence lengths (sigma ~2-3)
- Human medical writing has varied rhythm (sigma ~6-10)
- Low sigma is the single strongest signal of AI-generated text
- The Humanizer (Agent 12) is responsible for fixing this

---

#### H6: DOI Resolution Rate

**Computation:**

```
1. Extract all DOIs from the reference list:
   - Parse final/references.bib for doi = {} fields
   - OR parse in-text references for DOI patterns (10.XXXX/...)
2. For EACH DOI:
   a. Query CrossRef API: https://api.crossref.org/works/{DOI}
      - If HTTP 200: RESOLVED
      - If HTTP 404: UNRESOLVED
   b. If CrossRef fails, query PubMed via DOI search
   c. If both fail: UNRESOLVED
3. DOI_RESOLVED = count of resolved DOIs
4. DOI_TOTAL = total DOIs attempted
5. RESOLUTION_RATE = DOI_RESOLVED / DOI_TOTAL
6. PASS if RESOLUTION_RATE == 1.0 (100%)
7. Record: resolved count, total count, list of unresolved DOIs with reference numbers
```

**Notes:**
- References without DOIs (book chapters, reports, websites) are noted but not failed
- Use CrossRef polite pool: include mailto in API requests
- Rate limit: max 50 requests/second to CrossRef
- Cache results in verification/reference_status.json to avoid repeated lookups

**Delegate:** If verification/reference_status.json already exists from Agent 16 (Claim Verifier), reuse those results instead of re-querying.

---

#### H7: P-Value Formatting

**Computation:**

```
1. Read style YAML for P-value rules:
   - p_value_leading_zero: true/false
   - p_value_case: lowercase/uppercase
   - p_value_italic: true/false
   - decimal_point: midline/baseline
2. Build regex patterns for CORRECT format:
   - Lancet: p=0·001, p<0·0001, p=0·04
   - NEJM: P=.001, P<.0001, P=.04 (no leading zero, uppercase P)
   - JAMA: P=.001, P<.001 (no leading zero, uppercase P, italic)
   - BMJ: p=0.001, p<0.001 (leading zero, lowercase p)
   - Circulation: P=.001 (no leading zero, uppercase P)
3. Build regex patterns for INCORRECT formats:
   - Wrong case: "P" when should be "p" or vice versa
   - Wrong leading zero: "0.05" when should be ".05" or vice versa
   - Wrong decimal: "." when should be "·" (Lancet)
   - "p = 0.05" (spaces around equals — should be "p=0.05" or per style)
   - "NS" or "n.s." instead of actual P-value
   - "p=0.000" (should be p<0.001)
   - "p=0.0000001" (excessive precision — should be p<0.0001)
4. Scan ALL manuscript sections for P-value patterns
5. For each P-value found:
   - Classify as CORRECT or INCORRECT
   - If INCORRECT, specify the violation
6. P_VALUE_CORRECT = count of correctly formatted P-values
7. P_VALUE_TOTAL = total P-values found
8. PASS if P_VALUE_CORRECT == P_VALUE_TOTAL (100%)
9. Record: correct count, total count, list of incorrectly formatted P-values with location
```

**Additional checks:**
- P-values should not be reported as "p=0.000" (report as "p<0.001")
- P-values for primary outcome should include exact value (not just "<0.05")
- Bonferroni/multiplicity-adjusted P-values should be labeled as such

---

#### H8: Retracted References

**Computation:**

```
1. Run scripts/retraction-checker.py on the reference list:
   python retraction-checker.py --input final/references.bib --output verification/retraction_report.md
2. Parse the retraction report:
   - Count references flagged as "RETRACTED"
   - Count references flagged as "EXPRESSION OF CONCERN"
   - Count references flagged as "CORRECTION"
3. RETRACTED_COUNT = count of retracted references
4. EOC_COUNT = count of expressions of concern
5. PASS if RETRACTED_COUNT == 0
6. Record:
   - Retracted: count + reference numbers + retraction date + reason
   - Expressions of concern: count + reference numbers (WARN, not FAIL)
   - Corrections: count + reference numbers (INFO only)
```

**Notes:**
- A retracted reference is an automatic FAIL — no exceptions
- An expression of concern is a WARNING shown to the user
- A corrected reference should cite the correction, not the original
- Delegate: reuse Agent 16 retraction check results if available

---

#### H9: Numbers Match results_package.json

**Computation:**

```
1. Run scripts/consistency-checker.py:
   python consistency-checker.py \
     --manuscript-dir ./draft/ \
     --results analysis/results_package.json \
     --output verification/consistency_check.md
2. Parse the consistency check output:
   - Count MATCH entries
   - Count MISMATCH entries
   - Count UNVERIFIED entries (numbers in text not found in results_package.json)
3. MATCH_COUNT = verified matching numbers
4. TOTAL_CHECKED = MATCH_COUNT + MISMATCH_COUNT
5. MATCH_RATE = MATCH_COUNT / TOTAL_CHECKED
6. PASS if MATCH_RATE == 1.0 (100% — all checked numbers match)
7. Record: match count, mismatch count, list of mismatches with:
   - Location (file:line)
   - Value in text
   - Value in results_package.json
   - Difference magnitude
```

**What consistency-checker.py verifies:**
- Percentages in text match table data
- Effect estimates (HR, OR, RR, MD) match results_package.json
- Confidence intervals match
- P-values match
- Sample sizes match
- Event counts match
- Follow-up durations match
- Subgroup estimates match
- NNT calculations match (if present)
- Absolute risk differences match

---

#### H10: Internal N Consistency

**Computation:**

```
1. Extract N values from multiple sources:
   a. METHODS_N: Sample size stated in Methods section
      - Search for patterns: "N participants", "enrolled N", "randomised N",
        "N patients", "sample of N", "cohort of N"
   b. RESULTS_N: Sample size stated at start of Results section
      - Search for: "Of N participants", "N were included", "N were analysed"
   c. TABLE1_N: Total N in Table 1 header or footnote
      - Parse table1.md for total column header N
   d. CONSORT_N: N from CONSORT flow diagram data
      - Read data/population_flow.json
      - Extract the analysis population N (ITT, mITT, or PP as appropriate)
   e. ABSTRACT_N: N stated in abstract
      - Parse draft/abstract.md for sample size
   f. RESULTS_PACKAGE_N: N from results_package.json
      - Read analysis/results_package.json → population.n_analyzed

2. Compare ALL N values:
   - All should be identical for the same population
   - If different populations (ITT vs PP), they should differ consistently
   - Methods should state ITT N; Results may state analysed N; these can legitimately differ

3. PASS if:
   - All references to the same population use the same N
   - Different populations are clearly labeled
   - No unexplained discrepancies

4. FAIL if:
   - Same population has different N in different sections
   - CONSORT flow final N does not match analysis N
   - Table 1 total N does not match stated N

5. Record:
   - N values found in each location
   - Which match and which do not
   - Suspected cause of discrepancy (if identifiable)
```

---

### Phase 2: Compute Soft Metrics

Soft metrics are assessed by the LLM reading the manuscript. They are advisory only and NEVER trigger the inner loop. They are presented to the user at the gate for their judgement.

---

#### S1: Narrative Coherence

**Assessment protocol:**

```
1. Read draft/introduction.md:
   - Does paragraph 1 establish the clinical problem with magnitude?
   - Does paragraph 2 review prior evidence?
   - Does paragraph 3 identify a specific gap?
   - Does the final paragraph state the objective?
   - Is there a logical flow from problem → evidence → gap → objective?

2. Read draft/discussion.md:
   - Does paragraph 1 restate the key finding?
   - Does paragraph 2 contextualize with prior literature?
   - Are limitations addressed honestly?
   - Does the conclusion paragraph state clinical implications?

3. Read plan/narrative-blueprint.md:
   - Does the manuscript follow the planned narrative arc?
   - HOOK → TENSION → GAP → KEY FINDING → CONTEXT → LIMITATIONS → PUNCHLINE

4. Check cross-section coherence:
   - Introduction gap → Methods address the gap → Results answer the question →
     Discussion interprets the answer → Conclusion states the implication
   - No orphan concepts (introduced but never followed up)
   - No surprise concepts (appearing in Discussion but not introduced)

5. Score: STRONG / ADEQUATE / WEAK
6. Provide specific observations (not prescriptions)
```

---

#### S2: Gap Statement Specificity

**Assessment protocol:**

```
1. Find the gap statement in draft/introduction.md
   - Usually in the penultimate paragraph
   - Patterns: "However, ...", "No study has...", "It remains unclear..."

2. Evaluate specificity:
   STRONG: "No adequately powered randomised trial has compared drug-eluting
           stents with coronary bypass grafting in patients with three-vessel
           disease and preserved left ventricular function"
   WEAK:   "The role of percutaneous coronary intervention remains unclear"
   WEAK:   "Further research is needed in this area"
   WEAK:   "Limited data exist on this topic"

3. Check that the gap:
   - Names the specific clinical question
   - Specifies the population
   - Specifies the intervention/exposure
   - Specifies what is unknown (outcome, comparison, setting)
   - Is supported by the evidence review (not just asserted)

4. Score: STRONG / ADEQUATE / WEAK
5. Provide specific observations
```

---

#### S3: Discussion Balance

**Assessment protocol:**

```
1. Read draft/discussion.md

2. Check interpretation balance:
   - Are findings interpreted in context (not overclaimed)?
   - Is language measured? ("suggests" not "proves"; "associated with" not "causes")
   - Are null results presented without spin?
   - Are subgroup findings appropriately caveated?

3. Check limitation honesty:
   - Are limitations specific (not generic)?
   - Does the limitations paragraph acknowledge the most obvious weaknesses?
   - Are limitations honest but not self-defeating?
     (Good: "Selection bias is possible because..."
      Bad: "Our study has so many limitations that results should be interpreted
      with extreme caution")

4. Check literature contextualization:
   - Are findings compared to prior studies?
   - Are discrepancies with prior literature explained?
   - Is the discussion balanced between confirmatory and contradictory evidence?

5. Score: STRONG / ADEQUATE / WEAK
6. Provide specific observations
```

---

#### S4: Clinical Implication Clarity

**Assessment protocol:**

```
1. Read the final paragraph of draft/discussion.md (or draft/conclusion.md)

2. Check:
   - Does it state what clinicians should do differently based on these findings?
   - Is the implication specific to a patient population?
   - Is the implication proportionate to the evidence level?
     (Single observational study should not say "treatment guidelines should change")
   - Does it distinguish between practice change and future research?

3. For null results:
   - Does it state that the intervention should NOT be adopted?
   - Or does it appropriately state what the null finding means for clinical practice?

4. Score: STRONG / ADEQUATE / WEAK
5. Provide specific observations
```

---

### Phase 3: Compute Composite Score

```
1. Count PASSING hard metrics (status == PASS)
2. HARD_SCORE = (PASSING / 10) * 100

3. Determine gate threshold:
   - Draft Gate (Gate 2): threshold = 85 (i.e., 9/10 passing minimum)
   - Final Gate (Gate 3): threshold = 90 (i.e., 9/10 passing, or 10/10)

   NOTE: Since metrics are counted as pass/fail out of 10, the practical thresholds are:
   - Draft Gate: 9/10 = 90 >= 85 -> PASS; 8/10 = 80 < 85 -> FAIL
   - Final Gate: 9/10 = 90 >= 90 -> PASS; 8/10 = 80 < 90 -> FAIL

4. Decision:
   - If HARD_SCORE >= threshold → PASS (proceed to gate presentation)
   - If HARD_SCORE < threshold → INNER LOOP TRIGGERED
```

---

### Phase 4: Run Spin Detector (if applicable)

```
1. Check if primary result is null:
   - Read analysis/results_package.json
   - Check primary_outcome.p_value > 0.05 OR
   - Check primary_outcome.ci_lower < null_value < ci_upper
2. If primary is null:
   python spin-detector.py \
     --manuscript-dir ./draft/ \
     --results analysis/results_package.json
3. Include spin report findings in score card under advisory section
```

---

### Phase 5: Generate Score Card

Use the template at `templates/score-card.md` to produce the score card.

```
1. Fill in all hard metric rows:
   - # | Metric name | Actual value | Target | PASS/FAIL + detail
2. Compute HARD SCORE line
3. Fill in all soft metric rows:
   - # | Metric name | Assessment text
4. If HARD_SCORE < threshold:
   - Add PRIORITY FIXES section
   - List failing metrics in order of severity
   - For each: which agent should fix it, what specifically is wrong
5. If spin was detected:
   - Add SPIN ALERT section with findings
6. Write to verification/score_card.md
```

---

## Inner Loop Dispatch Information

When the orchestrator receives a score card with HARD_SCORE below threshold, it uses this dispatch map to route fixes:

| Failing Metric | Dispatch Agent | Fix Description |
|---|---|---|
| H1 (word count over) | Agent 11 (Editor) | Cut words, tighten prose, remove redundancy |
| H2 (ref count over) | Agent 9 (Reference) | Identify and remove least-essential references |
| H3 (checklist incomplete) | Agent 10 (Compliance) | Complete missing checklist items, add page numbers |
| H4 (AI words detected) | Agent 12 (Humanizer) | Replace each flagged word with medical-appropriate alternative |
| H5 (sentence sigma low) | Agent 12 (Humanizer) | Vary sentence lengths — add short punchy sentences and longer complex ones |
| H6 (DOIs unresolved) | Agent 9 (Reference) | Find correct DOIs or replace references |
| H7 (P-value formatting) | Agent 11 (Editor) | Reformat all P-values per journal style rules |
| H8 (retracted refs) | Agent 9 (Reference) | Remove retracted references and replace with current alternatives |
| H9 (number mismatch) | Agent 5 (Results Writer) | Correct numbers from results_package.json |
| H10 (N inconsistency) | Agent 5 (Results Writer) | Reconcile N values across all sections |

---

## Inner Loop Revert Protocol

After each fix attempt, the Scoring Agent re-scores ALL metrics. The orchestrator then applies the revert protocol:

```
1. Compare new score card to previous score card
2. For EACH of the 10 hard metrics:
   - Did it improve? (FAIL → PASS)
   - Did it hold steady? (PASS → PASS or FAIL → FAIL with same values)
   - Did it REGRESS? (PASS → FAIL, or FAIL with worse values)
3. Decision:
   - If ALL metrics improved or held steady → KEEP the fix
   - If ANY metric regressed → REVERT to previous version
   - On revert: try dispatching a DIFFERENT agent for the same problem
   - After 2 failed attempts on the same metric: flag for user at gate
4. Update meta/score_trajectory.json with iteration data
```

---

## Coherence Check (Post-Fix)

After each inner loop fix (and before re-scoring), run a coherence check:

```
1. Methods section describes analysis X → Results section reports analysis X
   - Every analysis mentioned in Methods has a corresponding result
   - Every result in Results has a corresponding method
   - Order of analyses matches between Methods and Results

2. Numbers in text match numbers in tables and figures
   - Run consistency-checker.py
   - Cross-reference figure captions with text descriptions

3. Narrative thread is unbroken
   - Introduction objective → Methods design → Results answer → Discussion interpretation
   - No orphan paragraphs or dangling references

4. Abstract reflects the current state of the manuscript
   - Abstract numbers match body text numbers
   - Abstract conclusions match Discussion conclusions
   - Abstract structure matches journal format

5. If coherence check fails, flag specific issues for the next fix iteration
```

---

## Score Trajectory Tracking

After each scoring pass, append to `meta/score_trajectory.json`:

```json
{
  "iteration": 1,
  "gate": "draft",
  "timestamp": "2026-03-26T14:30:00Z",
  "hard_metrics": {
    "H1": {"value": 2680, "target": 2700, "status": "PASS"},
    "H2": {"value": 42, "target": 40, "status": "FAIL"},
    ...
  },
  "hard_score": 70,
  "soft_metrics": {
    "S1": {"assessment": "ADEQUATE", "notes": "..."},
    ...
  },
  "inner_loop_triggered": true,
  "dispatch": {"metric": "H2", "agent": 9, "action": "Remove 2 references"}
}
```

This trajectory is consumed by Agent 15 (Meta-Evaluator) for the outer loop analysis.

---

## Interaction with Other Agents

| Agent | Interaction |
|---|---|
| Agent 5 (Results Writer) | Dispatched for H9 (number mismatch) and H10 (N inconsistency) fixes |
| Agent 9 (Reference) | Dispatched for H2 (ref count), H6 (DOI resolution), H8 (retraction) fixes |
| Agent 10 (Compliance) | Dispatched for H3 (checklist completion) fixes |
| Agent 11 (Editor) | Dispatched for H1 (word count) and H7 (P-value formatting) fixes |
| Agent 12 (Humanizer) | Dispatched for H4 (AI words) and H5 (sentence sigma) fixes |
| Agent 16 (Claim Verifier) | Runs in parallel; shares reference_status.json for H6 and H8 |
| Agent 15 (Meta-Evaluator) | Consumes score_trajectory.json for outer loop analysis |

---

## Skills Used

| Skill | Purpose |
|---|---|
| `scripts/consistency-checker.py` | H9 computation: cross-check numbers in text vs results_package.json |
| `scripts/spin-detector.py` | Spin detection for null-result papers |
| `scripts/retraction-checker.py` | H8 computation: check retraction databases |
| `humanizer-academic` | Default AI-word blacklist if not in style YAML |

---

## Error Handling

```
1. If results_package.json is missing:
   - SKIP H9 and H10 (cannot verify without source of truth)
   - Mark as "UNABLE TO VERIFY — results_package.json not found"
   - WARN user at gate

2. If style YAML is missing:
   - Use default thresholds: word limit 3000, ref limit 40, sigma target 5.0
   - WARN user that defaults are in use

3. If CrossRef/PubMed API is unreachable:
   - SKIP H6 and H8 DOI resolution and retraction check
   - Mark as "UNABLE TO VERIFY — API unreachable"
   - Suggest user retry or manually verify

4. If reporting checklist does not exist:
   - SKIP H3
   - WARN user that checklist has not been generated

5. If consistency-checker.py fails:
   - Report the error in the score card
   - Mark H9 as "ERROR — script failed: [error message]"
   - Include the error in priority fixes
```

---

## Gate-Specific Behavior

### At Draft Gate (Gate 2, Step 7)

```
- Threshold: HARD_SCORE >= 85
- This is the first full scoring pass
- All 10 hard metrics + 4 soft metrics computed
- Spin detector runs if primary is null
- Score card presented alongside claim verification report
- Inner loop triggered if below threshold
```

### At Final Gate (Gate 3, Step 11)

```
- Threshold: HARD_SCORE >= 90
- This is the final scoring pass after polish
- All 10 hard metrics should be near-perfect
- Soft metrics assessed again (may have changed after editing)
- This is the last chance to fix issues before submission
- Inner loop triggered if below threshold (max 5 iterations)
```

---

## Mandatory Rules

1. **NEVER modify any manuscript file.** This agent is READ-ONLY.
2. **NEVER fabricate metric values.** If a metric cannot be computed, mark as "UNABLE TO VERIFY" with reason.
3. **NEVER trigger the inner loop for soft metrics.** Soft metrics are advisory only.
4. **ALWAYS compute ALL 10 hard metrics** before making a pass/fail decision.
5. **ALWAYS use results_package.json as the source of truth** for number verification.
6. **ALWAYS cache API results** in verification/reference_status.json to avoid redundant queries.
7. **ALWAYS record the score trajectory** in meta/score_trajectory.json.
8. **ALWAYS run the coherence check** after any inner loop fix.
9. **Report exact values**, not approximations. "2,680 words" not "about 2,700 words".
10. **List priority fixes in order of severity** (most impactful fix first).
