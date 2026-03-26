# File Inventory

## Summary
- **Total files:** 63
- **Total estimated lines:** ~25,000+
- **Repository:** https://github.com/drcharit/medical-paper-agents

---

## Root (2 files)

| File | Purpose |
|---|---|
| `SKILL.md` | Master architecture document (~1,130 lines). Defines all 20 agents, 5 gates, 15-step topology, scoring, loops, style system, data pipeline, claim verification. THE single source of truth. |
| `README.md` | Quick-start guide. Prerequisites, invocation, modes, agent roster. |

---

## Agent Protocols — `agents/` (20 files)

| File | Lines | Agent | Phase |
|---|---|---|---|
| `agent-00-orchestrator.md` | ~1,010 | Orchestrator | All |
| `agent-00.5-triage.md` | ~424 | Triage / Journal Fit | Pre-pipeline |
| `agent-01-literature.md` | ~400 | Literature & Gap Analysis | Phase 1 |
| `agent-02-story-architect.md` | ~338 | Story Architect | Phase 1 |
| `agent-03-study-design.md` | ~420 | Study Design & Methods | Phase 1 |
| `agent-04-statistician.md` | ~604 | Statistician (dual role) | Phase 0 + 2 |
| `agent-05-results-writer.md` | ~315 | Results Writer | Phase 2 |
| `agent-06-figure-engine.md` | ~429 | Figure Engine | Phase 2 |
| `agent-07-narrative-writer.md` | ~396 | Narrative Writer | Phase 2 |
| `agent-08-abstract-summary.md` | ~384 | Abstract & Summary | Phase 2 |
| `agent-09-reference-citation.md` | ~321 | Reference & Citation | Phase 3 |
| `agent-10-compliance-ethics.md` | ~536 | Compliance & Ethics | Phase 3 |
| `agent-11-editor.md` | ~408 | Editor | Phase 3 |
| `agent-12-humanizer.md` | ~426 | Humanizer | Phase 3 |
| `agent-13-peer-review-response.md` | ~501 | Peer Review Response | Post-submission |
| `agent-14-scoring.md` | ~773 | Scoring Agent | Cross-cutting |
| `agent-15-meta-evaluator.md` | ~820 | Meta-Evaluator | Post-completion |
| `agent-16-claim-verifier.md` | ~700 | Claim Verifier | Cross-cutting |
| `agent-17-data-engineer.md` | ~1,030 | Data Engineer | Phase 0 |
| `agent-18-data-analyst.md` | ~1,064 | Data Analyst | Phase 0 |

---

## Journal Style Profiles — `styles/` (5 files)

| File | Journal | Key Distinctions |
|---|---|---|
| `lancet.yaml` | The Lancet | British English, midline decimal (·), rINN drugs, Research in Context |
| `nejm.yaml` | NEJM | American English, USAN drugs, 2,700 word limit, conservative tone |
| `jama.yaml` | JAMA | AMA style, italic P, no leading zero, Key Points (Q/F/M) |
| `bmj.yaml` | BMJ | British English, BAN drugs (adrenaline), 8 abstract headings, active voice required |
| `circulation.yaml` | Circulation | AMA style, 7,000 word limit, Clinical Perspective, lists ALL authors |

---

## Gate Definitions — `gates/` (5 files)

| File | Gate | Threshold |
|---|---|---|
| `gate-0a-data.md` | Data Gate | User approval |
| `gate-0b-results.md` | Results Gate | User approval |
| `gate-1-plan.md` | Plan Gate | User approval |
| `gate-2-draft.md` | Draft Gate | Hard score ≥ 85 |
| `gate-3-final.md` | Final Gate | Hard score ≥ 90 |

---

## Reference Specifications — `references/` (5 files)

| File | Content |
|---|---|
| `conflict-resolution-rules.md` | 6-level priority hierarchy with examples |
| `hard-soft-metrics-spec.md` | 10 hard + 4 soft metric definitions, formulas, thresholds |
| `inner-loop-protocol.md` | Score-dispatch-fix-verify-revert iteration process |
| `outer-loop-protocol.md` | Meta-evaluation, protocol update proposals |
| `data-pipeline-spec.md` | 6-stage pipeline, hash chain, immutability rules |

---

## Templates — `templates/` (10 files)

| File | Purpose |
|---|---|
| `project-init-multi-agent.md` | Full project directory structure, initialization checklist |
| `results-package-schema.json` | JSON Schema for results_package.json (~1,014 lines) |
| `narrative-blueprint.md` | Story Architect output format (9-element arc) |
| `null-result-narrative.md` | Null-result story framing with spin prevention |
| `triage-report.md` | Journal fit assessment with scoring rubric |
| `score-card.md` | Scoring agent output (hard + soft metrics) |
| `coherence-check.md` | Post-inner-loop coherence verification |
| `ppi-statement.md` | Patient and Public Involvement statement |
| `credit-statement.md` | CRediT contributor roles (14 roles) |
| `pre-submission-inquiry.md` | Lightweight inquiry output format |

---

## Python Scripts — `scripts/` (16 files)

### Data Pipeline Scripts
| File | Purpose |
|---|---|
| `data-ingest.py` | Universal data reader (CSV, Excel, SAS, Stata, SPSS, Parquet) |
| `data-validate.py` | Medical data validation (impossible values, duplicates, consistency) |
| `data-derive.py` | Derive populations, composite endpoints, CONSORT flow numbers |
| `results-packager.py` | Assemble results_package.json from analysis outputs |
| `assumption-checks.py` | PH test, normality, VIF, homoscedasticity |
| `multiple-imputation.py` | MICE-style multiple imputation with Rubin's rules |

### Visualization Scripts
| File | Purpose |
|---|---|
| `km-plot.py` | Kaplan-Meier with number-at-risk table |
| `roc-curve.py` | ROC with AUC + CI + optimal threshold |
| `funnel-plot.py` | Publication bias funnel plot |
| `waterfall-plot.py` | Treatment response waterfall |
| `swimmer-plot.py` | Patient timeline swimmer plot |
| `competing-risks.py` | Cumulative incidence (Fine-Gray) |
| `figure-styler.py` | Apply journal YAML style to any matplotlib figure |

### Checker Scripts
| File | Purpose |
|---|---|
| `consistency-checker.py` | Verify numbers in text match results_package.json |
| `spin-detector.py` | Detect positive spin on null results |
| `retraction-checker.py` | Check references against retraction databases |

---

## Documentation — `docs/` (3 files)

| File | Purpose |
|---|---|
| `ARCHITECTURE.md` | This architecture overview |
| `FILE-INVENTORY.md` | Complete file listing with descriptions |
| `USAGE-GUIDE.md` | How to use the skill step by step |
