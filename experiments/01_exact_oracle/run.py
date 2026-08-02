#!/usr/bin/env python3
"""Independent exhaustive validation of BRANCHSNV's parsimony reconstruction.

The oracle in this script does not import or reuse BRANCHSNV's Sankoff
implementation. Topologies and focal edges are specified independently as
explicit parent maps. For each observed tip pattern, the oracle enumerates all
A/C/G/T assignments to internal nodes, calculates the global minimum number of
unordered state changes, and retains every parent-child state pair attainable
on the focal edge among globally optimal assignments.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import os
import platform
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

STATES = ("A", "C", "G", "T")
STATE_INDEX = {state: index for index, state in enumerate(STATES)}
CANONICAL_ALPHABET = "ACGT"
FULL_ALPHABET = "ACGTRYSWKMBDHVN?-"
IUPAC: dict[str, frozenset[str]] = {
    "A": frozenset("A"),
    "C": frozenset("C"),
    "G": frozenset("G"),
    "T": frozenset("T"),
    "R": frozenset("AG"),
    "Y": frozenset("CT"),
    "S": frozenset("CG"),
    "W": frozenset("AT"),
    "K": frozenset("GT"),
    "M": frozenset("AC"),
    "B": frozenset("CGT"),
    "D": frozenset("AGT"),
    "H": frozenset("ACT"),
    "V": frozenset("ACG"),
    "N": frozenset("ACGT"),
    "?": frozenset("ACGT"),
    "-": frozenset("ACGT"),
}


@dataclass(frozen=True)
class TopologyCase:
    name: str
    description: str
    topology_type: str
    branch_type: str
    newick: str
    tips: tuple[str, ...]
    parent: tuple[tuple[str, str], ...]
    focal_parent: str
    focal_child: str
    focal_descendants: frozenset[str]

    @property
    def parent_map(self) -> dict[str, str]:
        return dict(self.parent)

    @property
    def nodes(self) -> tuple[str, ...]:
        names = set(self.tips)
        for child, parent in self.parent:
            names.add(child)
            names.add(parent)
        return tuple(sorted(names))

    @property
    def internal_nodes(self) -> tuple[str, ...]:
        tip_set = set(self.tips)
        return tuple(node for node in self.nodes if node not in tip_set)


CASES = (
    TopologyCase(
        name="balanced5_internal",
        description="Balanced five-tip tree; focal branch leads to the A+B clade.",
        topology_type="bifurcating",
        branch_type="internal",
        newick="(O,((A,B),(C,D)));",
        tips=("O", "A", "B", "C", "D"),
        parent=(("O", "R"), ("X", "R"), ("AB", "X"), ("CD", "X"),
                ("A", "AB"), ("B", "AB"), ("C", "CD"), ("D", "CD")),
        focal_parent="X",
        focal_child="AB",
        focal_descendants=frozenset(("A", "B")),
    ),
    TopologyCase(
        name="balanced5_terminal",
        description="Balanced five-tip tree; focal branch leads to terminal tip A.",
        topology_type="bifurcating",
        branch_type="terminal",
        newick="(O,((A,B),(C,D)));",
        tips=("O", "A", "B", "C", "D"),
        parent=(("O", "R"), ("X", "R"), ("AB", "X"), ("CD", "X"),
                ("A", "AB"), ("B", "AB"), ("C", "CD"), ("D", "CD")),
        focal_parent="AB",
        focal_child="A",
        focal_descendants=frozenset(("A",)),
    ),
    TopologyCase(
        name="balanced5_root_adjacent",
        description="Balanced five-tip tree; focal branch is adjacent to the root.",
        topology_type="bifurcating",
        branch_type="root-adjacent internal",
        newick="(O,((A,B),(C,D)));",
        tips=("O", "A", "B", "C", "D"),
        parent=(("O", "R"), ("X", "R"), ("AB", "X"), ("CD", "X"),
                ("A", "AB"), ("B", "AB"), ("C", "CD"), ("D", "CD")),
        focal_parent="R",
        focal_child="X",
        focal_descendants=frozenset(("A", "B", "C", "D")),
    ),
    TopologyCase(
        name="pectinate6_internal",
        description="Unbalanced six-tip tree; focal branch leads to C+D+E.",
        topology_type="bifurcating pectinate",
        branch_type="internal",
        newick="(O,(A,(B,(C,(D,E)))));",
        tips=("O", "A", "B", "C", "D", "E"),
        parent=(("O", "R"), ("X1", "R"), ("A", "X1"), ("X2", "X1"),
                ("B", "X2"), ("X3", "X2"), ("C", "X3"), ("DE", "X3"),
                ("D", "DE"), ("E", "DE")),
        focal_parent="X2",
        focal_child="X3",
        focal_descendants=frozenset(("C", "D", "E")),
    ),
    TopologyCase(
        name="multifurcating6_internal",
        description="Six-tip tree with a three-way polytomy; focal branch leads to A+B+C.",
        topology_type="multifurcating",
        branch_type="internal",
        newick="(O,((A,B,C),(D,E)));",
        tips=("O", "A", "B", "C", "D", "E"),
        parent=(("O", "R"), ("X", "R"), ("ABC", "X"), ("DE", "X"),
                ("A", "ABC"), ("B", "ABC"), ("C", "ABC"),
                ("D", "DE"), ("E", "DE")),
        focal_parent="X",
        focal_child="ABC",
        focal_descendants=frozenset(("A", "B", "C")),
    ),
    TopologyCase(
        name="multifurcating6_terminal",
        description="Six-tip tree with a three-way polytomy; focal branch leads to terminal tip C.",
        topology_type="multifurcating",
        branch_type="terminal",
        newick="(O,((A,B,C),(D,E)));",
        tips=("O", "A", "B", "C", "D", "E"),
        parent=(("O", "R"), ("X", "R"), ("ABC", "X"), ("DE", "X"),
                ("A", "ABC"), ("B", "ABC"), ("C", "ABC"),
                ("D", "DE"), ("E", "DE")),
        focal_parent="ABC",
        focal_child="C",
        focal_descendants=frozenset(("C",)),
    ),
    TopologyCase(
        name="small4_ambiguity_exhaustive",
        description="Four-tip pectinate tree used for exhaustive evaluation of all supported symbols.",
        topology_type="bifurcating pectinate",
        branch_type="internal",
        newick="(O,(A,(B,C)));",
        tips=("O", "A", "B", "C"),
        parent=(("O", "R"), ("X", "R"), ("A", "X"), ("BC", "X"),
                ("B", "BC"), ("C", "BC")),
        focal_parent="X",
        focal_child="BC",
        focal_descendants=frozenset(("B", "C")),
    ),
)


@dataclass(frozen=True)
class AssignmentRecord:
    internal_edge_score: int
    tip_parent_states: tuple[int, ...]
    focal_parent_state: int
    focal_child_state: int | None


@dataclass
class CaseCounts:
    canonical_exhaustive: int = 0
    ambiguity_exhaustive: int = 0
    generated: int = 0
    mismatches: int = 0
    no_change: int = 0
    unambiguous_change: int = 0
    change_state_ambiguous: int = 0
    placement_ambiguous: int = 0

    @property
    def total(self) -> int:
        return self.canonical_exhaustive + self.ambiguity_exhaustive + self.generated

    def add_status(self, status: str) -> None:
        if status not in {
            "no_change",
            "unambiguous_change",
            "change_state_ambiguous",
            "placement_ambiguous",
        }:
            raise ValueError(f"Unexpected status: {status}")
        setattr(self, status, getattr(self, status) + 1)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def descendants(case: TopologyCase, node: str) -> frozenset[str]:
    parent = case.parent_map
    children: dict[str, list[str]] = {}
    for child, parent_node in parent.items():
        children.setdefault(parent_node, []).append(child)
    stack = [node]
    result: set[str] = set()
    tip_set = set(case.tips)
    while stack:
        current = stack.pop()
        if current in tip_set:
            result.add(current)
        else:
            stack.extend(children.get(current, []))
    return frozenset(result)


def validate_case_specification(case: TopologyCase) -> None:
    parent = case.parent_map
    if case.focal_child not in parent:
        raise ValueError(f"{case.name}: focal child has no parent")
    if parent[case.focal_child] != case.focal_parent:
        raise ValueError(f"{case.name}: focal edge does not match parent map")
    observed = descendants(case, case.focal_child)
    if observed != case.focal_descendants:
        raise ValueError(
            f"{case.name}: explicit focal descendants {sorted(observed)} do not match "
            f"declared descendants {sorted(case.focal_descendants)}"
        )


class ExhaustiveOracle:
    """Brute-force oracle with topology-independent precomputation."""

    def __init__(self, case: TopologyCase) -> None:
        validate_case_specification(case)
        self.case = case
        self.internal_nodes = case.internal_nodes
        self.internal_index = {node: index for index, node in enumerate(self.internal_nodes)}
        self.tip_index = {tip: index for index, tip in enumerate(case.tips)}
        self.assignments = self._compile_assignments()

    def _compile_assignments(self) -> tuple[AssignmentRecord, ...]:
        parent_map = self.case.parent_map
        records: list[AssignmentRecord] = []
        tips = set(self.case.tips)
        for values in itertools.product(range(4), repeat=len(self.internal_nodes)):
            state = dict(zip(self.internal_nodes, values))
            internal_score = 0
            tip_parent_states = [0] * len(self.case.tips)
            for child, parent in self.case.parent:
                parent_state = state[parent]
                if child in tips:
                    tip_parent_states[self.tip_index[child]] = parent_state
                else:
                    internal_score += int(parent_state != state[child])
            focal_parent_state = state[self.case.focal_parent]
            focal_child_state = (
                None if self.case.focal_child in tips else state[self.case.focal_child]
            )
            records.append(
                AssignmentRecord(
                    internal_edge_score=internal_score,
                    tip_parent_states=tuple(tip_parent_states),
                    focal_parent_state=focal_parent_state,
                    focal_child_state=focal_child_state,
                )
            )
        return tuple(records)

    def reconstruct(self, pattern: str) -> tuple[int, tuple[tuple[str, str], ...], str]:
        if len(pattern) != len(self.case.tips):
            raise ValueError("Pattern length does not match tip count")
        allowed = tuple(tuple(STATE_INDEX[state] for state in IUPAC[symbol]) for symbol in pattern)
        best_score: int | None = None
        best_pairs: set[tuple[str, str]] = set()
        focal_tip_index = self.tip_index.get(self.case.focal_child)

        for assignment in self.assignments:
            score = assignment.internal_edge_score
            terminal_minima: list[int] = []
            for tip_position, parent_state in enumerate(assignment.tip_parent_states):
                minimum = 0 if parent_state in allowed[tip_position] else 1
                terminal_minima.append(minimum)
                score += minimum

            if best_score is not None and score > best_score:
                continue

            if assignment.focal_child_state is None:
                assert focal_tip_index is not None
                edge_minimum = terminal_minima[focal_tip_index]
                focal_child_states = tuple(
                    state
                    for state in allowed[focal_tip_index]
                    if int(assignment.focal_parent_state != state) == edge_minimum
                )
            else:
                focal_child_states = (assignment.focal_child_state,)

            focal_pairs = {
                (STATES[assignment.focal_parent_state], STATES[child_state])
                for child_state in focal_child_states
            }
            if best_score is None or score < best_score:
                best_score = score
                best_pairs = focal_pairs
            elif score == best_score:
                best_pairs.update(focal_pairs)

        if best_score is None or not best_pairs:
            raise RuntimeError("Oracle failed to find a reconstruction")
        pairs = tuple(sorted(best_pairs))
        changes = tuple(parent != child for parent, child in pairs)
        if all(changes):
            status = "unambiguous_change" if len(pairs) == 1 else "change_state_ambiguous"
        elif any(changes):
            status = "placement_ambiguous"
        else:
            status = "no_change"
        return best_score, pairs, status


def exhaustive_patterns(alphabet: str, length: int) -> Iterator[str]:
    for symbols in itertools.product(alphabet, repeat=length):
        yield "".join(symbols)


def deterministic_generated_patterns(
    case_name: str,
    length: int,
    count: int,
    seed: str,
) -> Iterator[str]:
    """Generate stable unique patterns without relying on Python's random module."""

    observed: set[str] = set()
    counter = 0
    while len(observed) < count:
        symbols: list[str] = []
        for position in range(length):
            payload = f"{seed}|{case_name}|{counter}|{position}".encode("utf-8")
            value = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
            symbols.append(FULL_ALPHABET[value % len(FULL_ALPHABET)])
        pattern = "".join(symbols)
        counter += 1
        if pattern in observed:
            continue
        observed.add(pattern)
        yield pattern


def prepare_branchsnv(branchsnv_root: Path):  # type: ignore[no-untyped-def]
    src = branchsnv_root.resolve() / "src"
    if not src.is_dir():
        raise SystemExit(f"BRANCHSNV source directory not found: {src}")
    sys.path.insert(0, str(src))
    import branchsnv  # pylint: disable=import-outside-toplevel
    from branchsnv.newick import parse_newick, select_exact_descendants
    from branchsnv.parsimony import compile_tree, reconstruct_site

    return branchsnv, parse_newick, select_exact_descendants, compile_tree, reconstruct_site


def ensure_production_case_matches_specification(
    case: TopologyCase,
    parse_newick,  # type: ignore[no-untyped-def]
    select_exact_descendants,  # type: ignore[no-untyped-def]
) -> object:
    tree = parse_newick(case.newick)
    production_tips = {tip.name for tip in tree.tips()}
    if production_tips != set(case.tips):
        raise RuntimeError(f"{case.name}: production parser tip set differs from specification")
    branch = select_exact_descendants(tree, set(case.focal_descendants))
    if set(branch.descendant_tips) != set(case.focal_descendants):
        raise RuntimeError(f"{case.name}: production branch differs from specification")
    return tree, branch


def write_tsv(path: Path, header: list[str], rows: Iterable[Iterable[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--branchsnv-root",
        type=Path,
        required=True,
        help="Path to a BRANCHSNV source checkout containing src/branchsnv.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory in which result files will be written.",
    )
    parser.add_argument(
        "--generated-per-case",
        type=int,
        default=5000,
        help="Unique deterministic full-alphabet patterns per non-small topology (default: 5000).",
    )
    parser.add_argument(
        "--seed",
        default="branchsnv-publication-validation-20260731",
        help="Text seed for deterministic generated patterns.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.generated_per_case < 0:
        raise SystemExit("--generated-per-case must be non-negative")
    output_dir: Path = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    branchsnv, parse_newick, select_exact_descendants, compile_tree, reconstruct_site = (
        prepare_branchsnv(args.branchsnv_root)
    )
    production_parsimony_path = args.branchsnv_root.resolve() / "src/branchsnv/parsimony.py"

    started = time.perf_counter()
    mismatches: list[tuple[object, ...]] = []
    counts: dict[str, CaseCounts] = {case.name: CaseCounts() for case in CASES}

    for case in CASES:
        tree, branch = ensure_production_case_matches_specification(
            case, parse_newick, select_exact_descendants
        )
        taxon_index = {name: index for index, name in enumerate(case.tips)}
        compiled = compile_tree(tree, branch.node, taxon_index)
        oracle = ExhaustiveOracle(case)

        suites: list[tuple[str, Iterable[str]]] = []
        if case.name == "small4_ambiguity_exhaustive":
            suites.append(
                ("ambiguity_exhaustive", exhaustive_patterns(FULL_ALPHABET, len(case.tips)))
            )
        else:
            suites.append(
                ("canonical_exhaustive", exhaustive_patterns(CANONICAL_ALPHABET, len(case.tips)))
            )
            suites.append(
                (
                    "generated",
                    deterministic_generated_patterns(
                        case.name,
                        len(case.tips),
                        args.generated_per_case,
                        args.seed,
                    ),
                )
            )

        for suite_name, patterns in suites:
            for pattern in patterns:
                expected_score, expected_pairs, expected_status = oracle.reconstruct(pattern)
                observed = reconstruct_site(compiled, pattern, gap="-", missing="?")
                case_counts = counts[case.name]
                setattr(case_counts, suite_name, getattr(case_counts, suite_name) + 1)
                case_counts.add_status(observed.status)
                if (
                    observed.score != expected_score
                    or observed.possible_pairs != expected_pairs
                    or observed.status != expected_status
                ):
                    case_counts.mismatches += 1
                    mismatches.append(
                        (
                            case.name,
                            suite_name,
                            pattern,
                            expected_score,
                            observed.score,
                            "|".join(f"{a}>{b}" for a, b in expected_pairs),
                            "|".join(f"{a}>{b}" for a, b in observed.possible_pairs),
                            expected_status,
                            observed.status,
                        )
                    )

    elapsed = time.perf_counter() - started
    total_comparisons = sum(item.total for item in counts.values())
    total_mismatches = sum(item.mismatches for item in counts.values())

    topology_rows = []
    for case in CASES:
        item = counts[case.name]
        topology_rows.append(
            (
                case.name,
                case.topology_type,
                case.branch_type,
                len(case.tips),
                ",".join(sorted(case.focal_descendants)),
                item.canonical_exhaustive,
                item.ambiguity_exhaustive,
                item.generated,
                item.total,
                item.mismatches,
                item.no_change,
                item.unambiguous_change,
                item.change_state_ambiguous,
                item.placement_ambiguous,
            )
        )

    write_tsv(
        output_dir / "topology_summary.tsv",
        [
            "case",
            "topology_type",
            "branch_type",
            "tip_count",
            "focal_descendants",
            "canonical_exhaustive_patterns",
            "ambiguity_exhaustive_patterns",
            "generated_patterns",
            "total_comparisons",
            "mismatches",
            "no_change",
            "unambiguous_change",
            "change_state_ambiguous",
            "placement_ambiguous",
        ],
        topology_rows,
    )
    write_tsv(
        output_dir / "mismatches.tsv",
        [
            "case",
            "suite",
            "pattern",
            "expected_score",
            "observed_score",
            "expected_pairs",
            "observed_pairs",
            "expected_status",
            "observed_status",
        ],
        mismatches,
    )

    status_totals = {
        status: sum(getattr(item, status) for item in counts.values())
        for status in (
            "no_change",
            "unambiguous_change",
            "change_state_ambiguous",
            "placement_ambiguous",
        )
    }
    write_tsv(
        output_dir / "status_summary.tsv",
        ["status", "comparisons"],
        ((status, count) for status, count in status_totals.items()),
    )

    summary = {
        "schema_version": 1,
        "experiment": "01_exact_oracle",
        "description": (
            "Independent exhaustive comparison of BRANCHSNV equal-cost unordered-state "
            "parsimony reconstruction against brute-force enumeration."
        ),
        "branchsnv_version": branchsnv.__version__,
        "branchsnv_parsimony_sha256": sha256_file(production_parsimony_path),
        "validation_script_sha256": sha256_file(Path(__file__).resolve()),
        "canonical_alphabet": CANONICAL_ALPHABET,
        "full_alphabet": FULL_ALPHABET,
        "seed": args.seed,
        "generated_per_non_small_case": args.generated_per_case,
        "topology_cases": len(CASES),
        "total_comparisons": total_comparisons,
        "total_mismatches": total_mismatches,
        "exact_agreement": total_mismatches == 0,
        "status_counts": status_totals,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    metadata = {
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 6),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "branchsnv_version": branchsnv.__version__,
        "exit_status": "PASS" if total_mismatches == 0 else "FAIL",
    }
    (output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(f"BRANCHSNV version: {branchsnv.__version__}")
    print(f"Topology cases: {len(CASES)}")
    print(f"Comparisons: {total_comparisons:,}")
    print(f"Mismatches: {total_mismatches:,}")
    print(f"Elapsed: {elapsed:.3f} s")
    print("PASS" if total_mismatches == 0 else "FAIL")
    return 0 if total_mismatches == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
