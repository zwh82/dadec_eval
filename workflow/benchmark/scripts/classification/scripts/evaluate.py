#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from common import atomic_write_json, atomic_write_text


LEGACY_GROUPS = [
    {"NC_000913.3"}, {"NC_003028.3"}, {"NC_003997.3"}, {"NC_007530.2"},
    {"NC_002695.2"}, {"NC_008261.1"}, {"NC_007795.1"}, {"NC_008312.1"},
    {"NC_002937.3", "NC_005863.1"}, {"NC_020291.1", "NC_020292.1"},
    {"NZ_CP009225.1"}, {"NZ_CP011663.1"}, {"NZ_LN831051.1"},
    {"NZ_LQXF01000001.1", "NZ_LQXF01000002.1", "NZ_LQXF01000003.1", "NZ_LQXF01000004.1", "NZ_LQXF01000005.1", "NZ_LQXF01000006.1", "NZ_LQXF01000007.1", "NZ_LQXF01000008.1", "NZ_LQXF01000009.1", "NZ_LQXF01000010.1", "NZ_LQXF01000011.1", "NZ_LQXF01000012.1", "NZ_LQXF01000013.1", "NZ_LQXF01000014.1", "NZ_LQXF01000015.1", "NZ_LQXF01000016.1", "NZ_LQXF01000017.1", "NZ_LQXF01000018.1", "NZ_LQXF01000019.1", "NZ_LQXF01000020.1", "NZ_LQXF01000021.1", "NZ_LQXF01000022.1", "NZ_LQXF01000023.1", "NZ_LQXF01000024.1", "NZ_LQXF01000025.1", "NZ_LQXF01000026.1", "NZ_LQXF01000027.1", "NZ_LQXF01000028.1", "NZ_LQXF01000029.1", "NZ_LQXF01000030.1", "NZ_LQXF01000031.1", "NZ_LQXF01000032.1", "NZ_LQXF01000033.1", "NZ_LQXF01000034.1", "NZ_LQXF01000035.1", "NZ_LQXF01000036.1", "NZ_LQXF01000037.1", "NZ_LQXF01000038.1", "NZ_LQXF01000039.1", "NZ_LQXF01000040.1", "NZ_LQXF01000041.1", "NZ_LQXF01000042.1", "NZ_LQXF01000043.1", "NZ_LQXF01000044.1", "NZ_LQXF01000045.1", "NZ_LQXF01000046.1", "NZ_LQXF01000047.1", "NZ_LQXF01000048.1", "NZ_LQXF01000049.1", "NZ_LQXF01000050.1", "NZ_LQXF01000051.1", "NZ_LQXF01000052.1", "NZ_LQXF01000053.1", "NZ_LQXF01000054.1", "NZ_LQXF01000055.1", "NZ_LQXF01000056.1", "NZ_LQXF01000057.1", "NZ_LQXF01000058.1", "NZ_LQXF01000059.1", "NZ_LQXF01000060.1", "NZ_LQXF01000061.1", "NZ_LQXF01000062.1", "NZ_LQXF01000063.1", "NZ_LQXF01000064.1", "NZ_LQXF01000065.1", "NZ_LQXF01000066.1", "NZ_LQXF01000067.1", "NZ_LQXF01000068.1", "NZ_LQXF01000069.1", "NZ_LQXF01000070.1", "NZ_LQXF01000071.1", "NZ_LQXF01000072.1", "NZ_LQXF01000073.1", "NZ_LQXF01000074.1", "NZ_LQXF01000075.1", "NZ_LQXF01000076.1", "NZ_LQXF01000077.1", "NZ_LQXF01000078.1", "NZ_LQXF01000079.1", "NZ_LQXF01000080.1", "NZ_LQXF01000081.1", "NZ_LQXF01000082.1", "NZ_LQXF01000083.1", "NZ_LQXF01000084.1", "NZ_LQXF01000085.1", "NZ_LQXF01000086.1", "NZ_LQXF01000087.1", "NZ_LQXF01000088.1", "NZ_LQXF01000089.1", "NZ_LQXF01000090.1", "NZ_LQXF01000091.1", "NZ_LQXF01000092.1", "NZ_LQXF01000093.1", "NZ_LQXF01000094.1", "NZ_LQXF01000095.1", "NZ_LQXF01000096.1", "NZ_LQXF01000097.1", "NZ_LQXF01000098.1"},
    {"NZ_CP017186.1", "NZ_CP017187.1"}, {"NZ_CP017183.1"}, {"CP019944.1"}, {"NZ_CP028325.1"},
    {"NZ_CP023671.1", "NZ_CP023672.1"}, {"NZ_AP017632.1"}, {"NZ_AP019716.1", "NZ_AP019717.1", "NZ_AP019718.1", "NZ_AP019719.1"},
    {"NZ_CP045110.1", "NZ_CP045108.1", "NZ_CP045109.1"}, {"NZ_CP040626.1", "NZ_CP040627.1", "NZ_CP040628.1", "NZ_CP040629.1"},
    {"NZ_CP065681.1", "NZ_CP065680.1"},
    {"NZ_JACYYI010000010.1", "NZ_JACYYI010000011.1", "NZ_JACYYI010000012.1", "NZ_JACYYI010000013.1", "NZ_JACYYI010000014.1", "NZ_JACYYI010000015.1", "NZ_JACYYI010000016.1", "NZ_JACYYI010000017.1", "NZ_JACYYI010000018.1", "NZ_JACYYI010000019.1", "NZ_JACYYI010000001.1", "NZ_JACYYI010000020.1", "NZ_JACYYI010000021.1", "NZ_JACYYI010000022.1", "NZ_JACYYI010000023.1", "NZ_JACYYI010000024.1", "NZ_JACYYI010000025.1", "NZ_JACYYI010000026.1", "NZ_JACYYI010000027.1", "NZ_JACYYI010000028.1", "NZ_JACYYI010000002.1", "NZ_JACYYI010000029.1", "NZ_JACYYI010000030.1", "NZ_JACYYI010000031.1", "NZ_JACYYI010000032.1", "NZ_JACYYI010000003.1", "NZ_JACYYI010000004.1", "NZ_JACYYI010000033.1", "NZ_JACYYI010000034.1", "NZ_JACYYI010000035.1", "NZ_JACYYI010000005.1", "NZ_JACYYI010000036.1", "NZ_JACYYI010000006.1", "NZ_JACYYI010000007.1", "NZ_JACYYI010000008.1", "NZ_JACYYI010000009.1"},
    {"NZ_CP077308.1", "NZ_CP077309.1", "NZ_CP077310.1"}, {"NZ_CP086003.1"}, {"NZ_AP026446.1"}, {"NZ_UFRW01000002.1", "NZ_UFRW01000001.1"},
    {"NZ_UAWJ01000035.1", "NZ_UAWJ01000031.1", "NZ_UAWJ01000030.1", "NZ_UAWJ01000029.1", "NZ_UAWJ01000028.1", "NZ_UAWJ01000032.1", "NZ_UAWJ01000027.1", "NZ_UAWJ01000034.1", "NZ_UAWJ01000026.1", "NZ_UAWJ01000010.1", "NZ_UAWJ01000001.1", "NZ_UAWJ01000009.1", "NZ_UAWJ01000012.1", "NZ_UAWJ01000008.1", "NZ_UAWJ01000011.1", "NZ_UAWJ01000004.1", "NZ_UAWJ01000021.1", "NZ_UAWJ01000003.1", "NZ_UAWJ01000007.1", "NZ_UAWJ01000006.1", "NZ_UAWJ01000033.1", "NZ_UAWJ01000002.1", "NZ_UAWJ01000013.1", "NZ_UAWJ01000018.1", "NZ_UAWJ01000025.1", "NZ_UAWJ01000014.1", "NZ_UAWJ01000024.1", "NZ_UAWJ01000015.1", "NZ_UAWJ01000016.1", "NZ_UAWJ01000017.1", "NZ_UAWJ01000019.1", "NZ_UAWJ01000023.1", "NZ_UAWJ01000020.1", "NZ_UAWJ01000005.1", "NZ_UAWJ01000022.1"},
]


def load_groups(path=None):
    if not path:
        return [set(group) for group in LEGACY_GROUPS]
    groups = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            groups.append(set(parts[-1].replace(",", " ").split()))
    return groups


def find_group(seq_id, groups):
    for group in groups:
        if seq_id in group:
            return group
    return set()


def score_assignment(path, groups):
    per_group = []
    total = 0
    right = 0
    assignments = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("readID"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            read_id = parts[0].split("-")[0]
            seq_id = parts[1]
            assignments.append((read_id, seq_id))
            total += 1
            if seq_id in find_group(read_id, groups):
                right += 1
    for group in groups:
        tp = fp = tn = fn = 0
        for read_id, seq_id in assignments:
            predicted = seq_id in group
            true = read_id in group
            if predicted and true:
                tp += 1
            elif predicted and not true:
                fp += 1
            elif not predicted and not true:
                tn += 1
            else:
                fn += 1
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        per_group.append({"members": sorted(group), "TP": tp, "FP": fp, "TN": tn, "FN": fn, "precision": precision, "recall": recall})
    macro_precision = sum(row["precision"] for row in per_group) / len(per_group) if per_group else 0.0
    macro_recall = sum(row["recall"] for row in per_group) / len(per_group) if per_group else 0.0
    macro_f1 = (2 * macro_precision * macro_recall / (macro_precision + macro_recall)) if macro_precision + macro_recall else 0.0

    # The historical evaluator averaged the one-vs-rest metrics for each of
    # the 30 groups.  Also expose the corresponding global (micro) values by
    # summing the one-vs-rest confusion counts before calculating precision and
    # recall.  The legacy keys below remain aliases for the macro values.
    total_tp = sum(row["TP"] for row in per_group)
    total_fp = sum(row["FP"] for row in per_group)
    total_tn = sum(row["TN"] for row in per_group)
    total_fn = sum(row["FN"] for row in per_group)
    micro_precision = total_tp / (total_tp + total_fp) if total_tp + total_fp else 0.0
    micro_recall = total_tp / (total_tp + total_fn) if total_tp + total_fn else 0.0
    micro_f1 = (2 * micro_precision * micro_recall / (micro_precision + micro_recall)) if micro_precision + micro_recall else 0.0
    accuracy = right / total if total else 0.0
    return {
        "status": "ok",
        "total_assignments": total,
        "correct_assignments": right,
        "accuracy": accuracy,
        "total_TP": total_tp,
        "total_FP": total_fp,
        "total_TN": total_tn,
        "total_FN": total_fn,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_F1": macro_f1,
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_F1": micro_f1,
        "micro_accuracy": accuracy,
        # Backward-compatible names used by the original workflow.
        "precision": macro_precision,
        "recall": macro_recall,
        "F1": macro_f1,
        "per_group": per_group,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--assignment", required=True)
    p.add_argument("--groups")
    p.add_argument("--json-output", required=True)
    p.add_argument("--text-output", required=True)
    args = p.parse_args()
    result = score_assignment(args.assignment, load_groups(args.groups))
    atomic_write_json(args.json_output, result)
    lines = ["hap\tTP\tFP\tTN\tFN\tprecision\trecall"]
    for row in result["per_group"]:
        lines.append("%s\t%d\t%d\t%d\t%d\t%.12g\t%.12g" % (
            ",".join(row["members"]), row["TP"], row["FP"], row["TN"], row["FN"], row["precision"], row["recall"]
        ))
    lines.extend([
        "all\t%d\t%d\t%d\t%d" % (result["total_TP"], result["total_FP"], result["total_TN"], result["total_FN"]),
        "correct_assignments:%d" % result["correct_assignments"],
        "total_assignments:%d" % result["total_assignments"],
        "precision:%s" % result["macro_precision"],
        "recall:%s" % result["macro_recall"],
        "acc:%s" % result["accuracy"],
        "F1:%s" % result["macro_F1"],
        "macro_precision:%s" % result["macro_precision"],
        "macro_recall:%s" % result["macro_recall"],
        "macro_F1:%s" % result["macro_F1"],
        "micro_precision:%s" % result["micro_precision"],
        "micro_recall:%s" % result["micro_recall"],
        "micro_F1:%s" % result["micro_F1"],
        "micro_accuracy:%s" % result["micro_accuracy"],
    ])
    atomic_write_text(args.text_output, "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
