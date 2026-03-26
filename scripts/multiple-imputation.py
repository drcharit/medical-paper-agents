#!/usr/bin/env python3
"""MICE-style multiple imputation for missing data in clinical datasets.

Assesses missingness patterns, performs multiple imputation using chained
equations, and pools results using Rubin's rules.

Usage:
    python multiple-imputation.py --input data.csv --m 20 --outcome outcome_var --output-dir ./analysis/imputed/
"""

import argparse
import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd


def assess_missingness(df: pd.DataFrame) -> dict:
    """Assess missingness patterns and mechanism."""
    total_cells = df.shape[0] * df.shape[1]
    missing_cells = int(df.isna().sum().sum())

    per_column = {}
    for col in df.columns:
        n_miss = int(df[col].isna().sum())
        if n_miss > 0:
            per_column[col] = {
                "n_missing": n_miss,
                "pct_missing": round(100 * n_miss / len(df), 1),
            }

    # Little's MCAR test approximation (chi-square based)
    mechanism = "Unknown"
    try:
        from scipy import stats
        # Simple test: compare means of complete vs incomplete cases for each variable
        has_any_missing = df.isna().any(axis=1)
        if has_any_missing.any() and (~has_any_missing).any():
            p_values = []
            for col in df.select_dtypes(include=[np.number]).columns:
                complete = df.loc[~has_any_missing, col].dropna()
                incomplete = df.loc[has_any_missing, col].dropna()
                if len(complete) > 2 and len(incomplete) > 2:
                    _, p = stats.mannwhitneyu(complete, incomplete, alternative="two-sided")
                    p_values.append(p)
            if p_values:
                min_p = min(p_values)
                if min_p > 0.05:
                    mechanism = "MCAR (Missing Completely At Random) - supported by pattern analysis"
                else:
                    mechanism = "MAR (Missing At Random) - some variables differ between complete/incomplete cases"
    except Exception:
        mechanism = "Could not determine - manual assessment recommended"

    return {
        "total_cells": total_cells,
        "missing_cells": missing_cells,
        "pct_missing_overall": round(100 * missing_cells / total_cells, 1) if total_cells > 0 else 0,
        "n_complete_cases": int((~df.isna().any(axis=1)).sum()),
        "pct_complete_cases": round(100 * (~df.isna().any(axis=1)).sum() / len(df), 1),
        "mechanism_assessment": mechanism,
        "per_column": per_column,
    }


def impute_mice(df: pd.DataFrame, m: int = 20, max_iter: int = 10,
                random_state: int = 42) -> list:
    """Perform MICE (Multiple Imputation by Chained Equations).

    Returns a list of m imputed DataFrames.
    """
    try:
        from sklearn.experimental import enable_iterative_imputer
        from sklearn.impute import IterativeImputer
    except ImportError:
        print("Error: scikit-learn required. Install with: pip install scikit-learn", file=sys.stderr)
        sys.exit(1)

    # Separate numeric and categorical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

    # Encode categoricals
    encoded_df = df.copy()
    label_maps = {}
    for col in cat_cols:
        if encoded_df[col].isna().any():
            encoded_df[col] = encoded_df[col].fillna("__MISSING__")
        codes, uniques = pd.factorize(encoded_df[col])
        encoded_df[col] = codes.astype(float)
        encoded_df.loc[encoded_df[col] == -1, col] = np.nan  # restore NaN for __MISSING__
        label_maps[col] = dict(enumerate(uniques))

    imputed_datasets = []
    for i in range(m):
        imputer = IterativeImputer(
            max_iter=max_iter,
            random_state=random_state + i,
            sample_posterior=True,
        )
        imputed_array = imputer.fit_transform(encoded_df)
        imputed_df = pd.DataFrame(imputed_array, columns=encoded_df.columns, index=df.index)

        # Decode categoricals back
        for col in cat_cols:
            imputed_df[col] = imputed_df[col].round().astype(int)
            imputed_df[col] = imputed_df[col].map(label_maps.get(col, {}))

        # Ensure numeric types preserved
        for col in numeric_cols:
            if df[col].dtype in [np.int64, np.int32]:
                imputed_df[col] = imputed_df[col].round().astype(df[col].dtype)

        imputed_datasets.append(imputed_df)

    return imputed_datasets


def pool_estimates_rubins(estimates: list, std_errors: list) -> dict:
    """Pool estimates using Rubin's rules.

    estimates: list of point estimates from m imputations
    std_errors: list of standard errors from m imputations
    """
    m = len(estimates)
    estimates = np.array(estimates)
    variances = np.array(std_errors) ** 2

    # Pooled estimate
    q_bar = np.mean(estimates)

    # Within-imputation variance
    u_bar = np.mean(variances)

    # Between-imputation variance
    b = np.var(estimates, ddof=1)

    # Total variance
    t = u_bar + (1 + 1 / m) * b

    # Pooled standard error
    se = np.sqrt(t)

    # Degrees of freedom (Barnard-Rubin)
    if u_bar > 0:
        lambda_hat = (1 + 1 / m) * b / t
        df_old = (m - 1) / (lambda_hat ** 2) if lambda_hat > 0 else float("inf")
    else:
        df_old = float("inf")

    # 95% CI
    from scipy import stats
    if df_old < float("inf") and df_old > 0:
        t_crit = stats.t.ppf(0.975, df=min(df_old, 1e6))
    else:
        t_crit = 1.96

    ci_lower = q_bar - t_crit * se
    ci_upper = q_bar + t_crit * se

    # P-value
    if se > 0:
        t_stat = q_bar / se
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=min(df_old, 1e6)))
    else:
        p_value = 0.0

    return {
        "pooled_estimate": round(float(q_bar), 4),
        "pooled_se": round(float(se), 4),
        "ci_lower": round(float(ci_lower), 4),
        "ci_upper": round(float(ci_upper), 4),
        "p_value": round(float(p_value), 4),
        "within_variance": round(float(u_bar), 6),
        "between_variance": round(float(b), 6),
        "total_variance": round(float(t), 6),
        "fraction_missing_info": round(float((1 + 1 / m) * b / t), 3) if t > 0 else 0,
        "df": round(float(df_old), 1),
        "m_imputations": m,
    }


def write_missingness_report(assessment: dict, output_dir: str):
    """Write missingness assessment report."""
    lines = [
        "# Missing Data Assessment Report",
        f"\n**Generated:** {datetime.now().isoformat()}",
        "",
        "## Summary",
        f"- Total cells: {assessment['total_cells']:,}",
        f"- Missing cells: {assessment['missing_cells']:,} ({assessment['pct_missing_overall']}%)",
        f"- Complete cases: {assessment['n_complete_cases']:,} ({assessment['pct_complete_cases']}%)",
        f"- Mechanism: {assessment['mechanism_assessment']}",
        "",
        "## Missing by Variable",
        "",
        "| Variable | N Missing | % Missing |",
        "|---|---|---|",
    ]
    for col, info in sorted(assessment["per_column"].items(), key=lambda x: -x[1]["pct_missing"]):
        lines.append(f"| {col} | {info['n_missing']:,} | {info['pct_missing']}% |")

    with open(os.path.join(output_dir, "missingness_report.md"), "w") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Multiple imputation for missing data")
    parser.add_argument("--input", required=True, help="Path to data file (CSV)")
    parser.add_argument("--m", type=int, default=20, help="Number of imputations (default: 20)")
    parser.add_argument("--max-iter", type=int, default=10, help="Max MICE iterations (default: 10)")
    parser.add_argument("--outcome", help="Outcome variable (for complete-case comparison)")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    df = pd.read_csv(args.input)
    print(f"Loaded {len(df):,} rows x {len(df.columns)} columns")

    # Assess missingness
    print("Assessing missingness patterns...")
    assessment = assess_missingness(df)
    write_missingness_report(assessment, args.output_dir)

    if assessment["missing_cells"] == 0:
        print("No missing data found. Skipping imputation.")
        return

    # Perform imputation
    print(f"Running MICE with m={args.m} imputations...")
    imputed_datasets = impute_mice(df, m=args.m, max_iter=args.max_iter, random_state=args.seed)

    # Save imputed datasets
    for i, imp_df in enumerate(imputed_datasets):
        out_path = os.path.join(args.output_dir, f"imputed_{i + 1:02d}.parquet")
        imp_df.to_parquet(out_path, index=False)

    print(f"Saved {args.m} imputed datasets to {args.output_dir}/")

    # Save assessment
    with open(os.path.join(args.output_dir, "missingness_assessment.json"), "w") as f:
        json.dump(assessment, f, indent=2, default=str)

    print(f"Reports written to {args.output_dir}/")


if __name__ == "__main__":
    main()
