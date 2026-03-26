#!/usr/bin/env python3
"""
Kaplan-Meier Survival Plot Generator

Generates publication-quality Kaplan-Meier survival curves with number-at-risk
tables, confidence interval bands, median survival lines, censoring ticks,
log-rank P-values, and Cox hazard ratios.

Part of the medical-paper-agents skill for the Figure Engine (Agent 06).

Usage:
    python km-plot.py --input data.csv --time time_col --event event_col \
        --group group_col --output km_plot.png

Dependencies:
    numpy, pandas, matplotlib, lifelines
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D

try:
    from lifelines import KaplanMeierFitter, CoxPHFitter
    from lifelines.statistics import logrank_test
except ImportError:
    print("Error: lifelines is required. Install with: pip install lifelines")
    sys.exit(1)


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


def load_data(input_path, time_col, event_col, group_col):
    """Load and validate the input CSV data."""
    df = pd.read_csv(input_path)

    for col in [time_col, event_col, group_col]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in data. Available: {list(df.columns)}")

    df = df.dropna(subset=[time_col, event_col, group_col])
    df[time_col] = pd.to_numeric(df[time_col], errors="coerce")
    df[event_col] = pd.to_numeric(df[event_col], errors="coerce").astype(int)
    df = df.dropna(subset=[time_col])

    if df[event_col].nunique() > 2:
        raise ValueError(f"Event column should be binary (0/1). Found {df[event_col].nunique()} unique values.")

    return df


def compute_km_estimates(df, time_col, event_col, group_col):
    """Fit Kaplan-Meier estimators per group."""
    groups = sorted(df[group_col].unique())
    kmf_dict = {}

    for group in groups:
        mask = df[group_col] == group
        kmf = KaplanMeierFitter()
        kmf.fit(
            durations=df.loc[mask, time_col],
            event_observed=df.loc[mask, event_col],
            label=str(group),
        )
        kmf_dict[group] = kmf

    return kmf_dict, groups


def compute_logrank(df, time_col, event_col, group_col, groups):
    """Compute log-rank test P-value between the first two groups."""
    if len(groups) < 2:
        return None

    g1 = df[df[group_col] == groups[0]]
    g2 = df[df[group_col] == groups[1]]

    result = logrank_test(
        g1[time_col], g2[time_col],
        event_observed_A=g1[event_col],
        event_observed_B=g2[event_col],
    )
    return result.p_value


def compute_cox_hr(df, time_col, event_col, group_col, groups):
    """Compute Cox proportional hazards ratio between groups."""
    if len(groups) < 2:
        return None, None, None

    df_cox = df[[time_col, event_col, group_col]].copy()
    df_cox[group_col] = (df_cox[group_col] == groups[1]).astype(int)

    try:
        cph = CoxPHFitter()
        cph.fit(df_cox, duration_col=time_col, event_col=event_col)
        hr = np.exp(cph.params_[group_col])
        ci = np.exp(cph.confidence_intervals_.values[0])
        return hr, ci[0], ci[1]
    except Exception as e:
        print(f"Warning: Cox model failed: {e}")
        return None, None, None


def get_number_at_risk(kmf, time_points):
    """Calculate the number at risk at specified time points."""
    n_at_risk = []
    event_table = kmf.event_table
    for t in time_points:
        mask = event_table.index <= t
        if mask.any():
            row = event_table.loc[mask].iloc[-1]
            n_at_risk.append(int(row["at_risk"] - row["observed"] - row["censored"]))
        else:
            n_at_risk.append(int(event_table.iloc[0]["at_risk"]))
    return n_at_risk


def plot_km(
    kmf_dict,
    groups,
    logrank_p,
    hr,
    hr_ci_lower,
    hr_ci_upper,
    output_path,
    title="Kaplan-Meier Survival Estimate",
    xlabel="Time",
    ylabel="Survival Probability",
    show_ci=True,
    show_censoring=True,
    show_median=True,
    show_at_risk=True,
    n_risk_ticks=6,
    dpi=300,
    figwidth=8,
    figheight=6,
):
    """Generate the Kaplan-Meier plot with all annotations."""
    # Determine time range
    max_time = max(kmf.timeline.max() for kmf in kmf_dict.values())
    time_points = np.linspace(0, max_time, n_risk_ticks).astype(int)

    # Figure setup
    if show_at_risk:
        fig, (ax_main, ax_risk) = plt.subplots(
            2, 1,
            figsize=(figwidth, figheight),
            gridspec_kw={"height_ratios": [4, 1], "hspace": 0.08},
            sharex=True,
        )
    else:
        fig, ax_main = plt.subplots(figsize=(figwidth, figheight))
        ax_risk = None

    # Plot each group
    for i, group in enumerate(groups):
        kmf = kmf_dict[group]
        color = OKABE_ITO[i % len(OKABE_ITO)]

        # Main survival curve
        ax_main.step(
            kmf.timeline,
            kmf.survival_function_.values.flatten(),
            where="post",
            color=color,
            linewidth=2,
            label=str(group),
        )

        # Confidence interval bands
        if show_ci:
            ci = kmf.confidence_interval_survival_function_
            ax_main.fill_between(
                kmf.timeline,
                ci.iloc[:, 0].values,
                ci.iloc[:, 1].values,
                step="post",
                alpha=0.15,
                color=color,
            )

        # Censoring ticks
        if show_censoring:
            event_table = kmf.event_table
            censored_times = event_table[event_table["censored"] > 0].index
            for t in censored_times:
                surv_at_t = kmf.predict(t)
                ax_main.plot(t, surv_at_t, "|", color=color, markersize=8, markeredgewidth=1.5)

        # Median survival line
        if show_median:
            median = kmf.median_survival_time_
            if np.isfinite(median):
                surv_at_median = 0.5
                ax_main.plot(
                    [0, median], [surv_at_median, surv_at_median],
                    "--", color=color, linewidth=0.8, alpha=0.5,
                )
                ax_main.plot(
                    [median, median], [0, surv_at_median],
                    "--", color=color, linewidth=0.8, alpha=0.5,
                )

    # Axis formatting
    ax_main.set_ylabel(ylabel, fontsize=12)
    ax_main.set_ylim(0, 1.05)
    ax_main.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1.0))
    ax_main.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax_main.spines["top"].set_visible(False)
    ax_main.spines["right"].set_visible(False)
    ax_main.grid(axis="y", alpha=0.3, linestyle="--")

    # Annotation: log-rank P and HR
    annotation_parts = []
    if logrank_p is not None:
        if logrank_p < 0.0001:
            annotation_parts.append("Log-rank P<0.0001")
        else:
            annotation_parts.append(f"Log-rank P={logrank_p:.4f}")

    if hr is not None:
        annotation_parts.append(f"HR {hr:.2f} (95% CI {hr_ci_lower:.2f}-{hr_ci_upper:.2f})")

    if annotation_parts:
        annotation_text = "\n".join(annotation_parts)
        ax_main.text(
            0.98, 0.02, annotation_text,
            transform=ax_main.transAxes,
            fontsize=10,
            verticalalignment="bottom",
            horizontalalignment="right",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8),
        )

    ax_main.legend(loc="lower left", fontsize=10, frameon=True, framealpha=0.9)

    # Number at risk table
    if show_at_risk and ax_risk is not None:
        ax_risk.set_xlim(ax_main.get_xlim())
        ax_risk.set_ylim(-0.5, len(groups) - 0.5)
        ax_risk.set_xlabel(xlabel, fontsize=12)
        ax_risk.set_yticks(range(len(groups)))
        ax_risk.set_yticklabels([str(g) for g in groups], fontsize=10)
        ax_risk.tick_params(axis="x", labelsize=10)
        ax_risk.spines["top"].set_visible(False)
        ax_risk.spines["right"].set_visible(False)
        ax_risk.spines["left"].set_visible(False)
        ax_risk.set_title("Number at risk", fontsize=10, loc="left", fontweight="bold")

        for i, group in enumerate(groups):
            kmf = kmf_dict[group]
            n_at_risk = get_number_at_risk(kmf, time_points)
            for j, (t, n) in enumerate(zip(time_points, n_at_risk)):
                ax_risk.text(
                    t, i, str(n),
                    ha="center", va="center",
                    fontsize=9,
                    color=OKABE_ITO[i % len(OKABE_ITO)],
                )

        ax_risk.set_xticks(time_points)
    else:
        ax_main.set_xlabel(xlabel, fontsize=12)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Kaplan-Meier plot saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate publication-quality Kaplan-Meier survival plots.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python km-plot.py --input trial_data.csv --time follow_up --event death --group arm --output km.png
    python km-plot.py --input data.csv --time months --event event --group treatment \\
        --output km.pdf --title "Overall Survival" --no-ci --dpi 600
        """,
    )
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--time", required=True, help="Column name for time-to-event")
    parser.add_argument("--event", required=True, help="Column name for event indicator (0/1)")
    parser.add_argument("--group", required=True, help="Column name for group variable")
    parser.add_argument("--output", required=True, help="Output file path (PNG, PDF, SVG, TIFF)")
    parser.add_argument("--title", default="Kaplan-Meier Survival Estimate", help="Plot title")
    parser.add_argument("--xlabel", default="Time", help="X-axis label")
    parser.add_argument("--ylabel", default="Survival Probability", help="Y-axis label")
    parser.add_argument("--no-ci", action="store_true", help="Hide confidence interval bands")
    parser.add_argument("--no-censoring", action="store_true", help="Hide censoring tick marks")
    parser.add_argument("--no-median", action="store_true", help="Hide median survival lines")
    parser.add_argument("--no-at-risk", action="store_true", help="Hide number-at-risk table")
    parser.add_argument("--n-risk-ticks", type=int, default=6, help="Number of at-risk time points")
    parser.add_argument("--dpi", type=int, default=300, help="Output resolution (default: 300)")
    parser.add_argument("--width", type=float, default=8.0, help="Figure width in inches")
    parser.add_argument("--height", type=float, default=6.0, help="Figure height in inches")

    args = parser.parse_args()

    # Validate input
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    # Load data
    df = load_data(args.input, args.time, args.event, args.group)
    print(f"Loaded {len(df)} observations with {df[args.group].nunique()} groups")

    # Compute KM estimates
    kmf_dict, groups = compute_km_estimates(df, args.time, args.event, args.group)

    # Compute statistics
    logrank_p = compute_logrank(df, args.time, args.event, args.group, groups)
    hr, hr_ci_lower, hr_ci_upper = compute_cox_hr(df, args.time, args.event, args.group, groups)

    # Print summary
    for group in groups:
        kmf = kmf_dict[group]
        median = kmf.median_survival_time_
        n = kmf.event_table.iloc[0]["at_risk"]
        events = int(kmf.event_table["observed"].sum())
        print(f"  {group}: N={int(n)}, events={events}, median={median:.1f}")

    if logrank_p is not None:
        print(f"  Log-rank P={logrank_p:.6f}")
    if hr is not None:
        print(f"  HR={hr:.3f} (95% CI {hr_ci_lower:.3f}-{hr_ci_upper:.3f})")

    # Generate plot
    plot_km(
        kmf_dict=kmf_dict,
        groups=groups,
        logrank_p=logrank_p,
        hr=hr,
        hr_ci_lower=hr_ci_lower,
        hr_ci_upper=hr_ci_upper,
        output_path=args.output,
        title=args.title,
        xlabel=args.xlabel,
        ylabel=args.ylabel,
        show_ci=not args.no_ci,
        show_censoring=not args.no_censoring,
        show_median=not args.no_median,
        show_at_risk=not args.no_at_risk,
        n_risk_ticks=args.n_risk_ticks,
        dpi=args.dpi,
        figwidth=args.width,
        figheight=args.height,
    )


if __name__ == "__main__":
    main()
