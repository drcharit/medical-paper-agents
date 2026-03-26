# Gate 3: Final Gate

## Position in Pipeline

**Follows:** Steps 8-11 — Agent 9 (Reference) || Agent 10 (Compliance), Agent 11 (Editor), Agent 12 (Humanizer), Agent 14 (Scoring) || Agent 16 (Claim Verifier)
**Precedes:** Submission-ready package delivery (and optionally Step 12 — Agent 13 for peer review response)
**Gate Type:** Automated Threshold + User Approval
**Threshold:** Hard score >= 90 (at least 9 out of 10 hard metrics passing)

---

## Purpose

Final quality check before the manuscript package is declared submission-ready. This gate
has the highest threshold because it is the last automated checkpoint. The package leaving
this gate goes directly to a journal editor. Every reference must resolve, every number
must match, every checklist item must be complete, and the prose must be free of detectable
AI artefacts.

---

## Required Artifacts

The orchestrator MUST verify that ALL of the following artifacts exist and are non-empty
before scoring and presenting Gate 3.

### Manuscript
| # | Artifact | Path | Description |
|---|----------|------|-------------|
| 1 | Polished Manuscript | `final/manuscript.md` | Complete, polished manuscript (all sections, post-humanizer) |
| 2 | Abstract | `final/abstract.md` | Journal-formatted abstract (final version) |
| 3 | Journal-Specific Panels | `final/{panel_name}.md` | Research in Context / Key Points / etc. |

### Submission Materials
| # | Artifact | Path | Description |
|---|----------|------|-------------|
| 4 | Cover Letter | `final/cover_letter.md` | Addressed to editor, summarises contribution |
| 5 | Ethics Declaration | `final/declarations/ethics.md` | IRB/ethics committee approval statement |
| 6 | COI Declaration | `final/declarations/coi.md` | Conflict of interest disclosures for all authors |
| 7 | Funding Statement | `final/declarations/funding.md` | Funding sources and role of funder |
| 8 | PPI Statement | `final/declarations/ppi.md` | Patient and public involvement statement |
| 9 | CRediT Statement | `final/declarations/credit.md` | Author contribution taxonomy |
| 10 | Data Sharing Statement | `final/declarations/data_sharing.md` | Data availability and access |
| 11 | AI Disclosure | `final/declarations/ai_disclosure.md` | AI tool usage disclosure per ICMJE |

### Quality Assurance
| # | Artifact | Path | Description |
|---|----------|------|-------------|
| 12 | Reporting Checklist | `final/reporting_checklist.md` | CONSORT/STROBE/PRISMA/CARE with page numbers filled |
| 13 | References | `final/references.bib` | Complete reference list in BibTeX (formatted per journal style) |
| 14 | Final Score Card | `verification/final_score_card.md` | 10 hard + 4 soft metrics, final pass |
| 15 | Final Claim Verification | `verification/final_claim_verification_report.md` | Final reference + claim check |

### Figures and Tables
| # | Artifact | Path | Description |
|---|----------|------|-------------|
| 16 | All Figures | `final/figures/` | Publication-quality, journal-styled |
| 17 | All Tables | `final/tables/` | Formatted per journal requirements |

---

## Automated Scoring (Inner Loop Trigger)

### Threshold

**Hard score >= 90** means at least 9 out of 10 hard metrics must PASS.

This is stricter than Gate 2 (>= 85) because the final package must be submission-ready.

### Inner Loop Activation

If the hard score is BELOW 90 after Agent 14 scores the final manuscript:

1. The inner loop is triggered automatically (see `references/inner-loop-protocol.md`)
2. The inner loop runs for up to 5 iterations
3. After each iteration, the score is recomputed
4. The loop stops when: score >= 90, OR 5 iterations exhausted, OR all metrics pass

If the score reaches >= 90, the package proceeds to gate presentation.

If 5 iterations are exhausted without reaching 90, the BEST-SCORING version is presented
to the user with a clear warning:

```
WARNING: Automated refinement did not reach the Final Gate threshold.
Best score achieved: [N]/10 after [M] iterations.
Remaining failures: [list of failing metrics with details].
The manuscript may require manual intervention before submission.
```

### Critical Metrics at Final Gate

Certain metrics are especially important at this stage:

| Metric | Why Critical at Final Gate |
|--------|---------------------------|
| H6 (DOI resolution) | Editors will reject if references don't resolve |
| H8 (No retractions) | Citing retracted work is a serious credibility issue |
| H9 (Numbers match) | Inconsistent numbers trigger desk rejection |
| H10 (N consistency) | Reviewers immediately check N across sections |

If any of these 4 metrics fail after inner loop exhaustion, the orchestrator flags them
as **CRITICAL UNRESOLVED** in the gate presentation.

---

## What to Present to the User

### Complete Submission Package
All artifacts listed above, assembled and cross-linked. The user should be able to take
this package and submit it directly to the journal submission system.

### Final Score Card
- Hard metrics summary: N/10 passing
- Each metric with value, target, status
- Comparison with Gate 2 score (improvement trajectory)
- Soft metrics with assessment text
- Inner loop summary (if triggered)

### Final Claim Verification Report
- Total claims: N
- Verified: N / Plausible: N / Unsupported: N / Contradicted: N
- All references resolved: YES / NO (list failures)
- Retracted references: 0 / N (list any found)
- Comparison with Gate 2 verification (any new issues)

### Submission Readiness Checklist
- [ ] Manuscript word count within journal limit
- [ ] Reference count within journal limit
- [ ] Figure/table count within journal limit
- [ ] All reporting checklist items completed with page numbers
- [ ] Cover letter addressed and complete
- [ ] All declarations present
- [ ] AI disclosure complete per ICMJE
- [ ] Abstract format matches journal requirements
- [ ] Journal-specific panels present and complete
- [ ] References formatted per journal style (Vancouver/AMA)

---

## User Actions at Gate 3

| Action | What Happens |
|--------|--------------|
| **Approve for submission** | Package is declared submission-ready. All files are in `final/`. The orchestrator generates a submission summary with file manifest and checksums. Pipeline complete. |
| **Request adjustments** | User specifies changes (e.g., "soften the clinical implication", "add co-author X to CRediT"). Orchestrator dispatches appropriate agents. Rescored. Gate 3 re-presents. |
| **Downgrade to Draft Gate** | User decides major changes are needed (e.g., "rewrite Discussion entirely"). Pipeline rolls back to Gate 2 state. Agents 5-8 re-engaged. |
| **Change target journal** | User decides to target a different journal. Orchestrator loads new style YAML. Significant rework triggered: formatting, abstract structure, special panels, word limits. Effectively re-enters at Gate 1 for re-planning. |
| **Override metric failure** | User explicitly accepts a failing metric. Metric marked as user-overridden. |

---

## Post-Approval: Submission Package

When the user approves Gate 3, the orchestrator produces:

### File Manifest
```
final/
  manuscript.md           — Main manuscript
  abstract.md             — Formatted abstract
  cover_letter.md         — Cover letter to editor
  references.bib          — Reference list
  reporting_checklist.md  — Completed checklist with page numbers
  {journal_panel}.md      — Journal-specific panel(s)
  declarations/
    ethics.md, coi.md, funding.md, ppi.md, credit.md,
    data_sharing.md, ai_disclosure.md
  figures/                — All figures (print-quality)
  tables/                 — All tables
supplement/
  protocol.md, full_sap.md, extended_tables/, sensitivity_analyses/,
  additional_figures/, analysis_code.py
```

### Checksums
SHA-256 hash of each file in the package, stored in `final/manifest.json`.

---

## Orchestrator Checklist

Before presenting Gate 3, the orchestrator verifies:

- [ ] All required artifacts exist and are non-empty (17 artifact groups)
- [ ] Agent 14 has scored the final manuscript and final_score_card.md is complete
- [ ] Agent 16 has verified claims and final_claim_verification_report.md is complete
- [ ] If hard score < 90: inner loop has been executed (up to 5 iterations)
- [ ] Best-scoring version is presented
- [ ] Agent 12 (Humanizer) was the LAST agent to touch prose — no agent wrote after it
- [ ] Clean data hash matches Gate 0a; results_package hash matches Gate 0b
- [ ] Reporting checklist has page numbers filled (not placeholders)
- [ ] Cover letter is addressed to the correct journal editor
- [ ] All declarations are present and non-boilerplate
- [ ] references.bib is formatted per the active journal style
- [ ] No CRITICAL UNRESOLVED metrics (H6, H8, H9, H10) — or user has been warned
