# Post-Inner-Loop Coherence Verification

**Manuscript:** [TITLE]
**Check date:** [DATE]
**Iteration:** [N] (after fix to [METRIC] by Agent [AGENT_NUMBER])

---

## 1. Methods-Results Mirror Structure

_Every analysis described in Methods must have a corresponding result, and vice versa._

| Analysis in Methods | Corresponding Result | Status |
|---|---|---|
| [Primary analysis: Cox PH for primary endpoint] | [Results section, para 1: HR, CI, P-value] | [MATCH / MISSING / EXTRA] |
| [Secondary analysis 1: ...] | [...] | [MATCH / MISSING / EXTRA] |
| [Secondary analysis 2: ...] | [...] | [MATCH / MISSING / EXTRA] |
| [Subgroup analyses: ...] | [...] | [MATCH / MISSING / EXTRA] |
| [Sensitivity analyses: ...] | [...] | [MATCH / MISSING / EXTRA] |

**Order check:** Do analyses appear in the same order in Methods and Results? [YES / NO -- describe discrepancy]

**Missing results:** [List any analyses in Methods without a corresponding result]
**Extra results:** [List any results not described in Methods]

---

## 2. Numbers-Tables-Figures Match

_Every number in the text must match the corresponding table or figure._

| Number in Text | Table/Figure Source | Match? | Notes |
|---|---|---|---|
| [e.g., "28.3% in intervention group"] | [Table 2, column 2, row 1] | [YES / NO] | [e.g., "Table says 28.4%"] |
| [e.g., "HR 0.72"] | [Figure 2 (forest plot)] | [YES / NO] | |
| [e.g., "N=2,400 randomised"] | [CONSORT flow diagram] | [YES / NO] | |
| [e.g., "Median follow-up 3.2 years"] | [Table 1 footnote] | [YES / NO] | |

**Cross-reference with results_package.json:** Run consistency-checker.py
- Output: [PASS / N mismatches found -- see verification/consistency_check.md]

---

## 3. Narrative Thread Integrity

_The story must flow logically from Introduction through Conclusion without breaks._

### Introduction objective -> Methods design

- Does the objective stated in the last paragraph of the Introduction match the study design in Methods? [YES / NO]
- Specific objective: "[quoted from Introduction]"
- Corresponding Methods opening: "[quoted from Methods]"

### Methods design -> Results answer

- Does the primary analysis result directly answer the stated objective? [YES / NO]
- Primary result location: [Results, paragraph N]

### Results -> Discussion interpretation

- Does the Discussion open with the primary finding? [YES / NO]
- First sentence of Discussion: "[quoted]"
- Does this match the primary result in Results? [YES / NO]

### Orphan concept check

- Concepts introduced in Introduction but not addressed in Discussion: [LIST or "None"]
- Concepts appearing in Discussion not introduced earlier: [LIST or "None"]

### Terminology consistency

- Is the primary endpoint named consistently throughout? [YES / NO -- list variants]
- Are interventions named consistently? [YES / NO -- list variants]
- Are patient groups named consistently? [YES / NO -- list variants]

---

## 4. Abstract Reflects Current Manuscript

_After inner loop fixes, the abstract may be out of date._

| Element | Abstract | Manuscript Body | Match? |
|---|---|---|---|
| Sample size (N) | [N from abstract] | [N from Results] | [YES / NO] |
| Primary effect estimate | [HR/OR from abstract] | [HR/OR from Results] | [YES / NO] |
| Confidence interval | [CI from abstract] | [CI from Results] | [YES / NO] |
| P-value | [P from abstract] | [P from Results] | [YES / NO] |
| Conclusion statement | [Interpretation from abstract] | [Conclusion from Discussion] | [YES / NO] |
| Secondary findings mentioned | [List] | [Present in Results?] | [YES / NO] |

**Abstract word count:** [COUNT] / [LIMIT] -- [WITHIN LIMIT / OVER BY N]

---

## Overall Coherence Status

| Check | Status |
|---|---|
| Methods-Results mirror | [PASS / FAIL] |
| Numbers-tables-figures match | [PASS / FAIL] |
| Narrative thread | [PASS / FAIL] |
| Abstract reflects manuscript | [PASS / FAIL] |

**Overall:** [ALL PASS / N issues requiring attention]

**Issues to address in next iteration:**
1. [Specific issue]
2. [Specific issue]
