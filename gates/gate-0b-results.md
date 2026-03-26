# Gate 0b: Results Gate

## Position in Pipeline

**Follows:** Step 0b — Agent 18 (Data Analyst), with Agent 4 (Statistician) reviewing SAP execution
**Precedes:** Step 0.5 — Agent 0.5 (Triage / Journal Fit)
**Gate Type:** User Approval (no automated scoring threshold)

---

## Purpose

Ensure that the statistical analysis was executed correctly per the SAP, that assumptions
were checked and met (or violations addressed), and that the results are clinically
plausible before any writing begins. Once approved, `results_package.json` becomes the
single immutable source of truth — no writing agent ever computes a number.

---

## Required Artifacts

The orchestrator MUST verify that ALL of the following artifacts exist and are non-empty
before presenting Gate 0b to the user.

| # | Artifact | Path | Description |
|---|----------|------|-------------|
| 1 | Results Package | `analysis/results_package.json` | All effect estimates, CIs, P-values, event counts, structured per schema |
| 2 | Assumption Checks | `analysis/assumption_checks.md` | PH test (Schoenfeld), normality (Shapiro-Wilk), VIF, homoscedasticity results |
| 3 | Statistical Report | `analysis/statistical_report.md` | Human-readable narrative summary of all findings |
| 4 | Table 1 | `analysis/table1.md` | Baseline characteristics by group (with SMD; p-values only if observational) |

### Conditional Artifacts (present if applicable)

| Artifact | Path | When Present |
|----------|------|--------------|
| KM Curves | `figures/km_*.png` | Survival/time-to-event studies |
| Forest Plots | `figures/forest_*.png` | Subgroup analyses or meta-analyses |
| Analysis Code | `analysis/analysis_code.py` | Always generated — reproducible code |
| Descriptive Stats | `analysis/descriptive_stats.md` | Always generated alongside Table 1 |

---

## What to Present to the User

The orchestrator summarises the following in a structured gate review panel:

### Primary Outcome
- **Effect estimate:** [HR / OR / RR / Beta] with exact value
- **95% confidence interval:** [lower, upper]
- **P-value:** exact value
- **Interpretation:** One-sentence plain-language summary
- **Null result flag:** YES / NO (CI includes null value)

### Key Secondary Results
- Bullet list of each secondary endpoint with effect estimate + CI + P
- Number of secondary endpoints analysed: N
- Number reaching statistical significance: N (with multiplicity adjustment noted if applied)

### Subgroup Analyses (if applicable)
- Summary table: subgroup, N per arm, effect estimate, interaction P-value
- Any subgroup with interaction P < 0.05 flagged

### Assumption Check Summary
- **Proportional hazards:** Met / Violated (if Cox model used)
- **Normality:** Met / Violated (if linear model used)
- **Multicollinearity (VIF):** All VIF < 5 / Flag variables with VIF > 5
- **Actions taken for violations:** (e.g., "PH violated for age — stratified Cox model used")

### Missing Data
- **Mechanism assessment:** MCAR / MAR / MNAR
- **Handling method:** Complete case / Multiple imputation (m = N) / Other
- **Sensitivity analysis concordance:** Primary result consistent under alternative approach? YES / NO

### Table 1 Summary
- N per group
- Key imbalances (any SMD > 0.1 highlighted)
- Missingness per key variable

---

## Scoring

**There is no automated scoring threshold at Gate 0b.** The results pipeline does not
produce a score card. The user reviews the statistical output and makes a judgment call.
Agent 4 (Statistician) provides a verification statement confirming the SAP was executed
correctly, which is included in the gate presentation.

### Statistician Verification Statement

Agent 4 reviews Agent 18's analysis and provides:
- Confirmation that the analysis matches the SAP
- Any deviations from the SAP (with justification)
- Assessment of assumption check responses
- Overall statistical quality statement

This statement is presented verbatim to the user at Gate 0b.

---

## User Actions at Gate 0b

| Action | What Happens |
|--------|--------------|
| **Approve** | `results_package.json` is locked (immutable). SHA-256 hash recorded. Pipeline proceeds to Step 0.5 (Triage). All writing agents will read ONLY from this approved package. |
| **Request additional analyses** | User specifies new analyses (e.g., "add a sensitivity analysis excluding site 7", "run a competing risks model"). Agent 18 executes; Agent 4 re-verifies. Gate 0b re-presents. |
| **Modify SAP** | User changes the statistical analysis plan (e.g., "switch primary model from Cox to Fine-Gray"). Agent 4 updates the SAP; Agent 18 re-executes. Gate 0b re-presents. |
| **Flag concerns** | User identifies issues (e.g., "these effect sizes seem implausibly large — check data filtering"). Agent 18 investigates, reports back. Gate 0b re-presents. |

---

## Post-Approval Immutability

Once the user approves Gate 0b:

1. `results_package.json` becomes **immutable**. No agent may modify it.
2. The SHA-256 hash is the reference checksum.
3. Every writing agent (5, 6, 7, 8) reads numbers ONLY from `results_package.json`.
4. Agent 14 (Scoring) uses `consistency-checker.py` to verify manuscript numbers against
   `results_package.json` — metric H9.
5. If the user later discovers a statistical issue (after Gate 0b), the orchestrator must:
   - Roll back to pre-Gate 0b state
   - Re-run Agent 18 (and Agent 4 verification) with corrections
   - Re-present Gate 0b
   - Re-run ALL downstream steps (0.5 onward)
   - Any existing manuscript sections are invalidated

---

## Null Result Detection

At Gate 0b, the orchestrator checks `results_package.json` for null result indicators:

- Primary endpoint P-value > 0.05
- Primary effect CI includes the null value (HR = 1.0, OR = 1.0, difference = 0)

If detected, the orchestrator:
1. Flags this prominently in the gate presentation
2. Informs the user that the null-result narrative template will be activated
3. Alerts Agent 2 (Story Architect) to use the null-result blueprint at Step 2

---

## Orchestrator Checklist

Before presenting Gate 0b, the orchestrator verifies:

- [ ] All 4 required artifacts exist and are non-empty
- [ ] `results_package.json` validates against `templates/results-package-schema.json`
- [ ] Internal N consistency: Table 1 N = CONSORT N from Gate 0a population_flow.json
- [ ] Agent 4 verification statement is present and does not flag critical issues
- [ ] Null result status is determined and flagged if applicable
- [ ] Analysis code (`analysis_code.py`) is present and matches the results
- [ ] Clean data hash in current environment matches the hash approved at Gate 0a
