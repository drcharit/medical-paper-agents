#!/usr/bin/env python3
"""
Funnel Plot Generator for Meta-Analyses

Generates publication-quality funnel plots for assessing publication bias
in meta-analyses. Includes pseudo 95% CI triangle lines and Egger's test
P-value annotation.

Part of the medical-paper-agents skill for the Figure Engine (Agent 06).

Usage:
    python funnel-plot.py --input studies.csv --effect effect_size \
        --se standard_error --output funnel.png

Dependencies:
    numpy, pandas, matplotlib, scipy
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats


def egger_test(effect_sizes, standard_errors):
    """Perform Egger's regression test for funnel plot asymmetry.

    Regresses the standardised effect (effect / SE) on precision (1 / SE).
    The intercept test assesses asymmetry.
    """
    precision = 1.0 / standard_errors
    standardised_effect = effect_sizes / standard_errors

    slope, intercept, r_value, p_value, std_err = stats.linregress(precision, standardised_effect)

    # The P-value for the intercept is what we report
    n = len(effect_sizes)
    t_stat = intercept / std_err
    p_intercept = 2 * stats.t.sf(abs(t_stat), df=n - 2)

    return p_intercept, intercept


def plot_funnel(
    effect_sizes,
    standard_errors,
    study_labels=None,
    output_path="funnel.png",
    title="Funnel Plot",
    xlabel="Effect Size",
    ylabel="Standard Error",
    pooled_effect=None,
    egger_p=None,
    dpi=300,
    figwidth=7,
    figheight=6,
):
    """Generate the funnel plot with pseudo 95% CI lines."""
    fig, ax = plt.subplots(figsize=(figwidth, figheight))

    # Calculate pooled effect if not provided (inverse-variance weighted)
    if pooled_effect is None:
        weights = 1.0 / (standard_errors ** 2)
        pooled_effect = np.sum(weights * effect_sizes) / np.sum(weights)

    # Pseudo 95% CI triangle
    se_range = np.linspace(0, max(standard_errors) * 1.15, 200)
    ci_lower = pooled_effect - 1.96 * se_range
    ci_upper = pooled_effect + 1.96 * se_range

    ax.fill_betweenx(
        se_range, ci_lower, ci_upper,
        alpha=0.08, color="#CCCCCC", label="Pseudo 95% CI",
    )
    ax.plot(ci_lower, se_range, "--", color="#999999", linewidth=0.8)
    ax.plot(ci_upper, se_range, "--", color="#999999", linewidth=0.8)

    # Vertical line at pooled effect
    ax.axvline(x=pooled_effect, color="#333333", linewidth=1, linestyle="-", alpha=0.6)

    # Scatter points
    ax.scatter(
        effect_sizes, standard_errors,
        s=50, c="#0072B2", edgecolors="white", linewidths=0.5, zorder=5,
        label=f"Studies (n={len(effect_sizes)})",
    )

    # Optional study labels
    if study_labels is not None:
        for i, label in enumerate(study_labels):
            ax.annotate(
                label,
                (effect_sizes[i], standard_errors[i]),
                textcoords="offset points",
                xytext=(5, 3),
                fontsize=7,
                alpha=0.7,
            )

    # Invert y-axis (smaller SE = more precise = top)
    ax.invert_yaxis()

    # Annotation for Egger's test
    if egger_p is not None:
        if egger_p < 0.001:
            p_text = "Egger's test P<0.001"
        else:
            p_text = f"Egger's test P={egger_p:.3f}"
        ax.text(
            0.02, 0.02, p_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="bottom",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8),
        )

    # Formatting
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper right", fontsize=9, frameon=True, framealpha=0.9)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Funnel plot saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate publication-quality funnel plots for meta-analyses.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python funnel-plot.py --input studies.csv --effect log_or --se se_log_or --output funnel.png
    python funnel-plot.py --input meta_data.csv --effect smd --se se --output funnel.pdf \\
        --title "Publication Bias Assessment" --labels study_name
        """,
    )
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--effect", required=True, help="Column name for effect size (e.g., log OR, SMD)")
    parser.add_argument("--se", required=True, help="Column name for standard error")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--labels", default=None, help="Column name for study labels (optional)")
    parser.add_argument("--title", default="Funnel Plot", help="Plot title")
    parser.add_argument("--xlabel", default="Effect Size", help="X-axis label")
    parser.add_argument("--pooled", type=float, default=None, help="Pooled effect estimate (auto-calculated if omitted)")
    parser.add_argument("--dpi", type=int, default=300, help="Output resolution (default: 300)")
    parser.add_argument("--width", type=float, default=7.0, help="Figure width in inches")
    parser.add_argument("--height", type=float, default=6.0, help="Figure height in inches")

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)

    for col in [args.effect, args.se]:
        if col not in df.columns:
            print(f"Error: Column '{col}' not found. Available: {list(df.columns)}")
            sys.exit(1)

    df = df.dropna(subset=[args.effect, args.se])
    effect_sizes = df[args.effect].values.astype(float)
    standard_errors = df[args.se].values.astype(float)
    study_labels = df[args.labels].values if args.labels and args.labels in df.columns else None

    print(f"Loaded {len(effect_sizes)} studies")

    # Egger's test
    egger_p = None
    if len(effect_sizes) >= 10:
        egger_p, intercept = egger_test(effect_sizes, standard_errors)
        print(f"  Egger's test: intercept={intercept:.3f}, P={egger_p:.4f}")
    else:
        print(f"  Egger's test: skipped (n={len(effect_sizes)} < 10 studies recommended)")

    plot_funnel(
        effect_sizes=effect_sizes,
        standard_errors=standard_errors,
        study_labels=study_labels,
        output_path=args.output,
        title=args.title,
        xlabel=args.xlabel,
        pooled_effect=args.pooled,
        egger_p=egger_p,
        dpi=args.dpi,
        figwidth=args.width,
        figheight=args.height,
    )


if __name__ == "__main__":
    main()
