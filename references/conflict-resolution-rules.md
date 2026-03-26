# Conflict Resolution Rules

## Overview

When multiple agents contribute to the same manuscript section or make competing claims, the orchestrator resolves conflicts using a fixed 6-level priority hierarchy. This document defines each level, provides concrete examples, and specifies how the orchestrator detects and resolves each conflict type.

---

## Priority Hierarchy

```
PRIORITY 1 (highest): Statistician (Agent 4)
    Domain: Statistical claims, effect estimates, P-values, CIs, sample sizes
    Overrules: ALL other agents

PRIORITY 2: Compliance & Ethics (Agent 10)
    Domain: Regulatory requirements, reporting guidelines, declarations
    Overrules: All agents except Statistician

PRIORITY 3: Claim Verifier (Agent 16)
    Domain: Factual accuracy, reference validity, claim-source alignment
    Overrules: All agents except Statistician and Compliance

PRIORITY 4: Story Architect (Agent 2)
    Domain: Narrative framing, story arc, section ordering
    Overrules: Narrative Writer (Agent 7) on structural decisions

PRIORITY 5: Humanizer (Agent 12)
    Domain: Prose style, word choice, sentence structure, AI detection
    Overrules: All agents on final prose (last writing agent)

PRIORITY 6 (absolute): User
    Domain: Everything
    Overrules: All agents at gates
```

---

## Priority 1: Statistician Overrules All on Statistical Claims

**Principle:** No agent may overstate, understate, reframe, or reinterpret a statistical finding beyond what the data supports. The Statistician is the final authority on what the numbers mean.

**Example 1 -- Overstated finding:**
- Story Architect (Agent 2) wants the Discussion to lead with a subgroup finding: "Among patients aged >75, mortality was reduced by 40%."
- Statistician (Agent 4) flags: the subgroup analysis has wide CIs (HR 0.60, 95% CI 0.31-1.17), the interaction test is non-significant (P=0.12), and the analysis was post-hoc.
- **Resolution:** Statistician wins. The Discussion must lead with the primary outcome. The subgroup finding may be mentioned as exploratory with appropriate caveats.

**Example 2 -- Spin on null result:**
- Narrative Writer (Agent 7) writes: "Although the primary endpoint did not reach statistical significance, there was a clear trend towards benefit (P=0.08)."
- Statistician (Agent 4) flags: "trend towards significance" is spin. The correct framing is: "No significant difference was observed (HR 0.87, 95% CI 0.74-1.02, P=0.08)."
- **Resolution:** Statistician wins. The sentence is replaced with the neutral formulation.

**Example 3 -- Incorrect number in prose:**
- Results Writer (Agent 5) writes "30% of patients experienced the primary endpoint."
- Statistician (Agent 4) verifies results_package.json shows 28.3%.
- **Resolution:** Statistician wins. The number must match results_package.json exactly.

**Detection:** The orchestrator runs `scripts/consistency-checker.py` after every writing step and cross-references all numerical claims against `analysis/results_package.json`. Any mismatch is flagged as a Priority 1 conflict.

---

## Priority 2: Compliance Overrules All on Regulatory Requirements

**Principle:** Regulatory and ethical requirements are non-negotiable. If a reporting guideline, journal policy, or ethical standard requires something, it must be included regardless of narrative preferences or word count pressure.

**Example 1 -- Omitted limitation:**
- Narrative Writer (Agent 7) omits a limitation about selection bias from the Discussion to save words.
- Compliance (Agent 10) identifies that STROBE item 19 requires explicit discussion of potential sources of bias.
- **Resolution:** Compliance wins. The limitation is reinstated. If word count is a concern, Editor (Agent 11) must find words to cut elsewhere.

**Example 2 -- Missing registration number:**
- Editor (Agent 11) removes the trial registration number from the abstract to improve flow.
- Compliance (Agent 10) flags that ICMJE policy requires the registration number in the abstract.
- **Resolution:** Compliance wins. The registration number is restored.

**Example 3 -- PPI statement omission:**
- The manuscript is submitted to BMJ, which requires a Patient and Public Involvement statement.
- No agent has produced one.
- **Resolution:** Compliance flags the gap. The orchestrator dispatches Compliance to generate the PPI statement before Gate 3.

**Detection:** The orchestrator verifies reporting checklist completion (H3 metric) after each compliance check. Compliance flags are raised whenever a mandatory reporting item is absent or incomplete.

---

## Priority 3: Claim Verifier Overrules All on Factual Accuracy

**Principle:** Every factual claim in the manuscript must be supported by a verifiable, non-retracted source. If a claim cannot be verified, it must be removed or revised regardless of how well it supports the narrative.

**Example 1 -- Unsupported citation:**
- Literature Agent (Agent 1) cites: "Previous studies have shown a 25% reduction in mortality with early intervention [14]."
- Claim Verifier (Agent 16) retrieves the abstract of reference 14 and finds it reports a 25% reduction in morbidity (not mortality), in a different population (children, not adults).
- **Resolution:** Claim Verifier wins. The claim is either corrected to match the source ("25% reduction in morbidity in paediatric populations") or a different reference is found.

**Example 2 -- Retracted reference:**
- Reference Agent (Agent 9) includes a 2019 paper that was retracted in November 2025 for data fabrication.
- Claim Verifier (Agent 16) detects the retraction via `scripts/retraction-checker.py`.
- **Resolution:** Claim Verifier wins. The reference is removed immediately. Any claims supported solely by this reference are also removed or re-sourced.

**Example 3 -- Hallucinated reference:**
- A reference does not resolve via DOI lookup on CrossRef, does not appear in PubMed, and has no matching title in OpenAlex.
- Claim Verifier flags it as a potential hallucination.
- **Resolution:** Claim Verifier wins. The reference is removed. The orchestrator dispatches Reference Agent (Agent 9) to find a legitimate replacement or remove the claim.

**Detection:** The orchestrator dispatches Claim Verifier at Steps 7 and 11 (parallel with Scoring). All references are checked for existence, metadata accuracy, retraction status, and claim-source alignment.

---

## Priority 4: Story Architect Overrules Narrative Writer on Framing

**Principle:** The Story Architect designs the narrative structure before any writing begins. The Narrative Writer executes that structure. If the Narrative Writer deviates from the approved blueprint, the Story Architect's blueprint takes precedence.

**Example 1 -- Deviated story arc:**
- Story Architect (Agent 2) specifies the Introduction should build from global disease burden to local evidence gap to the specific unanswered question.
- Narrative Writer (Agent 7) writes an Introduction that opens with molecular mechanisms and reaches the clinical question only in paragraph 4.
- **Resolution:** Story Architect wins. The Introduction is restructured to follow the blueprint: global burden first, mechanisms integrated into the gap statement.

**Example 2 -- Wrong Discussion opening:**
- Story Architect's blueprint specifies: "Discussion opens with the primary finding restated without p-value, then contextualises against existing evidence."
- Narrative Writer opens with: "This study has several strengths and limitations."
- **Resolution:** Story Architect wins. The Discussion is reordered per the blueprint.

**Example 3 -- Null-result framing:**
- Story Architect specifies the null-result template: lead with the null finding, frame it as informative.
- Narrative Writer buries the null result in paragraph 3 of the Discussion and leads with an exploratory secondary finding.
- **Resolution:** Story Architect wins. The null result is moved to the first sentence of the Discussion.

**Detection:** The orchestrator compares the structural outline of the Narrative Writer's output against `plan/narrative-blueprint.md`. Section ordering, opening sentences, and punchline placement are checked against the blueprint.

---

## Priority 5: Humanizer Has Final Say on Prose Style

**Principle:** The Humanizer is the LAST writing agent in the pipeline. No agent modifies prose after the Humanizer. This ensures the final manuscript sounds natural and avoids AI-detection patterns.

**Example 1 -- AI vocabulary introduced by Editor:**
- Editor (Agent 11) polishes a sentence to: "This comprehensive study elucidates the pivotal role of early intervention."
- Humanizer (Agent 12) flags: "comprehensive", "elucidates", and "pivotal" are on the AI-word blacklist.
- **Resolution:** Humanizer wins. The sentence becomes: "This study clarifies the role of early intervention."

**Example 2 -- Uniform sentence length after editing:**
- After Editor (Agent 11) runs, sentence length standard deviation drops to 2.8 (target is 5.0 or higher).
- Humanizer (Agent 12) restructures sentences to vary length: short punchy sentences between longer complex ones.
- **Resolution:** Humanizer wins. The varied version is kept.

**Example 3 -- Post-Humanizer modification attempt:**
- After Humanizer has run (Step 10), Scoring Agent (Agent 14) identifies that a sentence still contains the word "utilize."
- The orchestrator does NOT dispatch Editor to fix it. Instead, the orchestrator re-dispatches Humanizer (Agent 12) to address the remaining flagged word.
- **Resolution:** Only Humanizer may touch prose after Step 10. This rule is absolute.

**Detection:** The orchestrator enforces the sequencing rule: after Agent 12 runs at Step 10, no agent with write access to manuscript files may be dispatched except Agent 12 itself. Agents 14 and 16 run at Step 11 in READ-ONLY mode.

---

## Priority 6: User Overrules Everyone at Gates

**Principle:** The user is the ultimate authority. At any gate, the user may override any agent's output, ignore scoring recommendations, change the journal target, redirect the narrative, or modify any section.

**Example 1 -- User overrides narrative direction:**
- Gate 1: Story Architect recommends leading with the mortality finding.
- User says: "Lead with the quality-of-life finding instead; it is more relevant to our target audience."
- **Resolution:** User wins. Story Architect's blueprint is updated. All downstream agents use the revised blueprint.

**Example 2 -- User keeps a flagged reference:**
- Gate 2: Claim Verifier flags reference 22 as "plausible but not directly verified" (abstract-only check, source discusses a related but not identical population).
- User says: "Keep it. I have read the full text and it supports the claim."
- **Resolution:** User wins. The reference is kept. The override is logged in the conflict log with the user's justification.

**Example 3 -- User accepts a below-threshold score:**
- Gate 3: Hard score is 80 (below the 90 threshold). The inner loop has run 5 iterations and cannot improve further.
- User says: "I am satisfied with this version. Proceed."
- **Resolution:** User wins. The manuscript proceeds to submission packaging despite the below-threshold score.

**Detection:** User overrides are captured at gate interaction points. Every override is logged in `meta/orchestrator_state.json` under `user_overrides` with a timestamp, the gate, the override description, and the original agent recommendation.

---

## Conflict Detection Mechanisms

### Automatic Detection

The orchestrator detects conflicts through these mechanisms:

| Mechanism | Conflicts Detected | When Run |
|---|---|---|
| `scripts/consistency-checker.py` | Number mismatches between prose and results_package.json | After every writing step |
| `scripts/spin-detector.py` | Statistical spin on null results | After Steps 5, 7, 9, 11 (when null_result_detected is true) |
| `scripts/retraction-checker.py` | Retracted or corrected references | Steps 7, 8, 11 |
| Reporting checklist diff | Missing mandatory items per guideline | After Agent 10 runs |
| Blueprint structure comparison | Deviations from narrative-blueprint.md | After Agent 7 runs |
| AI-word blacklist scan | Blacklisted words in prose | After every writing step |

### Manual Detection

Some conflicts cannot be detected automatically and surface only at gates:

- Interpretation disagreements (is this finding clinically meaningful?)
- Tone and emphasis disputes (how strongly to state a conclusion)
- Content omission decisions (what to include vs exclude for word count)

These are presented to the user at the gate with both options and a recommendation.

---

## Same-Level Conflicts

When two agents at the SAME priority level disagree, the orchestrator cannot resolve automatically. This is rare but possible in these scenarios:

| Scenario | Agents | Resolution |
|---|---|---|
| Statistical claim is also a regulatory requirement | Agent 4 (P1) vs Agent 10 (P2) | Statistician wins on the number; Compliance wins on the disclosure obligation. Both requirements are met. |
| Compliance requirement contradicts factual accuracy | Agent 10 (P2) vs Agent 16 (P3) | Compliance wins. If the required statement contains a factual error, it is corrected but the statement itself is kept. |
| Two verification findings conflict | Agent 16 (P3) internal conflict | The more conservative finding prevails. If a claim is both "verified" by one source and "unsupported" by another, it is flagged for user review. |

If a same-level conflict genuinely cannot be resolved, the orchestrator escalates to the user at the next gate, presenting both positions with the relevant evidence.

---

## Resolution Logging

Every conflict resolution is logged in `meta/orchestrator_state.json` under `conflict_log`:

```json
{
  "timestamp": "ISO-8601",
  "step": "STEP_N",
  "conflict_type": "statistical | regulatory | factual | framing | style | user_override",
  "priority_level": 1,
  "description": "Concise description of the conflict",
  "agents_involved": [4, 7],
  "winner": 4,
  "winner_name": "Statistician",
  "resolution": "What was changed and why",
  "escalated_to_user": false,
  "user_override": false
}
```

The Meta-Evaluator (Agent 15) analyses the conflict log during post-mortem to identify recurring conflicts that may indicate agent protocol weaknesses. Frequent conflicts between the same pair of agents suggest that one agent's protocol needs strengthening to prevent the conflict from arising in the first place.
