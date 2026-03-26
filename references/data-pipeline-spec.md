# Data Pipeline Specification

## Version 1.0.0
## Date: 2026-03-26
## Author: Medical Paper Agents System

---

## 1. OVERVIEW

The data pipeline transforms raw clinical data into an immutable results package that serves as the single source of truth for all numbers in the manuscript. It enforces a strict separation between data producers (Agents 17, 18) and data consumers (all writing agents).

### The Golden Rule

**Numbers flow ONE way. No writing agent ever computes a number.**

```
raw_data -> clean_data -> analysis_data -> results_package.json -> manuscript
  (immutable)  (immutable       (immutable         (immutable
                after 0a)        after 0a)          after 0b)
```

Every writing agent (5, 6, 7, 8) READS from `results_package.json`. If a number appears in prose that does not exist in `results_package.json`, it is an error. Agent 14 (Scoring) enforces this via `scripts/consistency-checker.py`.

---

## 2. 6-STAGE PIPELINE

### Stage Overview

| Stage | Agent | Input | Output | Script |
|---|---|---|---|---|
| 1. Ingest | 17 | Raw data file | data_profile.md, data_dictionary.json | data-ingest.py |
| 2. Validate | 17 | Ingested data | validation_report.md, cleaning_log.md, clean data | data-validate.py |
| 3. Derive | 17 | Clean data + protocol | Population datasets, population_flow.json | data-derive.py |
| 4. Describe | 18 | Analysis data + SAP | table1.md, descriptive_stats.md | table1.py |
| 5. Analyse | 18 | Analysis data + SAP | All statistical results (JSON) | analysis-template.py |
| 6. Package | 18 | All analysis outputs | results_package.json | results-packager.py |

### Gate Boundaries

```
Stages 1-3 (Agent 17) -> GATE 0a (Data Gate) -> Stages 4-6 (Agent 18) -> GATE 0b (Results Gate)
```

Gate 0a approval seals stages 1-3 outputs. Gate 0b approval seals stage 6 output. No downstream modification is permitted after approval.

---

## 3. STAGE SPECIFICATIONS

### Stage 1: Ingest and Profile

**Input:** Raw data file path (CSV, Excel, SAS, Stata, SPSS, Parquet, JSON, REDCap export, or directory of files)

**Processing:**
1. Copy raw file to `data/raw/` without modification
2. Read data into memory (polars for large files, pandas for specialty formats)
3. Detect column types (numeric, categorical, datetime, identifier, binary)
4. Generate descriptive statistics per column
5. Compute SHA-256 hash of raw file

**Output:**
| Artifact | Path | Format |
|---|---|---|
| Data profile | `data/data_profile.md` | Markdown |
| Data dictionary | `data/data_dictionary.json` | JSON |
| Raw data hash | `data/raw_data_hash.txt` | Text |

**Error conditions:** Unrecognised format, encoding failure, empty file, memory overflow.

### Stage 2: Validate and Clean

**Input:** Ingested data from Stage 1

**Processing:**
1. Apply impossible-value rules (medical domain: age, BMI, labs, dates, vitals)
2. Detect exact and fuzzy duplicates
3. Run cross-field consistency checks (temporal ordering, logical coherence)
4. Correct variable types (string-to-date, coded-to-categorical)
5. Standardise units (mg/dL to mmol/L, lb to kg)
6. Flag outliers using IQR method AND clinical thresholds
7. Standardise missing value representations to null

**Output:**
| Artifact | Path | Format |
|---|---|---|
| Clean dataset | `data/clean/*.parquet` | Parquet |
| Clean dataset (interchange) | `data/clean/*.csv` | CSV |
| Validation report | `data/validation_report.md` | Markdown |
| Cleaning log | `data/cleaning_log.md` | Markdown |
| Data hashes (updated) | `data/data_hashes.json` | JSON |

**Critical rule:** Outliers are FLAGGED, never removed. User decides at Gate 0a.

**Error conditions:** No identifier found, all values missing in column, ambiguous dates, uncertain units.

### Stage 3: Derive and Define Populations

**Input:** Clean data from Stage 2, study protocol (optional)

**Processing:**
1. Apply inclusion/exclusion criteria SEQUENTIALLY, tracking N at each step
2. Define populations (ITT, mITT, PP, Safety)
3. Create composite endpoints (MACE, co-primary, time-to-first-event)
4. Derive standard variables (BMI, eGFR, follow-up duration, age categories)
5. Create subgroup variables from protocol specifications
6. Generate CONSORT/STROBE flow structure

**Output:**
| Artifact | Path | Format |
|---|---|---|
| ITT dataset | `data/analysis/analysis_itt.parquet` | Parquet |
| mITT dataset | `data/analysis/analysis_mitt.parquet` | Parquet |
| PP dataset | `data/analysis/analysis_pp.parquet` | Parquet |
| Safety dataset | `data/analysis/analysis_safety.parquet` | Parquet |
| Population flow | `data/population_flow.json` | JSON |
| Data hashes (updated) | `data/data_hashes.json` | JSON |

**Critical rule:** N decrements must be additive. N_raw - sum(exclusions) = N_analysis.

**Error conditions:** Missing protocol criteria, endpoint variable absent, count discrepancy, missing composite component.

### Stage 4: Describe

**Input:** Analysis datasets from Stage 3, SAP from Agent 4

**Processing:**
1. Generate Table 1 (RCT: no p-values + SMD; Observational: with p-values)
2. Assess distribution shape per variable (Shapiro-Wilk)
3. Compute follow-up duration (reverse KM for median)
4. Compute event rates per endpoint per arm
5. Summarise missingness patterns and assess mechanism (Little's MCAR test)

**Output:**
| Artifact | Path | Format |
|---|---|---|
| Table 1 | `analysis/table1.md` | Markdown |
| Descriptive statistics | `analysis/descriptive_stats.md` | Markdown |

**Error conditions:** Variable not in data, Shapiro-Wilk fails on large N, zero events.

### Stage 5: Analyse

**Input:** Analysis datasets, SAP, Table 1 results

**Processing:**
1. Execute primary analysis per SAP (Cox PH, logistic, linear, mixed model)
2. Run assumption checks (PH via Schoenfeld, normality, VIF, homoscedasticity)
3. Execute all secondary analyses
4. Execute all subgroup analyses with interaction tests
5. Execute all sensitivity analyses (PP, complete case, alternative models)
6. Handle missing data (MCAR/MAR/MNAR assessment, MICE if MAR)
7. Perform survival analysis (KM, log-rank, number-at-risk, reverse KM follow-up)
8. Generate reproducible analysis code

**Output:**
| Artifact | Path | Format |
|---|---|---|
| Primary results | `analysis/primary_results.json` | JSON |
| Secondary results | `analysis/secondary_results.json` | JSON |
| Subgroup results | `analysis/subgroup_results.json` | JSON |
| Sensitivity results | `analysis/sensitivity_results.json` | JSON |
| Assumption checks | `analysis/assumption_checks.md` | Markdown |
| Analysis code | `analysis/analysis_code.py` | Python |
| Figures | `analysis/figures/` | PNG/SVG |

**Error conditions:** Convergence failure, perfect separation, PH violation, zero events in subgroup, imputation failure.

### Stage 6: Package Results

**Input:** All Stage 4-5 outputs, population_flow.json

**Processing:**
1. Assemble all results into `results_package.json`
2. Validate against `templates/results-package-schema.json`
3. Compute SHA-256 hash of the package
4. Run internal consistency checks (5 mandatory cross-references)
5. Generate human-readable statistical report

**Output:**
| Artifact | Path | Format |
|---|---|---|
| Results package | `analysis/results_package.json` | JSON |
| Statistical report | `analysis/statistical_report.md` | Markdown |
| Data hashes (updated) | `data/data_hashes.json` | JSON |

**Error conditions:** Schema validation failure, N consistency failure, hash mismatch.

---

## 4. HASH CHAIN DEFINITION

### Purpose

SHA-256 hashes create a tamper-evident chain from raw data to final results. Any modification to an upstream artifact invalidates all downstream hashes.

### Chain Structure

```
H0 = SHA-256(raw_data_file)
  |
H1 = SHA-256(clean_data.parquet)
  |
H2a = SHA-256(analysis_itt.parquet)
H2b = SHA-256(analysis_mitt.parquet)
H2c = SHA-256(analysis_pp.parquet)
H2d = SHA-256(analysis_safety.parquet)
  |
H3 = SHA-256(population_flow.json)
  |
H4 = SHA-256(results_package.json)
```

### Hash Computation

All hashes use SHA-256 computed over the full file bytes:

```python
import hashlib

def compute_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()
```

### Hash Storage

All hashes are stored in `data/data_hashes.json`:

```json
{
  "raw_data":       { "file": "...", "sha256": "...", "timestamp": "..." },
  "clean_data":     { "file": "...", "sha256": "...", "timestamp": "..." },
  "analysis_itt":   { "file": "...", "sha256": "...", "timestamp": "..." },
  "analysis_mitt":  { "file": "...", "sha256": "...", "timestamp": "..." },
  "analysis_pp":    { "file": "...", "sha256": "...", "timestamp": "..." },
  "analysis_safety":{ "file": "...", "sha256": "...", "timestamp": "..." },
  "population_flow":{ "file": "...", "sha256": "...", "timestamp": "..." },
  "results_package":{ "file": "...", "sha256": "...", "timestamp": "..." }
}
```

### Hash Verification

At each gate, the presenting agent verifies that stored hashes match current file contents. A mismatch indicates unauthorised modification and halts the pipeline.

---

## 5. IMMUTABILITY RULES

### Rule 1: Raw Data Is Never Modified

The `data/raw/` directory is write-once. After the raw file is copied in Stage 1, no agent, script, or process may modify, delete, or append to any file in this directory. The raw data hash (H0) must remain valid for the lifetime of the project.

### Rule 2: Clean Data Is Immutable After Gate 0a

Before Gate 0a, the clean data may be regenerated if the user requests re-cleaning. After the user approves at Gate 0a:
- `data/clean/` becomes immutable
- `data/analysis/` becomes immutable
- `data/data_hashes.json` entries for H1, H2a-H2d, H3 are sealed
- Any change requires re-running Agent 17 from scratch and re-presenting at Gate 0a

### Rule 3: Results Package Is Immutable After Gate 0b

Before Gate 0b, the results package may be regenerated if the user requests additional analyses. After the user approves at Gate 0b:
- `analysis/results_package.json` becomes immutable
- Its hash (H4) is sealed
- No writing agent may introduce a number not in this package
- Any change requires re-running Agent 18 and re-presenting at Gate 0b

### Rule 4: Immutability Cascade

If an upstream artifact must change, ALL downstream artifacts are invalidated:
- Raw data change -> everything re-runs (Stages 1-6, Gates 0a and 0b)
- Clean data change -> Stages 3-6 re-run (Gates 0a and 0b)
- Population change -> Stages 3-6 re-run (Gates 0a and 0b)
- SAP change -> Stages 4-6 re-run (Gate 0b only)

---

## 6. DATA FORMAT STANDARDS

### Analysis Datasets: Parquet

All analysis-ready datasets are stored in Apache Parquet format:
- Columnar storage for efficient analytical queries
- Built-in compression (snappy by default)
- Schema embedded in file (self-describing)
- Preserves data types exactly (no CSV type-guessing)
- Readable by pandas, polars, R (arrow), Stata (via conversion)

### Results: JSON

All statistical results are stored as JSON:
- `results_package.json` -- the master results file
- `primary_results.json` -- detailed primary analysis
- `secondary_results.json` -- all secondary analyses
- `subgroup_results.json` -- subgroup analyses
- `sensitivity_results.json` -- sensitivity analyses
- `population_flow.json` -- CONSORT/STROBE flow
- `data_dictionary.json` -- variable metadata
- `data_hashes.json` -- hash chain

JSON is chosen because it is human-readable, machine-parseable, schema-validatable, and universally supported.

### Interchange: CSV

CSV files are provided alongside Parquet for:
- Review by collaborators who do not have Parquet readers
- Import into statistical packages (SAS, Stata, SPSS, R)
- Data sharing and archival

CSV is NEVER the primary analysis format (Parquet is). CSV is provided as a convenience copy.

### Reports: Markdown

All human-readable reports are Markdown:
- `data_profile.md`
- `validation_report.md`
- `cleaning_log.md`
- `assumption_checks.md`
- `statistical_report.md`
- `table1.md`
- `descriptive_stats.md`

### Figures: PNG and SVG

All statistical figures are saved in both formats:
- PNG at 300 DPI for manuscript inclusion
- SVG for scalable, editable vector graphics

---

## 7. ERROR HANDLING BY STAGE

### Stage 1 Error Protocol

| Error | Severity | Action |
|---|---|---|
| File not found | FATAL | Report to user; cannot proceed |
| Unrecognised format | FATAL | Report supported formats; ask user to convert |
| Encoding error | RECOVERABLE | Try UTF-8, Latin-1, CP1252 in order; if all fail, ask user |
| Memory overflow | RECOVERABLE | Switch to chunked/polars reading; if still fails, ask user to subset |
| Empty file | FATAL | Report to user; cannot proceed |
| Corrupt file | FATAL | Report to user; request replacement |

### Stage 2 Error Protocol

| Error | Severity | Action |
|---|---|---|
| No identifier column | WARNING | Flag to user with candidates; proceed without duplicate check |
| Entirely missing column | WARNING | Flag at gate; do not drop column |
| Ambiguous date format | WARNING | Flag with examples; use most common format; confirm at gate |
| Unit uncertainty | WARNING | Flag with value range; proceed with best guess; confirm at gate |
| >50% values flagged impossible | CRITICAL | Likely unit or coding error; halt and ask user before proceeding |

### Stage 3 Error Protocol

| Error | Severity | Action |
|---|---|---|
| Missing protocol criteria | BLOCKING | Ask orchestrator for criteria; cannot define populations without them |
| Endpoint variable absent | CRITICAL | Report missing variable; list available alternatives |
| N does not reconcile | CRITICAL | Report discrepancy with details; do not guess |
| Composite component missing | WARNING | Report; derive partial composite if protocol allows |

### Stage 4 Error Protocol

| Error | Severity | Action |
|---|---|---|
| Variable not in analysis data | WARNING | Skip variable in Table 1; document omission |
| Normality test inconclusive | WARNING | Use median (IQR) as safer default; note in report |
| Zero events in arm | WARNING | Report rate as 0; note insufficient events for comparison |

### Stage 5 Error Protocol

| Error | Severity | Action |
|---|---|---|
| Convergence failure | CRITICAL | Try alternative optimiser; simplify model; report with diagnostics |
| Perfect separation | CRITICAL | Use Firth's penalised likelihood; document |
| PH assumption violated | WARNING | Fit stratified Cox or time-varying model; report both |
| Zero events in subgroup | WARNING | Report as non-estimable; do not force-fit |
| Imputation divergence | CRITICAL | Simplify imputation model; check collinearity; report |

### Stage 6 Error Protocol

| Error | Severity | Action |
|---|---|---|
| Schema validation failure | BLOCKING | Fix offending field; do not present until valid |
| N inconsistency | CRITICAL | Investigate source; fix if error; document if legitimate |
| Hash mismatch | CRITICAL | Verify pipeline integrity; re-run from last known good state |

### Severity Definitions

- **FATAL:** Pipeline cannot proceed. User intervention required.
- **CRITICAL:** Pipeline can proceed but results may be unreliable. Prominent flag at gate.
- **BLOCKING:** This specific stage cannot complete. Other stages may proceed.
- **WARNING:** Issue noted and flagged. Pipeline continues. User reviews at gate.
- **RECOVERABLE:** System attempts automatic recovery. If recovery fails, escalate to WARNING or CRITICAL.

---

## 8. CROSS-STAGE CONSISTENCY CHECKS

These checks are run at Stage 6 packaging time and again at each gate:

| Check | Assertion | Failure Action |
|---|---|---|
| N primary = N Table 1 | primary_results.n == table1.total_n | Investigate and fix |
| N primary = N CONSORT | primary_results.n == consort_flow.analysed.n | Investigate and fix |
| N subgroup = N primary | sum(subgroup.levels.n) == primary_results.n | Investigate and fix |
| N sensitivity = N population | sensitivity.n == populations[pop].n | Investigate and fix |
| Events <= N | events_per_arm <= n_per_arm | Fix if violated |
| Person-years plausible | person_years ~ n * median_followup | Flag if >20% deviation |
| Effect direction consistent | HR < 1 iff rate_treatment < rate_control | Investigate if inconsistent |
| CI contains estimate | ci_lower <= estimate <= ci_upper | Fix (computation error) |
| P-value consistent with CI | p < 0.05 iff CI excludes null | Investigate if inconsistent |

---

## 9. PIPELINE EXECUTION SEQUENCE

```
USER provides: raw data file + research question + (optional) study protocol

1. Orchestrator creates project directory structure
2. Orchestrator dispatches Agent 17 (Data Engineer)

   Agent 17 executes:
     Stage 1: Ingest    -> data_profile.md, data_dictionary.json, raw_data_hash
     Stage 2: Validate  -> validation_report.md, cleaning_log.md, clean data
     Stage 3: Derive    -> population datasets, population_flow.json

3. Orchestrator presents GATE 0a to user
   User reviews: validation report, flagged values, population counts
   User action: APPROVE / REQUEST CHANGES / FLAG ISSUES

4. If approved: clean data and analysis datasets become IMMUTABLE
5. Orchestrator dispatches Agent 18 (Data Analyst)

   Agent 18 executes:
     Stage 4: Describe  -> table1.md, descriptive_stats.md
     Stage 5: Analyse   -> all results JSONs, assumption checks, figures
     Stage 6: Package   -> results_package.json, statistical_report.md

6. Orchestrator presents GATE 0b to user
   User reviews: statistical results, assumption checks, key findings
   User action: APPROVE / REQUEST ANALYSES / MODIFY SAP / FLAG CONCERNS

7. If approved: results_package.json becomes IMMUTABLE
8. Pipeline complete. Manuscript writing phase begins (Agents 0.5-12).
   ALL writing agents read from results_package.json. None compute numbers.
```
