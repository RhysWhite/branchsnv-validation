#!/usr/bin/env python3
"""Truth-blind scoring functions for comparator benchmark v1."""
from __future__ import annotations

from collections import Counter
from typing import Iterable


def _safe_prf(tp: int, fp: int, fn: int) -> dict[str, float | int]:
    if tp + fp == 0:
        precision = 1.0 if tp + fn == 0 else 0.0
    else:
        precision = tp / (tp + fp)

    if tp + fn == 0:
        recall = 1.0
    else:
        recall = tp / (tp + fn)

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return {
        "true_positive_count": tp,
        "false_positive_count": fp,
        "false_negative_count": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def branch_event_key(row: dict) -> tuple[str, int, str, str]:
    return (
        str(row["edge_id"]),
        int(row["position"]),
        str(row["ancestral_state"]).upper(),
        str(row["derived_state"]).upper(),
    )


def score_branch_events(
    truth_rows: Iterable[dict],
    predicted_rows: Iterable[dict],
) -> dict[str, float | int]:
    truth = {branch_event_key(r) for r in truth_rows}
    pred = {branch_event_key(r) for r in predicted_rows}
    tp = len(truth & pred)
    return _safe_prf(tp, len(pred - truth), len(truth - pred))


def score_homoplasy_sites(
    truth_positions: Iterable[int],
    predicted_positions: Iterable[int],
) -> dict[str, float | int]:
    truth = {int(x) for x in truth_positions}
    pred = {int(x) for x in predicted_positions}
    tp = len(truth & pred)
    out = _safe_prf(tp, len(pred - truth), len(truth - pred))
    return {
        "true_positive_site_count": out["true_positive_count"],
        "false_positive_site_count": out["false_positive_count"],
        "false_negative_site_count": out["false_negative_count"],
        "site_precision": out["precision"],
        "site_recall": out["recall"],
        "site_f1": out["f1"],
    }


def recurrence_count_absolute_error(
    truth_counts: dict[int, int],
    predicted_counts: dict[int, int],
) -> float:
    positions = sorted(set(map(int, truth_counts)) | set(map(int, predicted_counts)))
    if not positions:
        return 0.0
    errors = [
        abs(int(predicted_counts.get(pos, 0)) - int(truth_counts.get(pos, 0)))
        for pos in positions
    ]
    return sum(errors) / len(errors)


def macro_average(rows: Iterable[dict], metric: str) -> float:
    vals = [float(r[metric]) for r in rows]
    if not vals:
        raise ValueError("cannot macro-average zero rows")
    return sum(vals) / len(vals)
