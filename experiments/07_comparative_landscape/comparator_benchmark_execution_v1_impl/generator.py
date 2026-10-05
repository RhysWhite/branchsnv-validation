#!/usr/bin/env python3
"""Independent deterministic truth generator for comparator benchmark v1.

Standard-library only.  This module never imports BRANCHSNV or comparator code.
Canonical generation is fail-closed behind an explicit future authorization token.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
import random
from typing import Dict, Iterable, List, Tuple

MASTER_SEED = 20261005012417
CANONICAL_LENGTH_BP = 10000
CANONICAL_TIP_COUNTS = {32, 128, 512}
CANONICAL_AUTH_ENV = "BRANCHSNV_CANONICAL_BENCHMARK_GENERATION_AUTHORIZED"
CANONICAL_AUTH_VALUE = "AUTHORIZED_AFTER_IMPLEMENTATION_FREEZE"

DNA = "ACGT"

EVENT_SITE_COUNTS = {
    "unique_only": {"unique": 40},
    "parallel": {"unique": 20, "parallel": 20},
    "convergent": {"unique": 20, "convergent": 20},
    "reversal": {"unique": 20, "reversal": 20},
    "mixed_recurrence": {"unique": 10, "parallel": 10, "convergent": 10, "reversal": 10},
}


@dataclass(frozen=True)
class Event:
    child: str
    edge_id: str
    position: int
    ancestral_state: str
    derived_state: str
    event_class: str


def scenario_seed(scenario_id: str) -> int:
    digest = sha256(f"{MASTER_SEED}|{scenario_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _require_power_of_two(n: int) -> None:
    if n < 2 or (n & (n - 1)) != 0:
        raise ValueError("tip count must be a power of two >= 2")


def build_topology(n_tips: int, seed: int) -> tuple[str, dict[str, tuple[str, str]], dict[str, str | None]]:
    """Build a deterministic randomized strictly bifurcating rooted topology."""
    _require_power_of_two(n_tips)
    rng = random.Random(seed)
    active = [f"T{i:04d}" for i in range(1, n_tips + 1)]
    rng.shuffle(active)
    children: dict[str, tuple[str, str]] = {}
    parent: dict[str, str | None] = {tip: None for tip in active}
    next_internal = 1

    while len(active) > 1:
        rng.shuffle(active)
        new_active: list[str] = []
        for i in range(0, len(active), 2):
            left, right = active[i], active[i + 1]
            node = f"N{next_internal:04d}"
            next_internal += 1
            children[node] = (left, right)
            parent[left] = node
            parent[right] = node
            parent[node] = None
            new_active.append(node)
        active = new_active

    root = active[0]
    parent[root] = None
    return root, children, parent


def descendant_tips(root: str, children: dict[str, tuple[str, str]]) -> dict[str, tuple[str, ...]]:
    memo: dict[str, tuple[str, ...]] = {}

    def visit(node: str) -> tuple[str, ...]:
        if node in memo:
            return memo[node]
        if node not in children:
            memo[node] = (node,)
        else:
            vals = sorted(visit(children[node][0]) + visit(children[node][1]))
            memo[node] = tuple(vals)
        return memo[node]

    visit(root)
    return memo


def canonical_edge_id(descendant_tip_names: Iterable[str]) -> str:
    material = "\n".join(sorted(descendant_tip_names)).encode("utf-8")
    return sha256(material).hexdigest()


def edge_ids(root: str, children: dict[str, tuple[str, str]]) -> dict[str, str]:
    desc = descendant_tips(root, children)
    return {
        node: canonical_edge_id(desc[node])
        for node in desc
        if node != root
    }


def _depths(root: str, children: dict[str, tuple[str, str]]) -> dict[str, int]:
    depths = {root: 0}
    stack = [root]
    while stack:
        node = stack.pop()
        for child in children.get(node, ()):
            depths[child] = depths[node] + 1
            stack.append(child)
    return depths


def _independent_pair(
    root: str,
    children: dict[str, tuple[str, str]],
    rng: random.Random,
) -> tuple[str, str]:
    desc = descendant_tips(root, children)
    edges = [x for x in desc if x != root]
    rng.shuffle(edges)
    for a in edges:
        A = set(desc[a])
        for b in edges:
            if a == b:
                continue
            if A.isdisjoint(desc[b]):
                return a, b
    raise RuntimeError("no independent edge pair")


def _nested_pair(
    root: str,
    children: dict[str, tuple[str, str]],
    rng: random.Random,
) -> tuple[str, str]:
    candidates = [n for n in children if n != root and children[n]]
    if not candidates:
        # For the smallest possible topology, the root child can be used.
        candidates = [n for n in children if n != root]
    if not candidates:
        # n=2 has no internal non-root node; unsupported for recurrence toy generation.
        raise RuntimeError("no nested edge pair")
    outer = rng.choice(candidates)
    inner = rng.choice(children[outer])
    return outer, inner


def _independent_from(
    root: str,
    children: dict[str, tuple[str, str]],
    excluded_outer: str,
    rng: random.Random,
) -> str:
    desc = descendant_tips(root, children)
    excluded = set(desc[excluded_outer])
    choices = [n for n in desc if n != root and set(desc[n]).isdisjoint(excluded)]
    if not choices:
        raise RuntimeError("no independent edge outside selected lineage")
    return rng.choice(choices)


def _alt(base: str, rng: random.Random, extra_exclude: Iterable[str] = ()) -> str:
    excluded = {base, *extra_exclude}
    choices = [x for x in DNA if x not in excluded]
    return rng.choice(choices)


def _root_sequence(length_bp: int, rng: random.Random) -> str:
    return "".join(rng.choice(DNA) for _ in range(length_bp))


def _event_plan(
    root: str,
    children: dict[str, tuple[str, str]],
    root_sequence: str,
    regime: str,
    rng: random.Random,
) -> list[tuple[str, int, str, str, str]]:
    if regime not in EVENT_SITE_COUNTS:
        raise ValueError(f"unknown event regime: {regime}")

    site_classes: list[str] = []
    for cls, count in EVENT_SITE_COUNTS[regime].items():
        site_classes.extend([cls] * count)

    if len(site_classes) > len(root_sequence):
        raise ValueError("sequence too short for requested distinct event sites")

    positions = rng.sample(range(1, len(root_sequence) + 1), len(site_classes))
    rng.shuffle(site_classes)
    plan: list[tuple[str, int, str, str, str]] = []

    for position, cls in zip(positions, site_classes):
        root_base = root_sequence[position - 1]

        if cls == "unique":
            edge = rng.choice([n for n in descendant_tips(root, children) if n != root])
            derived = _alt(root_base, rng)
            plan.append((edge, position, root_base, derived, "unique"))

        elif cls == "parallel":
            a, b = _independent_pair(root, children, rng)
            derived = _alt(root_base, rng)
            plan.append((a, position, root_base, derived, "parallel"))
            plan.append((b, position, root_base, derived, "parallel"))

        elif cls == "reversal":
            outer, inner = _nested_pair(root, children, rng)
            intermediate = _alt(root_base, rng)
            plan.append((outer, position, root_base, intermediate, "reversal_forward"))
            plan.append((inner, position, intermediate, root_base, "reversal_back"))

        elif cls == "convergent":
            outer, inner = _nested_pair(root, children, rng)
            independent = _independent_from(root, children, outer, rng)
            intermediate = _alt(root_base, rng)
            target = _alt(root_base, rng, [intermediate])
            plan.append((outer, position, root_base, intermediate, "convergence_prerequisite"))
            plan.append((inner, position, intermediate, target, "convergent"))
            plan.append((independent, position, root_base, target, "convergent"))

        else:
            raise AssertionError(cls)

    return plan


def _path_to_root(node: str, parent: dict[str, str | None]) -> list[str]:
    path = []
    cur = node
    while parent[cur] is not None:
        path.append(cur)
        cur = parent[cur]  # child name identifies edge parent->child
    path.reverse()
    return path


def _apply_events(
    root: str,
    children: dict[str, tuple[str, str]],
    parent: dict[str, str | None],
    root_sequence: str,
    plan: list[tuple[str, int, str, str, str]],
) -> tuple[dict[str, str], list[Event], dict[str, float]]:
    eids = edge_ids(root, children)
    by_edge_pos: dict[tuple[str, int], tuple[str, str, str]] = {}
    for child, pos, anc, der, cls in plan:
        key = (child, pos)
        if key in by_edge_pos:
            raise RuntimeError(f"duplicate event on one edge/site: {key}")
        by_edge_pos[key] = (anc, der, cls)

    tips = sorted(n for n in parent if n not in children)
    sequences: dict[str, str] = {}

    for tip in tips:
        seq = list(root_sequence)
        for child in _path_to_root(tip, parent):
            for (event_child, pos), (anc, der, _cls) in by_edge_pos.items():
                if event_child != child:
                    continue
                observed = seq[pos - 1]
                if observed != anc:
                    raise RuntimeError(
                        f"event ancestry mismatch tip={tip} edge={child} pos={pos} "
                        f"expected={anc} observed={observed}"
                    )
                seq[pos - 1] = der
        sequences[tip] = "".join(seq)

    events = [
        Event(
            child=child,
            edge_id=eids[child],
            position=pos,
            ancestral_state=anc,
            derived_state=der,
            event_class=cls,
        )
        for child, pos, anc, der, cls in plan
    ]

    counts: dict[str, int] = {node: 0 for node in eids}
    for e in events:
        counts[e.child] += 1
    length_bp = len(root_sequence)
    branch_lengths = {
        child: max(1e-6, counts[child] / length_bp)
        for child in counts
    }
    return sequences, events, branch_lengths


def to_newick(
    root: str,
    children: dict[str, tuple[str, str]],
    branch_lengths: dict[str, float],
) -> str:
    def render(node: str) -> str:
        if node in children:
            left, right = children[node]
            body = f"({render(left)},{render(right)}){node}"
        else:
            body = node
        if node != root:
            body += f":{branch_lengths[node]:.10f}"
        return body
    return render(root) + ";"


def _mask_missing(
    sequences: dict[str, str],
    variable_positions: list[int],
    seed: int,
) -> tuple[dict[str, str], list[tuple[str, int]]]:
    tips = sorted(sequences)
    cells = [(tip, pos) for tip in tips for pos in variable_positions]
    n_missing_exact = len(cells) * 5
    if n_missing_exact % 100 != 0:
        raise ValueError("5% missingness is not an integer number of variable-site cells")
    n_missing = n_missing_exact // 100
    rng = random.Random(seed)
    chosen = set(rng.sample(cells, n_missing))
    out = {}
    for tip in tips:
        seq = list(sequences[tip])
        for t, pos in chosen:
            if t == tip:
                seq[pos - 1] = "N"
        out[tip] = "".join(seq)
    return out, sorted(chosen)


def generate_dataset(
    scenario_id: str,
    n_tips: int,
    regime: str,
    observation_condition: str,
    *,
    length_bp: int = CANONICAL_LENGTH_BP,
    canonical: bool = False,
) -> dict:
    if canonical:
        if os.environ.get(CANONICAL_AUTH_ENV) != CANONICAL_AUTH_VALUE:
            raise PermissionError(
                "canonical benchmark generation is not authorized; "
                f"set {CANONICAL_AUTH_ENV} only after a later explicit authorization"
            )
        if n_tips not in CANONICAL_TIP_COUNTS or length_bp != CANONICAL_LENGTH_BP:
            raise ValueError("canonical dimensions differ from frozen benchmark design")

    seed = scenario_seed(scenario_id)
    rng = random.Random(seed)
    root, children, parent = build_topology(n_tips, seed)
    root_seq = _root_sequence(length_bp, rng)
    plan = _event_plan(root, children, root_seq, regime, rng)
    sequences, events, branch_lengths = _apply_events(
        root, children, parent, root_seq, plan
    )

    variable_positions = sorted({e.position for e in events})
    if len(variable_positions) != 40:
        raise RuntimeError("frozen generator must produce exactly 40 variable event sites")

    observed = dict(sequences)
    missing_mask: list[tuple[str, int]] = []
    if observation_condition == "missing_5pct":
        observed, missing_mask = _mask_missing(
            sequences,
            variable_positions,
            scenario_seed(scenario_id + "|missing"),
        )
    elif observation_condition != "complete":
        raise ValueError(f"unknown observation condition: {observation_condition}")

    truth_recurrence_count: dict[int, int] = {}
    for e in events:
        truth_recurrence_count[e.position] = truth_recurrence_count.get(e.position, 0) + 1
    recurrent_positions = sorted(
        pos for pos, count in truth_recurrence_count.items() if count >= 2
    )

    return {
        "scenario_id": scenario_id,
        "seed": seed,
        "root": root,
        "root_sequence": root_seq,
        "children": children,
        "parent": parent,
        "edge_ids": edge_ids(root, children),
        "branch_lengths": branch_lengths,
        "tree_newick": to_newick(root, children, branch_lengths),
        "truth_sequences": sequences,
        "observed_sequences": observed,
        "events": [e.__dict__ for e in events],
        "variable_positions": variable_positions,
        "recurrent_positions": recurrent_positions,
        "truth_recurrence_count": truth_recurrence_count,
        "missing_mask": missing_mask,
        "canonical": canonical,
    }
