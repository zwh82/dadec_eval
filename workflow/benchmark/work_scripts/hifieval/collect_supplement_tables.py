#!/usr/bin/env python3
"""Generate Supplementary Tables S4--S7 from completed HiFiEval outputs."""

import argparse
import csv
from pathlib import Path

from collect_raw_uc import collect_and_validate


METHODS = [
    ("dadec", "DADEC"),
    ("fmlrc", "FMLRC"),
    ("f_hero", "F\\_HERO"),
    ("ratatosk", "Ratatosk"),
    ("r_hero", "R\\_HERO"),
    ("lordec", "LoRDEC"),
    ("l_hero", "L\\_HERO"),
    ("colormap", "CoLoRMap"),
    ("proovread", "Proovread"),
]


def integer(value):
    return f"{int(value):,}"


def rate(value):
    return f"{float(value):.5f}"


def read_tsv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_breakdown(root, method):
    path = root / method / "unfiltered" / f"{method}.base.eval.tsv"
    rows = read_tsv(path)
    result = {}
    for row in rows:
        if row["chrName"] == "all":
            result[row["error_type"]] = row
    missing = {"all", "insertion", "deletion", "mismatch"} - set(result)
    if missing:
        raise ValueError(f"{path}: missing aggregate rows: {sorted(missing)}")
    return result


def read_summary(root):
    rows = read_tsv(root / "summary.tsv")
    result = {(row["method"], row["filter_state"]): row for row in rows}
    for method, _ in METHODS:
        for state in ("unfiltered", "filtered"):
            if (method, state) not in result:
                raise ValueError(f"{root / 'summary.tsv'}: missing {method}/{state}")
    return result


def breakdown_table(root, number, dataset, include_raw=False):
    lines = [
        "\\begin{table}[H]",
        f"\\caption{{Base-level correct-correction ($CC$), under-correction ($UC$), and over-correction ($OC$) counts for {dataset}, with counts separated by error type.}}\\label{{tableS{number}}}",
        "\\resizebox{\\textwidth}{!}{%",
        "\\begin{tabular}{l" + "r" * 12 + "}",
        "\\toprule",
        "Method & \\multicolumn{3}{c}{All errors} & \\multicolumn{3}{c}{Insertions} & \\multicolumn{3}{c}{Deletions} & \\multicolumn{3}{c}{Mismatches} \\\\",
        "\\cmidrule(lr){2-4} \\cmidrule(lr){5-7} \\cmidrule(lr){8-10} \\cmidrule(lr){11-13}",
        "& $OC$ & $UC$ & $CC$ & $OC$ & $UC$ & $CC$ & $OC$ & $UC$ & $CC$ & $OC$ & $UC$ & $CC$ \\\\",
        "\\midrule",
    ]
    if include_raw:
        raw_counts, _ = collect_and_validate(root)
        values = []
        for error_type in ("all", "insertion", "deletion", "mismatch"):
            values.extend(("--", integer(raw_counts[error_type]), "--"))
        lines.append("Raw & " + " & ".join(values) + " \\\\")
    for method, label in METHODS:
        rows = read_breakdown(root, method)
        values = []
        for error_type in ("all", "insertion", "deletion", "mismatch"):
            row = rows[error_type]
            values.extend(integer(row[key]) for key in ("oc", "uc", "cc"))
        lines.append(label + " & " + " & ".join(values) + " \\\\")
    note = (
        "\\item \\small {Note: Counts are reported before filtering reads with read-level over-correction. "
        "Error-type counts can overlap at a genomic position and therefore need not sum to the all-error counts.}"
    )
    lines.extend([
        "\\bottomrule",
        "\\end{tabular}}",
        "\\begin{tablenotes}",
        note,
        "\\end{tablenotes}",
        "\\end{table}",
    ])
    return "\n".join(lines)


def metrics_table(root, number, dataset):
    rows = read_summary(root)
    lines = [
        "\\begin{table}[H]",
        f"\\caption{{Correction-event rates and read- and base-level correction outcomes for {dataset}.}}\\label{{tableS{number}}}",
        "\\resizebox{\\textwidth}{!}{%",
        "\\begin{tabular}{lrrrrrrrr}",
        "\\toprule",
        "Method & \\multicolumn{2}{c}{Defined measures} & \\multicolumn{3}{c}{Read level} & \\multicolumn{3}{c}{Base level} \\\\",
        "\\cmidrule(lr){2-3} \\cmidrule(lr){4-6} \\cmidrule(lr){7-9}",
        "& FDR & FNR & $OC_{read}$ & $UC_{read}$ & $CC_{read}$ & $OC$ & $UC$ & $CC$ \\\\",
        "\\midrule",
    ]
    for method, label in METHODS:
        unfiltered = rows[(method, "unfiltered")]
        filtered = rows[(method, "filtered")]
        unfiltered_values = [rate(unfiltered["FDR"]), rate(unfiltered["FNR"])]
        unfiltered_values.extend(integer(unfiltered[key]) for key in ("read_oc", "read_uc", "read_cc"))
        unfiltered_values.extend(integer(unfiltered[key]) for key in ("base_oc", "base_uc", "base_cc"))
        filtered_values = [rate(filtered["FDR"]), rate(filtered["FNR"]), "--", "--", "--"]
        filtered_values.extend(integer(filtered[key]) for key in ("base_oc", "base_uc", "base_cc"))
        lines.append(label + " & " + " & ".join(unfiltered_values) + " \\\\")
        lines.append(" & " + " & ".join(filtered_values) + " \\\\")
        if method != METHODS[-1][0]:
            lines.append("\\addlinespace[2pt]")
    lines.extend([
        "\\bottomrule",
        "\\end{tabular}}",
        "\\begin{tablenotes}",
        "\\item \\small {Note: For each method, the first row reports unfiltered results and the second row reports results after excluding reads classified as $OC_{read}$. $\\mathrm{FNR}=\\mathrm{UC}/(\\mathrm{UC}+\\mathrm{CC})$ and $\\mathrm{FDR}=\\mathrm{OC}/(\\mathrm{CC}+\\mathrm{OC})$; both measures in the second row were recalculated from the filtered base-level counts. Read-level counts are common to both rows and are shown only in the first row. }",
        "\\end{tablenotes}",
        "\\end{table}",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=Path("benchmark/results/hifieval"))
    parser.add_argument("--output", type=Path, default=Path("benchmark/results/hifieval/supplement_tables_S4_S7.tex"))
    args = parser.parse_args()

    ecoli = args.results_root / "ecoli3_20x"
    arabidopsis = args.results_root / "arabidopsis_sim_32x"
    tables = [
        breakdown_table(ecoli, 4, "the three-strain \\textit{E. coli} dataset", include_raw=True),
        breakdown_table(arabidopsis, 5, "the simulated \\textit{Arabidopsis thaliana} dataset"),
        metrics_table(ecoli, 6, "the three-strain \\textit{E. coli} dataset"),
        metrics_table(arabidopsis, 7, "the simulated \\textit{Arabidopsis thaliana} dataset"),
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n\n".join(tables) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
