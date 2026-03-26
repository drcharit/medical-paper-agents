#!/usr/bin/env python3
"""Universal data ingestion and profiling for medical research datasets.

Reads raw data in multiple formats (CSV, Excel, SAS, Stata, SPSS, Parquet, TSV),
generates a data dictionary, data profile, and computes a SHA-256 hash of the input.

Usage:
    python data-ingest.py --input data.csv --output-dir ./data/
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd


SUPPORTED_FORMATS = {
    ".csv": "csv",
    ".tsv": "tsv",
    ".xlsx": "excel",
    ".xls": "excel",
    ".parquet": "parquet",
    ".sas7bdat": "sas",
    ".dta": "stata",
    ".sav": "spss",
}


def compute_file_hash(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def read_data(filepath: str) -> pd.DataFrame:
    """Read data file in any supported format."""
    ext = Path(filepath).suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {ext}. Supported: {list(SUPPORTED_FORMATS.keys())}")

    fmt = SUPPORTED_FORMATS[ext]
    if fmt == "csv":
        return pd.read_csv(filepath)
    elif fmt == "tsv":
        return pd.read_csv(filepath, sep="\t")
    elif fmt == "excel":
        return pd.read_excel(filepath)
    elif fmt == "parquet":
        return pd.read_parquet(filepath)
    elif fmt == "sas":
        return pd.read_sas(filepath)
    elif fmt == "stata":
        return pd.read_stata(filepath)
    elif fmt == "spss":
        try:
            import pyreadstat
            df, meta = pyreadstat.read_sav(filepath)
            return df
        except ImportError:
            raise ImportError("pyreadstat required for SPSS files: pip install pyreadstat")
    return pd.DataFrame()


def classify_dtype(series: pd.Series) -> str:
    """Classify a pandas series into a semantic type."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_bool_dtype(series):
        return "binary"
    if pd.api.types.is_numeric_dtype(series):
        n_unique = series.nunique()
        if n_unique <= 2:
            return "binary"
        elif n_unique <= 20:
            return "categorical"
        else:
            return "numeric"
    if pd.api.types.is_categorical_dtype(series) or pd.api.types.is_object_dtype(series):
        n_unique = series.nunique()
        if n_unique <= 2:
            return "binary"
        elif n_unique <= 50:
            return "categorical"
        else:
            return "text"
    return "unknown"


def generate_data_dictionary(df: pd.DataFrame) -> list:
    """Generate a data dictionary for the dataframe."""
    dictionary = []
    for col in df.columns:
        series = df[col]
        n_missing = int(series.isna().sum())
        n_total = len(series)
        entry = {
            "variable": col,
            "dtype": str(series.dtype),
            "semantic_type": classify_dtype(series),
            "n_total": n_total,
            "n_missing": n_missing,
            "pct_missing": round(100 * n_missing / n_total, 1) if n_total > 0 else 0,
            "n_unique": int(series.nunique()),
        }
        non_null = series.dropna()
        if len(non_null) > 0:
            if pd.api.types.is_numeric_dtype(series):
                entry["min"] = float(non_null.min())
                entry["max"] = float(non_null.max())
                entry["mean"] = round(float(non_null.mean()), 2)
                entry["median"] = round(float(non_null.median()), 2)
                entry["std"] = round(float(non_null.std()), 2)
            sample = non_null.head(5).tolist()
            entry["sample_values"] = [str(v) for v in sample]
        else:
            entry["sample_values"] = []
        dictionary.append(entry)
    return dictionary


def generate_profile(df: pd.DataFrame, filepath: str, file_hash: str) -> dict:
    """Generate a high-level data profile."""
    type_counts = {"numeric": 0, "categorical": 0, "binary": 0, "datetime": 0, "text": 0, "unknown": 0}
    for col in df.columns:
        t = classify_dtype(df[col])
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "file": os.path.basename(filepath),
        "sha256_hash": file_hash,
        "generated_at": datetime.now().isoformat(),
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1e6, 2),
        "column_types": type_counts,
        "total_missing_cells": int(df.isna().sum().sum()),
        "pct_missing_overall": round(100 * df.isna().sum().sum() / (len(df) * len(df.columns)), 1),
        "columns_with_no_missing": int((df.isna().sum() == 0).sum()),
        "columns_with_gt_20pct_missing": int((df.isna().mean() > 0.2).sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }


def write_profile_md(profile: dict, dictionary: list, output_dir: str):
    """Write data profile as markdown."""
    lines = [
        "# Data Profile Report",
        "",
        f"**File:** {profile['file']}",
        f"**SHA-256:** `{profile['sha256_hash']}`",
        f"**Generated:** {profile['generated_at']}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Rows | {profile['n_rows']:,} |",
        f"| Columns | {profile['n_columns']} |",
        f"| Memory | {profile['memory_usage_mb']} MB |",
        f"| Total missing cells | {profile['total_missing_cells']:,} ({profile['pct_missing_overall']}%) |",
        f"| Columns with no missing | {profile['columns_with_no_missing']} |",
        f"| Columns with >20% missing | {profile['columns_with_gt_20pct_missing']} |",
        f"| Duplicate rows | {profile['duplicate_rows']} |",
        "",
        "## Column Types",
        "",
        "| Type | Count |",
        "|---|---|",
    ]
    for t, c in profile["column_types"].items():
        if c > 0:
            lines.append(f"| {t} | {c} |")

    lines += [
        "",
        "## Variable Summary",
        "",
        "| Variable | Type | Semantic | Missing (%) | Unique | Min | Max | Mean |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for d in dictionary:
        min_val = d.get("min", "—")
        max_val = d.get("max", "—")
        mean_val = d.get("mean", "—")
        lines.append(
            f"| {d['variable']} | {d['dtype']} | {d['semantic_type']} | "
            f"{d['n_missing']} ({d['pct_missing']}%) | {d['n_unique']} | "
            f"{min_val} | {max_val} | {mean_val} |"
        )

    with open(os.path.join(output_dir, "data_profile.md"), "w") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Ingest and profile medical research data")
    parser.add_argument("--input", required=True, help="Path to raw data file")
    parser.add_argument("--output-dir", required=True, help="Output directory for profile and dictionary")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Computing file hash...")
    file_hash = compute_file_hash(args.input)

    print(f"Reading data from {args.input}...")
    df = read_data(args.input)
    print(f"Loaded {len(df):,} rows x {len(df.columns)} columns")

    print("Generating data dictionary...")
    dictionary = generate_data_dictionary(df)

    print("Generating data profile...")
    profile = generate_profile(df, args.input, file_hash)

    # Write outputs
    with open(os.path.join(args.output_dir, "data_dictionary.json"), "w") as f:
        json.dump(dictionary, f, indent=2, default=str)

    write_profile_md(profile, dictionary, args.output_dir)

    with open(os.path.join(args.output_dir, "raw_data_hash.txt"), "w") as f:
        f.write(f"{file_hash}  {os.path.basename(args.input)}\n")

    print(f"Outputs written to {args.output_dir}/")
    print(f"  - data_profile.md")
    print(f"  - data_dictionary.json")
    print(f"  - raw_data_hash.txt")


if __name__ == "__main__":
    main()
