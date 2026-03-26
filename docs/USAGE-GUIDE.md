# Usage Guide

## Quick Start

### Invoke the skill

Say any of these in Claude Code:
- "write medical paper"
- "write for lancet" / "write for nejm" / "write for jama"
- "clinical paper" / "research article" / "journal submission"

### What you need to provide

| Input | Required? | Description |
|---|---|---|
| Raw data file | Yes | CSV, Excel, SAS, Stata, SPSS, or Parquet |
| Research question | Yes | What clinical question does this study address? |
| Study type | Yes | RCT, cohort, case-control, cross-sectional, systematic review, case report |
| Target journal | Recommended | Lancet, NEJM, JAMA, BMJ, Circulation (or "recommend" for triage) |
| Study protocol | Optional | If available, helps Agent 3 write Methods |
| Author list | Optional | Names + roles for CRediT statement |

---

## Three Modes

### 1. Full Pipeline (default)

Raw data + research question → 15 steps → submission-ready manuscript

This runs all 20 agents through 5 gates. You review and approve at each gate before the next phase begins.

### 2. Pre-Submission Inquiry

Say: "pre-submission inquiry for Lancet"

Runs only Agents 1, 2, 7, 8, 11. Produces:
- Structured abstract in journal format
- Research in Context panel (Lancet) or Key Points (JAMA)
- Cover letter

Tests journal interest before investing in a full manuscript.

### 3. Revision Mode

Say: "respond to peer review" and paste the reviewer comments.

Runs Agent 13 (Peer Review Response). Produces:
- Point-by-point response letter
- Tracked changes in manuscript
- Revision cover letter

---

## What Happens at Each Gate

### Gate 0a: DATA
You see: validation report, flagged impossible values, duplicate count, exclusion counts.
You decide: approve the cleaned data, or request re-cleaning.

### Gate 0b: RESULTS
You see: primary effect estimate + CI + P, key secondary results, assumption check summary.
You decide: approve the results, or request additional analyses.

### Gate 1: PLAN
You see: triage report (journal recommendation), narrative blueprint, methods outline, literature gap.
You decide: approve the plan, change target journal, or redirect the narrative.

### Gate 2: DRAFT
You see: full manuscript draft, score card (10 hard metrics + 4 soft metrics), claim verification report.
If hard score < 85: inner loop runs automatically (max 5 iterations) before presenting to you.
You decide: approve, request section rewrites, or add content.

### Gate 3: FINAL
You see: polished manuscript, cover letter, all declarations, reporting checklist, final score.
If hard score < 90: inner loop runs automatically before presenting.
You decide: approve for submission, or request final adjustments.

---

## Project Directory

When invoked, the system creates:

```
paper-project-YYYY-MM-DD/
├── data/           (raw, clean, analysis datasets)
├── analysis/       (results_package.json, statistical outputs)
├── plan/           (paper plan, narrative blueprint, triage report)
├── draft/          (manuscript sections, figures, tables)
├── supplement/     (protocol, full SAP, extended analyses)
├── final/          (polished manuscript, cover letter, declarations)
├── verification/   (score card, claim verification, consistency check)
├── revisions/      (peer review response, tracked changes)
└── meta/           (score trajectory, agent dispatch log)
```

---

## Supported Manuscript Types

| Type | Reporting Guideline | Auto-Selected |
|---|---|---|
| RCT | CONSORT (25 items) | Yes |
| Cohort / Case-Control / Cross-Sectional | STROBE (22 items) | Yes |
| Systematic Review / Meta-Analysis | PRISMA (27 items) | Yes |
| Case Report | CARE (13 items) | Yes |
| Trial Protocol | SPIRIT (33 items) | Yes |
| Diagnostic Accuracy | STARD (25 items) | Yes |
| Health Economic Evaluation | CHEERS (28 items) | Yes |

---

## Existing Skills Integration

This skill orchestrates (does not replace) these existing skills:

| Skill | Used For |
|---|---|
| `paper-writer` | Templates, references, compilation scripts |
| `literature-review` | PRISMA-compliant systematic searches |
| `scientific-visualization` | Publication-quality figure styling |
| `scientific-schematics` | CONSORT/PRISMA diagrams, graphical abstracts |
| `citation-management` | DOI verification, BibTeX formatting |
| `pubmed-database` | MeSH queries, abstract retrieval |
| `openalex-database` | 240M+ works, citation data |
| `humanizer-academic` | AI detection patterns, word blacklist |
| `statsmodels` / `statistical-analysis` | Statistical model execution |
| `scientific-writing` | IMRAD structure, prose quality |

---

## Tips

- **Start with "recommend"** for target journal if unsure — the Triage Agent will score your study against each journal's editorial priorities.
- **Provide a protocol** if you have one — it dramatically improves the Methods section and reporting checklist.
- **Review the narrative blueprint** carefully at Gate 1 — this is the story arc that guides the entire paper.
- **The score card at Gate 2** tells you exactly what's wrong and which agent will fix it.
- **For null results**, the system automatically activates the null-result narrative template and spin detector.
