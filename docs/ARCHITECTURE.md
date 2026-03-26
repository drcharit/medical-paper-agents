# Medical Paper Agents: Architecture Documentation

## Overview

A multi-agent orchestration system for writing publication-quality medical research papers for top-tier journals (Lancet, NEJM, JAMA, BMJ, Circulation). 20 specialized agents, 5 human review gates, automated scoring with iterative refinement, claim verification, and a data pipeline from raw data to submission-ready manuscript.

**Repo:** https://github.com/drcharit/medical-paper-agents
**Skill path:** `~/.claude/skills/medical-paper-agents/`
**Invocation:** "write medical paper", "write for lancet", "clinical paper", or `/medical-paper-agents`

---

## Design Principles

1. **Numbers flow one way.** Raw data → results_package.json → prose. No writing agent ever computes a number.
2. **Agents = markdown protocols** loaded by the orchestrator one at a time into context. Not multi-process.
3. **Existing skills delegated to, never replaced.** Agent protocols say "invoke the literature-review skill" — they don't duplicate its logic.
4. **Hard metrics trigger automation; soft metrics are advisory.** Avoids the circularity of LLMs grading their own prose.
5. **Human gates at every phase transition.** You approve data, results, plan, draft, and final before each phase proceeds.

---

## Agent Roster (20 agents)

### Planning Phase
| # | Agent | Function |
|---|---|---|
| 0 | Orchestrator | Routes work, loads style profile, manages state, conflict resolution |
| 0.5 | Triage / Journal Fit | Evaluates if study is journal-worthy, recommends target journal |
| 1 | Literature & Gap Analysis | Systematic search, evidence synthesis, gap identification |
| 2 | Story Architect | Narrative blueprint (runs before any writing begins) |
| 3 | Study Design & Methods | Methods section, reporting guideline selection |
| 4 | Statistician | Dual role: SAP writer (Phase 0) + results verifier (Phase 2) |

### Data Phase
| # | Agent | Function |
|---|---|---|
| 17 | Data Engineer | Ingest raw data, validate, clean, derive populations |
| 18 | Data Analyst | Execute SAP on real data, produce results_package.json |

### Drafting Phase
| # | Agent | Function |
|---|---|---|
| 5 | Results Writer | Results section (reads ONLY from results_package.json) |
| 6 | Figure Engine | Routes to correct viz tool, applies journal style |
| 7 | Narrative Writer | Introduction, Discussion, journal-specific panels |
| 8 | Abstract & Summary | Journal-specific abstract (written last) |

### Polish Phase
| # | Agent | Function |
|---|---|---|
| 9 | Reference & Citation | Format citations, verify DOIs, check retractions |
| 10 | Compliance & Ethics | Reporting checklist, IRB, PPI, CRediT, declarations |
| 11 | Editor | Scientific English, flow, cover letter |
| 12 | Humanizer | AI-word removal, natural voice (last writing agent) |

### Quality & Verification
| # | Agent | Function |
|---|---|---|
| 14 | Scoring Agent | Read-only. Hard metrics (computable) + soft metrics (advisory) |
| 15 | Meta-Evaluator | Outer loop: identifies weak agents, proposes protocol improvements |
| 16 | Claim Verifier | Reference existence, retraction check, claim-source alignment |

### Post-Submission
| # | Agent | Function |
|---|---|---|
| 13 | Peer Review Response | Point-by-point response, revision tracking |

---

## 5-Gate System

```
DATA GATE (0a)     → You review: validation report, flagged values, exclusion counts
RESULTS GATE (0b)  → You review: statistical results, assumption checks, key findings
PLAN GATE (1)      → You review: paper plan, narrative blueprint, methods, triage report
DRAFT GATE (2)     → You review: manuscript + claim verification + score (threshold ≥85)
FINAL GATE (3)     → You review: polished manuscript + full verification (threshold ≥90)
```

---

## 15-Step Execution Topology

```
Step 0a:  Agent 17 (Data Engineer)              SOLO
  ═══ DATA GATE ═══
Step 0b:  Agent 18 (Data Analyst)               SOLO
  ═══ RESULTS GATE ═══
Step 0.5: Agent 0.5 (Triage)                    SOLO
Step 1:   Agent 1 (Literature)                  SOLO
Step 2:   Agent 2 (Story) ∥ Agent 3 (Methods)   PARALLEL
Step 3:   Agent 4 (Statistician verify)         SOLO
  ═══ PLAN GATE ═══
Step 4:   Agent 5 (Results) ∥ Agent 6 (Figures)  PARALLEL
Step 5:   Agent 7 (Narrative)                   SOLO
Step 6:   Agent 8 (Abstract)                    SOLO
Step 7:   Agent 14 (Score) ∥ Agent 16 (Verify)   PARALLEL
  ═══ DRAFT GATE ═══
Step 8:   Agent 9 (Refs) ∥ Agent 10 (Compliance) PARALLEL
Step 9:   Agent 11 (Editor)                     SOLO
Step 10:  Agent 12 (Humanizer)                  SOLO
Step 11:  Agent 14 (Score) ∥ Agent 16 (Verify)   PARALLEL
  ═══ FINAL GATE ═══
```

---

## Scoring System

### Hard Metrics (computable, trigger inner loop)

| # | Metric | Target |
|---|---|---|
| H1 | Word count within journal limit | ≤ limit |
| H2 | Reference count within limit | ≤ limit |
| H3 | Reporting checklist completion | ≥ 90% |
| H4 | AI-flagged word count | ≤ 3 |
| H5 | Sentence length std dev | ≥ 5.0 |
| H6 | DOI resolution | 100% |
| H7 | P-value formatting correct | 100% |
| H8 | No retracted references | 0 |
| H9 | Numbers match results_package.json | 100% |
| H10 | Internal N consistency | All match |

### Soft Metrics (advisory, shown at gate)

| # | Metric |
|---|---|
| S1 | Narrative coherence |
| S2 | Gap statement specificity |
| S3 | Discussion balance |
| S4 | Clinical implication clarity |

---

## Inner Loop (Iterative Refinement)

When hard metrics fall below gate threshold:

1. Score → 2. Identify weakest metric → 3. Dispatch responsible agent → 4. Fix → 5. Re-score → 6. Improved? Keep. Regressed? Revert. → 7. Coherence check → 8. Max 5 iterations

---

## Outer Loop (Skill Self-Improvement)

After paper completion, Agent 15 (Meta-Evaluator):
- Reviews score trajectory across iterations
- Identifies which agents were dispatched most for fixes
- Proposes protocol updates (presented to you for approval)
- Approved updates become permanent rules in agent protocols

---

## Conflict Resolution Hierarchy

```
Priority 1: Statistician overrules all on statistical claims
Priority 2: Compliance overrules all on regulatory requirements
Priority 3: Claim Verifier overrules all on factual accuracy
Priority 4: Story Architect overrules Narrative Writer on framing
Priority 5: Humanizer has final say on prose style
Priority 6: User overrules everyone at gates
```

---

## Data Pipeline (6 stages)

```
Stage 1: Ingest & Profile     → data_profile.md, data_dictionary.json
Stage 2: Validate & Clean     → validation_report.md, cleaning_log.md
Stage 3: Derive & Populations → ITT/PP/safety datasets, CONSORT flow numbers
Stage 4: Describe              → Table 1, descriptive stats
Stage 5: Analyse               → Primary, secondary, subgroup, sensitivity results
Stage 6: Package               → results_package.json (THE source of truth)
```

**Golden Rule:** Numbers flow one way. No writing agent computes numbers. All read from results_package.json. Immutable hash chain: raw_data → clean_data → results_package.

---

## Journal Style System

5 YAML profiles in `styles/` covering per-journal:
- Spelling variant (British/American)
- Decimal format (midline for Lancet, baseline for others)
- P-value format (leading zero or not, italic or not)
- Drug naming (rINN, USAN, BAN)
- Abstract headings and word limits
- AI-word blacklist (30 words)
- Sentence style targets

| Element | Lancet | NEJM | JAMA | BMJ | Circulation |
|---|---|---|---|---|---|
| English | British | American | American | British | American |
| Decimal | Midline (·) | Baseline (.) | Baseline (.) | Baseline (.) | Baseline (.) |
| P-value | 0·04 | .04 | .04 | 0.04 | .04 |
| Abstract | 300w, 5 headings | 250w, 4 headings | 350w + Key Points | 400w, 8 headings | 350w, 4 headings |
| Special | Research in Context | None | Key Points (Q/F/M) | What this adds | Clinical Perspective |

---

## Claim Verification (Hallucination Prevention)

3-step process:
1. **Extract** all factual claims with citations from manuscript
2. **Verify references** — DOI resolution, metadata match, retraction check
3. **Align claims to sources** — compare claim against abstract (or full text for high-stakes claims)

Each claim scored: VERIFIED / PLAUSIBLE / UNSUPPORTED / CONTRADICTED

---

## Null-Result Handling

- Story Architect has a null-result narrative template
- Spin detector (`scripts/spin-detector.py`) catches: "trend towards significance", reframing null primary as positive secondary, burying null after positive subgroup
- Narrative Writer: null result punchline = "stop doing X" or "don't adopt Y"

---

## Editor Corrections Incorporated

12 corrections from Lancet editor review:

1. Triage/Journal Fit Agent (prevents submitting wrong-level papers)
2. Hard/soft scoring split (avoids LLM grading its own work)
3. Supplementary materials infrastructure
4. Conflict resolution hierarchy
5. Null-result narrative template + spin detector
6. Full-text claim verification for high-stakes claims
7. Pre-submission inquiry mode
8. Patient and Public Involvement (PPI) statement
9. CRediT contributor roles taxonomy
10. Data quality assessment
11. Guideline cross-reference in Discussion
12. Post-inner-loop coherence check

---

## Modes of Operation

### Full Pipeline (default)
Raw data + research question → all 15 steps → submission-ready manuscript

### Pre-Submission Inquiry
Agents 1, 2, 7, 8, 11 only → abstract + panel + cover letter (tests journal interest)

### Revision Mode
Peer reviewer comments → Agent 13 → point-by-point response + tracked changes
