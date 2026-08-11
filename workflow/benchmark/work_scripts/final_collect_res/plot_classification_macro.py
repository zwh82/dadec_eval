#!/usr/bin/env python3
"""Plot classification macro metrics with a publication-ready Matplotlib layout."""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / "benchmark/results/classification/30strains_legacy_collected/selected_results.tsv"
OUTPUT_BASE = ROOT / "paper/classification_python"
SOURCE_FILE = ROOT / "paper/classification_macro_python_source.tsv"

COVERAGES = ["20x", "30x", "40x", "50x"]
METHODS = [
    "DADEC", "FMLRC", "F_HERO", "Ratatosk", "R_HERO",
    "LoRDEC", "L_HERO", "CoLoRMap", "Proovread",
]
DISPLAY_NAMES = {
    "DADEC": "DADEC", "FMLRC": "FMLRC", "F_HERO": "F-HERO",
    "Ratatosk": "Ratatosk", "R_HERO": "R-HERO", "LoRDEC": "LoRDEC",
    "L_HERO": "L-HERO", "CoLoRMap": "CoLoRMap", "Proovread": "Proovread",
}
METRICS = [
    ("macro_precision", "Macro precision"),
    ("macro_recall", "Macro recall"),
    ("macro_F1", "Macro F1-score"),
]

COLORS = {
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


mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 6.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.7,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
})


def load_data() -> pd.DataFrame:
    data = pd.read_csv(INPUT, sep="\t")
    data = data[
        data["coverage"].isin(COVERAGES) & data["method"].isin(METHODS)
    ].copy()
    data["coverage"] = pd.Categorical(data["coverage"], COVERAGES, ordered=True)
    data["method"] = pd.Categorical(data["method"], METHODS, ordered=True)
    data = data.sort_values(["method", "coverage"])

    expected = pd.MultiIndex.from_product([METHODS, COVERAGES])
    observed = pd.MultiIndex.from_frame(data[["method", "coverage"]].astype(str))
    missing = expected.difference(observed)
    duplicates = observed[observed.duplicated()].unique()
    if len(missing) or len(duplicates):
        raise ValueError(f"Input grid is incomplete or duplicated: missing={list(missing)}, duplicates={list(duplicates)}")
    if data[[name for name, _ in METRICS]].isna().any().any():
        raise ValueError("Selected macro metrics contain missing values")
    return data


def draw_figure(data: pd.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.55), sharey=True)
    x = np.arange(len(COVERAGES))
    draw_order = [method for method in METHODS if method != "DADEC"] + ["DADEC"]

    for panel_idx, (ax, (metric, title)) in enumerate(zip(axes, METRICS)):
        for method in draw_order:
            values = (
                data[data["method"] == method]
                .set_index("coverage")
                .reindex(COVERAGES)[metric]
                .to_numpy()
            )
            focus = method == "DADEC"
            ax.plot(
                x, values,
                color=COLORS[method],
                linewidth=1.9 if focus else 0.95,
                marker=MARKERS[method],
                markersize=4.7 if focus else 3.7,
                markerfacecolor="none" if method in OPEN_MARKERS else COLORS[method],
                markeredgecolor=COLORS[method],
                markeredgewidth=0.9,
                solid_capstyle="round",
                solid_joinstyle="round",
                label=DISPLAY_NAMES[method],
                zorder=3 if focus else 2,
            )

        ax.set_xlim(-0.22, 3.22)
        ax.set_ylim(0.6125, 0.7225)
        ax.set_xticks(x, ["20", "30", "40", "50"])
        ax.set_yticks(np.arange(0.62, 0.721, 0.02))
        ax.grid(axis="y", color="#E9E9E9", linewidth=0.5)
        ax.set_axisbelow(True)
        ax.spines["left"].set_visible(True)
        ax.spines["left"].set_color("#595959")
        ax.spines["bottom"].set_color("#595959")
        ax.tick_params(axis="both", color="#595959", labelcolor="#1A1A1A", length=2.5, width=0.7)
        ax.set_title(title, pad=7)
        ax.text(-0.10, 1.025, chr(ord("a") + panel_idx), transform=ax.transAxes,
                fontsize=8.5, fontweight="bold", va="bottom", ha="left")

    axes[1].set_xlabel("Short-read coverage (×)", labelpad=6)

    handles, labels = axes[0].get_legend_handles_labels()
    lookup = dict(zip(labels, handles))
    fig.legend(
        [lookup[DISPLAY_NAMES[m]] for m in METHODS],
        [DISPLAY_NAMES[m] for m in METHODS],
        loc="lower center", bbox_to_anchor=(0.5, 0.025),
        ncol=5, frameon=False, handlelength=2.1, columnspacing=1.3,
        handletextpad=0.5, labelspacing=0.7,
    )
    fig.subplots_adjust(left=0.045, right=0.992, top=0.88, bottom=0.235, wspace=0.12)
    return fig


def save_figure(fig: plt.Figure) -> None:
    OUTPUT_BASE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_BASE.with_suffix(".svg"), bbox_inches=None, facecolor="white")
    fig.savefig(OUTPUT_BASE.with_suffix(".pdf"), bbox_inches=None, facecolor="white")
    fig.savefig(OUTPUT_BASE.with_suffix(".tiff"), dpi=600, bbox_inches=None,
                facecolor="white", pil_kwargs={"compression": "tiff_lzw"})
    fig.savefig(OUTPUT_BASE.parent / f"{OUTPUT_BASE.name}_preview.png", dpi=300,
                bbox_inches=None, facecolor="white")


def main() -> None:
    data = load_data()
    fig = draw_figure(data)
    save_figure(fig)
    # data[["coverage", "method", *[name for name, _ in METRICS]]].to_csv(
    #     SOURCE_FILE, sep="\t", index=False
    # )
    plt.close(fig)
    print(f"Wrote {OUTPUT_BASE}.svg/.pdf/.tiff and {OUTPUT_BASE}_preview.png")
    # print(f"Wrote {SOURCE_FILE}")


if __name__ == "__main__":
    main()
