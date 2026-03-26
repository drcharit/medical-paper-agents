# Null-Result Narrative Blueprint

> Template for papers where the primary outcome is not statistically significant (p > 0.05 or CI includes null value). Null results are NOT failures. Well-powered null results are among the most important studies in medicine because they prevent widespread adoption of ineffective or harmful interventions.

---

## When to Use This Template

This template activates when `results_package.json` shows ANY of:
- Primary outcome p-value > 0.05
- Primary outcome confidence interval includes the null value (HR=1.0, OR=1.0, difference=0)
- The orchestrator flags the study as a null result

All elements below replace or extend the corresponding elements in the standard `narrative-blueprint.md`.

---

## Working Title

<!-- Null-result titles should be direct and honest. Do NOT obscure the null finding. -->
<!-- GOOD: "[Intervention] Did Not Reduce [Outcome] in [Population]: The [TRIAL NAME]" -->
<!-- GOOD: "Effect of [Intervention] on [Outcome] in [Population]: The [TRIAL NAME]" -->
<!-- BAD: "[Intervention] and [Outcome] in [Population]" (hides the null) -->
<!-- BAD: "Novel Insights from [TRIAL NAME]" (euphemism for null) -->

**Title:** [working title -- must not obscure the null finding]

---

## Result Classification

**Classification:** NULL

**Basis:** [Primary outcome: effect estimate, CI crossing null, p-value]

---

## Opening Hook

<!-- Same as positive-result papers. The clinical problem is real and urgent regardless of result direction. -->

[The clinical problem with numbers and urgency -- identical standards as positive result]

---

## Tension

<!-- Emphasise why the intervention seemed promising BEFORE this trial. -->
<!-- Build the case that made this trial worth doing. -->
<!-- Sources: biological rationale, prior observational data, smaller trials, expert opinion, animal studies -->

[Prior evidence that made the intervention promising, with citations]

**Tension framing:** The stronger the prior expectation of benefit, the more important the null finding.

---

## Gap Statement

<!-- Frame the gap as the ABSENCE of a definitive trial, not the absence of a positive result. -->
<!-- GOOD: "No adequately powered randomised trial has tested [intervention] for [hard endpoint] in [population]" -->
<!-- BAD: "It is unknown whether [intervention] improves [outcome]" (too vague) -->

[Gap statement -- emphasise that this is the first/largest/most rigorous test]

---

## Study Frame

<!-- Same as positive. Emphasise design quality: well-powered, blinded, independently adjudicated. -->
<!-- The rigour of the trial is what makes the null finding definitive. -->

[Study frame sentence -- emphasise design strengths]

---

## Key Finding

<!-- State the null result PLAINLY. No hedging, no softening, no "trend towards." -->
<!-- MANDATORY FORMAT: "[Intervention] did not [reduce/improve/prevent] [primary outcome] compared with [comparator] (effect estimate, 95% CI, p-value)" -->

[Key finding -- direct statement of null result with full statistics]

**Spin check -- the following are PROHIBITED in this section:**

| Prohibited Phrasing | Why It Is Spin | Required Alternative |
|---|---|---|
| "trend towards significance" | Implies result is almost positive | Report effect estimate with CI; let reader interpret |
| "numerically lower/higher" | Implies clinical significance without statistical support | State the exact estimate and CI |
| "approached significance" | No such concept in frequentist statistics | Report exact p-value |
| "borderline significant" | Misleading unless p is within rounding of 0.05 | "Not statistically significant (p=[exact])" |
| "failed to reach significance" | Implies the trial failed, not the intervention | "[Intervention] did not significantly [verb] [outcome]" |

---

## Twist / Nuance (Null-Result Specific)

<!-- The twist for a null result must explain WHY the null finding is informative. -->
<!-- Choose one or more of these framings: -->

**Option A -- Closes a clinical question:**
"This trial definitively answers whether [intervention] improves [outcome] in [population]. The answer is no."

**Option B -- Prevents harm from ineffective therapy:**
"Without this trial, [intervention] might have been widely adopted based on [observational data/smaller trials/biological rationale], exposing patients to [costs/side effects] without benefit."

**Option C -- Contradicts strong prior belief:**
"Despite [strong biological rationale / positive observational data / expert consensus], [intervention] did not improve [outcome], challenging the assumption that [mechanism] translates to clinical benefit."

**Option D -- Reveals unexpected finding:**
"Although the primary outcome was null, the trial revealed [unexpected safety signal / significant secondary outcome / important subgroup finding]."

**Option E -- Informs resource allocation:**
"These findings suggest that resources currently directed toward [intervention] in [population] should be redirected to [alternative approach]."

[Write the selected twist framing here]

**Selected option:** [A / B / C / D / E]

**Data support:** [Reference to results_package.json]

---

## Clinical Punchline (Null-Result Specific)

<!-- Must state a CONCRETE clinical action. "Further research is needed" is NOT acceptable as the punchline. -->

**Choose one of these action framings:**

1. **STOP:** "Clinicians should not [prescribe/recommend/perform] [intervention] for [indication] on the basis of these findings."
2. **CONTINUE:** "Current standard of care ([current practice]) should continue; [intervention] does not offer additional benefit."
3. **REDIRECT:** "Efforts to improve [outcome] in [population] should focus on [alternative intervention/approach] rather than [studied intervention]."
4. **REFINE:** "While [intervention] did not improve [outcome] overall, [subgroup finding] warrants further investigation in a dedicated trial." (Use ONLY if a pre-specified subgroup interaction was significant.)

[Write the clinical punchline here]

---

## Limitations Frame (Null-Result Specific)

<!-- For null results, the limitations section has a dual purpose: -->
<!-- 1. Honest about real limitations (as always) -->
<!-- 2. Defend the reliability of the null finding (the trial was well-powered, well-conducted) -->

<!-- DO: Emphasise that the null finding is reliable because the trial had adequate power -->
<!-- DO: State what effect size the trial could have detected (from power calculation) -->
<!-- DO NOT: Suggest the trial was underpowered (unless it objectively was) -->
<!-- DO NOT: Apologise for the null result -->
<!-- DO NOT: Use limitations to imply the intervention might still work -->

1. **[Limitation 1]:** [Description]. [This limitation [does/does not] affect the reliability of the null finding because...].
2. **Power and detectable effect:** This trial was powered to detect a [X]% relative risk reduction. The observed effect (HR [value]) with 95% CI [lower]-[upper] rules out a benefit larger than [upper bound] but does not exclude a smaller effect that may still be clinically meaningful.
3. **[Limitation 3]:** [Description]. [Mitigating factor].
4. **[Limitation 4 (if applicable)]:** [Description]. [Mitigating factor].

---

## Discussion Structure for Null Results

<!-- Agent 7 (Narrative Writer) MUST follow this structure for null-result Discussion sections. -->

| Paragraph | Content | Prohibited Content |
|---|---|---|
| Para 1 | State the null primary finding. First sentence = main result. | Do NOT open with a positive secondary finding |
| Para 2 | Context: why this null finding matters given prior evidence (Tension, revisited) | Do NOT minimise the null finding |
| Para 3 | Twist: why the null finding is informative (from twist section above) | Do NOT imply the intervention might still work |
| Para 4 | Secondary and subgroup findings, clearly labelled as such | Do NOT present subgroup findings as primary |
| Para 5 | Comparison with prior studies: how does this null result change the evidence landscape? | Do NOT cherry-pick studies that support the intervention |
| Para 6 | Limitations, with power defence | Do NOT suggest the trial was underpowered |
| Para 7 | Clinical punchline: concrete action statement | Do NOT end with "further research is needed" |

---

## Spin Detection Checklist

<!-- Agent 14 (Scoring) uses this checklist via scripts/spin-detector.py. Agent 2 (Story Architect) ensures the blueprint does not contain spin BEFORE writing begins. -->

| Check | Pass/Fail |
|---|---|
| Does the title clearly indicate a null or neutral result? | [ ] |
| Does the abstract Findings/Results section lead with the null primary outcome? | [ ] |
| Does the Discussion open with the null primary finding (not a positive secondary)? | [ ] |
| Is the word "trend" absent from descriptions of non-significant results? | [ ] |
| Are all subgroup findings labelled as exploratory? | [ ] |
| Is the Conclusion about what the null finding means (not about future research)? | [ ] |
| Are effect estimates reported with CIs (not just p-values)? | [ ] |
| Is the trial described as "well-powered" (if it was) rather than "may have been underpowered"? | [ ] |

---

## Examples of Well-Framed Null Results

**ISCHEMIA Trial (NEJM 2020):**
- Key Finding: "An initial invasive strategy did not reduce the risk of ischemic cardiovascular events or death from any cause compared with an initial conservative strategy over a median of 3.2 years."
- Why it worked: Direct, no hedging, practice-changing (stopped routine PCI for stable CAD).

**VITAL Trial (NEJM 2019):**
- Key Finding: "Supplementation with vitamin D did not result in a lower incidence of invasive cancer or cardiovascular events than placebo."
- Why it worked: Closed a decades-long debate with definitive evidence.

**ORBITA Trial (Lancet 2018):**
- Key Finding: "PCI did not increase exercise time by more than the effect of a sham procedure in patients with stable angina."
- Why it worked: Provocative null finding against strong clinical intuition; sham-controlled design made the null definitive.
