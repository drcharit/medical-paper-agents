#!/usr/bin/env python3
"""
Treatment Response Waterfall Plot Generator

Generates publication-quality waterfall plots showing per-patient percentage
change from baseline, color-coded by response category (CR, PR, SD, PD).
Common in oncology clinical trials.

Part of the medical-paper-agents skill for the Figure Engine (Agent 06).

Usage:
    python waterfall-plot.py --input responses.csv --change pct_change \
        --output waterfall.png

Dependencies:
    numpy, pandas, matplotlib
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# RECIST response category colors (colorblind-safe)
RESPONSE_COLORS = {
    "CR": "#009E73",   # bluish green — complete response
    "PR": "#56B4E9",   # sky blue — partial response
    "SD": "#E69F00",   # orange — stable disease
    "PD": "#D55E00",   # vermillion — progressive disease
    "NE": "#999999",   # gray — not evaluable
}

RESPONSE_ORDER = ["CR", "PR", "SD", "PD", "NE"]


def classify_response(pct_change):
    """Classify response category based on RECIST-like criteria."""
    if pct_change <= -100:
        return "CR"
    elif pct_change <= -30:
        return "PR"
    elif pct_change < 20:
        return "SD"
    else:
        return "PD"


def plot_waterfall(
    pct_changes,
    categories=None,
    patient_ids=None,
    output_path="waterfall.png",
    title="Treatment Response (Waterfall Plot)",
    ylabel="Change from Baseline (%)",
    pr_threshold=-30,
    pd_threshold=20,
    dpi=300,
    figwidth=10,
    figheight=5,
):
    """Generate a sorted waterfall plot of treatment responses."""
    n_patients = len(pct_changes)

    # Sort by response (best to worst)
    sort_idx = np.argsort(pct_changes)
    pct_sorted = pct_changes[sort_idx]

    if categories is not None:
        cat_sorted = categories[sort_idx]
    else:
        cat_sorted = np.array([classify_response(v) for v in pct_sorted])

    # Map categories to colors
    colors = [RESPONSE_COLORS.get(c, "#999999") for c in cat_sorted]

    fig, ax = plt.subplots(figsize=(figwidth, figheight))

    # Bar plot
    x_positions = np.arange(n_patients)
    bars = ax.bar(x_positions, pct_sorted, width=0.8, color=colors, edgecolor="white", linewidth=0.3)

    # Reference lines
    ax.axhline(y=pr_threshold, color="#0072B2", linewidth=1.2, linestyle="--", alpha=0.7,
               label=f"Partial Response ({pr_threshold}%)")
    ax.axhline(y=pd_threshold, color="#D55E00", linewidth=1.2, linestyle="--", alpha=0.7,
               label=f"Progressive Disease (+{pd_threshold}%)")
    ax.axhline(y=0, color="#333333", linewidth=0.8, alpha=0.5)

    # Formatting
    ax.set_xlabel("Patients", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlim(-0.5, n_patients - 0.5)
    ax.set_xticks([])  # Hide individual patient labels
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    # Legend for response categories
    from matplotlib.patches import Patch
    legend_patches = []
    for cat in RESPONSE_ORDER:
        count = np.sum(cat_sorted == cat)
        if count > 0:
            legend_patches.append(
                Patch(facecolor=RESPONSE_COLORS[cat], label=f"{cat} (n={count})")
            )
    legend_patches.append(plt.Line2D([0], [0], color="#0072B2", linestyle="--", label=f"PR threshold ({pr_threshold}%)"))
    legend_patches.append(plt.Line2D([0], [0], color="#D55E00", linestyle="--", label=f"PD threshold (+{pd_threshold}%)"))

    ax.legend(handles=legend_patches, loc="upper left", fontsize=9, frameon=True, framealpha=0.9)

    # Summary annotation
    n_cr = np.sum(cat_sorted == "CR")
    n_pr = np.sum(cat_sorted == "PR")
    n_sd = np.sum(cat_sorted == "SD")
    n_pd = np.sum(cat_sorted == "PD")
    orr = n_cr + n_pr
    dcr = n_cr + n_pr + n_sd

    summary = f"ORR: {orr}/{n_patients} ({100*orr/n_patients:.0f}%)    DCR: {dcr}/{n_patients} ({100*dcr/n_patients:.0f}%)"
    ax.text(
        0.98, 0.02, summary,
        transform=ax.transAxes,
        fontsize=10,
        ha="right", va="bottom",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8),
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Waterfall plot saved to: {output_path}")
    print(f"  N={n_patients}: CR={n_cr}, PR={n_pr}, SD={n_sd}, PD={n_pd}")
    print(f"  ORR={100*orr/n_patients:.1f}%, DCR={100*dcr/n_patients:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Generate treatment response waterfall plots.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python waterfall-plot.py --input responses.csv --change pct_change --output waterfall.png
    python waterfall-plot.py --input data.csv --change best_response_pct \\
        --category response_cat --output waterfall.pdf --dpi 600
        """,
    )
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--change", required=True, help="Column name for percent change from baseline")
    parser.add_argument("--category", default=None, help="Column for response category (CR/PR/SD/PD). Auto-classified if omitted.")
    parser.add_argument("--patient-id", default=None, help="Column for patient identifiers (optional)")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--title", default="Treatment Response (Waterfall Plot)", help="Plot title")
    parser.add_argument("--pr-threshold", type=float, default=-30, help="Partial response threshold (default: -30)")
    parser.add_argument("--pd-threshold", type=float, default=20, help="Progressive disease threshold (default: +20)")
    parser.add_argument("--dpi", type=int, default=300, help="Output resolution (default: 300)")
    parser.add_argument("--width", type=float, default=10.0, help="Figure width in inches")
    parser.add_argument("--height", type=float, default=5.0, help="Figure height in inches")

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)

    if args.change not in df.columns:
        print(f"Error: Column '{args.change}' not found. Available: {list(df.columns)}")
        sys.exit(1)

    df = df.dropna(subset=[args.change])
    pct_changes = df[args.change].values.astype(float)
    categories = df[args.category].values if args.category and args.category in df.columns else None
    patient_ids = df[args.patient_id].values if args.patient_id and args.patient_id in df.columns else None

    print(f"Loaded {len(pct_changes)} patient responses")

    plot_waterfall(
        pct_changes=pct_changes,
        categories=categories,
        patient_ids=patient_ids,
        output_path=args.output,
        title=args.title,
        pr_threshold=args.pr_threshold,
        pd_threshold=args.pd_threshold,
        dpi=args.dpi,
        figwidth=args.width,
        figheight=args.height,
    )


if __name__ == "__main__":
    main()
