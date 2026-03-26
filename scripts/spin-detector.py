#!/usr/bin/env python3
"""
spin-detector.py — Detect positive spin on null results in medical manuscripts

Part of the medical-paper-agents skill.
Used by Agent 14 (Scoring) when primary outcome is null.

Spin = misleading reporting that distorts the interpretation of results
and may mislead readers about the true effect of the intervention.

Reference: Boutron et al., JAMA 2010; Lazarus et al., BMJ 2010.

Usage:
    python spin-detector.py \
        --manuscript-dir ./draft/ \
        --results results_package.json

    python spin-detector.py \
        --manuscript-dir ./draft/ \
        --results results_package.json \
        --output spin_report.md
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SpinInstance:
    """A detected instance of spin in the manuscript."""
    pattern_name: str
    severity: str           # HIGH, MEDIUM, LOW
    file: str
    line: int
    text: str               # the offending sentence or passage
    explanation: str
    suggestion: str


# ---------------------------------------------------------------------------
# Spin patterns
# ---------------------------------------------------------------------------

# Each pattern is a tuple: (name, severity, regex, explanation_template, suggestion_template)
LANGUAGE_PATTERNS = [
    (
        "trend_towards_significance",
        "HIGH",
        re.compile(
            r'trend\s+toward(?:s)?\s+(?:statistical\s+)?significance',
            re.IGNORECASE,
        ),
        "The phrase 'trend towards significance' implies the result would have been "
        "significant with more power. A non-significant result is non-significant.",
        "Replace with: 'The difference was not statistically significant "
        "(HR X.XX, 95% CI X.XX-X.XX, p=X.XX).'",
    ),
    (
        "trend_toward_general",
        "MEDIUM",
        re.compile(
            r'(?:a\s+)?trend\s+toward(?:s)?\s+(?:lower|higher|reduced|increased|improved|better|fewer)',
            re.IGNORECASE,
        ),
        "Using 'trend toward' with directional language implies a meaningful "
        "direction when the result is not statistically significant.",
        "Report the point estimate and CI without directional language: "
        "'The HR was X.XX (95% CI X.XX-X.XX, p=X.XX).'",
    ),
    (
        "numerically_but_not_significant",
        "HIGH",
        re.compile(
            r'numerically\s+(?:lower|higher|better|worse|greater|fewer|less|smaller|larger)'
            r'(?:\s+but)?\s+not\s+(?:statistically\s+)?significant',
            re.IGNORECASE,
        ),
        "'Numerically lower but not statistically significant' is spin. "
        "It implies the direction is real but the study lacked power.",
        "Report the result with its CI: 'No significant difference was observed "
        "(HR X.XX, 95% CI X.XX-X.XX, p=X.XX).'",
    ),
    (
        "marginally_significant",
        "HIGH",
        re.compile(
            r'(?:marginally|borderline|nearly|almost|approaching)\s+(?:statistically\s+)?significant',
            re.IGNORECASE,
        ),
        "There is no such thing as 'marginally significant'. "
        "A result is significant or it is not.",
        "Report the exact P-value and CI. Let the reader interpret.",
    ),
    (
        "approached_significance",
        "HIGH",
        re.compile(
            r'approached\s+(?:statistical\s+)?significance',
            re.IGNORECASE,
        ),
        "'Approached significance' implies the result was almost positive. "
        "P-values near 0.05 are not 'almost significant'.",
        "Report: 'The difference was not statistically significant (p=X.XX).'",
    ),
    (
        "failed_to_reach",
        "MEDIUM",
        re.compile(
            r'failed\s+to\s+(?:reach|achieve|attain)\s+(?:statistical\s+)?significance',
            re.IGNORECASE,
        ),
        "'Failed to reach significance' implies the study failed, rather than "
        "that the intervention does not have the expected effect.",
        "Use: 'did not demonstrate a significant difference' or 'the difference "
        "was not statistically significant'.",
    ),
    (
        "encouraging_results",
        "MEDIUM",
        re.compile(
            r'(?:encouraging|promising|favourable|favorable)\s+(?:results?|findings?|outcomes?|trend)',
            re.IGNORECASE,
        ),
        "Describing null results as 'encouraging' or 'promising' is spin. "
        "The primary endpoint was not met.",
        "Report the result objectively. Reserve 'promising' for Discussion "
        "of future research directions only, if at all.",
    ),
    (
        "despite_not_significant",
        "MEDIUM",
        re.compile(
            r'(?:despite|although|while|even\s+though)\s+(?:the\s+)?'
            r'(?:difference|result|finding|outcome)\s+(?:was\s+)?not\s+'
            r'(?:statistically\s+)?significant',
            re.IGNORECASE,
        ),
        "Prefacing a non-significant result with 'despite' or 'although' "
        "frames the null as a disappointment rather than a valid finding.",
        "State the result directly without hedging qualifiers.",
    ),
    (
        "potential_benefit",
        "LOW",
        re.compile(
            r'potential\s+(?:clinical\s+)?benefit',
            re.IGNORECASE,
        ),
        "Claiming 'potential benefit' from a null trial requires strong justification. "
        "Ensure this is supported by pre-specified secondary outcomes.",
        "If the primary outcome is null, be cautious about claiming 'potential benefit' "
        "from secondary or subgroup analyses.",
    ),
    (
        "suggests_benefit",
        "LOW",
        re.compile(
            r'(?:suggest|indicate|point\s+to|support)\w*\s+(?:a\s+)?(?:clinical\s+)?benefit',
            re.IGNORECASE,
        ),
        "Claiming the null result 'suggests benefit' is potentially spin "
        "if the primary endpoint was not met.",
        "If the primary endpoint was null, state that the study did not demonstrate "
        "the hypothesised benefit. Secondary findings should be clearly labeled as such.",
    ),
]


def is_primary_null(results_data: dict) -> bool:
    """Determine if the primary outcome is null from results_package.json.

    A primary outcome is null if:
    - P-value > 0.05, OR
    - CI for effect estimate includes the null value (1.0 for ratios, 0 for differences)
    """
    # Try various common key structures
    primary = None
    for key_path in [
        'primary_outcome', 'primary', 'primary_endpoint',
        'results.primary', 'outcomes.primary',
    ]:
        obj = results_data
        for part in key_path.split('.'):
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                obj = None
                break
        if obj is not None:
            primary = obj
            break

    if primary is None:
        # Try to find any key containing "primary"
        def find_primary(d, depth=0):
            if depth > 5:
                return None
            if isinstance(d, dict):
                for k, v in d.items():
                    if 'primary' in k.lower():
                        return v
                    result = find_primary(v, depth + 1)
                    if result is not None:
                        return result
            return None
        primary = find_primary(results_data)

    if primary is None:
        return False  # cannot determine; assume not null

    if isinstance(primary, dict):
        p_value = primary.get('p_value', primary.get('p', primary.get('pvalue')))
        ci_lower = primary.get('ci_lower', primary.get('ci_lo', primary.get('conf_low')))
        ci_upper = primary.get('ci_upper', primary.get('ci_hi', primary.get('conf_high')))
        estimate = primary.get('estimate', primary.get('effect', primary.get('hr',
                   primary.get('or', primary.get('rr')))))

        # Check P-value
        if p_value is not None:
            try:
                if float(p_value) > 0.05:
                    return True
            except (ValueError, TypeError):
                pass

        # Check CI includes null
        if ci_lower is not None and ci_upper is not None:
            try:
                lo, hi = float(ci_lower), float(ci_upper)
                # For ratios (HR, OR, RR): null = 1.0
                if estimate is not None:
                    est = float(estimate)
                    if 0 < est < 10:  # likely a ratio
                        if lo <= 1.0 <= hi:
                            return True
                    else:  # likely a difference
                        if lo <= 0 <= hi:
                            return True
                else:
                    # Guess: if both bounds are positive and span 1.0
                    if lo <= 1.0 <= hi:
                        return True
            except (ValueError, TypeError):
                pass

    return False


def check_abstract_order(abstract_path: str, results_data: dict) -> list[SpinInstance]:
    """Check if the abstract leads with a positive secondary instead of the null primary."""
    findings = []
    if not os.path.exists(abstract_path):
        return findings

    with open(abstract_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the Findings/Results section of the abstract
    in_findings = False
    findings_lines = []
    findings_start_line = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip().lower()
        if any(h in stripped for h in ['## findings', '## results', '**findings**',
                                        '**results**', 'findings:', 'results:']):
            in_findings = True
            findings_start_line = i
            continue
        if in_findings:
            if stripped.startswith('##') or stripped.startswith('**') and ':' in stripped:
                break  # next section
            findings_lines.append((i, line.strip()))

    if not findings_lines:
        return findings

    # Check if first sentence mentions "not significant" or null primary
    first_sentences = ' '.join(text for _, text in findings_lines[:3])
    mentions_null = bool(re.search(
        r'(?:not\s+significant|no\s+significant|did\s+not\s+(?:differ|reduce|improve))',
        first_sentences, re.IGNORECASE
    ))
    mentions_positive_secondary = bool(re.search(
        r'(?:significant(?:ly)?\s+(?:reduced|improved|lower|higher|fewer))',
        first_sentences, re.IGNORECASE
    ))

    if mentions_positive_secondary and not mentions_null:
        findings.append(SpinInstance(
            pattern_name="abstract_leads_with_secondary",
            severity="HIGH",
            file="abstract.md",
            line=findings_start_line,
            text=first_sentences[:200],
            explanation=(
                "The abstract Findings/Results section appears to lead with a positive "
                "secondary finding rather than the null primary outcome. This is a common "
                "form of spin in null trials."
            ),
            suggestion=(
                "The first sentence of the abstract results should state the primary "
                "outcome result, including that it was not statistically significant."
            ),
        ))

    return findings


def check_discussion_opening(discussion_path: str) -> list[SpinInstance]:
    """Check if Discussion paragraph 1 mentions the null primary result."""
    findings = []
    if not os.path.exists(discussion_path):
        return findings

    with open(discussion_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Get first paragraph (skip headers)
    first_para_lines = []
    started = False
    first_line_num = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            if started:
                break
            continue
        if not started:
            first_line_num = i
            started = True
        first_para_lines.append(stripped)

    if not first_para_lines:
        return findings

    first_para = ' '.join(first_para_lines)

    mentions_null = bool(re.search(
        r'(?:not\s+significant|no\s+significant|did\s+not\s+(?:demonstrate|show|find)|'
        r'null|negative\s+(?:result|finding|trial)|not\s+met|was\s+not\s+achieved)',
        first_para, re.IGNORECASE
    ))

    if not mentions_null:
        findings.append(SpinInstance(
            pattern_name="discussion_buries_null",
            severity="HIGH",
            file="discussion.md",
            line=first_line_num,
            text=first_para[:200],
            explanation=(
                "The first paragraph of the Discussion does not appear to mention "
                "the null primary result. In a null trial, the Discussion must open "
                "with the primary finding."
            ),
            suggestion=(
                "Begin the Discussion with: 'In this [study type] of [N] patients, "
                "[intervention] did not significantly reduce [primary outcome] compared "
                "with [control] (HR X.XX, 95% CI X.XX-X.XX, p=X.XX).'"
            ),
        ))

    return findings


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def scan_for_spin(manuscript_dir: str, results_path: str) -> list[SpinInstance]:
    """Scan all manuscript files for spin patterns."""
    all_findings: list[SpinInstance] = []

    # Load results to check if primary is null
    with open(results_path, 'r', encoding='utf-8') as f:
        results_data = json.load(f)

    primary_is_null = is_primary_null(results_data)
    if not primary_is_null:
        # Not a null result — spin detection less relevant but still check language
        pass

    # Scan each manuscript file for language patterns
    manuscript_files = sorted(Path(manuscript_dir).glob("*.md"))
    for md_file in manuscript_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            continue

        filename = md_file.name
        for line_idx, line_text in enumerate(lines, 1):
            stripped = line_text.strip()
            if not stripped or stripped.startswith('#'):
                continue

            for name, severity, pattern, explanation, suggestion in LANGUAGE_PATTERNS:
                if pattern.search(stripped):
                    all_findings.append(SpinInstance(
                        pattern_name=name,
                        severity=severity,
                        file=filename,
                        line=line_idx,
                        text=stripped[:200],
                        explanation=explanation,
                        suggestion=suggestion,
                    ))

    # Structural checks (only meaningful for null results)
    if primary_is_null:
        abstract_path = os.path.join(manuscript_dir, "abstract.md")
        all_findings.extend(check_abstract_order(abstract_path, results_data))

        discussion_path = os.path.join(manuscript_dir, "discussion.md")
        all_findings.extend(check_discussion_opening(discussion_path))

    return all_findings


def generate_report(findings: list[SpinInstance], output_path: str, primary_null: bool) -> None:
    """Write the spin detection report."""
    lines = [
        "# Spin Detection Report",
        "",
        f"**Generated by:** spin-detector.py",
        f"**Primary outcome null:** {'Yes' if primary_null else 'No / Unknown'}",
        f"**Total spin instances detected:** {len(findings)}",
        "",
    ]

    if not findings:
        lines.extend([
            "No spin patterns detected. The manuscript appears to report results objectively.",
            "",
        ])
    else:
        # Group by severity
        high = [f for f in findings if f.severity == "HIGH"]
        medium = [f for f in findings if f.severity == "MEDIUM"]
        low = [f for f in findings if f.severity == "LOW"]

        lines.extend([
            "## Summary",
            "",
            f"| Severity | Count |",
            f"|---|---|",
            f"| HIGH | {len(high)} |",
            f"| MEDIUM | {len(medium)} |",
            f"| LOW | {len(low)} |",
            "",
            "---",
            "",
        ])

        if high:
            lines.extend(["## High Severity (must fix)", ""])
            for f in high:
                lines.extend([
                    f"### {f.pattern_name}",
                    f"**File:** {f.file}, **Line:** {f.line}",
                    f"**Text:** \"{f.text}\"",
                    f"**Issue:** {f.explanation}",
                    f"**Suggested fix:** {f.suggestion}",
                    "",
                ])

        if medium:
            lines.extend(["## Medium Severity (should fix)", ""])
            for f in medium:
                lines.extend([
                    f"### {f.pattern_name}",
                    f"**File:** {f.file}, **Line:** {f.line}",
                    f"**Text:** \"{f.text}\"",
                    f"**Issue:** {f.explanation}",
                    f"**Suggested fix:** {f.suggestion}",
                    "",
                ])

        if low:
            lines.extend(["## Low Severity (consider fixing)", ""])
            for f in low:
                lines.extend([
                    f"### {f.pattern_name}",
                    f"**File:** {f.file}, **Line:** {f.line}",
                    f"**Text:** \"{f.text}\"",
                    f"**Issue:** {f.explanation}",
                    f"**Suggested fix:** {f.suggestion}",
                    "",
                ])

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Report written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Detect positive spin on null results in medical manuscripts"
    )
    parser.add_argument(
        "--manuscript-dir",
        required=True,
        help="Directory containing manuscript markdown files",
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Path to results_package.json",
    )
    parser.add_argument(
        "--output",
        default="spin_report.md",
        help="Output report path (default: spin_report.md)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.manuscript_dir):
        print(f"ERROR: Manuscript directory not found: {args.manuscript_dir}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.results):
        print(f"ERROR: Results package not found: {args.results}", file=sys.stderr)
        sys.exit(1)

    # Check if primary is null
    with open(args.results, 'r', encoding='utf-8') as f:
        results_data = json.load(f)
    primary_null = is_primary_null(results_data)
    print(f"Primary outcome null: {primary_null}")

    # Run spin detection
    findings = scan_for_spin(args.manuscript_dir, args.results)
    print(f"Spin instances detected: {len(findings)}")

    # Generate report
    generate_report(findings, args.output, primary_null)

    # Exit code
    high_count = sum(1 for f in findings if f.severity == "HIGH")
    if high_count > 0:
        print(f"\nWARNING: {high_count} HIGH severity spin instance(s) detected.")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
