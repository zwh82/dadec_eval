#!/usr/bin/env python3
"""Shared naming helpers for benchmark run directories and evaluations."""

import re
from decimal import Decimal, InvalidOperation


METHODS = (
    "dadec",
    "f_hero",
    "fmlrc",
    "l_hero",
    "lordec",
    "proovread",
    "r_hero",
    "ratatosk",
    "colormap",
    "vechat",
    "dechat",
)
ALLOWED_AMBIGUITY_SCORES = ("0.99", "0.9999")
SCORE_TO_DIRECTORY = {
    "0.99": "metaquast",
    "0.9999": "metaquast.ambiguity9999",
}
_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9_-]*")


def validate_slug(value, label="slug"):
    value = str(value)
    if not _SLUG_RE.fullmatch(value):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


def derive_run_group(run_id, method=None):
    """Return the data-group prefix before ``_<method>`` in a run id."""
    run_id = validate_slug(run_id, "run id")
    methods = (method,) if method else METHODS
    matches = []
    for candidate in methods:
        if candidate not in METHODS:
            raise ValueError(f"Unknown method for run grouping: {candidate!r}")
        match = re.search(rf"_{re.escape(candidate)}(?:_|$)", run_id)
        if match:
            matches.append((match.start(), candidate))
    if not matches:
        raise ValueError(f"Cannot derive data group from run id: {run_id!r}")
    position, _ = min(matches)
    return validate_slug(run_id[:position], "run group")


def _canonical_score(value):
    try:
        score = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid MetaQUAST ambiguity score: {value!r}") from None
    for allowed in ALLOWED_AMBIGUITY_SCORES:
        if score == Decimal(allowed):
            return allowed
    raise ValueError(
        f"Unsupported MetaQUAST ambiguity score {value!r}; "
        f"choose from {', '.join(ALLOWED_AMBIGUITY_SCORES)}"
    )


def normalize_ambiguity_scores(value=None):
    """Normalize a scalar, list, or comma-separated score selection."""
    if value in (None, ""):
        items = ALLOWED_AMBIGUITY_SCORES
    elif isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
    elif isinstance(value, (list, tuple)):
        items = value
    else:
        items = [value]
    if not items:
        raise ValueError("At least one MetaQUAST ambiguity score is required")
    result = []
    for item in items:
        score = _canonical_score(item)
        if score not in result:
            result.append(score)
    return result


def evaluation_variants(tool, ambiguity_scores=None):
    tool = str(tool).lower()
    if tool == "quast":
        return [("quast", "NA")]
    if tool != "metaquast":
        raise ValueError("evaluation.tool must be 'metaquast' or 'quast'")
    return [
        (SCORE_TO_DIRECTORY[score], score)
        for score in normalize_ambiguity_scores(ambiguity_scores)
    ]
