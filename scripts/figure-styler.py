#!/usr/bin/env python3
"""
Journal Figure Style Applicator

Applies journal-specific styling to matplotlib figures or existing image files.
Loads YAML style profiles and enforces: decimal format (midline dot for Lancet),
font sizes, axis labels, P-value formatting, colorblind-safe palettes, and
correct DPI/dimensions for target journal.

Can be used as CLI tool or imported as a module.

Part of the medical-paper-agents skill for the Figure Engine (Agent 06).

CLI Usage:
    python figure-styler.py --input figure.png --journal lancet --output styled.png

Module Usage:
    from figure_styler import apply_journal_style, get_journal_config
    fig, ax = plt.subplots()
    # ... plot ...
    apply_journal_style(fig, ax, journal="lancet")
    fig.savefig("output.png")

Dependencies:
    numpy, matplotlib, pyyaml, Pillow
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

try:
    import yaml
except ImportError:
    print("Error: pyyaml is required. Install with: pip install pyyaml")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    Image = None


# --------------------------------------------------------------------------
# Okabe-Ito colorblind-safe palette
# --------------------------------------------------------------------------
OKABE_ITO = [
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
    "#000000",  # black
]

# --------------------------------------------------------------------------
# Default style profiles (used if YAML not found)
# --------------------------------------------------------------------------
DEFAULT_STYLES = {
    "lancet": {
        "journal_name": "The Lancet",
        "font_family": "Arial",
        "font_size_min": 8,
        "font_size_axis_label": 11,
        "font_size_title": 13,
        "font_size_tick": 9,
        "font_size_legend": 9,
        "decimal_point": "midline",
        "p_value_leading_zero": True,
        "p_value_case": "lowercase",
        "p_value_italic": False,
        "p_threshold_format": "p<0.0001",
        "dpi": 300,
        "single_column_mm": 89,
        "double_column_mm": 183,
        "max_height_mm": 247,
        "file_formats": ["tiff", "eps", "pdf"],
        "colorblind_palette": OKABE_ITO,
    },
    "nejm": {
        "journal_name": "NEJM",
        "font_family": "Arial",
        "font_size_min": 8,
        "font_size_axis_label": 11,
        "font_size_title": 13,
        "font_size_tick": 9,
        "font_size_legend": 9,
        "decimal_point": "period",
        "p_value_leading_zero": True,
        "p_value_case": "uppercase",
        "p_value_italic": False,
        "p_threshold_format": "P<0.001",
        "dpi": 300,
        "single_column_mm": 86,
        "double_column_mm": 178,
        "max_height_mm": 235,
        "file_formats": ["tiff", "eps", "pdf"],
        "colorblind_palette": OKABE_ITO,
    },
    "jama": {
        "journal_name": "JAMA",
        "font_family": "Arial",
        "font_size_min": 8,
        "font_size_axis_label": 10,
        "font_size_title": 12,
        "font_size_tick": 8,
        "font_size_legend": 8,
        "decimal_point": "period",
        "p_value_leading_zero": False,
        "p_value_case": "uppercase",
        "p_value_italic": False,
        "p_threshold_format": "P<.001",
        "dpi": 300,
        "single_column_mm": 86,
        "double_column_mm": 178,
        "max_height_mm": 235,
        "file_formats": ["tiff", "eps", "pdf"],
        "colorblind_palette": OKABE_ITO,
    },
    "bmj": {
        "journal_name": "BMJ",
        "font_family": "Arial",
        "font_size_min": 8,
        "font_size_axis_label": 11,
        "font_size_title": 13,
        "font_size_tick": 9,
        "font_size_legend": 9,
        "decimal_point": "period",
        "p_value_leading_zero": True,
        "p_value_case": "lowercase",
        "p_value_italic": False,
        "p_threshold_format": "p<0.001",
        "dpi": 300,
        "single_column_mm": 84,
        "double_column_mm": 174,
        "max_height_mm": 240,
        "file_formats": ["tiff", "eps", "pdf"],
        "colorblind_palette": OKABE_ITO,
    },
    "circulation": {
        "journal_name": "Circulation",
        "font_family": "Arial",
        "font_size_min": 8,
        "font_size_axis_label": 10,
        "font_size_title": 12,
        "font_size_tick": 9,
        "font_size_legend": 9,
        "decimal_point": "period",
        "p_value_leading_zero": True,
        "p_value_case": "uppercase",
        "p_value_italic": False,
        "p_threshold_format": "P<0.001",
        "dpi": 300,
        "single_column_mm": 86,
        "double_column_mm": 178,
        "max_height_mm": 235,
        "file_formats": ["tiff", "eps", "pdf"],
        "colorblind_palette": OKABE_ITO,
    },
}


def get_journal_config(journal: str, styles_dir: Optional[str] = None) -> Dict[str, Any]:
    """Load journal style configuration from YAML file or defaults.

    Args:
        journal: Journal name (lancet, nejm, jama, bmj, circulation)
        styles_dir: Directory containing YAML style files

    Returns:
        Dictionary with style configuration
    """
    journal_key = journal.lower().strip()

    # Try to load from YAML
    if styles_dir:
        yaml_path = Path(styles_dir) / f"{journal_key}.yaml"
        if yaml_path.exists():
            with open(yaml_path, "r") as f:
                yaml_config = yaml.safe_load(f)
            # Merge with defaults
            config = DEFAULT_STYLES.get(journal_key, DEFAULT_STYLES["lancet"]).copy()
            if yaml_config:
                # Map YAML fields to our internal format
                fmt = yaml_config.get("formatting", {})
                config["decimal_point"] = fmt.get("decimal_point", config["decimal_point"])
                config["p_value_leading_zero"] = fmt.get("p_value_leading_zero", config["p_value_leading_zero"])
                config["p_value_case"] = fmt.get("p_value_case", config["p_value_case"])
                config["p_value_italic"] = fmt.get("p_value_italic", config["p_value_italic"])
                config["journal_name"] = yaml_config.get("journal_name", config["journal_name"])
            return config

    # Fall back to defaults
    if journal_key in DEFAULT_STYLES:
        return DEFAULT_STYLES[journal_key].copy()

    print(f"Warning: Unknown journal '{journal}'. Using Lancet defaults.")
    return DEFAULT_STYLES["lancet"].copy()


def format_decimal(value: float, config: Dict[str, Any], precision: int = 2) -> str:
    """Format a decimal number according to journal style.

    Args:
        value: Numeric value to format
        config: Journal style configuration
        precision: Number of decimal places

    Returns:
        Formatted string with correct decimal separator
    """
    formatted = f"{value:.{precision}f}"
    if config.get("decimal_point") == "midline":
        formatted = formatted.replace(".", "\u00b7")  # midline dot
    return formatted


def format_p_value(p: float, config: Dict[str, Any]) -> str:
    """Format a P-value according to journal style.

    Args:
        p: P-value
        config: Journal style configuration

    Returns:
        Formatted P-value string
    """
    case = config.get("p_value_case", "lowercase")
    leading_zero = config.get("p_value_leading_zero", True)
    decimal = "\u00b7" if config.get("decimal_point") == "midline" else "."

    p_char = "p" if case == "lowercase" else "P"

    if p < 0.0001:
        threshold = config.get("p_threshold_format", f"{p_char}<0{decimal}0001")
        return threshold
    elif p < 0.001:
        if leading_zero:
            return f"{p_char}<0{decimal}001"
        else:
            return f"{p_char}<{decimal}001"
    else:
        if leading_zero:
            p_str = f"{p:.3f}"
        else:
            p_str = f"{p:.3f}".lstrip("0")

        if config.get("decimal_point") == "midline":
            p_str = p_str.replace(".", "\u00b7")

        return f"{p_char}={p_str}"


def format_ci(estimate: float, ci_lower: float, ci_upper: float,
              config: Dict[str, Any], precision: int = 2) -> str:
    """Format an effect estimate with 95% CI according to journal style."""
    est = format_decimal(estimate, config, precision)
    low = format_decimal(ci_lower, config, precision)
    high = format_decimal(ci_upper, config, precision)

    journal = config.get("journal_name", "").lower()

    if "lancet" in journal:
        return f"{est} (95% CI {low} to {high})"
    elif "jama" in journal or "circulation" in journal:
        return f"{est} (95% CI, {low}-{high})"
    elif "nejm" in journal:
        return f"{est} (95% CI, {low} to {high})"
    else:
        return f"{est} (95% CI {low} to {high})"


def apply_journal_style(
    fig: Optional[plt.Figure] = None,
    ax: Optional[plt.Axes] = None,
    journal: str = "lancet",
    styles_dir: Optional[str] = None,
    column_width: str = "single",
) -> Dict[str, Any]:
    """Apply journal-specific styling to a matplotlib figure.

    Args:
        fig: matplotlib Figure object
        ax: matplotlib Axes object (or list of axes)
        journal: Target journal name
        styles_dir: Directory containing YAML style files
        column_width: 'single' or 'double' column width

    Returns:
        The journal configuration dictionary used
    """
    config = get_journal_config(journal, styles_dir)

    # Set matplotlib rcParams
    plt.rcParams["font.family"] = config.get("font_family", "Arial")
    plt.rcParams["font.size"] = config.get("font_size_tick", 9)

    if fig is None and ax is None:
        return config

    # Handle multiple axes
    axes_list = [ax] if not isinstance(ax, (list, np.ndarray)) else list(ax)
    axes_list = [a for a in axes_list if a is not None]

    for a in axes_list:
        # Font sizes
        a.title.set_fontsize(config.get("font_size_title", 13))
        a.xaxis.label.set_fontsize(config.get("font_size_axis_label", 11))
        a.yaxis.label.set_fontsize(config.get("font_size_axis_label", 11))
        a.tick_params(labelsize=config.get("font_size_tick", 9))

        # Legend font
        legend = a.get_legend()
        if legend:
            for text in legend.get_texts():
                text.set_fontsize(config.get("font_size_legend", 9))

        # Clean spines
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)

    # Figure dimensions
    if fig is not None:
        mm_to_inch = 0.0393701
        if column_width == "single":
            width_mm = config.get("single_column_mm", 89)
        else:
            width_mm = config.get("double_column_mm", 183)

        current_w, current_h = fig.get_size_inches()
        aspect = current_h / current_w if current_w > 0 else 1.0
        new_w = width_mm * mm_to_inch
        new_h = min(new_w * aspect, config.get("max_height_mm", 247) * mm_to_inch)
        fig.set_size_inches(new_w, new_h)

    return config


def style_existing_image(
    input_path: str,
    output_path: str,
    journal: str = "lancet",
    styles_dir: Optional[str] = None,
    target_dpi: int = 300,
):
    """Apply journal styling to an existing image file.

    This handles DPI adjustment and dimension validation.
    For full style application, figures should be styled during creation.

    Args:
        input_path: Path to input image
        output_path: Path to output image
        journal: Target journal
        styles_dir: YAML styles directory
        target_dpi: Target DPI
    """
    if Image is None:
        print("Error: Pillow is required for image processing. Install with: pip install Pillow")
        sys.exit(1)

    config = get_journal_config(journal, styles_dir)
    target_dpi = config.get("dpi", target_dpi)

    img = Image.open(input_path)

    # Get current DPI
    current_dpi = img.info.get("dpi", (72, 72))
    if isinstance(current_dpi, tuple):
        current_dpi = current_dpi[0]

    print(f"  Input: {img.size[0]}x{img.size[1]} px, ~{current_dpi} DPI")

    # If DPI is too low, warn but save with metadata
    if current_dpi < target_dpi:
        print(f"  Warning: Input DPI ({current_dpi}) is below target ({target_dpi}).")
        print(f"  For best results, regenerate the figure at {target_dpi} DPI.")

    # Save with correct DPI metadata
    img.save(output_path, dpi=(target_dpi, target_dpi))
    print(f"  Output saved to: {output_path} ({target_dpi} DPI)")

    # Quality report
    mm_to_px = target_dpi / 25.4
    width_mm = img.size[0] / mm_to_px
    height_mm = img.size[1] / mm_to_px

    single_col = config.get("single_column_mm", 89)
    double_col = config.get("double_column_mm", 183)

    print(f"  Dimensions: {width_mm:.0f} x {height_mm:.0f} mm")
    print(f"  Journal constraints: single={single_col}mm, double={double_col}mm")

    if width_mm <= single_col * 1.1:
        print(f"  Fits: single column")
    elif width_mm <= double_col * 1.1:
        print(f"  Fits: double column")
    else:
        print(f"  Warning: Exceeds double column width. Consider resizing.")


def quality_check(fig_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Run quality checks on a figure file.

    Returns a report dictionary with pass/fail for each criterion.
    """
    report = {
        "file": str(fig_path),
        "journal": config.get("journal_name", "Unknown"),
        "checks": {},
    }

    if Image is None:
        report["error"] = "Pillow not available for quality checks"
        return report

    try:
        img = Image.open(fig_path)
    except Exception as e:
        report["error"] = str(e)
        return report

    # DPI check
    dpi = img.info.get("dpi", (72, 72))
    if isinstance(dpi, tuple):
        dpi = dpi[0]
    target_dpi = config.get("dpi", 300)
    report["checks"]["dpi"] = {
        "value": dpi,
        "target": target_dpi,
        "pass": dpi >= target_dpi,
    }

    # Dimension check
    mm_to_px = dpi / 25.4
    width_mm = img.size[0] / mm_to_px
    max_width = config.get("double_column_mm", 183)
    report["checks"]["width_mm"] = {
        "value": round(width_mm, 1),
        "max": max_width,
        "pass": width_mm <= max_width * 1.05,
    }

    # Color mode
    report["checks"]["color_mode"] = {
        "value": img.mode,
        "pass": img.mode in ("RGB", "CMYK", "L"),
    }

    # Overall pass
    report["overall_pass"] = all(c["pass"] for c in report["checks"].values())

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Apply journal-specific styling to figures.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python figure-styler.py --input figure.png --journal lancet --output styled.png
    python figure-styler.py --input figure.tiff --journal jama --output styled.tiff --dpi 600
    python figure-styler.py --check figure.png --journal nejm

Supported journals: lancet, nejm, jama, bmj, circulation
        """,
    )
    parser.add_argument("--input", help="Path to input figure file")
    parser.add_argument("--output", help="Path to output styled figure")
    parser.add_argument("--journal", required=True, help="Target journal (lancet/nejm/jama/bmj/circulation)")
    parser.add_argument("--styles-dir", default=None, help="Directory containing journal YAML files")
    parser.add_argument("--dpi", type=int, default=None, help="Override target DPI")
    parser.add_argument("--check", help="Run quality check on a figure file (no styling)")
    parser.add_argument("--info", action="store_true", help="Print journal style configuration")

    args = parser.parse_args()

    # Auto-detect styles directory
    if args.styles_dir is None:
        script_dir = Path(__file__).parent.parent
        styles_dir = script_dir / "styles"
        if styles_dir.exists():
            args.styles_dir = str(styles_dir)

    # Info mode
    if args.info:
        config = get_journal_config(args.journal, args.styles_dir)
        print(f"Style configuration for: {config['journal_name']}")
        for key, value in sorted(config.items()):
            if key != "colorblind_palette":
                print(f"  {key}: {value}")
        return

    # Quality check mode
    if args.check:
        config = get_journal_config(args.journal, args.styles_dir)
        report = quality_check(args.check, config)
        print(f"Quality check: {report['file']}")
        print(f"Journal: {report['journal']}")
        for name, check in report.get("checks", {}).items():
            status = "PASS" if check["pass"] else "FAIL"
            print(f"  [{status}] {name}: {check['value']} (target: {check.get('target', check.get('max', 'N/A'))})")
        overall = "PASS" if report.get("overall_pass") else "FAIL"
        print(f"Overall: {overall}")
        return

    # Styling mode
    if not args.input or not args.output:
        parser.error("--input and --output are required for styling mode")

    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    print(f"Applying {args.journal} style to: {args.input}")
    style_existing_image(
        input_path=args.input,
        output_path=args.output,
        journal=args.journal,
        styles_dir=args.styles_dir,
        target_dpi=args.dpi or 300,
    )


if __name__ == "__main__":
    main()
