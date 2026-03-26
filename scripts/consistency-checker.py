#!/usr/bin/env python3
"""
consistency-checker.py — Verify numbers in manuscript text match results_package.json

Part of the medical-paper-agents skill.
Used by Agent 14 (Scoring) for H9 (number match) and H10 (internal N consistency).

Usage:
    python consistency-checker.py \
        --manuscript-dir ./draft/ \
        --results results_package.json \
        --output consistency_check.md

    python consistency-checker.py \
        --manuscript-dir ./draft/ \
        --results results_package.json \
        --output consistency_check.md \
        --population-flow data/population_flow.json \
        --table1 analysis/table1.md
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ExtractedNumber:
    """A number found in the manuscript text."""
    value: str                # raw string as it appears in text
    numeric_value: float      # parsed numeric value
    number_type: str          # percentage, effect_estimate, ci_bound, p_value, sample_size, count, other
    context: str              # surrounding sentence
    file: str                 # source markdown file
    line: int                 # line number (1-based)
    matched: bool = False     # whether matched to results_package.json
    match_key: str = ""       # what it matched against in results_package
    match_value: Optional[float] = None  # expected value from results_package
    status: str = "UNVERIFIED"  # MATCH, MISMATCH, UNVERIFIED


@dataclass
class ConsistencyResult:
    """Overall consistency check results."""
    total_numbers: int = 0
    matched: int = 0
    mismatched: int = 0
    unverified: int = 0
    n_consistency: str = "UNCHECKED"
    n_values: dict = field(default_factory=dict)
    numbers: list = field(default_factory=list)
    mismatches: list = field(default_factory=list)
    direction_errors: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Number extraction from manuscript markdown
# ---------------------------------------------------------------------------

# Regex patterns for different number types
PATTERNS = {
    "percentage": re.compile(
        r'(\d+(?:\.\d+)?(?:\xb7\d+)?)\s*%',
        re.UNICODE
    ),
    "hr": re.compile(
        r'(?:HR|hazard\s+ratio)\s*[=:]\s*(\d+(?:[.\xb7]\d+)?)',
        re.IGNORECASE | re.UNICODE
    ),
    "or": re.compile(
        r'(?:OR|odds\s+ratio)\s*[=:]\s*(\d+(?:[.\xb7]\d+)?)',
        re.IGNORECASE | re.UNICODE
    ),
    "rr": re.compile(
        r'(?:RR|risk\s+ratio|relative\s+risk)\s*[=:]\s*(\d+(?:[.\xb7]\d+)?)',
        re.IGNORECASE | re.UNICODE
    ),
    "md": re.compile(
        r'(?:MD|mean\s+difference)\s*[=:]\s*(-?\d+(?:[.\xb7]\d+)?)',
        re.IGNORECASE | re.UNICODE
    ),
    "ci_range": re.compile(
        r'95%?\s*CI\s*[=:,]?\s*(\d+(?:[.\xb7]\d+)?)\s*[-\u2013\u2014to]+\s*(\d+(?:[.\xb7]\d+)?)',
        re.IGNORECASE | re.UNICODE
    ),
    "p_value": re.compile(
        r'[pP]\s*[=<>]\s*0?[.\xb7](\d+)',
        re.UNICODE
    ),
    "p_value_full": re.compile(
        r'[pP]\s*([=<>])\s*(0?[.\xb7]\d+)',
        re.UNICODE
    ),
    "sample_size": re.compile(
        r'(?:N|n)\s*=\s*(\d[\d,\s]*\d|\d+)',
        re.UNICODE
    ),
    "enrolled": re.compile(
        r'(\d[\d,]*)\s+(?:patients?|participants?|subjects?|individuals?)\s+(?:were\s+)?'
        r'(?:enrolled|randomised|randomized|included|recruited|screened)',
        re.IGNORECASE
    ),
    "of_n": re.compile(
        r'[Oo]f\s+(\d[\d,]*)\s+(?:patients?|participants?|subjects?)',
    ),
    "nnt": re.compile(
        r'(?:NNT|number\s+needed\s+to\s+treat)\s*[=:]\s*(\d+(?:[.\xb7]\d+)?)',
        re.IGNORECASE | re.UNICODE
    ),
    "ard": re.compile(
        r'(?:ARD|absolute\s+risk\s+(?:difference|reduction))\s*[=:]\s*(-?\d+(?:[.\xb7]\d+)?)\s*%?',
        re.IGNORECASE | re.UNICODE
    ),
    "follow_up": re.compile(
        r'(?:median\s+)?follow[- ]?up\s+(?:of\s+|was\s+|period\s+)?(\d+(?:[.\xb7]\d+)?)\s*'
        r'(?:years?|months?|days?|weeks?)',
        re.IGNORECASE | re.UNICODE
    ),
    "event_count": re.compile(
        r'(\d[\d,]*)\s+(?:events?|deaths?|endpoints?|outcomes?)\s+(?:occurred|were\s+observed)',
        re.IGNORECASE
    ),
}

# Direction language patterns
DIRECTION_PATTERNS = {
    "lower": re.compile(r'\b(?:lower|reduced|decreased|fewer|less)\b', re.IGNORECASE),
    "higher": re.compile(r'\b(?:higher|increased|greater|more|elevated)\b', re.IGNORECASE),
}


def normalize_number(s: str) -> float:
    """Convert a manuscript number string to a float.

    Handles:
    - Midline dots (Lancet): 23\u00b74 -> 23.4
    - Commas in thousands: 2,400 -> 2400
    - Thin spaces in thousands: 10 000 -> 10000
    - Leading zero absence: .04 -> 0.04
    """
    s = s.strip()
    # Replace midline dot with decimal point
    s = s.replace('\u00b7', '.')
    # Remove commas and thin/non-breaking spaces used as thousand separators
    s = re.sub(r'[,\s\u2009\u00a0]', '', s)
    # Handle missing leading zero
    if s.startswith('.'):
        s = '0' + s
    try:
        return float(s)
    except ValueError:
        return float('nan')


def extract_numbers_from_file(filepath: str) -> list[ExtractedNumber]:
    """Extract all numbers from a markdown file."""
    numbers = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return numbers

    filename = os.path.basename(filepath)

    for line_idx, line_text in enumerate(lines, start=1):
        # Skip markdown headers, table separators, and empty lines
        stripped = line_text.strip()
        if not stripped or stripped.startswith('#') or re.match(r'^[\|\-\s:]+$', stripped):
            continue

        # Extract percentages
        for m in PATTERNS["percentage"].finditer(line_text):
            val_str = m.group(1)
            numbers.append(ExtractedNumber(
                value=f"{val_str}%",
                numeric_value=normalize_number(val_str),
                number_type="percentage",
                context=stripped,
                file=filename,
                line=line_idx,
            ))

        # Extract hazard ratios
        for m in PATTERNS["hr"].finditer(line_text):
            val_str = m.group(1)
            numbers.append(ExtractedNumber(
                value=f"HR {val_str}",
                numeric_value=normalize_number(val_str),
                number_type="effect_estimate",
                context=stripped,
                file=filename,
                line=line_idx,
            ))

        # Extract odds ratios
        for m in PATTERNS["or"].finditer(line_text):
            val_str = m.group(1)
            numbers.append(ExtractedNumber(
                value=f"OR {val_str}",
                numeric_value=normalize_number(val_str),
                number_type="effect_estimate",
                context=stripped,
                file=filename,
                line=line_idx,
            ))

        # Extract risk ratios
        for m in PATTERNS["rr"].finditer(line_text):
            val_str = m.group(1)
            numbers.append(ExtractedNumber(
                value=f"RR {val_str}",
                numeric_value=normalize_number(val_str),
                number_type="effect_estimate",
                context=stripped,
                file=filename,
                line=line_idx,
            ))

        # Extract mean differences
        for m in PATTERNS["md"].finditer(line_text):
            val_str = m.group(1)
            numbers.append(ExtractedNumber(
                value=f"MD {val_str}",
                numeric_value=normalize_number(val_str),
                number_type="effect_estimate",
                context=stripped,
                file=filename,
                line=line_idx,
            ))

        # Extract confidence intervals
        for m in PATTERNS["ci_range"].finditer(line_text):
            lo_str, hi_str = m.group(1), m.group(2)
            numbers.append(ExtractedNumber(
                value=f"CI lower {lo_str}",
                numeric_value=normalize_number(lo_str),
                number_type="ci_bound",
                context=stripped,
                file=filename,
                line=line_idx,
            ))
            numbers.append(ExtractedNumber(
                value=f"CI upper {hi_str}",
                numeric_value=normalize_number(hi_str),
                number_type="ci_bound",
                context=stripped,
                file=filename,
                line=line_idx,
            ))

        # Extract P-values
        for m in PATTERNS["p_value_full"].finditer(line_text):
            operator = m.group(1)
            val_str = m.group(2)
            numbers.append(ExtractedNumber(
                value=f"p{operator}{val_str}",
                numeric_value=normalize_number(val_str),
                number_type="p_value",
                context=stripped,
                file=filename,
                line=line_idx,
            ))

        # Extract sample sizes (N=...)
        for m in PATTERNS["sample_size"].finditer(line_text):
            val_str = m.group(1)
            numbers.append(ExtractedNumber(
                value=f"N={val_str}",
                numeric_value=normalize_number(val_str),
                number_type="sample_size",
                context=stripped,
                file=filename,
                line=line_idx,
            ))

        # Extract enrolled/randomised counts
        for m in PATTERNS["enrolled"].finditer(line_text):
            val_str = m.group(1)
            numbers.append(ExtractedNumber(
                value=f"enrolled {val_str}",
                numeric_value=normalize_number(val_str),
                number_type="sample_size",
                context=stripped,
                file=filename,
                line=line_idx,
            ))

        # Extract "Of N participants" counts
        for m in PATTERNS["of_n"].finditer(line_text):
            val_str = m.group(1)
            numbers.append(ExtractedNumber(
                value=f"Of {val_str}",
                numeric_value=normalize_number(val_str),
                number_type="sample_size",
                context=stripped,
                file=filename,
                line=line_idx,
            ))

        # Extract NNT
        for m in PATTERNS["nnt"].finditer(line_text):
            val_str = m.group(1)
            numbers.append(ExtractedNumber(
                value=f"NNT {val_str}",
                numeric_value=normalize_number(val_str),
                number_type="other",
                context=stripped,
                file=filename,
                line=line_idx,
            ))

        # Extract follow-up durations
        for m in PATTERNS["follow_up"].finditer(line_text):
            val_str = m.group(1)
            numbers.append(ExtractedNumber(
                value=f"follow-up {val_str}",
                numeric_value=normalize_number(val_str),
                number_type="other",
                context=stripped,
                file=filename,
                line=line_idx,
            ))

    return numbers


# ---------------------------------------------------------------------------
# Results package parsing
# ---------------------------------------------------------------------------

def flatten_json(obj: dict, prefix: str = "") -> dict[str, float]:
    """Flatten a nested JSON into dot-separated key-value pairs (numeric only)."""
    flat = {}
    for key, value in obj.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_json(value, full_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    flat.update(flatten_json(item, f"{full_key}[{i}]"))
                elif isinstance(item, (int, float)):
                    flat[f"{full_key}[{i}]"] = float(item)
        elif isinstance(value, (int, float)):
            flat[full_key] = float(value)
        elif isinstance(value, str):
            try:
                flat[full_key] = float(value)
            except ValueError:
                pass
    return flat


def load_results_package(filepath: str) -> dict[str, float]:
    """Load results_package.json and flatten it."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return flatten_json(data)


# ---------------------------------------------------------------------------
# Matching logic
# ---------------------------------------------------------------------------

TOLERANCE_EXACT = 0.001       # for effect estimates, CIs
TOLERANCE_PERCENTAGE = 0.5    # for percentages (allow 0.5% drift)
TOLERANCE_P_VALUE = 0.005     # for P-values
TOLERANCE_COUNT = 0           # for sample sizes and counts (must be exact)


def match_number_to_results(num: ExtractedNumber, results: dict[str, float]) -> bool:
    """Try to match an extracted number against results_package values.

    Returns True if a match or close match was found.
    Sets num.matched, num.match_key, num.match_value, and num.status.
    """
    target = num.numeric_value
    if target != target:  # NaN check
        num.status = "UNVERIFIED"
        return False

    best_match_key = None
    best_match_value = None
    best_diff = float('inf')

    for key, value in results.items():
        if value != value:  # skip NaN values in results
            continue

        diff = abs(target - value)

        # Determine tolerance based on type
        if num.number_type == "sample_size":
            tolerance = TOLERANCE_COUNT
        elif num.number_type == "percentage":
            tolerance = TOLERANCE_PERCENTAGE
        elif num.number_type == "p_value":
            tolerance = TOLERANCE_P_VALUE
        elif num.number_type in ("effect_estimate", "ci_bound"):
            tolerance = TOLERANCE_EXACT
        else:
            tolerance = TOLERANCE_EXACT

        # Check for exact or near match
        if diff <= tolerance and diff < best_diff:
            best_diff = diff
            best_match_key = key
            best_match_value = value

    if best_match_key is not None:
        num.matched = True
        num.match_key = best_match_key
        num.match_value = best_match_value
        if best_diff == 0 or (best_diff <= TOLERANCE_EXACT):
            num.status = "MATCH"
        else:
            num.status = "MISMATCH"
            # Close but not exact — flag it
            if num.number_type == "percentage" and best_diff <= TOLERANCE_PERCENTAGE:
                num.status = "MATCH"  # acceptable rounding for percentages
        return True
    else:
        num.status = "UNVERIFIED"
        return False


def check_direction_consistency(num: ExtractedNumber, results: dict[str, float]) -> Optional[str]:
    """Check if direction language matches the effect estimate direction.

    E.g., HR < 1.0 should be described as 'lower/reduced', not 'higher/increased'.
    Returns an error message if direction mismatch is found, else None.
    """
    if num.number_type != "effect_estimate":
        return None

    context_lower = num.context.lower()
    has_lower = bool(DIRECTION_PATTERNS["lower"].search(context_lower))
    has_higher = bool(DIRECTION_PATTERNS["higher"].search(context_lower))

    if not has_lower and not has_higher:
        return None  # no direction language to check

    val = num.numeric_value
    if val < 1.0 and has_higher and not has_lower:
        return (
            f"Direction mismatch: {num.value} < 1.0 but context says "
            f"'higher/increased'. Expected 'lower/reduced'."
        )
    elif val > 1.0 and has_lower and not has_higher:
        return (
            f"Direction mismatch: {num.value} > 1.0 but context says "
            f"'lower/reduced'. Expected 'higher/increased'."
        )
    return None


# ---------------------------------------------------------------------------
# N consistency check
# ---------------------------------------------------------------------------

def check_n_consistency(
    numbers: list[ExtractedNumber],
    results: dict[str, float],
    population_flow: Optional[dict] = None,
    table1_path: Optional[str] = None,
) -> dict:
    """Check that N is consistent across Methods, Results, Table 1, CONSORT, and results_package.

    Returns a dict with N values from each source and a status.
    """
    n_values = {}

    # 1. Extract N from manuscript sections
    for num in numbers:
        if num.number_type == "sample_size":
            section = num.file.replace('.md', '').capitalize()
            key = f"Manuscript ({section})"
            if key not in n_values:
                n_values[key] = []
            n_values[key].append(int(num.numeric_value))

    # 2. Extract N from results_package.json
    n_keys = [k for k in results if any(
        term in k.lower() for term in ['n_total', 'n_analyzed', 'n_enrolled',
                                        'sample_size', 'n_randomised', 'n_randomized',
                                        'population.n', 'n_itt', 'n_pp']
    )]
    for k in n_keys:
        n_values[f"results_package ({k})"] = [int(results[k])]

    # 3. Extract N from population_flow.json
    if population_flow:
        for key in ['n_enrolled', 'n_randomised', 'n_randomized', 'n_analyzed',
                     'n_itt', 'n_per_protocol', 'n_safety']:
            if key in population_flow:
                n_values[f"population_flow ({key})"] = [int(population_flow[key])]
        # Handle nested structures
        if 'flow' in population_flow and isinstance(population_flow['flow'], list):
            for step in population_flow['flow']:
                if isinstance(step, dict) and 'n' in step:
                    label = step.get('label', 'step')
                    n_values[f"population_flow ({label})"] = [int(step['n'])]

    # 4. Extract N from Table 1 (if path provided)
    if table1_path and os.path.exists(table1_path):
        try:
            with open(table1_path, 'r', encoding='utf-8') as f:
                table1_text = f.read()
            # Look for total N in table header or first row
            n_match = re.search(
                r'[Tt]otal\s*(?:\(|,|:)?\s*[Nn]\s*=?\s*(\d[\d,]*)',
                table1_text
            )
            if n_match:
                n_values["Table 1 (total)"] = [int(normalize_number(n_match.group(1)))]
            # Look for group Ns
            for gm in re.finditer(
                r'(\w[\w\s]*?)\s*\(?\s*[Nn]\s*=\s*(\d[\d,]*)\s*\)?',
                table1_text
            ):
                label = gm.group(1).strip()
                n_val = int(normalize_number(gm.group(2)))
                n_values[f"Table 1 ({label})"] = [n_val]
        except Exception:
            pass

    # 5. Determine consistency
    # Collect the "primary" N from each source (largest or first)
    primary_ns = {}
    for source, values in n_values.items():
        primary_ns[source] = max(values) if values else 0

    all_ns = list(primary_ns.values())
    if not all_ns:
        return {"status": "UNCHECKED", "reason": "No N values found", "n_values": n_values}

    unique_ns = set(all_ns)
    if len(unique_ns) == 1:
        return {"status": "PASS", "n_values": n_values}
    elif len(unique_ns) <= 3:
        # Multiple N values may be legitimate (ITT vs PP vs safety)
        # Check if they can be explained by different populations
        return {
            "status": "WARN",
            "reason": f"Multiple N values found: {unique_ns}. May reflect different analysis populations.",
            "n_values": n_values,
        }
    else:
        return {
            "status": "FAIL",
            "reason": f"Inconsistent N values across sources: {primary_ns}",
            "n_values": n_values,
        }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(result: ConsistencyResult, output_path: str) -> None:
    """Write the consistency check report to a markdown file."""
    lines = [
        "# Consistency Check Report",
        "",
        f"**Generated by:** consistency-checker.py",
        f"**Total numbers extracted:** {result.total_numbers}",
        f"**Matched to results_package.json:** {result.matched}",
        f"**Mismatched:** {result.mismatched}",
        f"**Unverified (not found in results_package):** {result.unverified}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total numbers in text | {result.total_numbers} |",
        f"| Matched (PASS) | {result.matched} |",
        f"| Mismatched (FAIL) | {result.mismatched} |",
        f"| Unverified | {result.unverified} |",
        f"| Match rate | {result.matched}/{result.matched + result.mismatched} "
        f"({100 * result.matched / max(1, result.matched + result.mismatched):.0f}%) |",
        f"| N consistency | {result.n_consistency} |",
        "",
    ]

    # Mismatches section
    if result.mismatches:
        lines.extend([
            "---",
            "",
            "## Mismatches (require correction)",
            "",
            "| File | Line | Value in Text | Expected (results_package) | Key | Difference |",
            "|---|---|---|---|---|---|",
        ])
        for num in result.mismatches:
            diff = abs(num.numeric_value - num.match_value) if num.match_value is not None else "N/A"
            if isinstance(diff, float):
                diff = f"{diff:.4f}"
            lines.append(
                f"| {num.file} | {num.line} | {num.value} | "
                f"{num.match_value} | {num.match_key} | {diff} |"
            )
        lines.append("")

    # Direction errors
    if result.direction_errors:
        lines.extend([
            "---",
            "",
            "## Direction Errors (critical)",
            "",
            "| File | Line | Issue |",
            "|---|---|---|",
        ])
        for file, line_num, message in result.direction_errors:
            lines.append(f"| {file} | {line_num} | {message} |")
        lines.append("")

    # N consistency
    lines.extend([
        "---",
        "",
        "## Internal N Consistency",
        "",
        f"**Status:** {result.n_consistency}",
        "",
    ])
    if result.n_values:
        lines.extend([
            "| Source | N Value(s) |",
            "|---|---|",
        ])
        for source, values in result.n_values.items():
            lines.append(f"| {source} | {values} |")
        lines.append("")

    # All verified numbers
    lines.extend([
        "---",
        "",
        "## All Extracted Numbers",
        "",
        "| File | Line | Value | Type | Status | Matched Key |",
        "|---|---|---|---|---|---|",
    ])
    for num in result.numbers:
        lines.append(
            f"| {num.file} | {num.line} | {num.value} | "
            f"{num.number_type} | {num.status} | {num.match_key or '—'} |"
        )
    lines.append("")

    # Write report
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Report written to: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Verify numbers in manuscript match results_package.json"
    )
    parser.add_argument(
        "--manuscript-dir",
        required=True,
        help="Directory containing manuscript markdown files (e.g., ./draft/)",
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Path to results_package.json",
    )
    parser.add_argument(
        "--output",
        default="consistency_check.md",
        help="Output report path (default: consistency_check.md)",
    )
    parser.add_argument(
        "--population-flow",
        default=None,
        help="Path to population_flow.json (optional, for N consistency)",
    )
    parser.add_argument(
        "--table1",
        default=None,
        help="Path to table1.md (optional, for N consistency)",
    )
    args = parser.parse_args()

    # Validate inputs
    if not os.path.isdir(args.manuscript_dir):
        print(f"ERROR: Manuscript directory not found: {args.manuscript_dir}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.results):
        print(f"ERROR: Results package not found: {args.results}", file=sys.stderr)
        sys.exit(1)

    # Load results package
    print(f"Loading results from: {args.results}")
    results = load_results_package(args.results)
    print(f"  Flattened {len(results)} numeric values from results_package.json")

    # Load population flow if provided
    population_flow = None
    if args.population_flow and os.path.isfile(args.population_flow):
        with open(args.population_flow, 'r', encoding='utf-8') as f:
            population_flow = json.load(f)
        print(f"  Loaded population flow from: {args.population_flow}")

    # Extract numbers from all manuscript files
    manuscript_files = sorted(Path(args.manuscript_dir).glob("*.md"))
    if not manuscript_files:
        print(f"WARNING: No markdown files found in {args.manuscript_dir}", file=sys.stderr)

    all_numbers: list[ExtractedNumber] = []
    for md_file in manuscript_files:
        nums = extract_numbers_from_file(str(md_file))
        all_numbers.extend(nums)
        print(f"  Extracted {len(nums)} numbers from {md_file.name}")

    print(f"Total numbers extracted: {len(all_numbers)}")

    # Match numbers against results package
    for num in all_numbers:
        match_number_to_results(num, results)

    # Check direction consistency
    direction_errors = []
    for num in all_numbers:
        error = check_direction_consistency(num, results)
        if error:
            direction_errors.append((num.file, num.line, error))

    # Check N consistency
    n_check = check_n_consistency(
        all_numbers,
        results,
        population_flow=population_flow,
        table1_path=args.table1,
    )

    # Compile results
    result = ConsistencyResult()
    result.total_numbers = len(all_numbers)
    result.matched = sum(1 for n in all_numbers if n.status == "MATCH")
    result.mismatched = sum(1 for n in all_numbers if n.status == "MISMATCH")
    result.unverified = sum(1 for n in all_numbers if n.status == "UNVERIFIED")
    result.n_consistency = n_check.get("status", "UNCHECKED")
    result.n_values = n_check.get("n_values", {})
    result.numbers = all_numbers
    result.mismatches = [n for n in all_numbers if n.status == "MISMATCH"]
    result.direction_errors = direction_errors

    # Generate report
    generate_report(result, args.output)

    # Summary
    print(f"\n--- Consistency Check Summary ---")
    print(f"  MATCH:      {result.matched}")
    print(f"  MISMATCH:   {result.mismatched}")
    print(f"  UNVERIFIED: {result.unverified}")
    print(f"  N status:   {result.n_consistency}")
    print(f"  Direction:  {len(direction_errors)} error(s)")

    # Exit code: non-zero if any mismatches or direction errors
    if result.mismatched > 0 or direction_errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
