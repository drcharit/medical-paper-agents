#!/usr/bin/env python3
"""
Patient Timeline Swimmer Plot Generator

Generates publication-quality swimmer plots showing individual patient
treatment timelines with event markers (response, progression, death,
dose reduction). Commonly used in oncology and clinical trial reporting.

Part of the medical-paper-agents skill for the Figure Engine (Agent 06).

Usage:
    python swimmer-plot.py --input timelines.csv --patient_id id \
        --start start --end end --events events.csv --output swimmer.png

Dependencies:
    numpy, pandas, matplotlib
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


# Colorblind-safe colors for treatment bars
BAR_COLORS = {
    "treatment": "#0072B2",
    "off_treatment": "#CCCCCC",
    "responder": "#009E73",
    "non_responder": "#D55E00",
}

# Event marker styles
EVENT_MARKERS = {
    "response": {"marker": "^", "color": "#009E73", "size": 80, "label": "Response"},
    "progression": {"marker": "v", "color": "#D55E00", "size": 80, "label": "Progression"},
    "death": {"marker": "X", "color": "#000000", "size": 80, "label": "Death"},
    "dose_reduction": {"marker": "D", "color": "#E69F00", "size": 60, "label": "Dose Reduction"},
    "adverse_event": {"marker": "s", "color": "#CC79A7", "size": 60, "label": "Adverse Event"},
    "ongoing": {"marker": ">", "color": "#56B4E9", "size": 80, "label": "Ongoing"},
    "censored": {"marker": "|", "color": "#333333", "size": 80, "label": "Censored"},
}


def plot_swimmer(
    timelines_df,
    patient_col,
    start_col,
    end_col,
    events_df=None,
    response_col=None,
    sort_by="duration",
    output_path="swimmer.png",
    title="Swimmer Plot",
    xlabel="Time (months)",
    dpi=300,
    figwidth=10,
    figheight=None,
):
    """Generate a swimmer plot with patient timelines and event markers."""
    df = timelines_df.copy()

    # Calculate duration
    df["_duration"] = df[end_col] - df[start_col]

    # Sort patients
    if sort_by == "duration":
        df = df.sort_values("_duration", ascending=True).reset_index(drop=True)
    elif sort_by == "response" and response_col and response_col in df.columns:
        df = df.sort_values([response_col, "_duration"], ascending=[False, True]).reset_index(drop=True)
    else:
        df = df.sort_values("_duration", ascending=True).reset_index(drop=True)

    n_patients = len(df)
    if figheight is None:
        figheight = max(4, n_patients * 0.35)

    fig, ax = plt.subplots(figsize=(figwidth, figheight))

    # Create patient ID to y-position mapping
    patient_order = {pid: i for i, pid in enumerate(df[patient_col])}

    # Draw horizontal bars for each patient
    for i, row in df.iterrows():
        y = i
        duration = row["_duration"]
        start = row[start_col]

        # Color based on response status if available
        if response_col and response_col in df.columns:
            bar_color = BAR_COLORS["responder"] if row[response_col] else BAR_COLORS["non_responder"]
        else:
            bar_color = BAR_COLORS["treatment"]

        ax.barh(
            y, duration, left=start, height=0.6,
            color=bar_color, edgecolor="white", linewidth=0.5, zorder=2,
        )

    # Overlay event markers
    event_types_seen = set()
    if events_df is not None:
        for _, event_row in events_df.iterrows():
            pid = event_row.get("patient_id", event_row.get(patient_col))
            if pid not in patient_order:
                continue

            y = patient_order[pid]
            event_time = event_row.get("time", event_row.get("event_time"))
            event_type = str(event_row.get("event_type", "response")).lower().strip()

            if event_type not in EVENT_MARKERS:
                continue

            style = EVENT_MARKERS[event_type]
            ax.scatter(
                event_time, y,
                marker=style["marker"],
                c=style["color"],
                s=style["size"],
                edgecolors="white",
                linewidths=0.5,
                zorder=3,
            )
            event_types_seen.add(event_type)

    # Formatting
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel("Patient", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_yticks(range(n_patients))
    ax.set_yticklabels(df[patient_col].values, fontsize=8)
    ax.set_ylim(-0.5, n_patients - 0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.2, linestyle="--")

    # Build legend
    legend_elements = []

    if response_col and response_col in df.columns:
        legend_elements.append(Line2D([0], [0], color=BAR_COLORS["responder"], lw=6, label="Responder"))
        legend_elements.append(Line2D([0], [0], color=BAR_COLORS["non_responder"], lw=6, label="Non-responder"))
    else:
        legend_elements.append(Line2D([0], [0], color=BAR_COLORS["treatment"], lw=6, label="On Treatment"))

    for event_type in EVENT_MARKERS:
        if event_type in event_types_seen:
            style = EVENT_MARKERS[event_type]
            legend_elements.append(
                Line2D([0], [0], marker=style["marker"], color="w",
                       markerfacecolor=style["color"], markersize=8, label=style["label"])
            )

    ax.legend(
        handles=legend_elements, loc="lower right",
        fontsize=9, frameon=True, framealpha=0.9,
    )

    # Summary
    max_time = df["_duration"].max()
    median_time = df["_duration"].median()
    summary = f"N={n_patients}  Median: {median_time:.1f}  Max: {max_time:.1f}"
    ax.text(
        0.98, 0.98, summary,
        transform=ax.transAxes, fontsize=9,
        ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.8),
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Swimmer plot saved to: {output_path}")
    print(f"  N={n_patients}, Median duration={median_time:.1f}, Max={max_time:.1f}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate patient timeline swimmer plots.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python swimmer-plot.py --input timelines.csv --patient_id id --start 0 --end duration \\
        --output swimmer.png
    python swimmer-plot.py --input timelines.csv --patient_id patient --start start \\
        --end end --events events.csv --response is_responder --sort response \\
        --output swimmer.pdf --title "Treatment Duration"

Input CSV format (timelines):
    patient_id, start, end, is_responder
    PT001, 0, 12.5, 1
    PT002, 0, 8.3, 0

Events CSV format (optional):
    patient_id, event_time, event_type
    PT001, 6.0, response
    PT001, 12.5, progression
    PT002, 8.3, death
        """,
    )
    parser.add_argument("--input", required=True, help="Path to timelines CSV file")
    parser.add_argument("--patient_id", required=True, help="Column name for patient identifier")
    parser.add_argument("--start", required=True, help="Column name for start time (or use literal '0')")
    parser.add_argument("--end", required=True, help="Column name for end time / duration")
    parser.add_argument("--events", default=None, help="Path to events CSV file (optional)")
    parser.add_argument("--response", default=None, help="Column name for response status (binary, for coloring)")
    parser.add_argument("--sort", default="duration", choices=["duration", "response"], help="Sort order")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--title", default="Swimmer Plot", help="Plot title")
    parser.add_argument("--xlabel", default="Time (months)", help="X-axis label")
    parser.add_argument("--dpi", type=int, default=300, help="Output resolution (default: 300)")
    parser.add_argument("--width", type=float, default=10.0, help="Figure width in inches")
    parser.add_argument("--height", type=float, default=None, help="Figure height in inches (auto if omitted)")

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)

    # Handle start column: if '0', create a zero column
    if args.start == "0":
        df["_start"] = 0
        start_col = "_start"
    else:
        start_col = args.start

    for col in [args.patient_id, start_col, args.end]:
        if col not in df.columns:
            print(f"Error: Column '{col}' not found. Available: {list(df.columns)}")
            sys.exit(1)

    # Load events if provided
    events_df = None
    if args.events:
        if not Path(args.events).exists():
            print(f"Warning: Events file not found: {args.events}. Proceeding without events.")
        else:
            events_df = pd.read_csv(args.events)
            print(f"Loaded {len(events_df)} events from {args.events}")

    print(f"Loaded {len(df)} patient timelines")

    plot_swimmer(
        timelines_df=df,
        patient_col=args.patient_id,
        start_col=start_col,
        end_col=args.end,
        events_df=events_df,
        response_col=args.response,
        sort_by=args.sort,
        output_path=args.output,
        title=args.title,
        xlabel=args.xlabel,
        dpi=args.dpi,
        figwidth=args.width,
        figheight=args.height,
    )


if __name__ == "__main__":
    main()
