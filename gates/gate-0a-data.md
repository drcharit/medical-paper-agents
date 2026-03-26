# Gate 0a: Data Gate

## Position in Pipeline

**Follows:** Step 0a — Agent 17 (Data Engineer)
**Precedes:** Step 0b — Agent 18 (Data Analyst)
**Gate Type:** User Approval (no automated scoring threshold)

---

## Purpose

Ensure that the raw data has been correctly ingested, validated, cleaned, and that derived
populations are accurate before any statistical analysis begins. This gate protects the
entire downstream pipeline: every number in the final manuscript traces back to the data
approved here.

---

## Required Artifacts

The orchestrator MUST verify that ALL of the following artifacts exist and are non-empty
before presenting Gate 0a to the user. If any artifact is missing, the gate cannot open.

| # | Artifact | Path | Description |
|---|----------|------|-------------|
| 1 | Data Profile | `data/data_profile.md` | N rows, N columns, variable types, distributions, missingness per variable |
| 2 | Validation Report | `data/validation_report.md` | Impossible values, duplicates, cross-field inconsistencies, outliers flagged |
| 3 | Cleaning Log | `data/cleaning_log.md` | Every transformation applied, with before/after counts and justification |
| 4 | Data Hashes | `data/data_hashes.json` | SHA-256 hashes of raw data file(s) and clean data file(s) |
| 5 | Population Flow | `data/population_flow.json` | N at each inclusion/exclusion step, final analysis population sizes |

---

## What to Present to the User

The orchestrator summarises the following in a structured gate review panel:

### Data Summary
- **Total rows loaded:** N (from data_profile.md)
- **Total columns loaded:** N (from data_profile.md)
- **Data source format:** CSV / Excel / SAS / Stata / SPSS / Parquet / REDCap

### Data Quality Summary
- **Flagged values count:** N impossible values identified (from validation_report.md)
- **Duplicate records:** N exact duplicates, N fuzzy matches (from validation_report.md)
- **Missing data:** Top 5 variables by missingness %, overall missingness rate
- **Outliers flagged:** N values flagged as potential outliers (NOT removed, flagged only)

### Population Flow
- **Starting N:** N records in raw data
- **Exclusion counts:** N excluded at each criterion step (from population_flow.json)
- **Final analysis populations:**
  - ITT: N
  - Modified ITT: N (if applicable)
  - Per-protocol: N (if applicable)
  - Safety: N (if applicable)

### Data Integrity
- **Raw data hash:** SHA-256 value (from data_hashes.json)
- **Clean data hash:** SHA-256 value (from data_hashes.json)

### Transformations Applied
- Bullet list of all cleaning steps from cleaning_log.md (variable renames, type corrections,
  unit conversions, derived variables)

---

## Scoring

**There is no automated scoring threshold at Gate 0a.** The data pipeline does not produce
a score card. The user reviews the artifacts and makes a judgment call. However, the
orchestrator MUST flag the following failure conditions before presenting the gate.

---

## Failure Conditions (Pre-Gate Checks)

The orchestrator runs these checks BEFORE presenting the gate. If any condition is met,
the orchestrator warns the user prominently.

| # | Condition | Detection | Severity |
|---|-----------|-----------|----------|
| F1 | No data loaded | `data_profile.md` reports 0 rows or does not exist | **BLOCKING** — cannot proceed |
| F2 | >20% missing in key variables | Any variable listed in the SAP as primary/secondary endpoint or key covariate has >20% missing | **WARNING** — prominently flagged |
| F3 | >5% impossible values | Count of impossible values / total cells > 5% | **WARNING** — prominently flagged |
| F4 | Zero records in any analysis population | Any population in `population_flow.json` has N = 0 | **BLOCKING** — cannot proceed |
| F5 | Hash mismatch | `data_hashes.json` cannot be computed or is internally inconsistent | **WARNING** — data integrity concern |

**BLOCKING** conditions prevent the gate from being presented as "ready for approval."
The user sees the issue and must direct Agent 17 to fix it before the gate can be re-attempted.

**WARNING** conditions are displayed prominently but the user may still approve if they
judge the issue acceptable (e.g., missingness is expected and will be handled by imputation).

---

## User Actions at Gate 0a

| Action | What Happens |
|--------|--------------|
| **Approve** | Clean data and population_flow.json are locked (immutable from this point). SHA-256 hashes recorded. Pipeline proceeds to Step 0b (Agent 18). |
| **Request re-cleaning** | User specifies what to change (e.g., "exclude patients aged < 18", "recode variable X"). Orchestrator re-dispatches Agent 17 with instructions. Gate 0a re-presents after re-cleaning. |
| **Flag additional issues** | User identifies problems not caught by validation (e.g., "these 12 IDs are known duplicates from site 3"). Agent 17 addresses and re-presents. |

---

## Post-Approval Immutability

Once the user approves Gate 0a:

1. The clean data files become **immutable**. No agent may modify them.
2. The `data_hashes.json` values are the reference checksums for the rest of the pipeline.
3. Agent 18 (Data Analyst) reads ONLY from the approved clean data.
4. If the user later discovers a data issue (after Gate 0a), the orchestrator must:
   - Roll back to pre-Gate 0a state
   - Re-run Agent 17 with corrections
   - Re-present Gate 0a
   - Re-run ALL downstream steps (0b onward)

---

## Orchestrator Checklist

Before presenting Gate 0a, the orchestrator verifies:

- [ ] All 5 required artifacts exist and are non-empty
- [ ] No BLOCKING failure conditions are active
- [ ] WARNING conditions are prominently displayed
- [ ] Population flow numbers are internally consistent (sum of excluded + included = total)
- [ ] Cleaning log entries are complete (no "TODO" or placeholder entries)
- [ ] Data hashes are valid SHA-256 format
