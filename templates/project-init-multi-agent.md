# Project Initialization Template: Multi-Agent Medical Paper System

This template defines the complete directory structure, initialization checklist, required user inputs, and style profile selection logic for a new medical paper project.

---

## Directory Structure

When the orchestrator initializes a new project, create the following directory tree. The root directory name follows the pattern `paper-project-YYYY-MM-DD`.

```
paper-project-YYYY-MM-DD/
│
├── data/
│   ├── raw/                         # Original data files -- NEVER modified after ingest
│   ├── clean/                       # Validated, cleaned datasets
│   ├── analysis/                    # Analysis-ready datasets per population (ITT, PP, safety)
│   ├── data_profile.md              # N rows, N columns, variable types, distributions
│   ├── data_dictionary.json         # Variable names, types, labels, coding schemes
│   ├── validation_report.md         # Impossible values, duplicates, inconsistencies
│   ├── cleaning_log.md              # Every transformation with before/after values
│   └── data_hashes.json             # SHA-256 hashes of raw and clean data files
│
├── analysis/
│   ├── statistical_plan.md          # Statistical analysis plan (verified by Statistician)
│   ├── results_package.json         # THE source of truth for ALL numbers in the paper
│   ├── analysis_code.py             # Reproducible analysis code
│   ├── assumption_checks.md         # PH, normality, VIF, homoscedasticity results
│   ├── statistical_report.md        # Human-readable summary of all findings
│   ├── primary_results.json         # Primary outcome analysis output
│   ├── secondary_results.json       # Secondary outcomes analysis output
│   ├── subgroup_results.json        # Subgroup analyses with interaction tests
│   ├── sensitivity_results.json     # Sensitivity and robustness analyses
│   ├── table1.md                    # Baseline characteristics table
│   └── figures/                     # All statistical figures (KM curves, forest plots, etc.)
│
├── plan/
│   ├── paper-plan.md                # Assembled plan document (Gate 1 artifact)
│   ├── narrative-blueprint.md       # Story arc: hook, tension, gap, resolution, punchline
│   ├── literature-matrix.md         # Evidence landscape summary with gap statement
│   ├── triage-report.md             # Journal fit assessment with per-journal scores
│   ├── reference_library.json       # All references collected during literature review
│   └── style-profile.yaml           # Copy of the loaded journal YAML configuration
│
├── draft/
│   ├── title-page.md                # Title, authors, affiliations, corresponding author
│   ├── abstract.md                  # Journal-formatted structured abstract
│   ├── introduction.md              # Introduction section
│   ├── methods.md                   # Methods section
│   ├── results.md                   # Results section (reads ONLY from results_package.json)
│   ├── discussion.md                # Discussion section
│   ├── conclusion.md                # Conclusion (if journal requires separate section)
│   ├── figures/                     # Publication-quality figures
│   └── tables/                      # Publication-quality tables
│
├── supplement/
│   ├── protocol.md                  # Full study protocol
│   ├── full_sap.md                  # Complete statistical analysis plan (unabbreviated)
│   ├── extended_tables/             # Tables too large for main text
│   ├── sensitivity_analyses/        # Alternative models, robustness checks
│   ├── additional_figures/          # Figures not included in main text
│   ├── reporting_checklist.md       # CONSORT/STROBE/PRISMA/CARE with page numbers
│   ├── search_strategy.md           # Full search strings (for systematic reviews)
│   └── analysis_code.py             # Reproducible analysis code (copy for supplement)
│
├── final/
│   ├── manuscript.md                # Combined final manuscript
│   ├── manuscript.pdf               # PDF render of final manuscript
│   ├── cover-letter.md              # Cover letter to editor
│   ├── declarations.md              # Ethics, COI, funding statements
│   ├── credit-statement.md          # CRediT contributor roles (14 taxonomy categories)
│   ├── ppi-statement.md             # Patient and Public Involvement statement
│   ├── data-sharing-statement.md    # Data availability and sharing policy
│   ├── ai-disclosure.md             # AI tool usage disclosure
│   └── references.bib               # Formatted reference list
│
├── verification/
│   ├── claim_verification_report.md # Reference verification + claim-source alignment
│   ├── score_card.md                # Hard metrics (10) + soft metrics (4)
│   ├── consistency_check.md         # Numbers in text vs tables vs figures vs RPJ
│   └── reference_status.json        # DOI resolution + retraction check results
│
├── revisions/                       # Populated after peer review
│   ├── reviewer-comments.md         # Reviewer feedback (pasted or imported)
│   ├── response-letter.md           # Point-by-point response to reviewers
│   └── tracked-changes.md           # Tracked changes document
│
└── meta/
    ├── orchestrator_state.json      # Pipeline state machine (current step, gates passed)
    ├── score_trajectory.json        # Score history across all iterations
    ├── agent_dispatch_log.json      # Log of every agent dispatch with inputs/outputs
    ├── protocol_updates.md          # Meta-Evaluator proposed improvements
    └── snapshots/                   # Inner loop version snapshots for revert capability
```

---

## Initialization Checklist

The orchestrator executes these steps in order when creating a new project:

```
[ ] 1. Create root directory: paper-project-YYYY-MM-DD
[ ] 2. Create all subdirectories (data/raw, data/clean, data/analysis, analysis/figures,
       plan, draft/figures, draft/tables, supplement/extended_tables,
       supplement/sensitivity_analyses, supplement/additional_figures,
       final, verification, revisions, meta/snapshots)
[ ] 3. Initialize meta/orchestrator_state.json with default state
[ ] 4. Initialize meta/score_trajectory.json as empty array []
[ ] 5. Initialize meta/agent_dispatch_log.json as empty array []
[ ] 6. Copy raw data file(s) to data/raw/
[ ] 7. Compute SHA-256 hash(es) of raw data and write to data/data_hashes.json
[ ] 8. Copy study protocol to plan/ (if provided)
[ ] 9. Load style profile: copy styles/{journal}.yaml to plan/style-profile.yaml
       (or defer to Triage agent if journal is "recommend")
[ ] 10. Set reporting guideline in state based on study type
[ ] 11. Record project creation timestamp in orchestrator_state.json
[ ] 12. Confirm directory structure to user and begin pipeline
```

---

## Required User Inputs

### Full Pipeline Mode

| Input | Required | Description | Example |
|---|---|---|---|
| Raw data file path | Yes | Path to dataset in any supported format | `/Users/cb/data/trial_data.csv` |
| Research question | Yes | One-sentence primary study objective | "Does early statin therapy reduce 30-day mortality in acute MI patients?" |
| Study type | Yes | Determines reporting guideline and pipeline behavior | RCT, cohort, case-control, cross-sectional, systematic review, meta-analysis, case report, diagnostic accuracy, health economic |
| Target journal | Yes | Journal name or "recommend" for triage | Lancet, NEJM, JAMA, BMJ, Circulation, or "recommend" |
| Study protocol | No | File path to existing study protocol | `/Users/cb/data/protocol_v3.pdf` |
| Author list | No (needed by Gate 3) | Names, affiliations, CRediT roles | See CRediT taxonomy below |

### Pre-Submission Inquiry Mode

| Input | Required | Description |
|---|---|---|
| Research question | Yes | One-sentence primary study objective |
| Study type | Yes | RCT, observational, systematic review, etc. |
| Target journal | Yes | Journal name or "recommend" |
| Key results summary | Yes | Effect estimates, CIs, P-values for primary outcome (or results_package.json) |

### Revision Mode

| Input | Required | Description |
|---|---|---|
| Project directory path | Yes | Path to existing paper-project-YYYY-MM-DD directory |
| Reviewer comments | Yes | File path or pasted text of peer reviewer feedback |

### CRediT Taxonomy (14 Roles)

When collecting author information, map each author to one or more roles:

1. Conceptualization
2. Data curation
3. Formal analysis
4. Funding acquisition
5. Investigation
6. Methodology
7. Project administration
8. Resources
9. Software
10. Supervision
11. Validation
12. Visualization
13. Writing -- original draft
14. Writing -- review and editing

---

## Style Profile Selection Logic

### Automatic Selection

When the user specifies a target journal, the orchestrator loads the corresponding YAML file:

| User Input | Style File Loaded |
|---|---|
| "Lancet" or "The Lancet" | `styles/lancet.yaml` |
| "NEJM" or "New England Journal" | `styles/nejm.yaml` |
| "JAMA" | `styles/jama.yaml` |
| "BMJ" or "British Medical Journal" | `styles/bmj.yaml` |
| "Circulation" | `styles/circulation.yaml` |

### Deferred Selection (Triage)

When the user says "recommend" or does not specify a journal:

1. Style profile loading is deferred (state.style_profile_loaded = false)
2. Agent 0.5 (Triage) runs at Step 0.5 and produces plan/triage-report.md
3. The triage report includes per-journal fit scores and a recommendation
4. The orchestrator loads the recommended journal's YAML automatically
5. The user can override at Gate 1 by selecting a different journal

### Profile Validation

After loading a style profile, the orchestrator verifies the YAML contains these required keys:

```
- journal_name
- english_variant
- formatting.decimal_point
- formatting.p_value_leading_zero
- abstract.max_words
- abstract.headings
- word_limits (at least one entry)
- reference_limit
- reference_style
- ai_word_blacklist (non-empty list)
- sentence_style.target_mean_length
```

If any key is missing, the orchestrator halts and reports: "Style profile for {journal} is incomplete. Missing keys: {list}. Fix the YAML before proceeding."

### Journal Change Procedure

At Gate 1 the user may change the target journal without penalty (no writing has occurred yet). After Gate 1, changing the journal requires re-running all writing steps (4-10) because formatting, terminology, word limits, and panel structures differ between journals. The orchestrator warns the user and requires confirmation before proceeding.

---

## Default Orchestrator State

The initial `meta/orchestrator_state.json` is populated with these values:

```json
{
  "project_id": "paper-project-YYYY-MM-DD",
  "mode": "full",
  "current_phase": 0,
  "current_step": "init",
  "current_gate": null,
  "journal": null,
  "style_profile_loaded": false,
  "study_type": null,
  "reporting_guideline": null,
  "null_result_detected": false,
  "inner_loop_active": false,
  "inner_loop_iteration": 0,
  "inner_loop_best_score": 0,
  "inner_loop_best_version": null,
  "gates_passed": [],
  "steps_completed": [],
  "agents_dispatched": [],
  "conflict_log": [],
  "user_overrides": [],
  "score_trajectory": [],
  "created_at": "YYYY-MM-DDTHH:MM:SS",
  "last_updated": "YYYY-MM-DDTHH:MM:SS"
}
```

The `mode`, `journal`, `study_type`, and `reporting_guideline` fields are filled in during user input collection. All other fields are updated as the pipeline progresses.

---

## Reporting Guideline Selection

The study type maps to a reporting guideline automatically:

| Study Type | Guideline | Items | Key Structural Impact |
|---|---|---|---|
| RCT | CONSORT | 25 | Flow diagram, extended Methods, adverse events |
| Cohort / Case-Control / Cross-Sectional | STROBE | 22 | Bias addressing, confounding |
| Systematic Review / Meta-Analysis | PRISMA | 27 | PICO, flow diagram, forest plots, GRADE |
| Case Report / Series | CARE | 13 | Timeline figure, patient perspective |
| Trial Protocol | SPIRIT | 33 | Pre-study protocol structure |
| Diagnostic Accuracy | STARD | 25 | Cross-tabulation, flow diagram |
| Health Economic Evaluation | CHEERS | 28 | Cost-effectiveness, QALY/DALY |
| Observational Meta-Analysis | MOOSE | 35 | Confounding assessment |

The selected guideline determines which checklist Agent 10 (Compliance) uses, which structural elements are mandatory, and which supplementary materials are required.

---

## Supported Data Formats

Agent 17 (Data Engineer) accepts raw data in the following formats:

| Format | Extension | Library Used |
|---|---|---|
| Comma-separated values | .csv | pandas / polars |
| Excel | .xlsx, .xls | openpyxl / xlrd |
| SAS | .sas7bdat | pyreadstat |
| Stata | .dta | pyreadstat |
| SPSS | .sav | pyreadstat |
| Apache Parquet | .parquet | pyarrow |
| REDCap API export | .csv (via API) | pandas |

The data is copied to `data/raw/` and hashed before any processing begins. The raw copy is never modified.
