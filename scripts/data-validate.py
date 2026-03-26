#!/usr/bin/env python3
"""Medical data validation with configurable rules.

Checks for impossible values, duplicates, cross-field consistency,
and outliers in clinical research datasets.

Usage:
    python data-validate.py --input clean.csv --output-dir ./data/
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

import numpy as np
import pandas as pd


# Built-in medical validation rules: (min, max) inclusive
MEDICAL_RANGES = {
    "age": (0, 120),
    "age_years": (0, 120),
    "bmi": (10, 80),
    "heart_rate": (20, 300),
    "hr": (20, 300),
    "systolic_bp": (50, 300),
    "sbp": (50, 300),
    "diastolic_bp": (20, 200),
    "dbp": (20, 200),
    "temperature": (30, 45),
    "temp": (30, 45),
    "spo2": (50, 100),
    "oxygen_saturation": (50, 100),
    "egfr": (0, 200),
    "hemoglobin": (2, 25),
    "hb": (2, 25),
    "creatinine": (0, 30),
    "sodium": (100, 180),
    "potassium": (1.5, 9.0),
    "glucose": (10, 1000),
    "hba1c": (2, 20),
    "alt": (0, 10000),
    "ast": (0, 10000),
    "platelets": (5, 2000),
    "wbc": (0.1, 500),
    "weight_kg": (1, 300),
    "height_cm": (30, 250),
    "ef": (5, 85),
    "lvef": (5, 85),
    "ejection_fraction": (5, 85),
}

DATE_COLUMN_PATTERNS = ["date", "dt", "dob", "enrollment", "randomization", "discharge", "death", "follow_up"]


def find_date_columns(df: pd.DataFrame) -> list:
    """Identify likely date columns."""
    date_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if any(p in col_lower for p in DATE_COLUMN_PATTERNS):
            date_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
    return date_cols


def check_impossible_values(df: pd.DataFrame) -> list:
    """Check numeric columns against medical range rules."""
    issues = []
    for col in df.columns:
        col_lower = col.lower().replace(" ", "_")
        if col_lower in MEDICAL_RANGES and pd.api.types.is_numeric_dtype(df[col]):
            vmin, vmax = MEDICAL_RANGES[col_lower]
            mask = df[col].notna() & ((df[col] < vmin) | (df[col] > vmax))
            n_violations = int(mask.sum())
            if n_violations > 0:
                bad_values = df.loc[mask, col].head(5).tolist()
                issues.append({
                    "type": "impossible_value",
                    "column": col,
                    "rule": f"Expected range [{vmin}, {vmax}]",
                    "n_violations": n_violations,
                    "sample_values": bad_values,
                    "row_indices": df.index[mask].tolist()[:20],
                })
    return issues


def check_negative_values(df: pd.DataFrame) -> list:
    """Check for negative values in columns that should be non-negative."""
    issues = []
    non_negative_patterns = ["count", "duration", "length", "weight", "height", "dose", "volume"]
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            col_lower = col.lower()
            if any(p in col_lower for p in non_negative_patterns):
                mask = df[col].notna() & (df[col] < 0)
                n_neg = int(mask.sum())
                if n_neg > 0:
                    issues.append({
                        "type": "negative_value",
                        "column": col,
                        "n_violations": n_neg,
                        "sample_values": df.loc[mask, col].head(5).tolist(),
                    })
    return issues


def check_future_dates(df: pd.DataFrame) -> list:
    """Check for dates in the future."""
    issues = []
    today = pd.Timestamp.now()
    for col in find_date_columns(df):
        try:
            dates = pd.to_datetime(df[col], errors="coerce")
            mask = dates.notna() & (dates > today)
            n_future = int(mask.sum())
            if n_future > 0:
                issues.append({
                    "type": "future_date",
                    "column": col,
                    "n_violations": n_future,
                    "sample_values": [str(d) for d in dates[mask].head(5).tolist()],
                })
        except Exception:
            pass
    return issues


def check_duplicates(df: pd.DataFrame, id_columns: list = None) -> list:
    """Check for duplicate records."""
    issues = []
    # Exact duplicates
    n_exact = int(df.duplicated().sum())
    if n_exact > 0:
        issues.append({
            "type": "exact_duplicate",
            "n_violations": n_exact,
            "pct": round(100 * n_exact / len(df), 2),
        })
    # ID-based duplicates
    if id_columns:
        for id_col in id_columns:
            if id_col in df.columns:
                n_dup = int(df[id_col].duplicated().sum())
                if n_dup > 0:
                    issues.append({
                        "type": "duplicate_id",
                        "column": id_col,
                        "n_violations": n_dup,
                        "sample_ids": df.loc[df[id_col].duplicated(keep=False), id_col].head(10).tolist(),
                    })
    return issues


def check_cross_field_consistency(df: pd.DataFrame) -> list:
    """Check logical consistency between fields."""
    issues = []
    cols_lower = {c.lower(): c for c in df.columns}

    # Death date requires death event
    death_date_col = None
    death_event_col = None
    for c in df.columns:
        cl = c.lower()
        if "death" in cl and "date" in cl:
            death_date_col = c
        if "death" in cl and "date" not in cl and "cause" not in cl:
            death_event_col = c

    if death_date_col and death_event_col:
        has_date = df[death_date_col].notna()
        has_event = df[death_event_col].isin([1, True, "yes", "Yes", "Y"])
        mismatch = has_date & ~has_event
        n = int(mismatch.sum())
        if n > 0:
            issues.append({
                "type": "cross_field",
                "rule": f"{death_date_col} present but {death_event_col} not indicated",
                "n_violations": n,
            })

    # Discharge after admission
    admit_col = None
    discharge_col = None
    for c in df.columns:
        cl = c.lower()
        if "admit" in cl or "admission" in cl:
            admit_col = c
        if "discharge" in cl:
            discharge_col = c

    if admit_col and discharge_col:
        try:
            admit_dt = pd.to_datetime(df[admit_col], errors="coerce")
            discharge_dt = pd.to_datetime(df[discharge_col], errors="coerce")
            mask = admit_dt.notna() & discharge_dt.notna() & (discharge_dt < admit_dt)
            n = int(mask.sum())
            if n > 0:
                issues.append({
                    "type": "cross_field",
                    "rule": f"{discharge_col} before {admit_col}",
                    "n_violations": n,
                })
        except Exception:
            pass

    return issues


def check_outliers_iqr(df: pd.DataFrame, multiplier: float = 3.0) -> list:
    """Flag outliers using the IQR method (flag, not remove)."""
    issues = []
    for col in df.select_dtypes(include=[np.number]).columns:
        series = df[col].dropna()
        if len(series) < 10:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr
        mask = (series < lower) | (series > upper)
        n_outliers = int(mask.sum())
        if n_outliers > 0:
            issues.append({
                "type": "outlier",
                "column": col,
                "method": f"IQR x{multiplier}",
                "bounds": f"[{lower:.2f}, {upper:.2f}]",
                "n_flagged": n_outliers,
                "sample_values": series[mask].head(5).tolist(),
            })
    return issues


def write_validation_report(all_issues: dict, df: pd.DataFrame, output_dir: str):
    """Write validation report as markdown."""
    lines = [
        "# Data Validation Report",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Rows:** {len(df):,}",
        f"**Columns:** {len(df.columns)}",
        "",
    ]

    total_issues = sum(len(v) for v in all_issues.values())
    lines.append(f"## Summary: {total_issues} issue types found\n")

    for category, issues in all_issues.items():
        if not issues:
            continue
        lines.append(f"### {category.replace('_', ' ').title()} ({len(issues)} issues)\n")
        for issue in issues:
            n = issue.get("n_violations", issue.get("n_flagged", 0))
            lines.append(f"- **{issue.get('column', 'N/A')}**: {n} violations")
            if "rule" in issue:
                lines.append(f"  - Rule: {issue['rule']}")
            if "sample_values" in issue:
                samples = ", ".join(str(v) for v in issue["sample_values"][:5])
                lines.append(f"  - Sample values: {samples}")
            lines.append("")

    if total_issues == 0:
        lines.append("No validation issues found. Data appears clean.\n")

    with open(os.path.join(output_dir, "validation_report.md"), "w") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Validate medical research data")
    parser.add_argument("--input", required=True, help="Path to data file (CSV, Parquet, etc.)")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--id-columns", nargs="*", help="ID columns to check for duplicates")
    parser.add_argument("--iqr-multiplier", type=float, default=3.0, help="IQR multiplier for outlier detection")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    ext = os.path.splitext(args.input)[1].lower()
    if ext == ".parquet":
        df = pd.read_parquet(args.input)
    elif ext == ".csv":
        df = pd.read_csv(args.input)
    else:
        df = pd.read_csv(args.input)

    print(f"Loaded {len(df):,} rows x {len(df.columns)} columns")
    print("Running validation checks...")

    all_issues = {
        "impossible_values": check_impossible_values(df),
        "negative_values": check_negative_values(df),
        "future_dates": check_future_dates(df),
        "duplicates": check_duplicates(df, args.id_columns),
        "cross_field": check_cross_field_consistency(df),
        "outliers": check_outliers_iqr(df, args.iqr_multiplier),
    }

    total = sum(len(v) for v in all_issues.values())
    print(f"Found {total} issue types")

    write_validation_report(all_issues, df, args.output_dir)

    with open(os.path.join(args.output_dir, "validation_issues.json"), "w") as f:
        json.dump(all_issues, f, indent=2, default=str)

    print(f"Outputs written to {args.output_dir}/")


if __name__ == "__main__":
    main()
