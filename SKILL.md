---
name: medical-paper-agents
description: >
  Multi-agent system for writing medical research papers targeting top-tier journals
  (Lancet, NEJM, JAMA, BMJ, Circulation). Orchestrates 20 specialized agents across
  a 5-gate, 15-step pipeline from raw data to submission-ready manuscript.
  Trigger: "write medical paper", "medical manuscript", "journal submission",
  "write for lancet", "write for nejm", "write for jama", "clinical paper",
  "research article", "medical paper agents"
allowed-tools: [Read, Write, Edit, Bash, Agent, Glob, Grep, WebFetch, WebSearch]
version: 1.0.0
metadata:
  skill-author: Dr. Charit Bhograj / Claude
  domain: medical-research
  journals: lancet, nejm, jama, bmj, circulation
---

# Medical Paper Agents: Multi-Agent Scientific Paper Writing System

A multi-agent orchestration system for writing publication-quality medical research papers
for top-tier journals. 20 specialized agents, 5 human review gates, automated scoring,
claim verification, and iterative refinement.

---

## TABLE OF CONTENTS

1. [Overview](#1-overview)
2. [Agent Roster](#2-agent-roster)
3. [Execution Topology](#3-execution-topology)
4. [Gate System](#4-gate-system)
5. [Data Pipeline](#5-data-pipeline)
6. [Style System](#6-style-system)
7. [Scoring System](#7-scoring-system)
8. [Inner Loop](#8-inner-loop-iterative-refinement)
9. [Outer Loop](#9-outer-loop-skill-self-improvement)
10. [Conflict Resolution](#10-conflict-resolution)
11. [Claim Verification](#11-claim-verification)
12. [Supplementary Materials](#12-supplementary-materials)
13. [Null-Result Handling](#13-null-result-handling)
14. [Pre-Submission Inquiry Mode](#14-pre-submission-inquiry-mode)
15. [Project Directory Structure](#15-project-directory-structure)
16. [Existing Skills Integration](#16-existing-skills-integration)
17. [Invocation and Workflow](#17-invocation-and-workflow)

---

## 1. OVERVIEW

### What This System Does

Takes raw clinical data + a research question and produces a submission-ready manuscript package including:
- Main manuscript (IMRAD structure, journal-formatted)
- All figures and tables (publication-quality, journal-styled)
- Supplementary materials (protocol, SAP, extended analyses)
- Cover letter
- Declarations (ethics, COI, funding, PPI, CRediT, data sharing, AI disclosure)
- Completed reporting checklist (CONSORT/STROBE/PRISMA/CARE with page numbers)
- Reference list (formatted, verified, retraction-checked)

### What Makes This Different

1. **20 specialized agents** — each with deep domain expertise (not one LLM doing everything)
2. **5 human review gates** — you approve data, results, plan, draft, and final before each phase
3. **Immutable number chain** — raw data → results_package.json → prose (writing agents never compute numbers)
4. **Claim verification** — every reference checked for existence, retraction, and claim-source alignment
5. **Hard metric scoring** — computable metrics trigger automated refinement; soft metrics are advisory
6. **Journal-specific style profiles** — YAML configs for Lancet/NEJM/JAMA/BMJ/Circulation
7. **Self-improvement** — Meta-Evaluator identifies weak agent protocols and proposes updates

### Supported Manuscript Types

| Type | Reporting Guideline | Key Structural Impact |
|---|---|---|
| Randomised Controlled Trial | CONSORT (25 items) | Flow diagram, extended Methods, adverse events |
| Cohort / Case-Control / Cross-Sectional | STROBE (22 items) | Bias addressing, confounding |
| Systematic Review / Meta-Analysis | PRISMA (27 items) | PICO, flow diagram, forest plots, GRADE |
| Case Report / Series | CARE (13 items) | Timeline figure, patient perspective |
| Trial Protocol | SPIRIT (33 items) | Pre-study protocol structure |
| Diagnostic Accuracy | STARD (25 items) | Cross-tabulation, flow diagram |
| Health Economic Evaluation | CHEERS (28 items) | Cost-effectiveness, QALY/DALY |
| Observational Meta-Analysis | MOOSE (35 items) | Confounding assessment |

---

## 2. AGENT ROSTER

### Complete Agent Table

| # | Agent Name | Phase | Role Model | Primary Function | Key Correction |
|---|---|---|---|---|---|
| 0 | **Orchestrator** | All | Project Manager | Routes work, loads style profile, manages state, enforces sequencing, dispatches inner loop | + Conflict resolution (Gap 4), + supplement routing (Gap 3) |
| 0.5 | **Triage / Journal Fit** | Pre-pipeline | Journal Editor (triage) | Evaluates if study is journal-worthy, recommends target journal, prevents wasted effort | **NEW** (Gap 1) |
| 1 | **Literature & Gap Analysis** | Phase 1 | Evidence Synthesizer | Systematic search, evidence synthesis, gap identification, reference library | Delegates to existing literature skills |
| 2 | **Story Architect** | Phase 1 | Senior Author (strategy) | Narrative blueprint: hook → tension → gap → resolution → punchline. Runs BEFORE writing. | + Null-result template (Gap 5) |
| 3 | **Study Design & Methods** | Phase 1 | Clinical Epidemiologist | Methods section, reporting guideline selection, protocol for supplement | + Supplementary output (Gap 3) |
| 4 | **Statistician** | Phase 0 + 2 | Biostatistician | DUAL ROLE: SAP writer (Phase 0) + results verifier (Phase 2). Sample size, missing data strategy. | + Data quality check (Gap 10) |
| 5 | **Results Writer** | Phase 2 | First Author (data) | Results section. GOLDEN RULE: reads ONLY from results_package.json, never computes. | Immutable number chain |
| 6 | **Figure Engine** | Phase 2 | Figure/Table Specialist | Routes to correct viz tool, applies journal style via figure-styler.py | + Journal-specific styling |
| 7 | **Narrative Writer** | Phase 2 | First Author (prose) | Introduction, Discussion, journal-specific panels. Guided by Story Architect blueprint. | + Guideline cross-reference (Gap 11) |
| 8 | **Abstract & Summary** | Phase 2 | Senior Author (distillation) | Journal-specific abstract format, keywords. Written LAST after all sections. | Format from style YAML |
| 9 | **Reference & Citation** | Phase 3 | Reference Manager | Format citations (Vancouver/AMA), verify DOIs, enforce limits, check retractions | + retraction-checker.py |
| 10 | **Compliance & Ethics** | Phase 3 | Compliance Officer | Reporting checklist, IRB, consent, registration, declarations | + PPI (Gap 8), + CRediT (Gap 9) |
| 11 | **Editor** | Phase 3 | Medical Editor | Scientific English, logical flow, promotional language removal, cover letter | + Pre-submission inquiry mode (Gap 7) |
| 12 | **Humanizer** | Phase 3 | Language Specialist | AI-word removal (135-word blacklist), sentence length variance, natural voice. LAST writing agent. | Positioned absolutely last |
| 13 | **Peer Review Response** | Post-submission | Revision Coordinator | Point-by-point response, revision tracking, rebuttal evidence | Triggered after reviews received |
| 14 | **Scoring Agent** | Cross-cutting | Journal Editor (evaluation) | READ-ONLY. Hard metrics (computable, trigger inner loop) + soft metrics (advisory at gate). | **Redesigned** (Gap 2) |
| 15 | **Meta-Evaluator** | Post-completion | Quality Improvement Director | Outer loop: diagnoses weak agents, proposes protocol updates. | Skill self-improvement |
| 16 | **Claim Verifier** | Cross-cutting | Fact Checker | Extract claims → verify references (DOI + retraction) → align claims to sources | + Full-text verification (Gap 6) |
| 17 | **Data Engineer** | Phase 0 | Data Scientist | Ingest raw data, validate, clean, derive populations, produce CONSORT flow numbers | **NEW** — data pipeline |
| 18 | **Data Analyst** | Phase 0 | Biostatistician (execution) | Execute SAP on real data, produce results_package.json — THE source of truth | **NEW** — data pipeline |

### Agent Protocol Files

Each agent has a dedicated protocol file in `agents/`:

```
agents/
├── agent-00-orchestrator.md       (state machine, dispatch logic, conflict resolution)
├── agent-00.5-triage.md           (journal fit evaluation criteria)
├── agent-01-literature.md         (search strategy, gap scoring, skill delegation)
├── agent-02-story-architect.md    (narrative blueprint, null-result template)
├── agent-03-study-design.md       (methods structure, guideline selection)
├── agent-04-statistician.md       (SAP writing, results verification, dual role)
├── agent-05-results-writer.md     (GOLDEN RULE: read-only from results_package.json)
├── agent-06-figure-engine.md      (figure type routing, journal styling)
├── agent-07-narrative-writer.md   (intro/discussion, guideline cross-reference)
├── agent-08-abstract-summary.md   (journal-specific format from YAML)
├── agent-09-reference-citation.md (formatting, DOI verification, retraction check)
├── agent-10-compliance-ethics.md  (checklist, IRB, PPI, CRediT, declarations)
├── agent-11-editor.md             (polish, cover letter, pre-submission inquiry)
├── agent-12-humanizer.md          (AI-word removal, natural voice, LAST writer)
├── agent-13-peer-review-response.md (point-by-point, revision tracking)
├── agent-14-scoring.md            (hard/soft metrics, read-only evaluation)
├── agent-15-meta-evaluator.md     (outer loop, protocol improvement)
├── agent-16-claim-verifier.md     (3-step verification, full-text for key claims)
├── agent-17-data-engineer.md      (ingest, validate, clean, derive)
└── agent-18-data-analyst.md       (execute SAP, produce results_package.json)
```

The orchestrator loads ONE agent protocol at a time into context (never all 20 simultaneously).

---

## 3. EXECUTION TOPOLOGY

### 15-Step Pipeline with Parallelism

```
USER INPUT: raw data file + research question + study protocol (optional)
│
▼
STEP 0a ─── Agent 17 (Data Engineer) ───────────────── SOLO
│           Ingest → Validate → Clean → Derive populations
│           Output: clean data, validation report, CONSORT flow numbers
│
╔═══════════════════════════════════╗
║  GATE 0a: DATA                    ║
║  You review: validation report,   ║
║  flagged values, exclusion counts ║
╚═══════════╤═══════════════════════╝
            │
STEP 0b ─── Agent 18 (Data Analyst) ────────────────── SOLO
│           + Agent 4 (Statistician) reviews SAP execution
│           Execute SAP → Describe → Analyse → Package
│           Output: results_package.json (THE source of truth)
│
╔═══════════════════════════════════╗
║  GATE 0b: RESULTS                 ║
║  You review: statistical results, ║
║  assumption checks, key findings  ║
╚═══════════╤═══════════════════════╝
            │
STEP 0.5 ── Agent 0.5 (Triage) ─────────────────────── SOLO
│           Evaluate journal fit, recommend target
│           Output: triage-report.md with per-journal scores
│           → Orchestrator loads journal style YAML
│
STEP 1 ──── Agent 1 (Literature & Gap) ─────────────── SOLO
│           Systematic search, evidence synthesis
│           Output: literature-matrix.md, gap statement, reference library
│
STEP 2 ──── Agent 2 (Story) ∥ Agent 3 (Methods) ───── PARALLEL ×2
│           Story: narrative blueprint (arc, hook, punchline)
│           Methods: methods section + reporting guideline selection
│           Both need Agent 1 output. Independent of each other.
│
STEP 3 ──── Agent 4 (Statistician verify) ──────────── SOLO
│           Verify SAP was executed correctly by Agent 18
│           Check: methods text matches actual analysis
│           Output: verified statistical methods section
│
╔═══════════════════════════════════╗
║  GATE 1: PLAN                     ║
║  You review: paper plan,          ║
║  narrative blueprint, methods,    ║
║  triage report, style profile     ║
╚═══════════╤═══════════════════════╝
            │
STEP 4 ──── Agent 5 (Results) ∥ Agent 6 (Figures) ─── PARALLEL ×2
│           Results: writes text from results_package.json
│           Figures: generates all tables + figures + diagrams
│           Both consume results_package.json. Independent outputs.
│
STEP 5 ──── Agent 7 (Narrative Writer) ─────────────── SOLO
│           Introduction (needs Agent 1 literature + Agent 2 blueprint)
│           Discussion (needs Agent 5 results for interpretation)
│           Journal-specific panels (Research in Context, Key Points, etc.)
│
STEP 6 ──── Agent 8 (Abstract & Summary) ───────────── SOLO
│           Written LAST — distills ALL prior sections
│           Journal-specific format from style YAML
│
STEP 7 ──── Agent 14 (Score) ∥ Agent 16 (Verify) ──── PARALLEL ×2
│           Scoring: compute hard metrics, assess soft metrics
│           Verifier: extract claims, check references, align to sources
│
╔═══════════════════════════════════════════════╗
║  GATE 2: DRAFT                                ║
║  You review: manuscript draft + claim          ║
║  verification report + score card              ║
║  Threshold: hard score ≥ 85                    ║
║  If below: INNER LOOP (max 5 iterations)       ║
╚═══════════╤═══════════════════════════════════╝
            │
STEP 8 ──── Agent 9 (Refs) ∥ Agent 10 (Compliance) ── PARALLEL ×2
│           References: format, verify DOIs, enforce limits, retraction check
│           Compliance: reporting checklist, IRB, PPI, CRediT, declarations
│           Touch different document sections. Independent.
│
STEP 9 ──── Agent 11 (Editor) ──────────────────────── SOLO
│           Scientific English, logical flow, cover letter
│           Needs references and compliance done first
│
STEP 10 ─── Agent 12 (Humanizer) ───────────────────── SOLO
│           AI-word removal, natural voice, sentence variance
│           ABSOLUTELY LAST writing agent. No agent touches prose after.
│
STEP 11 ─── Agent 14 (Score) ∥ Agent 16 (Verify) ──── PARALLEL ×2
│           Final scoring pass + final claim verification
│
╔═══════════════════════════════════════════════╗
║  GATE 3: FINAL                                ║
║  You review: polished manuscript + full        ║
║  verification report + score card              ║
║  Threshold: hard score ≥ 90                    ║
║  If below: INNER LOOP (max 5 iterations)       ║
╚═══════════╤═══════════════════════════════════╝
            │
            ▼
      SUBMISSION-READY PACKAGE
            │
      (after peer review received)
            │
STEP 12 ─── Agent 13 (Peer Review Response) ────────── SOLO
│           Point-by-point response, revision tracking
│
STEP 13 ─── Agent 15 (Meta-Evaluator) ──────────────── SOLO
            Post-mortem: score trajectory, weak agents, protocol updates
```

### Parallelism Summary

| Step | Agents | Mode | Rationale |
|---|---|---|---|
| 0a | 17 | Solo | Everything depends on clean data |
| 0b | 18 (+4 review) | Solo | Results depend on clean data |
| 0.5 | 0.5 | Solo | Journal selection determines style profile |
| 1 | 1 | Solo | Everything depends on evidence landscape |
| 2 | 2 ∥ 3 | **Parallel ×2** | Story arc and methods design are independent |
| 3 | 4 | Solo | Needs methods from Agent 3 |
| 4 | 5 ∥ 6 | **Parallel ×2** | Text and visuals are independent artifacts |
| 5 | 7 | Solo | Discussion interprets results (needs Agent 5) |
| 6 | 8 | Solo | Abstract distills ALL sections |
| 7 | 14 ∥ 16 | **Parallel ×2** | Both read-only on manuscript |
| 8 | 9 ∥ 10 | **Parallel ×2** | References vs declarations — different sections |
| 9 | 11 | Solo | Needs refs and compliance done first |
| 10 | 12 | Solo | Must be absolutely last writer |
| 11 | 14 ∥ 16 | **Parallel ×2** | Final quality + fact check |
| 12 | 13 | Solo | Only after external review |
| 13 | 15 | Solo | Post-mortem on entire process |

**Total: 15 steps, 5 parallel (steps 2, 4, 7, 8, 11), 10 sequential**
**Max agents running simultaneously: 2**

---

## 4. GATE SYSTEM

### Gate 0a: DATA GATE

**After:** Agent 17 (Data Engineer)
**Threshold:** User approval (no automated score)
**Artifacts presented:**
- `data/data_profile.md` — N rows, N columns, variable types, distributions
- `data/validation_report.md` — impossible values, duplicates, inconsistencies flagged
- `data/cleaning_log.md` — every transformation documented
- `data/data_hashes.json` — SHA-256 of raw and clean data
- Population flow counts (N excluded at each step)

**User actions:** Approve, request re-cleaning, flag additional issues

### Gate 0b: RESULTS GATE

**After:** Agent 18 (Data Analyst)
**Threshold:** User approval (no automated score)
**Artifacts presented:**
- `analysis/results_package.json` — all effect estimates, CIs, P-values
- `analysis/assumption_checks.md` — PH assumption, normality, VIF, etc.
- `analysis/statistical_report.md` — human-readable summary of findings
- Table 1 (baseline characteristics)
- Key figures (KM curves, forest plots if applicable)

**User actions:** Approve, request additional analyses, modify SAP

### Gate 1: PLAN GATE

**After:** Agents 0.5, 1, 2, 3, 4
**Threshold:** User approval (no automated score)
**Artifacts presented:**
- `plan/triage-report.md` — journal fit scores + recommendation
- `plan/paper-plan.md` — assembled plan document
- `plan/narrative-blueprint.md` — story arc
- `plan/literature-matrix.md` — evidence summary + gap statement
- `draft/methods.md` — draft methods section
- `analysis/statistical_plan.md` — verified SAP
- Selected style profile (journal YAML loaded)

**User actions:** Approve, change target journal, redirect narrative, modify methods

### Gate 2: DRAFT GATE

**After:** Agents 5-8, scored by 14, verified by 16
**Threshold:** Hard score ≥ 85 (triggers inner loop if below)
**Artifacts presented:**
- Full manuscript draft (all sections)
- `verification/score_card.md` — 10 hard metrics + 4 soft metrics
- `verification/claim_verification_report.md` — reference status + claim alignment
- All figures and tables

**User actions:** Approve, request section rewrites, add content, redirect narrative

### Gate 3: FINAL GATE

**After:** Agents 9-12, scored by 14, verified by 16
**Threshold:** Hard score ≥ 90 (triggers inner loop if below)
**Artifacts presented:**
- Polished manuscript
- Cover letter
- All declarations (ethics, COI, funding, PPI, CRediT, data sharing, AI)
- Completed reporting checklist with page numbers
- Final score card
- Final claim verification report
- Complete submission package

**User actions:** Approve for submission, request final adjustments

---

## 5. DATA PIPELINE

### The Golden Rule

**Numbers flow ONE way. No writing agent ever computes a number.**

```
raw_data (immutable) → clean_data (immutable after Gate 0a) → results_package.json (immutable after Gate 0b)
     │                        │                                        │
  SHA-256 hash            SHA-256 hash                            SHA-256 hash
     │                        │                                        │
  (you verify              (you verify                            (you verify
   at Data Gate)            at Data Gate)                          at Results Gate)
```

Every writing agent READS from `results_package.json`. If Agent 5 (Results Writer) says "HR 0.78" and `results_package.json` says `"estimate": 0.78`, it is correct by construction. If they don't match, Agent 14 (Scoring) flags it via `consistency-checker.py`.

### 6-Stage Pipeline

#### Stage 1: Ingest & Profile (Agent 17)
- Read raw data in any format: CSV, Excel, SAS (.sas7bdat), Stata (.dta), SPSS (.sav), Parquet, REDCap API export
- Auto-generate data dictionary: variable names, types, labels, coding schemes
- Profile: N rows, N columns, missingness %, distributions, value ranges
- Compute data fingerprint (SHA-256 hash)
- **Script:** `scripts/data-ingest.py`
- **Output:** `data/data_profile.md`, `data/data_dictionary.json`, `data/raw_data_hash.txt`

#### Stage 2: Validate & Clean (Agent 17)
- Impossible values: age <0 or >120, BMI <10 or >80, negative lab values, dates in future
- Duplicate records: exact + fuzzy matching
- Cross-field consistency: death date before enrollment, discharge before admission
- Variable type corrections: strings → dates, coded numerics → categories
- Outlier flagging (NOT removal — flagged for human review at Gate 0a)
- Unit standardisation (mg/dL → mmol/L if needed)
- **Script:** `scripts/data-validate.py`
- **Output:** `data/clean/`, `data/validation_report.md`, `data/cleaning_log.md`

#### Stage 3: Derive & Define Populations (Agent 17)
- Apply inclusion/exclusion criteria (track N excluded at each step → CONSORT flow)
- Define analysis populations:
  - ITT (all randomised)
  - Modified ITT (randomised + received ≥1 dose)
  - Per-protocol (completed as planned)
  - Safety population (received ≥1 dose)
- Create composite endpoints: MACE (MI + stroke + CV death), co-primary endpoints, time-to-first-event
- Derive variables: BMI, eGFR, follow-up duration, age categories
- Create subgroup variables: pre-specified from protocol
- **Script:** `scripts/data-derive.py`
- **Output:** `data/analysis/analysis_itt.parquet`, `analysis_pp.parquet`, `analysis_safety.parquet`, `data/population_flow.json`

#### Stage 4: Describe (Agent 18)
- Table 1: baseline characteristics by group
  - RCT mode: NO p-values (differences are random by design)
  - Observational mode: WITH p-values
  - Include standardised mean differences (SMD)
- Missingness summary per variable per group
- Follow-up duration summary
- Event rates by group
- **Script:** Delegates to existing `paper-writer/scripts/table1.py` (enhanced)
- **Output:** `analysis/table1.md`, `analysis/descriptive_stats.md`

#### Stage 5: Analyse (Agent 18)
- **Primary analysis:** Execute pre-specified analysis per SAP
  - Cox PH → HR + 95% CI + P-value
  - Logistic regression → OR + 95% CI
  - Linear regression → β + 95% CI
  - Mixed model → estimated difference
- **Assumption checks:** Proportional hazards (Schoenfeld), normality (Shapiro-Wilk), VIF, homoscedasticity
- **Secondary analyses:** Each pre-specified secondary endpoint
- **Subgroup analyses:** Effect estimate per subgroup + interaction test (treatment × subgroup)
- **Sensitivity analyses:** Per-protocol, complete case vs imputed, alternative model
- **Missing data:** MCAR/MAR/MNAR assessment, multiple imputation (m=20-50)
- **Survival analysis:** Kaplan-Meier + log-rank + Cox + number at risk + median follow-up (reverse KM)
- **Scripts:** `scripts/assumption-checks.py`, `scripts/multiple-imputation.py`, delegates to `analysis-template.py`
- **Output:** `analysis/primary_results.json`, `analysis/secondary_results.json`, `analysis/subgroup_results.json`, `analysis/sensitivity_results.json`, `analysis/assumption_checks.md`, `analysis/analysis_code.py`

#### Stage 6: Package Results (Agent 18)
- Assemble `results_package.json` from all analysis outputs
- Validate against schema (`templates/results-package-schema.json`)
- Compute hash
- Internal consistency check: N in primary = N in Table 1 = N in CONSORT diagram
- **Script:** `scripts/results-packager.py`
- **Output:** `analysis/results_package.json`, `analysis/statistical_report.md`

---

## 6. STYLE SYSTEM

### Journal Style Profiles

Each journal has a YAML configuration file in `styles/` that every writing agent loads.

**Files:** `styles/lancet.yaml`, `styles/nejm.yaml`, `styles/jama.yaml`, `styles/bmj.yaml`, `styles/circulation.yaml`

**Data source:** `/Users/cb/Documents/research/Medical_Journal_Style_Reference_Guide.md`

### Profile Structure

```yaml
# Example: styles/lancet.yaml
journal_name: "The Lancet"
english_variant: british

spelling:
  ise_ize: "-ise"          # randomised, minimised, characterised
  our_or: "-our"           # behaviour, tumour, colour
  re_er: "-re"             # centre, fibre, litre
  ae_digraph: "-ae-"       # anaemia, haematology, paediatric
  oe_digraph: "-oe-"       # oesophagus, oedema, diarrhoea

drug_naming: rINN           # international nonproprietary names

formatting:
  decimal_point: midline    # 23·4 (MANDATORY — unique to Lancet)
  thousands_separator: thin_space
  numbers_below_ten: spell_out
  p_value_leading_zero: true
  p_value_case: lowercase   # p=0·04
  oxford_comma: true
  quotation_marks: single
  date_format: "DD Month YYYY"

abstract:
  max_words: 300
  headings:
    - Background
    - Methods
    - Findings            # NOT "Results"
    - Interpretation      # NOT "Conclusions"
    - Funding

special_panels:
  - name: "Research in Context"
    sections:
      - "Evidence before this study"
      - "Added value of this study"
      - "Implications of all the available evidence"

voice:
  active_voice: encouraged
  first_person: accepted
  tone: authoritative_global_advocacy
  promotional_language: forbidden

word_limits:
  original_research: 3000
  rct: 4500
  systematic_review: 3500
  comment: 1500
  correspondence: 250

reference_limit: 30
reference_style: vancouver
figure_table_limit: 5

sentence_style:
  target_mean_length: 22
  target_std_dev: 8.0
  max_consecutive_same_start: 2

ai_word_blacklist:
  - delve
  - elucidate
  - underscore
  - showcase
  - bolster
  - foster
  - harness
  - leverage
  - meticulous
  - intricate
  - pivotal
  - groundbreaking
  - transformative
  - comprehensive
  - multifaceted
  - nuanced
  - notably
  - seamlessly
  - landscape
  - tapestry
  - testament
  - crucial
  - invaluable
  - revolutionize
  - innovative
  - commendable
  - profoundly
  - utilize
  - plethora
  - myriad
```

### Key Differences by Journal

| Element | Lancet | NEJM | JAMA | BMJ | Circulation |
|---|---|---|---|---|---|
| English | British (-ise) | American (-ize) | American (-ize) | British (-ise) | American (-ize) |
| Decimal | **Midline (·)** | Baseline (.) | Baseline (.) | Baseline (.) | Baseline (.) |
| P-value zero | Yes (0·04) | No (.04) | No (.04) | Yes (0.04) | No (.04) |
| Abstract | 300w: Bg/Meth/**Find/Interp**/Fund | 250w: Bg/Meth/Res/Conc | 350w: + Key Points (Q/F/M) | 400w: 8 headings | 350w: Bg/Meth/Res/Conc |
| Special panel | Research in Context | None | Key Points | What this study adds | Clinical Perspective |
| Word limit | 3000-4500 | 2700 | 3000 | Flexible | ~7000 |
| Ref limit | 30 | ~40 | 50-75 | Flexible | 50 |
| Drug names | rINN | USAN | USAN | BAN | USAN |
| Tone | Advocacy, global | Conservative, terse | Clear, clinical | Accessible, plain | Specialty-focused |

---

## 7. SCORING SYSTEM

### Hard Metrics (Computable — Trigger Inner Loop)

These are objectively measurable. They are computed by `scripts/consistency-checker.py` and pattern matching. They trigger the inner loop when they fail.

| # | Metric | Computation | Target | Responsible Agent |
|---|---|---|---|---|
| H1 | Word count within limit | Count words in manuscript sections | ≤ journal limit | 11 (Editor) |
| H2 | Reference count within limit | Count references | ≤ journal limit | 9 (Reference) |
| H3 | Reporting checklist completion | Count completed items / total | ≥ 90% | 10 (Compliance) |
| H4 | AI-flagged word count | Count words from blacklist | ≤ 3 | 12 (Humanizer) |
| H5 | Sentence length std dev | Compute σ of sentence word counts | ≥ 5.0 | 12 (Humanizer) |
| H6 | References resolve via DOI | Query CrossRef/PubMed per DOI | 100% | 9 (Reference) |
| H7 | P-values correctly formatted | Pattern match against journal style | 100% | 11 (Editor) |
| H8 | No retracted references | Query retraction databases | 0 retracted | 9 (Reference) |
| H9 | Numbers match results_package.json | `consistency-checker.py` cross-check | 100% match | 5 (Results Writer) |
| H10 | Internal N consistency | Methods N = Results N = Table 1 N = CONSORT N | All match | 14 (Scoring) |

### Soft Metrics (Advisory — Shown at Gate, Do NOT Trigger Inner Loop)

These require LLM assessment. They are presented to the user at each gate but do NOT trigger automated refinement (avoiding the circularity problem of LLMs grading their own work).

| # | Metric | Assessment Method | What It Evaluates |
|---|---|---|---|
| S1 | Narrative coherence | Does Introduction build to gap? Does Discussion open with key finding? | Story arc integrity |
| S2 | Gap statement specificity | Does the gap name a specific clinical unknown (not "remains unclear")? | Novelty claim strength |
| S3 | Discussion balance | Are limitations honest but not self-defeating? Is interpretation measured? | Academic maturity |
| S4 | Clinical implication clarity | Does the paper state what clinicians should do differently? | Practice relevance |

### Score Card Format

```markdown
## SCORE CARD — [Gate Name] — Draft v[N]

### HARD METRICS (automated)
| # | Metric | Value | Target | Status |
|---|---|---|---|---|
| H1 | Word count | 2,680 | ≤ 2,700 | ✅ PASS |
| H2 | Reference count | 42 | ≤ 40 | ❌ FAIL — 2 over limit |
| H3 | Reporting checklist | 22/25 | ≥ 90% (23) | ❌ FAIL — items 11a, 19 incomplete |
| H4 | AI-flagged words | 7 | ≤ 3 | ❌ FAIL — "comprehensive" ×2, "notably" ×3, "crucial" ×2 |
| H5 | Sentence length σ | 3.2 | ≥ 5.0 | ❌ FAIL — too uniform |
| H6 | DOI resolution | 40/42 | 100% | ❌ FAIL — refs 23, 37 unresolved |
| H7 | P-value format | 100% | 100% | ✅ PASS |
| H8 | Retracted refs | 1 | 0 | ❌ FAIL — ref 14 retracted 2025-11 |
| H9 | Numbers match | 98% | 100% | ❌ FAIL — line 67: "30%" vs 28.3% in results_package |
| H10 | N consistency | FAIL | All match | ❌ FAIL — Methods: 2400, CONSORT: 2398 |

HARD SCORE: 3/10 PASS → INNER LOOP TRIGGERED

### SOFT METRICS (advisory — for your review)
| # | Metric | Assessment |
|---|---|---|
| S1 | Narrative coherence | Introduction builds well; Discussion opens with secondary finding — consider leading with primary |
| S2 | Gap statement | "The role of X remains unclear" — consider specifying what aspect is unclear |
| S3 | Discussion balance | Limitations section is thorough; interpretation measured |
| S4 | Clinical implication | Clear: "These findings support early initiation of..." |
```

---

## 8. INNER LOOP (Iterative Refinement)

### Trigger

The inner loop activates when hard metrics fall below the gate threshold (≥85 at Draft Gate, ≥90 at Final Gate).

### Process

```
1. SCORE: Compute all hard metrics
2. IDENTIFY: Find the lowest-scoring (worst-failing) metric
3. MAP: Determine which agent is responsible for that metric
4. DISPATCH: Load that agent's protocol, give it the specific failure
5. FIX: Agent produces a targeted fix
6. RE-SCORE: Compute all hard metrics again
7. COMPARE:
   - If ALL dimensions improved or held steady → KEEP the fix
   - If ANY dimension regressed → REVERT to previous version
8. COHERENCE CHECK: Run consistency-checker.py
   - Methods ↔ Results mirror structure?
   - Numbers in text ↔ tables ↔ figures match?
   - Narrative thread unbroken?
   - Abstract reflects current manuscript?
9. REPEAT: Go to step 1
10. STOP CONDITIONS:
    - Hard score ≥ threshold → proceed to gate presentation
    - 5 iterations reached → present BEST version to user at gate
    - All metrics passing → proceed
```

### Metric-to-Agent Dispatch Map

| Metric Failed | Agent Dispatched | Fix Action |
|---|---|---|
| H1 (word count) | 11 (Editor) | Cut words, tighten prose |
| H2 (ref count) | 9 (Reference) | Remove least-essential references |
| H3 (checklist) | 10 (Compliance) | Complete missing checklist items |
| H4 (AI words) | 12 (Humanizer) | Replace flagged words |
| H5 (sentence σ) | 12 (Humanizer) | Vary sentence lengths |
| H6 (DOI resolve) | 9 (Reference) | Fix or replace broken references |
| H7 (P-value format) | 11 (Editor) | Reformat P-values per journal style |
| H8 (retractions) | 9 (Reference) | Replace retracted references |
| H9 (number match) | 5 (Results Writer) | Correct numbers from results_package.json |
| H10 (N consistency) | 5 (Results Writer) | Reconcile N across sections |

### Revert Protocol

If a fix causes regression in any metric:
1. Discard the fix entirely
2. Restore the previous version
3. Try dispatching a DIFFERENT agent for the same problem
4. If no improvement after 2 attempts on the same metric, flag for user at gate

---

## 9. OUTER LOOP (Skill Self-Improvement)

### When It Runs

Agent 15 (Meta-Evaluator) runs AFTER a paper is complete (Step 13) or after the user provides feedback.

### What It Analyses

1. **Score trajectory:** How did the score change across inner loop iterations at each gate?
2. **Agent dispatch frequency:** Which agents were dispatched most often for fixes? (indicates weak protocols)
3. **Recurring failures:** Did the same metric fail across multiple gates?
4. **User feedback:** What did the user change at each gate? What was rejected?
5. **Time-to-convergence:** How many iterations did each gate need?

### What It Produces

```markdown
## META-EVALUATION REPORT

### Diagnosis
- Humanizer was dispatched 4/5 iterations at Draft Gate for AI words
  → Protocol needs stronger initial instruction to avoid blacklisted words
- Results Writer had N mismatch in 2/3 papers
  → Protocol needs explicit instruction to verify N from CONSORT flow
- Narrative Writer consistently weak on gap statements (S2 scored low)
  → Protocol needs examples of strong vs weak gap statements

### Proposed Protocol Updates (require your approval)
1. agent-12-humanizer.md: Add rule "Before writing ANY sentence, check if it
   contains words from the blacklist. Pre-filter, don't post-fix."
2. agent-05-results-writer.md: Add rule "First line of Results MUST state:
   'Of [N from CONSORT] participants randomised, [N] were included in the
   primary analysis.' Cross-check against population_flow.json."
3. agent-07-narrative-writer.md: Add examples section with 5 strong gap
   statements from published Lancet papers.
```

### Approval

Protocol updates are ALWAYS presented to the user for approval before being saved. The user is the "meta-programmer" — they iterate on how agents work, not on the paper itself.

---

## 10. CONFLICT RESOLUTION

### Priority Hierarchy

When agents produce conflicting outputs, the orchestrator resolves using this fixed hierarchy:

```
PRIORITY 1: Statistician (Agent 4) overrules ALL agents on statistical claims
  Example: Story Architect wants to lead with secondary finding that Statistician
  flags as having wide CIs and post-hoc status → Statistician wins

PRIORITY 2: Compliance (Agent 10) overrules ALL agents on regulatory requirements
  Example: Narrative Writer wants to omit a limitation that Compliance says is
  required by the reporting guideline → Compliance wins

PRIORITY 3: Claim Verifier (Agent 16) overrules ALL agents on factual accuracy
  Example: Literature Agent cites a paper for a claim, Claim Verifier finds the
  paper doesn't support that claim → Claim Verifier wins, claim is removed/revised

PRIORITY 4: Story Architect (Agent 2) overrules Narrative Writer (Agent 7) on framing
  Example: Narrative Writer deviates from the narrative blueprint → Story Architect's
  blueprint takes precedence

PRIORITY 5: Humanizer (Agent 12) has final say on prose style
  Example: Editor introduces a construction that Humanizer flags as AI-like →
  Humanizer's version prevails (Humanizer is the LAST writing agent)

PRIORITY 6: USER overrules everyone at gates
  Any gate decision by the user supersedes all agent outputs
```

### Implementation

The orchestrator checks for conflicts after each step where multiple agents contribute to the same document section. Conflicts are resolved silently using the hierarchy. Unresolvable conflicts (e.g., two Priority 1 agents disagree) are escalated to the user at the next gate.

---

## 11. CLAIM VERIFICATION

### 3-Step Process (Agent 16)

#### Step 1: Claim Extraction

Parse the manuscript and extract every:
- Factual assertion with a citation (e.g., "Mortality was 30% lower [14]")
- Statistical claim (percentages, HR, OR, CI values)
- "It has been shown that..." constructions
- Prevalence/incidence statements
- Drug efficacy claims
- Guideline recommendations cited

**Output:** `claims_list.json` with claim text, source reference, section, line number, claim type, DOI

#### Step 2: Reference Verification

For EACH reference in the paper:

a) **EXISTS CHECK** — Query CrossRef by DOI, PubMed by PMID, OpenAlex by DOI. If not found in ANY → FLAG as potential hallucination.

b) **METADATA MATCH** — Does title match? Authors? Journal? Year? If mismatch → FLAG.

c) **RETRACTION CHECK** — Query CrossRef for "update-to" type "retraction", check PubMed retraction notices. If retracted → BLOCK.

d) **EXPRESSION OF CONCERN CHECK** — Similar to retraction. If flagged → WARN.

**Script:** `scripts/retraction-checker.py`
**Output:** `verification/reference_status.json`

#### Step 3: Claim-Source Alignment

For EACH claim with a citation:

a) **RETRIEVE** the cited paper's abstract (via PubMed/OpenAlex)

b) **For high-stakes claims** (Introduction gap statement, Discussion interpretation): attempt full-text retrieval via `bgpt-paper-search`, PMC open-access, bioRxiv preprint

c) **COMPARE** the claim against the source:
- Does the source support this specific claim?
- Are the numbers accurate? (30% vs 28% drift)
- Is the directionality correct? (reduced vs increased)
- Is the population the same? (adults vs children)

d) **CONFIDENCE SCORE:**
- ✅ VERIFIED — source directly supports the claim
- ⚠️ PLAUSIBLE — source is related but claim is interpretive
- ❌ UNSUPPORTED — source does not support this claim
- 🔴 CONTRADICTED — source says the opposite

e) **MARK:** "verified against abstract only" vs "verified against full text"

**Output:** `verification/claim_verification_report.md`

---

## 12. SUPPLEMENTARY MATERIALS

### What Goes in the Supplement

The orchestrator creates a `supplement/` directory at project initialisation. Multiple agents contribute:

| Agent | Supplementary Output |
|---|---|
| 3 (Study Design) | Full protocol |
| 4 (Statistician) | Complete statistical analysis plan |
| 5 (Results Writer) | Extended data tables, additional sensitivity analyses |
| 6 (Figure Engine) | Additional figures not in main text |
| 10 (Compliance) | Completed reporting checklist with page numbers |
| 18 (Data Analyst) | analysis_code.py (reproducible code) |

### Structure

```
supplement/
├── protocol.md               (full study protocol)
├── full_sap.md               (complete SAP, not abbreviated)
├── extended_tables/           (tables too large for main text)
├── sensitivity_analyses/      (alternative models, robustness checks)
├── additional_figures/        (figures not included in main text)
├── reporting_checklist.md     (CONSORT/STROBE with page numbers)
├── search_strategy.md         (for systematic reviews: full search strings)
└── analysis_code.py           (reproducible analysis code)
```

---

## 13. NULL-RESULT HANDLING

### Detection

The orchestrator checks `results_package.json` for the primary outcome. If:
- P-value for primary outcome > 0.05, OR
- Confidence interval for primary effect includes the null value (HR=1.0, OR=1.0, difference=0)

→ Flag as null result and activate null-result protocols.

### Story Architect: Null-Result Narrative Template

```
TENSION:       The problem is real and the intervention seemed promising
GAP:           No adequately powered trial had tested this
KEY FINDING:   The intervention did NOT improve the primary outcome
TWIST:         This null finding is informative because [specific reason]
PUNCHLINE:     Clinicians should NOT adopt X / should STOP doing Y
LIMITATIONS:   Honest but not self-defeating — the trial was well-powered
               and the null finding is reliable
```

### Spin Detection

Agent 14 (Scoring) includes a spin detector (`scripts/spin-detector.py`) that flags:

| Spin Pattern | Example | Fix |
|---|---|---|
| "Trend towards significance" | "There was a trend towards reduced mortality (p=0.08)" | Report as: "No significant difference was observed (HR 0.87, 95% CI 0.74-1.02, p=0.08)" |
| Reframing null primary as positive secondary | Leading Discussion with a significant secondary endpoint | Lead with the null primary result |
| Burying the null | Null result mentioned in paragraph 3 of Discussion | Null result MUST be the first sentence of Discussion |
| "Numerically lower but not significant" | Implying the result is "almost significant" | State the result and its CI; let the reader interpret |
| Selective emphasis on subgroups | Highlighting the one subgroup that was significant | State that no pre-specified subgroup interaction was significant |

---

## 14. PRE-SUBMISSION INQUIRY MODE

### What It Is

A lightweight pipeline mode that produces ONLY the materials needed for a pre-submission inquiry to the target journal. Many editors (especially at Lancet) respond to inquiries within days, saving months of full manuscript preparation if the study is not a fit.

### Pipeline

Uses only Agents 1, 2, 7, 8, 11:

```
Agent 1 (Literature) → evidence summary + gap
Agent 2 (Story Architect) → narrative blueprint
Agent 7 (Narrative Writer) → Research in Context panel OR Key Points
Agent 8 (Abstract) → structured abstract in journal format
Agent 11 (Editor) → cover letter explaining why this journal
```

### Output

```
pre-submission-inquiry/
├── abstract.md            (journal-formatted)
├── research-in-context.md (Lancet) OR key-points.md (JAMA)
├── cover-letter.md        (why this journal, key findings)
└── summary-table.md       (study design, N, endpoints, key results)
```

---

## 15. PROJECT DIRECTORY STRUCTURE

When invoked, the orchestrator creates this directory structure:

```
paper-project-[YYYY-MM-DD]/
├── data/
│   ├── raw/                    (original data files — NEVER modified)
│   ├── clean/                  (validated, cleaned data)
│   ├── analysis/               (analysis-ready datasets per population)
│   ├── data_profile.md
│   ├── data_dictionary.json
│   ├── validation_report.md
│   ├── cleaning_log.md
│   └── data_hashes.json        (SHA-256 of raw + clean)
├── analysis/
│   ├── statistical_plan.md
│   ├── results_package.json    (THE source of truth for ALL numbers)
│   ├── analysis_code.py        (reproducible code)
│   ├── assumption_checks.md
│   ├── statistical_report.md
│   ├── primary_results.json
│   ├── secondary_results.json
│   ├── subgroup_results.json
│   ├── sensitivity_results.json
│   ├── table1.md
│   └── figures/                (all statistical figures)
├── plan/
│   ├── paper-plan.md           (Gate 1 artifact)
│   ├── narrative-blueprint.md
│   ├── literature-matrix.md
│   ├── triage-report.md
│   └── style-profile.yaml     (copy of loaded journal config)
├── draft/
│   ├── title-page.md
│   ├── abstract.md
│   ├── introduction.md
│   ├── methods.md
│   ├── results.md
│   ├── discussion.md
│   ├── conclusion.md
│   ├── figures/
│   └── tables/
├── supplement/
│   ├── protocol.md
│   ├── full_sap.md
│   ├── extended_tables/
│   ├── sensitivity_analyses/
│   ├── additional_figures/
│   ├── reporting_checklist.md  (with page numbers)
│   └── analysis_code.py
├── final/
│   ├── manuscript.md
│   ├── manuscript.pdf
│   ├── cover-letter.md
│   ├── declarations.md
│   ├── credit-statement.md     (CRediT taxonomy — Gap 9)
│   ├── ppi-statement.md        (Patient and Public Involvement — Gap 8)
│   ├── data-sharing-statement.md
│   ├── ai-disclosure.md
│   └── references.bib
├── verification/
│   ├── claim_verification_report.md
│   ├── score_card.md
│   ├── consistency_check.md
│   └── reference_status.json
├── revisions/                  (populated after peer review)
│   ├── reviewer-comments.md
│   ├── response-letter.md
│   └── tracked-changes.md
└── meta/
    ├── score_trajectory.json   (scores across iterations)
    ├── agent_dispatch_log.json (which agents were called for fixes)
    └── protocol_updates.md     (Meta-Evaluator output)
```

---

## 16. EXISTING SKILLS INTEGRATION

This system DELEGATES to existing skills — it never replaces them. Agent protocols contain instructions like "invoke the literature-review skill" or "use the pubmed-database skill."

### Integration Map

| Existing Skill | Used By Agent(s) | Integration Pattern |
|---|---|---|
| `paper-writer/` (34 templates, 28 refs, 7 scripts) | 3, 5, 7, 8, 10, 11, 13 | Templates loaded by agent protocols; scripts called directly |
| `literature-review/` (PRISMA workflow, verify_citations.py) | 1, 9, 16 | Full workflow delegated; DOI verification reused |
| `scientific-visualization/` (style_presets.py, figure_export.py) | 6 | Style presets extended by figure-styler.py |
| `scientific-schematics/` (AI diagram generation) | 6 | CONSORT/PRISMA diagrams, graphical abstracts, pathway diagrams |
| `citation-management/` (DOI→BibTeX, CrossRef) | 9, 16 | DOI resolution, metadata verification |
| `pubmed-database/` (MeSH queries, E-utilities) | 1, 16 | Abstract retrieval, PMID lookup |
| `openalex-database/` (240M+ works) | 1, 16 | DOI verification, citation counts, retraction status |
| `biorxiv-database/` (preprints) | 1, 16 | Preprint search, PDF access |
| `bgpt-paper-search/` (full-text structured data) | 16 | Full-text claim verification |
| `research-lookup/` (Perplexity / Parallel Chat routing) | 1, 2 | Quick research queries, academic paper searches |
| `humanizer-academic/` (AI detection patterns) | 12 | Word blacklist, detection patterns, before/after examples |
| `statsmodels/`, `statistical-analysis/`, `scikit-learn/` | 18 | Statistical model execution |
| `scikit-survival/` | 18 | Survival analysis (Cox, KM, competing risks) |
| `scientific-writing/` (IMRAD, prose quality) | 7, 11 | Writing principles, field-specific language |
| `peer-review/` (review methodology) | 13 | Systematic review approach for responses |

### Skill Evolution Independence

Because agent protocols REFERENCE existing skills by delegation (not by copying content), improvements to existing skills automatically benefit the multi-agent system. If `paper-writer/scripts/table1.py` is enhanced, Agent 18 benefits without any change to its protocol.

---

## 17. INVOCATION AND WORKFLOW

### How to Invoke

```
/medical-paper-agents
```

Or trigger via: "write medical paper", "medical manuscript", "journal submission", "write for lancet", "write for nejm", "clinical paper", "research article"

### Invocation Modes

#### Full Pipeline Mode (default)
User provides: raw data file + research question + study protocol (optional)
System executes: all 15 steps through all 5 gates

#### Pre-Submission Inquiry Mode
User says: "pre-submission inquiry for [journal]"
System executes: Agents 1, 2, 7, 8, 11 only → produces abstract + panel + cover letter

#### Revision Mode
User provides: peer reviewer comments
System executes: Agent 13 (Peer Review Response) → produces point-by-point response + tracked changes

### First Interaction

When invoked, the orchestrator:

1. Asks the user for:
   - Raw data file path
   - Research question / study objective
   - Study type (RCT, observational, systematic review, case report, etc.)
   - Target journal (or "recommend" for triage)
   - Study protocol (if available)
   - Author list with roles (for CRediT)

2. Creates the project directory structure

3. Loads the appropriate style profile (or defers to Agent 0.5 Triage if journal not specified)

4. Selects the reporting guideline based on study type

5. Begins Step 0a (Data Engineer) or Step 0.5 (Triage) depending on whether data is provided

### Mandatory Rules

1. **NEVER compute a number in prose.** All numbers come from results_package.json.
2. **NEVER fabricate a reference.** All references must resolve via DOI/PMID.
3. **NEVER skip a gate.** Every gate requires explicit user approval.
4. **NEVER modify raw data.** The raw/ directory is read-only after ingest.
5. **NEVER run the inner loop more than 5 times.** Present best version and let user decide.
6. **ALWAYS load the style profile** before any writing agent runs.
7. **ALWAYS run the claim verifier** before presenting at Draft and Final gates.
8. **ALWAYS check for retractions** before finalising references.
9. **Humanizer is ALWAYS the last writing agent.** No agent touches prose after Agent 12.
10. **Conflict resolution follows the fixed hierarchy.** No exceptions without user override.

---

## APPENDIX A: New Scripts

| Script | Purpose | Key Dependencies |
|---|---|---|
| `scripts/data-ingest.py` | Universal data reader (CSV, Excel, SAS, Stata, SPSS, Parquet) | pandas, polars, pyreadstat |
| `scripts/data-validate.py` | Medical data validation (impossible values, duplicates, consistency) | pandas, pandera |
| `scripts/data-derive.py` | Derive populations, composite endpoints, CONSORT flow numbers | pandas |
| `scripts/results-packager.py` | Assemble results_package.json from analysis outputs | json, hashlib |
| `scripts/assumption-checks.py` | PH test, normality, VIF, homoscedasticity | statsmodels, scipy |
| `scripts/multiple-imputation.py` | MICE-style multiple imputation | sklearn, miceforest |
| `scripts/km-plot.py` | Enhanced Kaplan-Meier with number-at-risk table | lifelines, matplotlib |
| `scripts/roc-curve.py` | ROC curve with AUC, CI, optimal threshold | sklearn, matplotlib |
| `scripts/funnel-plot.py` | Publication bias funnel plot | matplotlib |
| `scripts/waterfall-plot.py` | Treatment response waterfall | matplotlib |
| `scripts/swimmer-plot.py` | Patient timeline swimmer plot | matplotlib |
| `scripts/competing-risks.py` | Cumulative incidence with competing risks | lifelines, matplotlib |
| `scripts/figure-styler.py` | Apply journal YAML style to any matplotlib figure | matplotlib, pyyaml |
| `scripts/consistency-checker.py` | Verify numbers in text match results_package.json | json, re |
| `scripts/spin-detector.py` | Detect positive spin on null results | re |
| `scripts/retraction-checker.py` | Check references against retraction databases | requests (CrossRef API) |

## APPENDIX B: Templates

| Template | Purpose |
|---|---|
| `templates/project-init-multi-agent.md` | Project directory structure and initialisation checklist |
| `templates/results-package-schema.json` | JSON Schema for results_package.json |
| `templates/narrative-blueprint.md` | Story Architect output format |
| `templates/null-result-narrative.md` | Null-result story framing template |
| `templates/triage-report.md` | Journal fit assessment format |
| `templates/score-card.md` | Scoring agent output format |
| `templates/coherence-check.md` | Post-inner-loop coherence verification |
| `templates/ppi-statement.md` | Patient and Public Involvement statement |
| `templates/credit-statement.md` | CRediT contributor roles (14 roles) |
| `templates/pre-submission-inquiry.md` | Lightweight pipeline output format |

## APPENDIX C: Reference Documents

| Reference | Purpose |
|---|---|
| `references/conflict-resolution-rules.md` | Priority hierarchy with examples |
| `references/hard-soft-metrics-spec.md` | Complete metric definitions and formulas |
| `references/inner-loop-protocol.md` | Iteration process, revert rules, coherence check |
| `references/outer-loop-protocol.md` | Meta-evaluation process, protocol update format |
| `references/data-pipeline-spec.md` | 6-stage pipeline specification, hash chain |
