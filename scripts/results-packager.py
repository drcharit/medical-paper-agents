#!/usr/bin/env python3
"""Assemble results_package.json from individual analysis outputs.

Collects primary, secondary, subgroup, and sensitivity analysis results,
validates internal consistency, and produces the single source of truth
for all manuscript numbers.

Usage:
    python results-packager.py --analysis-dir ./analysis/ --output results_package.json
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np


def load_json_safe(filepath: str) -> dict:
    """Load a JSON file, returning empty dict if not found."""
    if os.path.exists(filepath):
        with open(filepath) as f:
            return json.load(f)
    return {}


def load_csv_as_records(filepath: str) -> list:
    """Load a CSV file as a list of dicts."""
    import pandas as pd
    if os.path.exists(filepath):
        return pd.read_csv(filepath).to_dict(orient="records")
    return []


def run_consistency_checks(package: dict) -> list:
    """Run internal consistency checks on the assembled package."""
    issues = []

    # Check N consistency across populations
    pop = package.get("populations", {})
    primary = package.get("primary_outcome", {})

    if pop and primary:
        pop_n = pop.get("itt", {}).get("n", 0)
        primary_n = primary.get("n_treatment", 0) + primary.get("n_control", 0)
        if pop_n > 0 and primary_n > 0 and pop_n != primary_n:
            issues.append(f"N mismatch: ITT population ({pop_n}) != primary analysis ({primary_n})")

    # Check CI contains point estimate
    for outcome_key in ["primary_outcome"] + [f"secondary_{i}" for i in range(20)]:
        outcome = package.get(outcome_key, {})
        if not outcome:
            continue
        est = outcome.get("estimate")
        ci_lo = outcome.get("ci_lower")
        ci_hi = outcome.get("ci_upper")
        if est is not None and ci_lo is not None and ci_hi is not None:
            if not (ci_lo <= est <= ci_hi):
                issues.append(f"{outcome_key}: CI [{ci_lo}, {ci_hi}] does not contain estimate {est}")

    # Check percentages in CONSORT flow
    consort = package.get("consort_flow", {})
    if consort:
        assessed = consort.get("assessed_for_eligibility", 0)
        randomised = consort.get("randomised", 0)
        excluded = consort.get("total_excluded", 0)
        if assessed > 0 and (randomised + excluded) != assessed:
            issues.append(f"CONSORT: assessed ({assessed}) != randomised ({randomised}) + excluded ({excluded})")

    return issues


def compute_package_hash(package: dict) -> str:
    """Compute SHA-256 hash of the results package."""
    content = json.dumps(package, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Assemble results_package.json")
    parser.add_argument("--analysis-dir", required=True, help="Directory containing analysis outputs")
    parser.add_argument("--output", default="results_package.json", help="Output file path")
    args = parser.parse_args()

    analysis_dir = args.analysis_dir
    if not os.path.isdir(analysis_dir):
        print(f"Error: Directory not found: {analysis_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Assembling results package from {analysis_dir}...")

    package = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "source_directory": os.path.abspath(analysis_dir),
            "generator": "results-packager.py v1.0",
        },
        "populations": load_json_safe(os.path.join(analysis_dir, "populations.json")),
        "consort_flow": load_json_safe(os.path.join(analysis_dir, "population_flow.json")),
        "primary_outcome": load_json_safe(os.path.join(analysis_dir, "primary_results.json")),
        "secondary_outcomes": load_json_safe(os.path.join(analysis_dir, "secondary_results.json")),
        "subgroup_analyses": load_json_safe(os.path.join(analysis_dir, "subgroup_results.json")),
        "sensitivity_analyses": load_json_safe(os.path.join(analysis_dir, "sensitivity_results.json")),
        "table1_data": load_json_safe(os.path.join(analysis_dir, "table1_data.json")),
        "survival_data": load_json_safe(os.path.join(analysis_dir, "survival_data.json")),
        "missing_data": load_json_safe(os.path.join(analysis_dir, "missing_data.json")),
    }

    # Run consistency checks
    issues = run_consistency_checks(package)
    if issues:
        print(f"\nWARNING: {len(issues)} consistency issues found:")
        for issue in issues:
            print(f"  - {issue}")

    package["metadata"]["consistency_issues"] = issues
    package["metadata"]["n_issues"] = len(issues)

    # Compute hash
    package_hash = compute_package_hash(package)
    package["metadata"]["sha256_hash"] = package_hash

    # Write output
    with open(args.output, "w") as f:
        json.dump(package, f, indent=2, default=str)

    print(f"\nResults package written to {args.output}")
    print(f"SHA-256: {package_hash}")
    print(f"Consistency issues: {len(issues)}")

    # Write consistency report
    report_path = os.path.join(os.path.dirname(args.output), "consistency_report.md")
    with open(report_path, "w") as f:
        f.write("# Results Package Consistency Report\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n")
        f.write(f"**Hash:** `{package_hash}`\n\n")
        if issues:
            f.write(f"## {len(issues)} Issues Found\n\n")
            for issue in issues:
                f.write(f"- {issue}\n")
        else:
            f.write("## No Issues Found\n\nAll consistency checks passed.\n")

    print(f"Consistency report: {report_path}")


if __name__ == "__main__":
    main()
