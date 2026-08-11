#!/usr/bin/env python3
import argparse
import math
from pathlib import Path


def calculate_stats(path):
    count = 0
    total = 0.0
    minimum = math.inf
    maximum = -math.inf

    with open(path) as handle:
        for line_number, line in enumerate(handle, 1):
            text = line.split("#", 1)[0].strip()
            if not text:
                continue
            try:
                value = float(text)
            except ValueError as error:
                raise ValueError(
                    f"{path}:{line_number}: invalid number: {text!r}"
                ) from error
            if not math.isfinite(value):
                raise ValueError(
                    f"{path}:{line_number}: value must be finite: {text!r}"
                )

            count += 1
            total += value
            minimum = min(minimum, value)
            maximum = max(maximum, value)

    if count == 0:
        raise ValueError(f"{path}: no numeric values found")
    if minimum == 0:
        raise ValueError(f"{path}: minimum is zero; max/min fold is undefined")

    return {
        "minimum": minimum,
        "maximum": maximum,
        "mean": total / count,
        "max_min_fold": maximum / minimum,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Calculate summary statistics for a one-value-per-line depth file."
    )
    parser.add_argument("input", type=Path, help="Depth file to read")
    parser.add_argument(
        "--precision", type=int, default=6, help="Decimal places in output (default: 6)"
    )
    args = parser.parse_args()
    if args.precision < 0:
        parser.error("--precision must be non-negative")

    try:
        stats = calculate_stats(args.input)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    for name in ("minimum", "maximum", "mean", "max_min_fold"):
        print(f"{name}\t{stats[name]:.{args.precision}f}")


if __name__ == "__main__":
    main()
