#!/usr/bin/env python3
"""Derive analysis populations, composite endpoints, and calculated variables.

Applies inclusion/exclusion criteria, defines ITT/PP/safety populations,
creates composite endpoints, and produces CONSORT flow numbers.

Usage:
    python data-derive.py --input clean.csv --config derive_config.yaml --output-dir ./data/analysis/
"""

import argparse
import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd


def apply_exclusion_criteria(df: pd.DataFrame, criteria: list) -> tuple:
    """Apply inclusion/exclusion criteria, tracking N at each step.

    criteria: list of dicts with keys 'name', 'column', 'condition', 'value'
    Returns: (filtered_df, flow_log)
    """
    flow_log = [{"step": "Assessed for eligibility", "n": len(df), "excluded": 0, "reason": None}]
    current = df.copy()

    for criterion in criteria:
        name = criterion["name"]
        col = criterion["column"]
        condition = criterion["condition"]  # eq, ne, gt, lt, gte, lte, in, notin, isna, notna
        value = criterion.get("value")

        before_n = len(current)
        if condition == "eq":
            mask = current[col] == value
        elif condition == "ne":
            mask = current[col] != value
        elif condition == "gt":
            mask = current[col] > value
        elif condition == "lt":
            mask = current[col] < value
        elif condition == "gte":
            mask = current[col] >= value
        elif condition == "lte":
            mask = current[col] <= value
        elif condition == "in":
            mask = current[col].isin(value)
        elif condition == "notin":
            mask = ~current[col].isin(value)
        elif condition == "isna":
            mask = current[col].isna()
        elif condition == "notna":
            mask = current[col].notna()
        else:
            print(f"Warning: Unknown condition '{condition}' for {name}, skipping")
            continue

        # For exclusion criteria, we KEEP rows that meet the criterion
        # For inclusion criteria (keep=True), we keep matching rows
        if criterion.get("type", "inclusion") == "exclusion":
            current = current[~mask]
        else:
            current = current[mask]

        excluded = before_n - len(current)
        flow_log.append({
            "step": name,
            "n": len(current),
            "excluded": excluded,
            "reason": name,
        })

    return current, flow_log


def define_populations(df: pd.DataFrame, config: dict) -> dict:
    """Define ITT, mITT, per-protocol, and safety populations."""
    populations = {}

    # ITT: all randomised
    randomised_col = config.get("randomised_column", "randomised")
    if randomised_col in df.columns:
        populations["itt"] = df[df[randomised_col] == 1].copy()
    else:
        populations["itt"] = df.copy()

    # mITT: randomised + received at least 1 dose
    dose_col = config.get("received_treatment_column", "received_treatment")
    if dose_col in df.columns:
        populations["mitt"] = populations["itt"][populations["itt"][dose_col] == 1].copy()
    else:
        populations["mitt"] = populations["itt"].copy()

    # Per-protocol: completed as planned
    completed_col = config.get("completed_protocol_column", "completed_protocol")
    if completed_col in df.columns:
        populations["pp"] = populations["itt"][populations["itt"][completed_col] == 1].copy()
    else:
        populations["pp"] = populations["itt"].copy()

    # Safety: received at least 1 dose (same as mITT typically)
    populations["safety"] = populations["mitt"].copy()

    return populations


def create_composite_endpoint(df: pd.DataFrame, endpoint_config: dict) -> pd.Series:
    """Create a composite endpoint from multiple component events.

    endpoint_config: {'name': 'MACE', 'components': ['mi', 'stroke', 'cv_death'], 'type': 'any'}
    """
    components = endpoint_config["components"]
    composite_type = endpoint_config.get("type", "any")

    if composite_type == "any":
        return df[components].max(axis=1).astype(int)
    elif composite_type == "all":
        return df[components].min(axis=1).astype(int)
    else:
        return df[components].max(axis=1).astype(int)


def create_time_to_event(df: pd.DataFrame, start_col: str, event_date_col: str,
                          censor_date_col: str, event_col: str) -> pd.DataFrame:
    """Create time-to-event variables."""
    result = df.copy()
    start = pd.to_datetime(result[start_col], errors="coerce")

    if event_date_col in result.columns:
        event_date = pd.to_datetime(result[event_date_col], errors="coerce")
    else:
        event_date = pd.NaT

    censor_date = pd.to_datetime(result[censor_date_col], errors="coerce")

    # Time = event date if event occurred, otherwise censor date
    has_event = result[event_col] == 1
    end_date = pd.Series(index=result.index, dtype="datetime64[ns]")
    end_date[has_event] = event_date[has_event] if not isinstance(event_date, type(pd.NaT)) else censor_date[has_event]
    end_date[~has_event] = censor_date[~has_event]

    result["time_to_event_days"] = (end_date - start).dt.days
    result["time_to_event_years"] = result["time_to_event_days"] / 365.25

    return result


def derive_bmi(df: pd.DataFrame, height_col: str = "height_cm", weight_col: str = "weight_kg") -> pd.Series:
    """Derive BMI from height (cm) and weight (kg)."""
    if height_col in df.columns and weight_col in df.columns:
        height_m = df[height_col] / 100
        return (df[weight_col] / (height_m ** 2)).round(1)
    return pd.Series(dtype=float)


def derive_egfr_ckdepi(df: pd.DataFrame, creat_col: str = "creatinine",
                        age_col: str = "age", sex_col: str = "sex") -> pd.Series:
    """Derive eGFR using CKD-EPI 2021 equation (race-free)."""
    if not all(c in df.columns for c in [creat_col, age_col, sex_col]):
        return pd.Series(dtype=float)

    scr = df[creat_col]
    age = df[age_col]
    is_female = df[sex_col].str.lower().isin(["f", "female", "0"])

    kappa = np.where(is_female, 0.7, 0.9)
    alpha = np.where(is_female, -0.241, -0.302)
    factor = np.where(is_female, 1.012, 1.0)

    min_ratio = np.minimum(scr / kappa, 1.0)
    max_ratio = np.maximum(scr / kappa, 1.0)

    egfr = 142 * (min_ratio ** alpha) * (max_ratio ** -1.200) * (0.9938 ** age) * factor
    return pd.Series(egfr, index=df.index).round(1)


def categorize_variable(series: pd.Series, bins: list, labels: list) -> pd.Series:
    """Categorize a continuous variable into groups."""
    return pd.cut(series, bins=bins, labels=labels, right=False)


def generate_consort_flow(flow_log: list, populations: dict, group_col: str = None,
                           df: pd.DataFrame = None) -> dict:
    """Generate CONSORT flow diagram numbers."""
    flow = {
        "assessed_for_eligibility": flow_log[0]["n"],
        "exclusions": [],
        "total_excluded": 0,
    }

    for entry in flow_log[1:]:
        if entry["excluded"] > 0:
            flow["exclusions"].append({
                "reason": entry["reason"],
                "n": entry["excluded"],
            })
            flow["total_excluded"] += entry["excluded"]

    # Population sizes
    for pop_name, pop_df in populations.items():
        flow[f"n_{pop_name}"] = len(pop_df)
        if group_col and group_col in pop_df.columns:
            for group_val in pop_df[group_col].unique():
                flow[f"n_{pop_name}_{group_val}"] = int((pop_df[group_col] == group_val).sum())

    return flow


def main():
    parser = argparse.ArgumentParser(description="Derive analysis populations and variables")
    parser.add_argument("--input", required=True, help="Path to cleaned data file")
    parser.add_argument("--config", help="Path to derivation config YAML (optional)")
    parser.add_argument("--output-dir", required=True, help="Output directory for analysis datasets")
    parser.add_argument("--group-col", help="Treatment group column name")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    ext = os.path.splitext(args.input)[1].lower()
    if ext == ".parquet":
        df = pd.read_parquet(args.input)
    else:
        df = pd.read_csv(args.input)

    print(f"Loaded {len(df):,} rows x {len(df.columns)} columns")

    # Load config if provided
    config = {}
    if args.config:
        import yaml
        with open(args.config) as f:
            config = yaml.safe_load(f)

    # Apply exclusion criteria
    criteria = config.get("exclusion_criteria", [])
    if criteria:
        filtered, flow_log = apply_exclusion_criteria(df, criteria)
    else:
        filtered = df.copy()
        flow_log = [{"step": "All records", "n": len(df), "excluded": 0, "reason": None}]

    # Define populations
    populations = define_populations(filtered, config)
    for name, pop_df in populations.items():
        print(f"Population '{name}': {len(pop_df):,} participants")

    # Derive variables
    if "height_cm" in filtered.columns and "weight_kg" in filtered.columns:
        for pop_name in populations:
            populations[pop_name]["bmi_derived"] = derive_bmi(populations[pop_name])

    if all(c in filtered.columns for c in ["creatinine", "age", "sex"]):
        for pop_name in populations:
            populations[pop_name]["egfr_derived"] = derive_egfr_ckdepi(populations[pop_name])

    # Create composite endpoints
    composites = config.get("composite_endpoints", [])
    for comp in composites:
        for pop_name in populations:
            pop_df = populations[pop_name]
            if all(c in pop_df.columns for c in comp["components"]):
                populations[pop_name][comp["name"]] = create_composite_endpoint(pop_df, comp)

    # Save populations
    for name, pop_df in populations.items():
        out_path = os.path.join(args.output_dir, f"analysis_{name}.parquet")
        pop_df.to_parquet(out_path, index=False)
        print(f"Saved {out_path} ({len(pop_df):,} rows)")

    # Generate CONSORT flow
    consort = generate_consort_flow(flow_log, populations, args.group_col, filtered)
    flow_path = os.path.join(args.output_dir, "population_flow.json")
    with open(flow_path, "w") as f:
        json.dump(consort, f, indent=2)
    print(f"Saved {flow_path}")

    # Write derivation log
    log_lines = [
        "# Data Derivation Log",
        f"\n**Generated:** {datetime.now().isoformat()}",
        f"\n## Exclusion Criteria Applied\n",
    ]
    for entry in flow_log:
        if entry["excluded"] > 0:
            log_lines.append(f"- {entry['reason']}: excluded {entry['excluded']} ({entry['n']} remaining)")
    log_lines.append(f"\n## Populations Defined\n")
    for name, pop_df in populations.items():
        log_lines.append(f"- **{name.upper()}**: {len(pop_df):,} participants")

    with open(os.path.join(args.output_dir, "derivation_log.md"), "w") as f:
        f.write("\n".join(log_lines))

    print("Done.")


if __name__ == "__main__":
    main()
