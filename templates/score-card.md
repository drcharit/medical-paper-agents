# SCORE CARD -- [GATE_NAME] -- Draft v[VERSION]

**Manuscript:** [TITLE]
**Target journal:** [JOURNAL]
**Scoring date:** [DATE]
**Scored by:** Agent 14 (Scoring Agent)

---

## HARD METRICS (automated -- trigger inner loop if below threshold)

| # | Metric | Value | Target | Status | Detail |
|---|---|---|---|---|---|
| H1 | Word count | [WORD_COUNT] | [WORD_LIMIT] | [PASS/FAIL] | [e.g., "52 words over limit"] |
| H2 | Reference count | [REF_COUNT] | [REF_LIMIT] | [PASS/FAIL] | [e.g., "2 over limit"] |
| H3 | Reporting checklist | [COMPLETED]/[TOTAL] ([PERCENT]%) | >= 90% | [PASS/FAIL] | [e.g., "Items 11a, 19 incomplete"] |
| H4 | AI-flagged words | [AI_WORD_COUNT] | <= 3 | [PASS/FAIL] | [e.g., "'comprehensive' x2, 'notably' x3"] |
| H5 | Sentence length sigma | [SIGMA] | >= [TARGET_SIGMA] | [PASS/FAIL] | [e.g., "Too uniform, needs variation"] |
| H6 | DOI resolution | [RESOLVED]/[TOTAL] | 100% | [PASS/FAIL] | [e.g., "Refs 23, 37 unresolved"] |
| H7 | P-value formatting | [CORRECT]/[TOTAL] | 100% | [PASS/FAIL] | [e.g., "Line 45: 'p = 0.05' should be 'p=0.05'"] |
| H8 | Retracted references | [RETRACTED_COUNT] | 0 | [PASS/FAIL] | [e.g., "Ref 14 retracted 2025-11"] |
| H9 | Numbers match results_package | [MATCH_RATE]% | 100% | [PASS/FAIL] | [e.g., "Line 67: '30%' vs 28.3%"] |
| H10 | Internal N consistency | [N_STATUS] | All match | [PASS/FAIL] | [e.g., "Methods: 2400, CONSORT: 2398"] |

**HARD SCORE: [PASSING]/10 PASS ([HARD_SCORE]%)**

**Gate threshold:** [THRESHOLD]% (Draft Gate: 85%, Final Gate: 90%)

**Decision:** [PASS -- proceed to gate presentation / INNER LOOP TRIGGERED]

---

## SOFT METRICS (advisory -- for user review, do NOT trigger inner loop)

| # | Metric | Assessment | Rating |
|---|---|---|---|
| S1 | Narrative coherence | [Assessment of introduction build, discussion opening, story arc integrity] | [STRONG/ADEQUATE/WEAK] |
| S2 | Gap statement specificity | [Assessment of whether gap names specific clinical unknown vs generic "unclear"] | [STRONG/ADEQUATE/WEAK] |
| S3 | Discussion balance | [Assessment of interpretation restraint, limitation honesty, literature context] | [STRONG/ADEQUATE/WEAK] |
| S4 | Clinical implication clarity | [Assessment of whether paper states what clinicians should do differently] | [STRONG/ADEQUATE/WEAK] |

---

## PRIORITY FIXES (if inner loop triggered)

_Listed in order of impact -- fix the highest-priority item first._

| Priority | Metric | Responsible Agent | Specific Action Required |
|---|---|---|---|
| 1 | [H_NUMBER] | Agent [N] ([NAME]) | [Specific fix description] |
| 2 | [H_NUMBER] | Agent [N] ([NAME]) | [Specific fix description] |
| 3 | [H_NUMBER] | Agent [N] ([NAME]) | [Specific fix description] |

---

## SPIN ALERT (if applicable -- null result papers only)

**Primary outcome null:** [Yes/No]
**Spin instances detected:** [COUNT]

| Severity | Pattern | Location | Suggested Fix |
|---|---|---|---|
| [HIGH/MEDIUM/LOW] | [pattern_name] | [file:line] | [suggestion] |

---

## ITERATION HISTORY (if this is not the first pass)

| Iteration | Hard Score | Metric Fixed | Agent Used | Result |
|---|---|---|---|---|
| 1 | [SCORE]% | — | — | Initial scoring |
| 2 | [SCORE]% | [H_NUMBER] | Agent [N] | [Improved/Reverted] |
| 3 | [SCORE]% | [H_NUMBER] | Agent [N] | [Improved/Reverted] |
