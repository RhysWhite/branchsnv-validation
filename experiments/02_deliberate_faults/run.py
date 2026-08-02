#!/usr/bin/env python3
"""Deliberate-fault validation for BRANCHSNV.

This experiment implements plausible but incorrect alternatives to BRANCHSNV's
ancestral reconstruction, branch selection, taxon mapping, and fixed-exclusive
classification rules. Each fault is challenged by exhaustive or deterministic
synthetic cases. The experiment succeeds only if every fault is distinguished
from the correct result by at least one permanent challenge.

The fault implementations are confined to this publication-validation
repository. BRANCHSNV production source is imported read-only and is never
modified.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import itertools
import json
import platform
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

CANONICAL = "ACGT"
CANONICAL_WITH_GAP = "ACGT-"
CANONICAL_WITH_MISSING = "ACGT?"


@dataclass
class FaultStats:
    fault_id: str
    category: str
    fault: str
    validation_principle: str
    compared_fields: str
    challenges: int = 0
    differentiating_challenges: int = 0
    first_witness: dict[str, Any] | None = field(default=None)

    @property
    def detected(self) -> bool:
        return self.differentiating_challenges > 0

    def evaluate(
        self,
        expected: Any,
        observed: Any,
        challenge: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.challenges += 1
        if expected == observed:
            return
        self.differentiating_challenges += 1
        if self.first_witness is None:
            witness: dict[str, Any] = {
                "challenge": challenge,
                "expected": normalise(expected),
                "faulted": normalise(observed),
            }
            if details:
                witness["details"] = normalise(details)
            self.first_witness = witness


def normalise(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): normalise(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [normalise(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(normalise(item) for item in value)
    if isinstance(value, Path):
        return str(value)
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_tsv(path: Path, header: list[str], rows: Iterable[Iterable[Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def load_experiment_one_module() -> Any:
    source = Path(__file__).resolve().parents[1] / "01_exact_oracle" / "run.py"
    spec = importlib.util.spec_from_file_location("branchsnv_exact_oracle", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load Experiment 1 oracle from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def prepare_branchsnv(branchsnv_root: Path) -> dict[str, Any]:
    src = branchsnv_root.resolve() / "src"
    if not src.is_dir():
        raise SystemExit(f"BRANCHSNV source directory not found: {src}")
    sys.path.insert(0, str(src))

    import branchsnv  # pylint: disable=import-outside-toplevel
    from branchsnv.errors import SelectionError  # pylint: disable=import-outside-toplevel
    from branchsnv.newick import (  # pylint: disable=import-outside-toplevel
        parse_newick,
        reroot_on_outgroup,
        select_exact_descendants,
        select_mrca_branch,
    )
    from branchsnv.parsimony import (  # pylint: disable=import-outside-toplevel
        compile_tree,
        reconstruct_site,
    )

    return {
        "module": branchsnv,
        "SelectionError": SelectionError,
        "parse_newick": parse_newick,
        "reroot_on_outgroup": reroot_on_outgroup,
        "select_exact_descendants": select_exact_descendants,
        "select_mrca_branch": select_mrca_branch,
        "compile_tree": compile_tree,
        "reconstruct_site": reconstruct_site,
    }


def classify_pairs(pairs: tuple[tuple[str, str], ...]) -> str:
    changes = tuple(parent != child for parent, child in pairs)
    if all(changes):
        return "unambiguous_change" if len(pairs) == 1 else "change_state_ambiguous"
    if any(changes):
        return "placement_ambiguous"
    return "no_change"


def result_record(score: int, pairs: tuple[tuple[str, str], ...], status: str) -> dict[str, Any]:
    return {
        "score": score,
        "possible_pairs": [f"{parent}>{child}" for parent, child in pairs],
        "status": status,
    }


def reverse_orientation_fault(
    score: int,
    pairs: tuple[tuple[str, str], ...],
) -> dict[str, Any]:
    reversed_pairs = tuple(sorted({(child, parent) for parent, child in pairs}))
    return result_record(score, reversed_pairs, classify_pairs(reversed_pairs))


def one_optimum_fault(
    score: int,
    pairs: tuple[tuple[str, str], ...],
) -> dict[str, Any]:
    retained = (pairs[0],)
    return result_record(score, retained, classify_pairs(retained))


def modal_state(pattern: str, positions: tuple[int, ...]) -> str:
    counts = {state: 0 for state in CANONICAL}
    for position in positions:
        counts[pattern[position]] += 1
    maximum = max(counts.values())
    return min(state for state, count in counts.items() if count == maximum)


def majority_state_fault(case: Any, pattern: str, expected_score: int) -> dict[str, Any]:
    descendant_positions = tuple(
        index for index, tip in enumerate(case.tips) if tip in case.focal_descendants
    )
    outside_positions = tuple(
        index for index, tip in enumerate(case.tips) if tip not in case.focal_descendants
    )
    parent = modal_state(pattern, outside_positions)
    child = modal_state(pattern, descendant_positions)
    pairs = ((parent, child),)
    return result_record(expected_score, pairs, classify_pairs(pairs))


def reconstruct_gap_as_fifth_state(case: Any, pattern: str) -> dict[str, Any]:
    """Faulted exhaustive reconstruction that treats '-' as an observed state."""

    states = tuple(CANONICAL_WITH_GAP)
    state_index = {state: index for index, state in enumerate(states)}
    tips = set(case.tips)
    internal_nodes = case.internal_nodes
    tip_position = {tip: index for index, tip in enumerate(case.tips)}
    focal_tip_position = tip_position.get(case.focal_child)

    best_score: int | None = None
    best_pairs: set[tuple[str, str]] = set()
    for values in itertools.product(range(len(states)), repeat=len(internal_nodes)):
        internal_state = dict(zip(internal_nodes, values))
        score = 0
        focal_parent = internal_state[case.focal_parent]
        focal_child_internal = (
            None if case.focal_child in tips else internal_state[case.focal_child]
        )

        for child, parent in case.parent:
            parent_state = internal_state[parent]
            if child in tips:
                child_state = state_index[pattern[tip_position[child]]]
            else:
                child_state = internal_state[child]
            score += int(parent_state != child_state)

        if best_score is not None and score > best_score:
            continue

        if focal_child_internal is None:
            assert focal_tip_position is not None
            focal_child_states = (state_index[pattern[focal_tip_position]],)
        else:
            focal_child_states = (focal_child_internal,)

        pairs = {(states[focal_parent], states[child]) for child in focal_child_states}
        if best_score is None or score < best_score:
            best_score = score
            best_pairs = pairs
        elif score == best_score:
            best_pairs.update(pairs)

    if best_score is None or not best_pairs:
        raise RuntimeError("Faulted five-state reconstruction found no solution")
    ordered = tuple(sorted(best_pairs))
    return result_record(best_score, ordered, classify_pairs(ordered))


def strict_fixed_exclusive(case: Any, pattern: str) -> bool:
    descendants = [
        pattern[index]
        for index, tip in enumerate(case.tips)
        if tip in case.focal_descendants
    ]
    outside = [
        pattern[index]
        for index, tip in enumerate(case.tips)
        if tip not in case.focal_descendants
    ]
    if not descendants or any(symbol not in CANONICAL for symbol in descendants):
        return False
    if len(set(descendants)) != 1:
        return False
    if any(symbol not in CANONICAL for symbol in outside):
        return False
    return descendants[0] not in outside


def lax_missing_outside_fault(case: Any, pattern: str) -> bool:
    descendants = [
        pattern[index]
        for index, tip in enumerate(case.tips)
        if tip in case.focal_descendants
    ]
    outside = [
        pattern[index]
        for index, tip in enumerate(case.tips)
        if tip not in case.focal_descendants
    ]
    if not descendants or any(symbol not in CANONICAL for symbol in descendants):
        return False
    if len(set(descendants)) != 1:
        return False
    observed_outside = [symbol for symbol in outside if symbol in CANONICAL]
    return descendants[0] not in observed_outside


def make_faults() -> dict[str, FaultStats]:
    definitions = (
        (
            "reverse_parent_child",
            "ancestral reconstruction",
            "Report child-to-parent state orientation on the selected edge.",
            "A rooted edge must be reported in the parent-to-child direction.",
            "score, possible state pairs, classification",
        ),
        (
            "majority_instead_of_parsimony",
            "ancestral reconstruction",
            "Infer one parent and child state from side-specific majority states.",
            "Local majority states cannot replace complete-tree parsimony reconstruction.",
            "possible state pairs, classification",
        ),
        (
            "gap_as_fifth_state",
            "state handling",
            "Treat the alignment gap character as a fifth evolutionary state.",
            "Configured gap and missing symbols must be treated as unknown nucleotide states.",
            "score, possible state pairs, classification",
        ),
        (
            "retain_one_optimum",
            "ancestral reconstruction",
            "Retain only the lexicographically first optimal state pair.",
            "Every focal-edge state pair occurring among global optima must be retained.",
            "possible state pairs, classification",
        ),
        (
            "opposite_branch_side",
            "branch selection",
            "Analyse the sibling clade rather than the requested focal clade.",
            "The exact requested descendant set must determine the analysed edge.",
            "score, possible state pairs, classification",
        ),
        (
            "ignore_outgroup_rooting",
            "rooting",
            "Use the Newick's existing root instead of the requested outgroup root.",
            "Branch membership and direction must be resolved after the requested rooting operation.",
            "branch-selection outcome",
        ),
        (
            "accept_mrca_superset",
            "branch selection",
            "Silently replace an exact descendant request with its MRCA branch.",
            "Exact descendant selection must reject requests whose MRCA contains additional tips.",
            "branch-selection outcome and selected descendants",
        ),
        (
            "match_taxa_by_column_order",
            "input mapping",
            "Map tree tips to alignment columns by position rather than taxon label.",
            "Tree and alignment taxa must be joined by exact names, independent of column order.",
            "score, possible state pairs, classification",
        ),
        (
            "allow_missing_outside_exclusive",
            "site classification",
            "Call a fixed-exclusive marker when outside taxa are missing but none observed share the state.",
            "Strict exclusivity requires every descendant and outside taxon to be callable.",
            "fixed-exclusive classification",
        ),
        (
            "equate_change_with_exclusive",
            "site classification",
            "Classify every unambiguous reconstructed branch change as fixed-exclusive.",
            "Fixed-exclusive markers and reconstructed substitutions are distinct definitions.",
            "fixed-exclusive classification",
        ),
    )
    return {
        item[0]: FaultStats(
            fault_id=item[0],
            category=item[1],
            fault=item[2],
            validation_principle=item[3],
            compared_fields=item[4],
        )
        for item in definitions
    }


def run_reconstruction_faults(exp1: Any, faults: dict[str, FaultStats], generated_per_case: int, seed: str) -> None:
    for case in exp1.CASES:
        oracle = exp1.ExhaustiveOracle(case)
        if case.name == "small4_ambiguity_exhaustive":
            suites: list[tuple[str, Iterable[str]]] = [
                ("all_supported_symbols", exp1.exhaustive_patterns(exp1.FULL_ALPHABET, len(case.tips)))
            ]
        else:
            suites = [
                ("canonical_exhaustive", exp1.exhaustive_patterns(CANONICAL, len(case.tips))),
                (
                    "deterministic_full_alphabet",
                    exp1.deterministic_generated_patterns(
                        case.name, len(case.tips), generated_per_case, seed
                    ),
                ),
            ]

        for suite_name, patterns in suites:
            for pattern in patterns:
                score, pairs, status = oracle.reconstruct(pattern)
                expected = result_record(score, pairs, status)
                challenge = f"{case.name}:{suite_name}:{pattern}"
                details = {
                    "topology": case.newick,
                    "focal_descendants": sorted(case.focal_descendants),
                    "tip_order": case.tips,
                    "pattern": pattern,
                }

                faults["reverse_parent_child"].evaluate(
                    expected,
                    reverse_orientation_fault(score, pairs),
                    challenge,
                    details,
                )
                faults["retain_one_optimum"].evaluate(
                    expected,
                    one_optimum_fault(score, pairs),
                    challenge,
                    details,
                )

                if all(symbol in CANONICAL for symbol in pattern):
                    faults["majority_instead_of_parsimony"].evaluate(
                        expected,
                        majority_state_fault(case, pattern, score),
                        challenge,
                        details,
                    )

    small_case = next(
        case for case in exp1.CASES if case.name == "small4_ambiguity_exhaustive"
    )
    oracle = exp1.ExhaustiveOracle(small_case)
    for pattern in exp1.exhaustive_patterns(CANONICAL_WITH_GAP, len(small_case.tips)):
        score, pairs, status = oracle.reconstruct(pattern)
        expected = result_record(score, pairs, status)
        faults["gap_as_fifth_state"].evaluate(
            expected,
            reconstruct_gap_as_fifth_state(small_case, pattern),
            f"{small_case.name}:gap_challenge:{pattern}",
            {
                "topology": small_case.newick,
                "focal_descendants": sorted(small_case.focal_descendants),
                "tip_order": small_case.tips,
                "pattern": pattern,
            },
        )


def run_opposite_side_fault(exp1: Any, production: dict[str, Any], faults: dict[str, FaultStats]) -> None:
    case = next(case for case in exp1.CASES if case.name == "balanced5_internal")
    oracle = exp1.ExhaustiveOracle(case)
    tree = production["parse_newick"](case.newick)
    wrong_branch = production["select_exact_descendants"](tree, {"C", "D"})
    taxon_index = {name: index for index, name in enumerate(case.tips)}
    wrong_compiled = production["compile_tree"](tree, wrong_branch.node, taxon_index)

    for pattern in exp1.exhaustive_patterns(CANONICAL, len(case.tips)):
        score, pairs, status = oracle.reconstruct(pattern)
        expected = result_record(score, pairs, status)
        wrong = production["reconstruct_site"](wrong_compiled, pattern, gap="-", missing="?")
        observed = result_record(wrong.score, wrong.possible_pairs, wrong.status)
        faults["opposite_branch_side"].evaluate(
            expected,
            observed,
            f"balanced5:AB_requested_CD_analysed:{pattern}",
            {
                "topology": case.newick,
                "requested_descendants": ["A", "B"],
                "faulted_descendants": ["C", "D"],
                "tip_order": case.tips,
                "pattern": pattern,
            },
        )


def run_rooting_fault(production: dict[str, Any], faults: dict[str, FaultStats]) -> None:
    challenges = (
        "((O,(C,D)),(A,B));",
        "((O,A),(B,(C,D)));",
        "(((A,B),O),(C,D));",
        "((A,(O,B)),(C,D));",
    )
    requested = {"A", "B", "C", "D"}
    selection_error = production["SelectionError"]

    for index, newick in enumerate(challenges, start=1):
        correct_tree = production["reroot_on_outgroup"](
            production["parse_newick"](newick), {"O"}
        )
        correct_branch = production["select_exact_descendants"](correct_tree, requested)
        expected = {
            "outcome": "selected",
            "descendants": list(correct_branch.descendant_tips),
        }

        try:
            wrong_tree = production["parse_newick"](newick)
            wrong_branch = production["select_exact_descendants"](wrong_tree, requested)
            observed: dict[str, Any] = {
                "outcome": "selected",
                "descendants": list(wrong_branch.descendant_tips),
            }
        except selection_error as exc:
            observed = {"outcome": "rejected", "error": str(exc)}

        faults["ignore_outgroup_rooting"].evaluate(
            expected,
            observed,
            f"rooting_case_{index}",
            {"newick": newick, "outgroup": ["O"], "requested_descendants": sorted(requested)},
        )


def run_mrca_fault(exp1: Any, production: dict[str, Any], faults: dict[str, FaultStats]) -> None:
    cases = (
        ("balanced5_internal", {"A", "C"}),
        ("pectinate6_internal", {"B", "D"}),
        ("multifurcating6_internal", {"A", "D"}),
    )
    selection_error = production["SelectionError"]

    for case_name, requested in cases:
        case = next(item for item in exp1.CASES if item.name == case_name)
        tree = production["parse_newick"](case.newick)
        try:
            production["select_exact_descendants"](tree, requested)
            expected: dict[str, Any] = {"outcome": "selected"}
        except selection_error as exc:
            expected = {"outcome": "rejected", "error_class": type(exc).__name__}

        mutant_branch = production["select_mrca_branch"](tree, requested)
        observed = {
            "outcome": "selected",
            "descendants": list(mutant_branch.descendant_tips),
        }
        faults["accept_mrca_superset"].evaluate(
            expected,
            observed,
            f"{case_name}:requested={','.join(sorted(requested))}",
            {
                "topology": case.newick,
                "requested_descendants": sorted(requested),
                "mrca_descendants": list(mutant_branch.descendant_tips),
            },
        )


def run_taxon_order_fault(exp1: Any, production: dict[str, Any], faults: dict[str, FaultStats]) -> None:
    case = next(case for case in exp1.CASES if case.name == "balanced5_internal")
    tree = production["parse_newick"](case.newick)
    branch = production["select_exact_descendants"](tree, set(case.focal_descendants))
    alignment_order = ("C", "O", "B", "D", "A")
    correct_index = {name: index for index, name in enumerate(alignment_order)}
    tree_tip_order = tuple(tip.name for tip in tree.tips())
    faulty_index = {name: index for index, name in enumerate(tree_tip_order)}
    correct_compiled = production["compile_tree"](tree, branch.node, correct_index)
    faulty_compiled = production["compile_tree"](tree, branch.node, faulty_index)

    biological_index = {name: index for index, name in enumerate(case.tips)}
    for biological_pattern in exp1.exhaustive_patterns(CANONICAL, len(case.tips)):
        alignment_pattern = "".join(
            biological_pattern[biological_index[name]] for name in alignment_order
        )
        correct = production["reconstruct_site"](
            correct_compiled, alignment_pattern, gap="-", missing="?"
        )
        wrong = production["reconstruct_site"](
            faulty_compiled, alignment_pattern, gap="-", missing="?"
        )
        expected = result_record(correct.score, correct.possible_pairs, correct.status)
        observed = result_record(wrong.score, wrong.possible_pairs, wrong.status)
        faults["match_taxa_by_column_order"].evaluate(
            expected,
            observed,
            f"permuted_alignment:{biological_pattern}",
            {
                "topology": case.newick,
                "tree_tip_order": tree_tip_order,
                "alignment_taxon_order": alignment_order,
                "biological_pattern_in_case_order": biological_pattern,
                "alignment_pattern": alignment_pattern,
                "focal_descendants": sorted(case.focal_descendants),
            },
        )


def run_classification_faults(exp1: Any, faults: dict[str, FaultStats]) -> None:
    internal_case = next(case for case in exp1.CASES if case.name == "balanced5_internal")

    for pattern in exp1.exhaustive_patterns(
        CANONICAL_WITH_MISSING, len(internal_case.tips)
    ):
        expected = strict_fixed_exclusive(internal_case, pattern)
        observed = lax_missing_outside_fault(internal_case, pattern)
        faults["allow_missing_outside_exclusive"].evaluate(
            expected,
            observed,
            f"fixed_exclusive_missing:{pattern}",
            {
                "topology": internal_case.newick,
                "tip_order": internal_case.tips,
                "focal_descendants": sorted(internal_case.focal_descendants),
                "pattern": pattern,
            },
        )

    terminal_case = next(case for case in exp1.CASES if case.name == "balanced5_terminal")
    terminal_oracle = exp1.ExhaustiveOracle(terminal_case)
    conflation_challenges: list[tuple[bool, str, bool, str]] = []
    for pattern in exp1.exhaustive_patterns(CANONICAL, len(terminal_case.tips)):
        expected = strict_fixed_exclusive(terminal_case, pattern)
        _score, _pairs, status = terminal_oracle.reconstruct(pattern)
        observed = status == "unambiguous_change"
        conflation_challenges.append((expected, pattern, observed, status))

    # Put false-positive calls first so the retained witness demonstrates the
    # principal interpretive risk: a reconstructed change need not be an
    # exclusive clade marker.
    conflation_challenges.sort(
        key=lambda item: (not (item[0] is False and item[2] is True), item[1])
    )
    for expected, pattern, observed, status in conflation_challenges:
        faults["equate_change_with_exclusive"].evaluate(
            expected,
            observed,
            f"definition_conflation:{pattern}",
            {
                "topology": terminal_case.newick,
                "tip_order": terminal_case.tips,
                "focal_descendants": sorted(terminal_case.focal_descendants),
                "pattern": pattern,
                "parsimony_status": status,
            },
        )


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
        help="Deterministic full-alphabet patterns per larger topology (default: 5000).",
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
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    exp1 = load_experiment_one_module()
    production = prepare_branchsnv(args.branchsnv_root)
    faults = make_faults()

    started_utc = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    run_reconstruction_faults(exp1, faults, args.generated_per_case, args.seed)
    run_opposite_side_fault(exp1, production, faults)
    run_rooting_fault(production, faults)
    run_mrca_fault(exp1, production, faults)
    run_taxon_order_fault(exp1, production, faults)
    run_classification_faults(exp1, faults)
    elapsed = time.perf_counter() - started

    ordered = list(faults.values())
    all_detected = all(item.detected for item in ordered)
    total_challenges = sum(item.challenges for item in ordered)
    total_differentiating = sum(item.differentiating_challenges for item in ordered)

    source_root = args.branchsnv_root.resolve() / "src" / "branchsnv"
    experiment_path = Path(__file__).resolve()
    exp1_path = experiment_path.parents[1] / "01_exact_oracle" / "run.py"
    summary = {
        "schema_version": 1,
        "experiment": "02_deliberate_faults",
        "branchsnv_version": production["module"].__version__,
        "faults_evaluated": len(ordered),
        "faults_detected": sum(item.detected for item in ordered),
        "all_faults_detected": all_detected,
        "total_challenges": total_challenges,
        "total_differentiating_challenges": total_differentiating,
        "generated_patterns_per_larger_topology": args.generated_per_case,
        "deterministic_seed": args.seed,
        "source_sha256": {
            "experiment_02_runner": sha256_file(experiment_path),
            "experiment_01_oracle": sha256_file(exp1_path),
            "branchsnv_parsimony": sha256_file(source_root / "parsimony.py"),
            "branchsnv_newick": sha256_file(source_root / "newick.py"),
            "branchsnv_analysis": sha256_file(source_root / "analysis.py"),
        },
        "faults": [
            {
                "fault_id": item.fault_id,
                "category": item.category,
                "fault": item.fault,
                "validation_principle": item.validation_principle,
                "compared_fields": item.compared_fields,
                "challenges": item.challenges,
                "differentiating_challenges": item.differentiating_challenges,
                "detected": item.detected,
                "first_witness": item.first_witness,
            }
            for item in ordered
        ],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )

    write_tsv(
        output_dir / "fault_summary.tsv",
        [
            "fault_id",
            "category",
            "fault",
            "validation_principle",
            "compared_fields",
            "challenges",
            "differentiating_challenges",
            "detection_fraction",
            "detected",
        ],
        (
            (
                item.fault_id,
                item.category,
                item.fault,
                item.validation_principle,
                item.compared_fields,
                item.challenges,
                item.differentiating_challenges,
                f"{item.differentiating_challenges / item.challenges:.9f}",
                str(item.detected).lower(),
            )
            for item in ordered
        ),
    )

    write_tsv(
        output_dir / "witnesses.tsv",
        ["fault_id", "category", "challenge", "expected_json", "faulted_json", "details_json"],
        (
            (
                item.fault_id,
                item.category,
                item.first_witness["challenge"] if item.first_witness else "",
                json.dumps(item.first_witness["expected"], sort_keys=True) if item.first_witness else "",
                json.dumps(item.first_witness["faulted"], sort_keys=True) if item.first_witness else "",
                json.dumps(item.first_witness.get("details", {}), sort_keys=True) if item.first_witness else "",
            )
            for item in ordered
        ),
    )

    metadata = {
        "experiment": "02_deliberate_faults",
        "started_utc": started_utc,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 6),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "branchsnv_root": str(args.branchsnv_root.resolve()),
        "output_dir": str(output_dir),
    }
    (output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )

    print(
        f"Evaluated {len(ordered)} deliberate faults across {total_challenges:,} challenges; "
        f"detected {sum(item.detected for item in ordered)}/{len(ordered)} faults."
    )
    for item in ordered:
        print(
            f"  {item.fault_id}: {item.differentiating_challenges:,}/"
            f"{item.challenges:,} differentiating challenges"
        )
    return 0 if all_detected else 1


if __name__ == "__main__":
    raise SystemExit(main())
