#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

from common import atomic_write_text


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--records-json", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    records = json.loads(args.records_json)
    rows = []
    for record in records:
        metrics_path = Path(record["metrics"])
        status_path = Path(record.get("status", ""))
        metrics = json.loads(metrics_path.read_text()) if metrics_path.is_file() else {"status": "missing_metrics"}
        status = json.loads(status_path.read_text()) if status_path.is_file() else {}
        rows.append({
            "coverage": record["coverage"],
            "sample": record["sample"],
            "status": status.get("status", metrics.get("status", "")),
            "precision": metrics.get("precision", ""),
            "recall": metrics.get("recall", ""),
            "accuracy": metrics.get("accuracy", ""),
            "F1": metrics.get("F1", ""),
            "macro_precision": metrics.get("macro_precision", metrics.get("precision", "")),
            "macro_recall": metrics.get("macro_recall", metrics.get("recall", "")),
            "macro_F1": metrics.get("macro_F1", metrics.get("F1", "")),
            "micro_precision": metrics.get("micro_precision", ""),
            "micro_recall": metrics.get("micro_recall", ""),
            "micro_F1": metrics.get("micro_F1", ""),
            "micro_accuracy": metrics.get("micro_accuracy", metrics.get("accuracy", "")),
            "total_assignments": metrics.get("total_assignments", ""),
            "report": record.get("report", ""),
            "assignment": record.get("assignment", ""),
        })
    header = [
        "coverage", "sample", "status", "precision", "recall", "accuracy", "F1",
        "macro_precision", "macro_recall", "macro_F1",
        "micro_precision", "micro_recall", "micro_F1", "micro_accuracy", "total_assignments",
        "report", "assignment",
    ]
    out_lines = []
    import io
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=header, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    atomic_write_text(args.output, buffer.getvalue())


if __name__ == "__main__":
    main()
