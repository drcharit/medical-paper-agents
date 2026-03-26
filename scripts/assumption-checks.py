#!/usr/bin/env python3
"""Statistical assumption testing for medical research analyses.

Tests proportional hazards, normality, multicollinearity, and homoscedasticity.
Produces an assumption check report with PASS/FAIL per test.

Usage:
    python assumption-checks.py --data analysis.csv --model cox --outcome "time event" --predictors "age sex bmi treatment"
"""

import argparse
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def test_normality(series: pd.Series, name: str, output_dir: str) -> dict:
    """Test normality using Shapiro-Wilk (N<5000) and D'Agostino-Pearson."""
    from scipy import stats
    result = {"variable": name, "tests": []}

    clean = series.dropna()
    if len(clean) < 8:
        result["tests"].append({"test": "Shapiro-Wilk", "status": "SKIP", "reason": "N < 8"})
        return result

    # Shapiro-Wilk (limited to N<5000)
    if len(clean) <= 5000:
        stat, p = stats.shapiro(clean)
        result["tests"].append({
            "test": "Shapiro-Wilk",
            "statistic": round(float(stat), 4),
            "p_value": round(float(p), 4),
            "status": "PASS" if p > 0.05 else "FAIL",
        })

    # D'Agostino-Pearson
    if len(clean) >= 20:
        stat, p = stats.normaltest(clean)
        result["tests"].append({
            "test": "D'Agostino-Pearson",
            "statistic": round(float(stat), 4),
            "p_value": round(float(p), 4),
            "status": "PASS" if p > 0.05 else "FAIL",
        })

    # Q-Q plot
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    stats.probplot(clean, dist="norm", plot=ax)
    ax.set_title(f"Q-Q Plot: {name}")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, f"qq_{name}.png"), dpi=150)
    plt.close(fig)
    result["qq_plot"] = f"qq_{name}.png"

    return result


def test_vif(df: pd.DataFrame, predictors: list) -> list:
    """Compute Variance Inflation Factor for each predictor."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    X = df[predictors].dropna()
    # Add constant
    X_with_const = X.copy()
    X_with_const["_const"] = 1.0

    results = []
    for i, col in enumerate(predictors):
        try:
            vif = variance_inflation_factor(X_with_const.values, i)
            results.append({
                "variable": col,
                "vif": round(float(vif), 2),
                "status": "PASS" if vif < 5 else ("WARNING" if vif < 10 else "FAIL"),
            })
        except Exception as e:
            results.append({"variable": col, "vif": None, "status": "ERROR", "error": str(e)})

    return results


def test_proportional_hazards(df: pd.DataFrame, time_col: str, event_col: str,
                               predictors: list) -> list:
    """Test proportional hazards assumption using Schoenfeld residuals."""
    try:
        from lifelines import CoxPHFitter
    except ImportError:
        return [{"test": "PH Assumption", "status": "SKIP", "reason": "lifelines not installed"}]

    cols = [time_col, event_col] + predictors
    analysis_df = df[cols].dropna()

    cph = CoxPHFitter()
    cph.fit(analysis_df, duration_col=time_col, event_col=event_col)

    try:
        ph_test = cph.check_assumptions(analysis_df, p_value_threshold=0.05, show_plots=False)
        # If no exception, assumptions are met
        results = []
        for pred in predictors:
            results.append({
                "variable": pred,
                "test": "Schoenfeld residuals",
                "status": "PASS",
                "note": "Proportional hazards assumption satisfied",
            })
        return results
    except Exception as e:
        # Parse the exception to find which variables fail
        msg = str(e)
        results = []
        for pred in predictors:
            if pred in msg:
                results.append({
                    "variable": pred,
                    "test": "Schoenfeld residuals",
                    "status": "FAIL",
                    "note": "Proportional hazards assumption violated",
                })
            else:
                results.append({
                    "variable": pred,
                    "test": "Schoenfeld residuals",
                    "status": "PASS",
                })
        return results


def test_homoscedasticity(residuals: np.ndarray, fitted: np.ndarray, output_dir: str) -> dict:
    """Test homoscedasticity using Breusch-Pagan test."""
    from scipy import stats

    result = {}
    # Breusch-Pagan test
    try:
        from statsmodels.stats.diagnostic import het_breuschpagan
        import statsmodels.api as sm
        X = sm.add_constant(fitted.reshape(-1, 1))
        bp_stat, bp_p, _, _ = het_breuschpagan(residuals, X)
        result = {
            "test": "Breusch-Pagan",
            "statistic": round(float(bp_stat), 4),
            "p_value": round(float(bp_p), 4),
            "status": "PASS" if bp_p > 0.05 else "FAIL",
        }
    except Exception as e:
        result = {"test": "Breusch-Pagan", "status": "ERROR", "error": str(e)}

    # Residuals vs fitted plot
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(fitted, residuals, alpha=0.4, s=10)
    ax.axhline(y=0, color="red", linestyle="--")
    ax.set_xlabel("Fitted Values")
    ax.set_ylabel("Residuals")
    ax.set_title("Residuals vs Fitted")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "residuals_vs_fitted.png"), dpi=150)
    plt.close(fig)

    return result


def write_report(all_results: dict, output_dir: str):
    """Write assumption checks report."""
    lines = [
        "# Statistical Assumption Checks",
        f"\n**Generated:** {datetime.now().isoformat()}",
        "",
    ]

    for section, results in all_results.items():
        lines.append(f"## {section}\n")
        if isinstance(results, list):
            for r in results:
                status = r.get("status", "N/A")
                var = r.get("variable", r.get("test", ""))
                icon = "PASS" if status == "PASS" else ("FAIL" if status == "FAIL" else "WARN")
                p = r.get("p_value", "")
                p_str = f" (P={p})" if p else ""
                lines.append(f"- **{var}**: {icon}{p_str}")
                if "note" in r:
                    lines.append(f"  - {r['note']}")
            lines.append("")
        elif isinstance(results, dict):
            status = results.get("status", "N/A")
            p = results.get("p_value", "")
            lines.append(f"- **{results.get('test', '')}**: {status} (P={p})")
            lines.append("")

    with open(os.path.join(output_dir, "assumption_checks.md"), "w") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Statistical assumption checks")
    parser.add_argument("--data", required=True, help="Path to analysis data (CSV)")
    parser.add_argument("--model", choices=["cox", "linear", "logistic"], default="linear")
    parser.add_argument("--outcome", required=True, nargs="+", help="Outcome column(s): single for linear/logistic, two (time event) for cox")
    parser.add_argument("--predictors", required=True, nargs="+", help="Predictor columns")
    parser.add_argument("--output-dir", default="./figures", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    df = pd.read_csv(args.data)
    print(f"Loaded {len(df)} rows, model type: {args.model}")

    all_results = {}

    # Multicollinearity (VIF) — applicable to all models
    print("Testing multicollinearity (VIF)...")
    all_results["Multicollinearity (VIF)"] = test_vif(df, args.predictors)

    if args.model == "cox":
        time_col, event_col = args.outcome[0], args.outcome[1]
        print("Testing proportional hazards assumption...")
        all_results["Proportional Hazards"] = test_proportional_hazards(
            df, time_col, event_col, args.predictors
        )
    else:
        # Normality of continuous predictors
        print("Testing normality...")
        normality_results = []
        for pred in args.predictors:
            if pd.api.types.is_numeric_dtype(df[pred]) and df[pred].nunique() > 10:
                res = test_normality(df[pred], pred, args.output_dir)
                normality_results.extend(res.get("tests", []))
        if normality_results:
            all_results["Normality"] = normality_results

    write_report(all_results, args.output_dir)
    print(f"Report: {os.path.join(args.output_dir, 'assumption_checks.md')}")


if __name__ == "__main__":
    main()
