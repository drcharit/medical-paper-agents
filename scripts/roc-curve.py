#!/usr/bin/env python3
"""
ROC Curve Generator

Generates publication-quality ROC curves with AUC and 95% CI (bootstrapped),
optimal threshold via Youden's J statistic, sensitivity/specificity annotations,
and support for multiple model comparison overlays.

Part of the medical-paper-agents skill for the Figure Engine (Agent 06).

Usage:
    python roc-curve.py --input data.csv --outcome outcome_col \
        --predictors "model1 model2" --output roc.png

Dependencies:
    numpy, pandas, matplotlib, scikit-learn
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, roc_auc_score


# Okabe-Ito colorblind-safe palette
OKABE_ITO = [
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#009E73",  # bluish green
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#CC79A7",  # reddish purple
    "#F0E442",  # yellow
    "#000000",  # black
]


def bootstrap_auc(y_true, y_score, n_bootstraps=2000, seed=42):
    """Compute AUC with 95% CI via bootstrapping (DeLong-approximation)."""
    rng = np.random.RandomState(seed)
    aucs = []

    for _ in range(n_bootstraps):
        indices = rng.randint(0, len(y_true), len(y_true))
        if len(np.unique(y_true[indices])) < 2:
            continue
        try:
            aucs.append(roc_auc_score(y_true[indices], y_score[indices]))
        except ValueError:
            continue

    aucs = np.array(aucs)
    if len(aucs) == 0:
        return np.nan, np.nan, np.nan

    auc_mean = np.mean(aucs)
    ci_lower = np.percentile(aucs, 2.5)
    ci_upper = np.percentile(aucs, 97.5)
    return auc_mean, ci_lower, ci_upper


def find_optimal_threshold(y_true, y_score):
    """Find optimal threshold using Youden's J statistic (sensitivity + specificity - 1)."""
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    j_statistic = tpr - fpr
    optimal_idx = np.argmax(j_statistic)
    optimal_threshold = thresholds[optimal_idx]
    optimal_sensitivity = tpr[optimal_idx]
    optimal_specificity = 1 - fpr[optimal_idx]
    return optimal_threshold, optimal_sensitivity, optimal_specificity, optimal_idx


def plot_roc(
    y_true,
    predictor_scores,
    predictor_names,
    output_path,
    title="Receiver Operating Characteristic",
    dpi=300,
    figwidth=7,
    figheight=7,
    show_optimal=True,
    n_bootstraps=2000,
):
    """Generate the ROC curve plot with AUC, CI, and optimal threshold."""
    fig, ax = plt.subplots(figsize=(figwidth, figheight))

    # Diagonal reference line
    ax.plot([0, 1], [0, 1], linestyle="--", color="#999999", linewidth=1, label="Reference (AUC=0.50)")

    legend_entries = []

    for i, (scores, name) in enumerate(zip(predictor_scores, predictor_names)):
        color = OKABE_ITO[i % len(OKABE_ITO)]

        # Compute ROC curve
        fpr, tpr, thresholds = roc_curve(y_true, scores)

        # Compute AUC with bootstrap CI
        auc_val, ci_lower, ci_upper = bootstrap_auc(
            y_true, scores, n_bootstraps=n_bootstraps
        )

        # Plot ROC curve
        label = f"{name}: AUC={auc_val:.3f} (95% CI {ci_lower:.3f}-{ci_upper:.3f})"
        ax.plot(fpr, tpr, color=color, linewidth=2, label=label)

        # Mark optimal threshold
        if show_optimal:
            opt_thresh, opt_sens, opt_spec, opt_idx = find_optimal_threshold(y_true, scores)
            ax.plot(
                fpr[opt_idx], tpr[opt_idx],
                "o", color=color, markersize=8, markeredgecolor="white", markeredgewidth=1.5,
                zorder=5,
            )
            # Annotate optimal point
            offset_x = 0.03 if fpr[opt_idx] < 0.7 else -0.15
            offset_y = -0.04 if tpr[opt_idx] > 0.3 else 0.04
            ax.annotate(
                f"Sens={opt_sens:.2f}\nSpec={opt_spec:.2f}\nThreshold={opt_thresh:.3f}",
                xy=(fpr[opt_idx], tpr[opt_idx]),
                xytext=(fpr[opt_idx] + offset_x, tpr[opt_idx] + offset_y),
                fontsize=8,
                color=color,
                arrowprops=dict(arrowstyle="->", color=color, lw=0.8),
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=color, alpha=0.8),
            )

        print(f"  {name}: AUC={auc_val:.4f} (95% CI {ci_lower:.4f}-{ci_upper:.4f})")
        if show_optimal:
            print(f"    Optimal threshold={opt_thresh:.4f}, Sensitivity={opt_sens:.4f}, Specificity={opt_spec:.4f}")

    # Formatting
    ax.set_xlabel("1 - Specificity (False Positive Rate)", fontsize=12)
    ax.set_ylabel("Sensitivity (True Positive Rate)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect("equal")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(alpha=0.2, linestyle="--")
    ax.legend(loc="lower right", fontsize=9, frameon=True, framealpha=0.9)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"ROC curve saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate publication-quality ROC curves with AUC and 95% CI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python roc-curve.py --input data.csv --outcome death --predictors "risk_score" --output roc.png
    python roc-curve.py --input data.csv --outcome outcome --predictors "model_a model_b model_c" \\
        --output roc.pdf --title "Model Comparison" --dpi 600
        """,
    )
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--outcome", required=True, help="Binary outcome column (0/1)")
    parser.add_argument("--predictors", required=True, help="Space-separated predictor column names (quoted)")
    parser.add_argument("--output", required=True, help="Output file path (PNG, PDF, SVG, TIFF)")
    parser.add_argument("--title", default="Receiver Operating Characteristic", help="Plot title")
    parser.add_argument("--no-optimal", action="store_true", help="Hide optimal threshold markers")
    parser.add_argument("--n-bootstraps", type=int, default=2000, help="Bootstrap iterations for CI (default: 2000)")
    parser.add_argument("--dpi", type=int, default=300, help="Output resolution (default: 300)")
    parser.add_argument("--width", type=float, default=7.0, help="Figure width in inches")
    parser.add_argument("--height", type=float, default=7.0, help="Figure height in inches")

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    # Load data
    df = pd.read_csv(args.input)
    predictor_names = args.predictors.split()

    # Validate columns
    if args.outcome not in df.columns:
        print(f"Error: Outcome column '{args.outcome}' not found. Available: {list(df.columns)}")
        sys.exit(1)

    for pred in predictor_names:
        if pred not in df.columns:
            print(f"Error: Predictor column '{pred}' not found. Available: {list(df.columns)}")
            sys.exit(1)

    # Prepare data
    y_true = df[args.outcome].values.astype(int)
    predictor_scores = [df[pred].values.astype(float) for pred in predictor_names]

    # Drop rows with NaN in any relevant column
    valid_mask = ~np.isnan(y_true.astype(float))
    for scores in predictor_scores:
        valid_mask &= ~np.isnan(scores)

    y_true = y_true[valid_mask]
    predictor_scores = [scores[valid_mask] for scores in predictor_scores]

    print(f"Loaded {len(y_true)} valid observations, {int(y_true.sum())} events")

    # Generate plot
    plot_roc(
        y_true=y_true,
        predictor_scores=predictor_scores,
        predictor_names=predictor_names,
        output_path=args.output,
        title=args.title,
        dpi=args.dpi,
        figwidth=args.width,
        figheight=args.height,
        show_optimal=not args.no_optimal,
        n_bootstraps=args.n_bootstraps,
    )


if __name__ == "__main__":
    main()
