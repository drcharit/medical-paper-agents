# Medical Paper Agents

A multi-agent orchestration system for writing publication-quality medical research papers targeting top-tier journals (Lancet, NEJM, JAMA, BMJ, Circulation). The system coordinates 20 specialized agents across a 15-step pipeline with 5 human review gates, automated scoring, claim verification, and iterative refinement -- taking you from raw clinical data and a research question to a submission-ready manuscript package.

## Prerequisites

The following existing skills must be installed. Agent protocols delegate to them at runtime:

- `paper-writer/` -- IMRAD templates, Table 1 script, reference templates
- `literature-review/` -- PRISMA workflow, citation verification
- `scientific-visualization/` -- Style presets, figure export
- `scientific-schematics/` -- CONSORT/PRISMA diagrams, graphical abstracts
- `citation-management/` -- DOI-to-BibTeX, CrossRef lookups
- `pubmed-database/` -- MeSH queries, E-utilities
- `openalex-database/` -- DOI verification, retraction status
- `biorxiv-database/` -- Preprint search
- `bgpt-paper-search/` -- Full-text structured data for claim verification
- `humanizer-academic/` -- AI-word blacklist, detection patterns
- `scientific-writing/` -- IMRAD structure, prose quality rules
- `statsmodels/`, `scikit-survival/`, `scikit-learn/` -- Statistical model execution

## How to Invoke

```
/medical-paper-agents
```

Or say any of these trigger phrases: "write medical paper", "medical manuscript", "journal submission", "write for lancet", "write for nejm", "write for jama", "clinical paper", "research article".

## Modes

### Full Pipeline (default)

Provide raw data, a research question, and optionally a study protocol. The system runs all 15 steps through 5 gates and produces a complete submission package.

### Pre-Submission Inquiry

Say "pre-submission inquiry for [journal]". Runs a lightweight pipeline (Agents 1, 2, 7, 8, 11 only) and produces an abstract, journal-specific panel (Research in Context / Key Points), cover letter, and summary table.

### Revision

Provide peer reviewer comments. Runs Agent 13 (Peer Review Response) and produces a point-by-point response letter with tracked changes.

## Agent Roster

| # | Agent | Primary Function |
|---|---|---|
| 0 | Orchestrator | State machine, dispatch, conflict resolution, gates |
| 0.5 | Triage / Journal Fit | Evaluates study-journal fit, recommends target |
| 1 | Literature & Gap Analysis | Systematic search, evidence synthesis, gap ID |
| 2 | Story Architect | Narrative blueprint (hook, tension, gap, resolution) |
| 3 | Study Design & Methods | Methods section, reporting guideline selection |
| 4 | Statistician | SAP writing (Phase 0) + results verification (Phase 2) |
| 5 | Results Writer | Results section from results_package.json only |
| 6 | Figure Engine | Tables, figures, diagrams with journal styling |
| 7 | Narrative Writer | Introduction, Discussion, journal-specific panels |
| 8 | Abstract & Summary | Journal-specific abstract, keywords |
| 9 | Reference & Citation | Format, verify DOIs, retraction check |
| 10 | Compliance & Ethics | Reporting checklist, IRB, PPI, CRediT, declarations |
| 11 | Editor | Scientific English, cover letter, logical flow |
| 12 | Humanizer | AI-word removal, natural voice (LAST writer) |
| 13 | Peer Review Response | Point-by-point rebuttal, revision tracking |
| 14 | Scoring Agent | Hard metrics (automated) + soft metrics (advisory) |
| 15 | Meta-Evaluator | Post-mortem, agent protocol improvement proposals |
| 16 | Claim Verifier | Reference verification, claim-source alignment |
| 17 | Data Engineer | Ingest, validate, clean, derive populations |
| 18 | Data Analyst | Execute SAP, produce results_package.json |

## Architecture

See [SKILL.md](SKILL.md) for the full architecture specification, including:

- Execution topology (15 steps, 5 parallel, 10 sequential)
- Gate system (5 human review gates with threshold scoring)
- Data pipeline (immutable number chain with SHA-256 hashes)
- Style system (journal-specific YAML profiles)
- Scoring system (10 hard metrics, 4 soft metrics)
- Inner loop (automated iterative refinement, max 5 iterations)
- Outer loop (skill self-improvement via Meta-Evaluator)
- Conflict resolution (6-level priority hierarchy)
- Claim verification (3-step process with retraction checking)

## Repository Structure

```
medical-paper-agents/
├── SKILL.md                     # Full architecture specification
├── README.md                    # This file
├── agents/                      # Agent protocol files (one per agent)
├── styles/                      # Journal YAML profiles (lancet, nejm, jama, bmj, circulation)
├── templates/                   # Project init, scoring, narrative templates
├── references/                  # Conflict resolution rules, metric specs, protocols
├── scripts/                     # Python scripts (data pipeline, scoring, verification)
└── gates/                       # Gate presentation templates
```
