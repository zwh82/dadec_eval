#!/usr/bin/env python3
"""Draw Fig. 3 from the collected short-read coverage-depth results.

The script reads the three selected-results tables directly and writes a
publication-ready PDF/SVG plus raster previews. Missing method-depth pairs are
left missing; no interpolation or imputation is performed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import LogFormatterMathtext
import numpy as np
import pandas as pd


METHOD_ORDER = [
    "DADEC", "FMLRC", "F_HERO", "Ratatosk", "R_HERO",
    "LoRDEC", "L_HERO", "CoLoRMap", "Proovread",
]

METHOD_LABELS = {
    "DADEC": "DADEC",
    "FMLRC": "FMLRC",
    "F_HERO": "F-HERO",
    "Ratatosk": "Ratatosk",
    "R_HERO": "R-HERO",
    "LoRDEC": "LoRDEC",
    "L_HERO": "L-HERO",
    "CoLoRMap": "CoLoRMap",
    "Proovread": "Proovread",
}

# Keep method colors and markers identical to plot_classification_macro.py.
METHOD_COLORS = {
    "DADEC": "#D62728", "FMLRC": "#FF7F0E", "F_HERO": "#2CA02C",
    "Ratatosk": "#1F77B4", "R_HERO": "#9467BD", "LoRDEC": "#8C564B",
    "L_HERO": "#E377C2", "CoLoRMap": "#7F7F7F", "Proovread": "#BCBD22",
}

MARKERS = {
    "DADEC": "o", "FMLRC": "^", "F_HERO": "s", "Ratatosk": "D",
    "R_HERO": "s", "LoRDEC": "^", "L_HERO": "D", "CoLoRMap": "v",
    "Proovread": "o",
}
OPEN_MARKERS = {"R_HERO", "LoRDEC", "L_HERO", "CoLoRMap", "Proovread"}

DATASETS = [
    ("arabidopsis", r"$\it{A.\ thaliana}$"),
    ("30s_ua", "30S-NU"),
    ("30s_ba", "30S-BA"),
]

DISPLAY_DEPTHS = {
    "arabidopsis": [5, 10, 20, 30],
    "30s_ua": [10, 20, 30, 40, 50],
    "30s_ba": [10, 20, 30, 40, 50],
}

COVERAGE_AXES = {
    "arabidopsis": ((0, 104), [0, 25, 50, 75, 100]),
    "30s_ua": ((98.4, 100.0), [98.5, 99.0, 99.5, 100.0]),
    "30s_ba": ((78, 92), [80, 85, 90]),
}


def configure_style() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 8,
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def load_results(results_root: Path, dataset: str) -> pd.DataFrame:
    path = results_root / dataset / "selected_results.tsv"
    if not path.is_file():
        raise FileNotFoundError(f"Missing input table: {path}")
    frame = pd.read_csv(path, sep="\t")
    required = {
        "short_coverage", "method", "residual_errors_per_100_kbp",
        "haplotype_coverage_percent",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{path} lacks columns: {', '.join(sorted(missing))}")
    frame = frame[frame["method"].isin(METHOD_ORDER)].copy()
    frame["depth"] = pd.to_numeric(
        frame["short_coverage"].astype(str).str.removesuffix("x"), errors="raise"
    )
    frame = frame[frame["depth"].isin(DISPLAY_DEPTHS[dataset])].copy()
    if frame.duplicated(["method", "depth"]).any():
        duplicates = frame.loc[
            frame.duplicated(["method", "depth"], keep=False),
            ["method", "short_coverage"],
        ]
        raise ValueError(f"Duplicate selected results in {path}:\n{duplicates}")
    return frame.sort_values(["method", "depth"])


def plot_metric(ax: mpl.axes.Axes, frame: pd.DataFrame, metric: str) -> None:
    depths = sorted(frame["depth"].unique())
    positions = np.arange(len(depths))
    draw_order = [method for method in METHOD_ORDER if method != "DADEC"] + ["DADEC"]
    for method in draw_order:
        values = (
            frame.loc[frame["method"] == method, ["depth", metric]]
            .set_index("depth").reindex(depths)[metric].to_numpy()
        )
        focus = method == "DADEC"
        ax.plot(
            positions, values,
            color=METHOD_COLORS[method],
            marker=MARKERS[method],
            markersize=4.7 if focus else 3.7,
            markerfacecolor="none" if method in OPEN_MARKERS else METHOD_COLORS[method],
            markeredgecolor=METHOD_COLORS[method],
            markeredgewidth=0.9,
            linewidth=1.45 if focus else 0.70,
            solid_capstyle="round",
            solid_joinstyle="round",
            zorder=3 if focus else 2,
        )
    ax.set_xlim(-0.20, len(depths) - 0.80)
    ax.set_xticks(positions, [str(int(x)) for x in depths])
    ax.grid(axis="y", color="#E9E9E9", linewidth=0.5)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color("#595959")
    ax.spines["bottom"].set_color("#595959")
    ax.tick_params(
        axis="both", color="#595959", labelcolor="#1A1A1A",
        length=2.5, width=0.7,
    )


def make_figure(results_root: Path) -> mpl.figure.Figure:
    configure_style()
    fig, axes = plt.subplots(
        2, 3, figsize=(7.2, 4.65),
        gridspec_kw={"hspace": 0.38, "wspace": 0.20},
    )

    for column, (dataset, title) in enumerate(DATASETS):
        frame = load_results(results_root, dataset)
        error_ax, coverage_ax = axes[0, column], axes[1, column]
        plot_metric(error_ax, frame, "residual_errors_per_100_kbp")
        plot_metric(coverage_ax, frame, "haplotype_coverage_percent")

        error_ax.set_yscale("log")
        error_ax.set_ylim(80, 20_000)
        error_ax.set_yticks([100, 1_000, 10_000])
        error_ax.yaxis.set_major_formatter(LogFormatterMathtext(base=10))
        coverage_ax.set_ylim(*COVERAGE_AXES[dataset][0])
        coverage_ax.set_yticks(COVERAGE_AXES[dataset][1])
        error_ax.set_title(title, fontweight="bold", pad=7)

    axes[0, 0].set_ylabel("Residual errors (per 100 kbp)")
    axes[1, 0].set_ylabel("Haplotype coverage (%)")
    axes[1, 1].set_xlabel("Short-read coverage (×)", labelpad=6)

    for label, ax in zip("abcdef", axes.flat):
        ax.text(
            -0.10, 1.025, label, transform=ax.transAxes,
            fontsize=8.5, fontweight="bold", va="bottom", ha="left",
        )

    handles = [
        Line2D(
            [0], [0], color=METHOD_COLORS[m], marker=MARKERS[m],
            linewidth=1.45 if m == "DADEC" else 0.70,
            markersize=4.7 if m == "DADEC" else 3.7,
            markerfacecolor="none" if m in OPEN_MARKERS else METHOD_COLORS[m],
            markeredgecolor=METHOD_COLORS[m], markeredgewidth=0.9,
            label=METHOD_LABELS[m],
        )
        for m in METHOD_ORDER
    ]
    fig.legend(
        handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.015),
        ncol=5, columnspacing=1.3, handlelength=2.1, handletextpad=0.5,
        labelspacing=0.7, fontsize=6.6,
    )
    fig.subplots_adjust(top=0.92, bottom=0.235, left=0.08, right=0.992)
    return fig


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-root", type=Path,
        default=repo_root / "benchmark" / "results" / "coverage_depths",
        help="Directory containing the three selected_results.tsv tables.",
    )
    parser.add_argument(
        "--output", type=Path, default=repo_root / "paper" / "coverage",
        help="Output path without an extension (default: paper/coverage).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fig = make_figure(args.results_root.resolve())
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".pdf"), bbox_inches=None, facecolor="white")
    fig.savefig(output.with_suffix(".svg"), bbox_inches=None, facecolor="white")
    fig.savefig(output.with_suffix(".png"), dpi=300, bbox_inches=None, facecolor="white")
    fig.savefig(output.with_suffix(".tiff"), dpi=600, bbox_inches=None,
                facecolor="white", pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    print(f"Wrote {output}.pdf/.svg/.png/.tiff")


if __name__ == "__main__":
    main()
