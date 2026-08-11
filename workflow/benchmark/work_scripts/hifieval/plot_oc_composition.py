#!/usr/bin/env python3
"""Plot current HiFiEval UC/OC error-type counts for the E. coli mixture."""

import argparse
import csv
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


METHODS = [
    ("dadec", "DADEC"), ("fmlrc", "FMLRC"), ("f_hero", "F_HERO"),
    ("ratatosk", "Ratatosk"), ("r_hero", "R_HERO"), ("lordec", "LoRDEC"),
    ("l_hero", "L_HERO"), ("colormap", "CoLoRMap"),
    ("proovread", "Proovread"),
]
ERROR_TYPES = ["insertion", "deletion", "mismatch"]
COLORS = {"insertion": "#4C78A8", "deletion": "#F2A65A", "mismatch": "#72B772"}


def aggregate_rows(root, method):
    path = root / method / "unfiltered" / f"{method}.base.eval.tsv"
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return {row["error_type"]: row for row in rows if row["chrName"] == "all"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("benchmark/results/hifieval/ecoli3_20x"))
    parser.add_argument("--output-prefix", type=Path, default=Path("paper/oc_composition"))
    args = parser.parse_args()

    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7,
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })

    x = np.arange(len(METHODS))
    width = 0.34
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    for offset, state, hatch in ((-width / 2, "uc", ""), (width / 2, "oc", "//")):
        bottom = np.zeros(len(METHODS))
        for error_type in ERROR_TYPES:
            values = np.array([
                int(aggregate_rows(args.input, method)[error_type][state])
                for method, _ in METHODS
            ], dtype=float) / 1e6
            ax.bar(
                x + offset, values, width, bottom=bottom,
                color=COLORS[error_type], edgecolor="white", linewidth=0.35,
                hatch=hatch, label=error_type.capitalize() if state == "uc" else None,
            )
            bottom += values

    ax.set_ylabel(r"Erroneous event count ($\times 10^6$)")
    ax.set_xticks(x, [label for _, label in METHODS], rotation=25, ha="right")
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.5, alpha=0.75)
    ax.set_axisbelow(True)

    from matplotlib.patches import Patch
    handles = [Patch(facecolor=COLORS[k], label=k.capitalize()) for k in ERROR_TYPES]
    handles.extend([
        Patch(facecolor="#BDBDBD", edgecolor="white", label=r"$UC$"),
        Patch(facecolor="#BDBDBD", edgecolor="white", hatch="//", label=r"$OC$"),
    ])
    ax.legend(handles=handles, ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.15))
    fig.tight_layout()

    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output_prefix.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(args.output_prefix.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(args.output_prefix.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {args.output_prefix}.pdf/.svg/.png")


if __name__ == "__main__":
    main()
