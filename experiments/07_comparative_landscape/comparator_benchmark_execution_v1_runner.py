#!/usr/bin/env python3
"""Truth-blind comparator benchmark runner v1.

Runner-v3 implementation.

This module deliberately contains no benchmark truth interface and no scoring
logic. Comparator-specific command construction and normalization are added
only through the frozen contracts authorized for runner-v3.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Mapping


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
IMPL = ROOT / "comparator_benchmark_execution_v1_impl"

sys.path.insert(0, str(IMPL))
import adapters  # noqa: E402


METHODS = (
    "ARPIP",
    "FastML",
    "HomoplasyFinder",
    "PAML",
    "PastML",
    "POUTINE",
    "SNPPar",
    "TreeTime",
)

AUTHORIZATION_ID = (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "RUNNER_IMPLEMENTATION_V3_001"
)

AUTHORIZATION_PATH = ROOT / (
    "comparator_benchmark_execution_v1_"
    "runner_implementation_v3_authorization.json"
)

ENVIRONMENT_RECIPES_PATH = (
    IMPL / "environment_recipes.json"
)

FROZEN_PATHS = {
    "adapters":
        IMPL / "adapters.py",

    "dataset_results_design":
        ROOT / (
            "comparator_benchmark_dataset_generation_v1_"
            "results_design.json"
        ),

    "dataset_results_sha256":
        ROOT / (
            "comparator_benchmark_dataset_generation_v1_"
            "results.sha256"
        ),

    "environment_recipes":
        IMPL / "environment_recipes.json",

    "method_matrix":
        ROOT / "comparator_benchmark_execution_v1_method_matrix.tsv",

    "metrics":
        IMPL / "metrics.py",

    "output_normalization_freeze":
        ROOT / (
            "comparator_benchmark_execution_v1_"
            "output_normalization_amendment_freeze.py"
        ),

    "output_normalization_manifest":
        ROOT / (
            "comparator_benchmark_execution_v1_"
            "output_normalization_amendment_manifest.json"
        ),

    "poutine_map_serialization_freeze":
        ROOT / (
            "comparator_benchmark_execution_v1_"
            "poutine_map_serialization_amendment_freeze.py"
        ),

    "poutine_map_serialization_manifest":
        ROOT / (
            "comparator_benchmark_execution_v1_"
            "poutine_map_serialization_amendment_manifest.json"
        ),

    "scenario_matrix":
        ROOT / "comparator_benchmark_execution_v1_scenario_matrix.tsv",

    "source_pins":
        IMPL / "source_pins.tsv",

    "toy_validation":
        IMPL / "toy_validation.py",

    "treetime_homoplasy_manifest":
        ROOT / (
            "comparator_benchmark_execution_v1_"
            "treetime_homoplasy_amendment_manifest.json"
        ),
}


class RunnerError(RuntimeError):
    """Fail-closed runner configuration or input error."""


@dataclass(frozen=True)
class ScenarioInputs:
    scenario_id: str
    alignment_fasta: Path
    tree_newick: Path
    reference_genbank: Path
    variable_positions: Path


RUNTIME_REQUIRED = {
    "ARPIP": {"executable"},
    "FastML": {"executable"},
    "HomoplasyFinder": {"java", "jar"},
    "PAML": {"executable"},
    "PastML": {"executable", "environment_dir"},
    "POUTINE": {"script", "environment_dir"},
    "SNPPar": {"executable", "environment_dir"},
    "TreeTime": {"executable", "environment_dir"},
}

RUNTIME_OPTIONAL = {
    "environment_dir",
    "source_dir",
    "build_dir",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


def verify_frozen_identities() -> dict[str, object]:
    if not AUTHORIZATION_PATH.is_file():
        raise RunnerError(
            "runner-v3 authorization file is absent"
        )

    authorization = json.loads(
        AUTHORIZATION_PATH.read_text()
    )

    if authorization.get("authorization_id") != AUTHORIZATION_ID:
        raise RunnerError(
            "runner-v3 authorization identity differs"
        )

    if authorization.get("status") != (
        "AUTHORIZED_NOT_YET_CONSUMED"
    ):
        raise RunnerError(
            "runner-v3 authorization status differs"
        )

    baseline = authorization.get("baseline_sha256")

    if not isinstance(baseline, dict):
        raise RunnerError(
            "runner-v3 authorization lacks baseline hashes"
        )

    if set(baseline) != set(FROZEN_PATHS):
        raise RunnerError(
            "runner-v3 frozen identity key set differs"
        )

    for name, path in FROZEN_PATHS.items():
        if not path.is_file():
            raise RunnerError(
                f"frozen artifact absent: {path}"
            )

        observed = sha256_file(path)
        expected = baseline[name]

        if observed != expected:
            raise RunnerError(
                "frozen artifact identity differs for "
                f"{name}: {observed} != {expected}"
            )

    return authorization


def load_frozen_environment_recipes() -> dict[str, object]:
    data = json.loads(
        ENVIRONMENT_RECIPES_PATH.read_text()
    )

    methods = data.get("methods")

    if not isinstance(methods, dict):
        raise RunnerError(
            "environment recipe file lacks methods mapping"
        )

    if set(methods) != set(METHODS):
        raise RunnerError(
            "frozen environment recipe method set differs"
        )

    return methods


def _contains_truth_component(path: Path) -> bool:
    return any(
        component.lower() == "truth"
        for component in path.parts
    )


def _existing_file(
    raw: object,
    *,
    field: str,
    executable: bool = False,
) -> Path:
    if not isinstance(raw, str) or not raw:
        raise RunnerError(
            f"{field} must be a non-empty absolute path"
        )

    path = Path(raw)

    if not path.is_absolute():
        raise RunnerError(
            f"{field} must be an absolute path"
        )

    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise RunnerError(
            f"{field} does not exist: {path}"
        ) from exc

    if not resolved.is_file():
        raise RunnerError(
            f"{field} is not a file: {resolved}"
        )

    if executable and not resolved.stat().st_mode & 0o111:
        raise RunnerError(
            f"{field} is not executable: {resolved}"
        )

    return resolved


def _existing_directory(
    raw: object,
    *,
    field: str,
) -> Path:
    if not isinstance(raw, str) or not raw:
        raise RunnerError(
            f"{field} must be a non-empty absolute path"
        )

    path = Path(raw)

    if not path.is_absolute():
        raise RunnerError(
            f"{field} must be an absolute path"
        )

    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise RunnerError(
            f"{field} does not exist: {path}"
        ) from exc

    if not resolved.is_dir():
        raise RunnerError(
            f"{field} is not a directory: {resolved}"
        )

    return resolved


def load_runtime_config(
    path: Path,
) -> dict[str, dict[str, str]]:
    if not path.is_file():
        raise RunnerError(
            f"runtime configuration absent: {path}"
        )

    raw = json.loads(path.read_text())

    if set(raw) != {"methods"}:
        raise RunnerError(
            "runtime configuration must contain only "
            "the top-level key 'methods'"
        )

    methods = raw["methods"]

    if not isinstance(methods, dict):
        raise RunnerError(
            "runtime configuration methods must be an object"
        )

    unknown_methods = set(methods) - set(METHODS)

    if unknown_methods:
        raise RunnerError(
            "runtime configuration contains unknown methods: "
            + ", ".join(sorted(unknown_methods))
        )

    normalized: dict[str, dict[str, str]] = {}

    for method, config in methods.items():
        if not isinstance(config, dict):
            raise RunnerError(
                f"runtime configuration for {method} "
                "must be an object"
            )

        required = RUNTIME_REQUIRED[method]
        allowed = required | RUNTIME_OPTIONAL

        missing = required - set(config)
        extra = set(config) - allowed

        if missing:
            raise RunnerError(
                f"runtime configuration for {method} "
                "is missing: "
                + ", ".join(sorted(missing))
            )

        if extra:
            raise RunnerError(
                f"runtime configuration for {method} "
                "has unexpected keys: "
                + ", ".join(sorted(extra))
            )

        resolved: dict[str, str] = {}

        for key, value in config.items():
            field = f"{method}.{key}"

            if key in {
                "environment_dir",
                "source_dir",
                "build_dir",
            }:
                resolved[key] = str(
                    _existing_directory(
                        value,
                        field=field,
                    )
                )

            elif key == "jar":
                resolved[key] = str(
                    _existing_file(
                        value,
                        field=field,
                    )
                )

            else:
                resolved[key] = str(
                    _existing_file(
                        value,
                        field=field,
                        executable=True,
                    )
                )

        normalized[method] = resolved

    return normalized


def _validate_scenario_id(
    scenario_id: str,
) -> None:
    if not re.fullmatch(
        r"[A-Za-z0-9_.-]+",
        scenario_id,
    ):
        raise RunnerError(
            "scenario id contains unsupported characters"
        )


def scenario_inputs_from_directory(
    scenario_id: str,
    directory: Path,
) -> ScenarioInputs:
    _validate_scenario_id(scenario_id)

    try:
        directory = directory.resolve(strict=True)
    except FileNotFoundError as exc:
        raise RunnerError(
            f"scenario directory does not exist: {directory}"
        ) from exc

    if not directory.is_dir():
        raise RunnerError(
            f"scenario input is not a directory: {directory}"
        )

    if _contains_truth_component(directory):
        raise RunnerError(
            "scenario input directory is inside a truth path"
        )

    required = {
        "alignment_fasta":
            directory / "alignment.fasta",
        "tree_newick":
            directory / "tree.nwk",
        "reference_genbank":
            directory / "reference.gb",
        "variable_positions":
            directory / "variable_positions.txt",
    }

    resolved: dict[str, Path] = {}

    for name, path in required.items():
        try:
            item = path.resolve(strict=True)
        except FileNotFoundError as exc:
            raise RunnerError(
                f"missing comparator-facing input: {path.name}"
            ) from exc

        if not item.is_file():
            raise RunnerError(
                f"comparator-facing input is not a file: {item}"
            )

        if _contains_truth_component(item):
            raise RunnerError(
                "truth path supplied as comparator-facing input"
            )

        resolved[name] = item

    return ScenarioInputs(
        scenario_id=scenario_id,
        **resolved,
    )


def read_variable_positions(
    path: Path,
) -> list[int]:
    positions: list[int] = []

    for raw in path.read_text().splitlines():
        value = raw.strip()

        if not value:
            continue

        try:
            position = int(value)
        except ValueError as exc:
            raise RunnerError(
                f"invalid variable position: {value!r}"
            ) from exc

        if position < 1:
            raise RunnerError(
                "variable positions must be positive"
            )

        positions.append(position)

    if len(set(positions)) != len(positions):
        raise RunnerError(
            "variable positions contain duplicates"
        )

    return positions


def validate_scenario_inputs(
    inputs: ScenarioInputs,
) -> dict[str, object]:
    sequences = adapters.read_fasta(
        inputs.alignment_fasta
    )

    if len(sequences) < 2:
        raise RunnerError(
            "alignment must contain at least two tips"
        )

    lengths = {
        len(sequence)
        for sequence in sequences.values()
    }

    if len(lengths) != 1:
        raise RunnerError(
            "alignment sequence lengths differ"
        )

    sequence_length = next(iter(lengths))

    if sequence_length < 1:
        raise RunnerError(
            "alignment sequences are empty"
        )

    tree_text = inputs.tree_newick.read_text()

    try:
        descendants = adapters.node_descendant_tips(
            tree_text
        )
    except ValueError as exc:
        raise RunnerError(
            f"invalid benchmark tree: {exc}"
        ) from exc

    tree_tips = {
        tips[0]
        for tips in descendants.values()
        if len(tips) == 1
    }

    if tree_tips != set(sequences):
        raise RunnerError(
            "alignment tips and tree tips differ"
        )

    positions = read_variable_positions(
        inputs.variable_positions
    )

    if any(
        position > sequence_length
        for position in positions
    ):
        raise RunnerError(
            "variable position lies outside alignment"
        )

    if not inputs.reference_genbank.read_text().strip():
        raise RunnerError(
            "reference GenBank input is empty"
        )

    return {
        "scenario_id": inputs.scenario_id,
        "tip_count": len(sequences),
        "alignment_length": sequence_length,
        "variable_positions": positions,
        "sequences": sequences,
        "tree_text": tree_text,
    }


def assert_new_result_root(
    path: Path,
) -> Path:
    if path.exists():
        raise RunnerError(
            "requested result root already exists: "
            f"{path}"
        )

    parent = path.parent.resolve(strict=True)

    if _contains_truth_component(parent):
        raise RunnerError(
            "result root may not be created inside a truth path"
        )

    return parent / path.name


# ---------------------------------------------------------------------------
# Runner-v3 stage 2: frozen command-plan construction only.
# No comparator execution occurs in this section.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CommandPlan:
    method: str
    scenario_id: str
    scenario_seed: int
    argv: tuple[str, ...]
    cwd: Path
    plan_root: Path
    generated_dir: Path
    native_dir: Path
    required_output_patterns: tuple[str, ...]
    frozen_run_contract: str


def _require_projected_positions(
    method: str,
    positions: list[int],
) -> None:
    if method in {"PastML", "POUTINE", "SNPPar"} and not positions:
        raise RunnerError(
            f"{method} requires at least one projected variable position"
        )


def build_command_plan(
    *,
    method: str,
    inputs: ScenarioInputs,
    runtime_config: Mapping[str, Mapping[str, str]],
    plan_root: Path,
    scenario_seed: int,
) -> CommandPlan:
    if method not in METHODS:
        raise RunnerError(
            f"unknown comparator method: {method}"
        )

    if method not in runtime_config:
        raise RunnerError(
            f"runtime configuration lacks requested method: {method}"
        )

    if (
        isinstance(scenario_seed, bool)
        or not isinstance(scenario_seed, int)
        or scenario_seed < 0
    ):
        raise RunnerError(
            "scenario seed must be a non-negative integer"
        )

    validated = validate_scenario_inputs(inputs)

    sequences = validated["sequences"]
    positions = validated["variable_positions"]
    tree_text = validated["tree_text"]

    assert isinstance(sequences, dict)
    assert isinstance(positions, list)
    assert isinstance(tree_text, str)

    _require_projected_positions(
        method,
        positions,
    )

    plan_root = assert_new_result_root(
        plan_root
    )

    plan_root.mkdir()

    generated_dir = plan_root / "generated"
    native_dir = plan_root / "native"

    generated_dir.mkdir()
    native_dir.mkdir()

    runtime = runtime_config[method]
    _assert_runtime_truth_blind(runtime)
    recipes = load_frozen_environment_recipes()
    recipe = recipes[method]

    if not isinstance(recipe, dict):
        raise RunnerError(
            f"frozen recipe for {method} is malformed"
        )

    argv: list[str]
    cwd = native_dir

    if method == "ARPIP":
        config = generated_dir / "arpip.params"

        config.write_text(
            adapters.arpip_config_text(
                str(inputs.alignment_fasta),
                str(inputs.tree_newick),
                str(native_dir),
                scenario_seed,
            )
        )

        argv = [
            runtime["executable"],
            f"params={config}",
        ]

        required_outputs = (
            "anc.fasta",
            "tree.nwk",
            "node_rel.txt",
        )

        frozen_contract = recipe["run_contract"]

    elif method == "FastML":
        argv = [
            runtime["executable"],
            "-s",
            str(inputs.alignment_fasta),
            "-mn",
            "-qf",
            "-t",
            str(inputs.tree_newick),
            "-b",
        ]

        required_outputs = (
            "seq.joint.txt",
            "tree.newick.txt",
        )

        frozen_contract = recipe["run_contract"]

    elif method == "HomoplasyFinder":
        argv = [
            runtime["java"],
            "-jar",
            runtime["jar"],
            "--fasta",
            str(inputs.alignment_fasta),
            "--tree",
            str(inputs.tree_newick),
        ]

        required_outputs = (
            "consistencyIndexReport_*.txt",
        )

        frozen_contract = recipe["run_contract"]

    elif method == "PAML":
        phylip = generated_dir / "alignment.phy"
        paml_tree = generated_dir / "tree.nwk"
        control = generated_dir / "baseml.ctl"

        phylip.write_text(
            adapters.paml_phylip_text(
                sequences
            )
        )

        paml_tree.write_text(
            adapters.paml_tree_text(
                tree_text,
                len(sequences),
            )
        )

        control.write_text(
            adapters.paml_baseml_ctl_text(
                str(phylip),
                str(paml_tree),
                str(native_dir / "main.out"),
            )
        )

        argv = [
            runtime["executable"],
            str(control),
        ]

        required_outputs = (
            "rst",
            "main.out",
        )

        frozen_contract = recipe["run_contract"]

    elif method == "PastML":
        table = generated_dir / "states.tsv"

        table.write_text(
            adapters.pastml_table_text(
                sequences,
                positions,
            )
        )

        site_columns = [
            f"site_{position}"
            for position in positions
        ]

        argv = [
            runtime["executable"],
            "--tree",
            str(inputs.tree_newick),
            "--data",
            str(table),
            "--columns",
            *site_columns,
            "--data_sep",
            "\t",
            "--out_data",
            str(
                native_dir
                / "reconstructed_states.tsv"
            ),
            "--work_dir",
            str(native_dir),
        ]

        required_outputs = (
            "reconstructed_states.tsv",
            "named.tree_tree.nwk",
        )

        frozen_contract = recipe["run_contract"]

    elif method == "POUTINE":
        variant_fasta = (
            generated_dir / "variants.fasta"
        )
        phenotype = (
            generated_dir / "phenotypes.tsv"
        )
        physical_map = (
            generated_dir / "positions.map"
        )

        variant_fasta.write_text(
            adapters.poutine_variant_fasta_text(
                sequences,
                positions,
            )
        )

        phenotype.write_text(
            adapters.poutine_dummy_phenotype_text(
                sequences,
            )
        )

        physical_map.write_text(
            adapters.poutine_physical_positions_map_text(
                positions,
            )
        )

        # poutine.sh uses relative Java classpath entries under
        # ./compiled. Preserve an isolated method/scenario cwd by
        # exposing that frozen runtime directory through a symlink.
        compiled_source = (
            Path(runtime["script"]).parent
            / "compiled"
        )

        if not compiled_source.is_dir():
            raise RunnerError(
                "POUTINE compiled runtime directory is absent: "
                f"{compiled_source}"
            )

        compiled_link = (
            native_dir
            / "compiled"
        )

        if compiled_link.exists() or compiled_link.is_symlink():
            raise RunnerError(
                "POUTINE compiled runtime link unexpectedly exists"
            )

        compiled_link.symlink_to(
            compiled_source,
            target_is_directory=True,
        )

        argv = [
            runtime["script"],
            "--fasta",
            str(variant_fasta),
            "--phenos",
            str(phenotype),
            "--tree",
            str(inputs.tree_newick),
            "--map",
            str(physical_map),
            "--replicates",
            "10",
            "--min_hcount",
            "0",
            "--threads",
            "1",
            "--out-dir",
            str(native_dir),
            "--out",
            "poutine.out",
            "--log",
            "poutine.log",
            "--anc-recon-out-dir",
            "ancestral_reconstruction",
        ]

        required_outputs = (
            "poutine.out",
        )

        frozen_contract = recipe["run_contract"]

    elif method == "SNPPar":
        mfasta = (
            generated_dir / "snps.fasta"
        )
        position_file = (
            generated_dir / "positions.txt"
        )

        mfasta.write_text(
            adapters.snppar_mfasta_text(
                sequences,
                positions,
            )
        )

        position_file.write_text(
            adapters.positions_text(
                positions
            )
        )

        argv = [
            runtime["executable"],
            "-m",
            str(mfasta),
            "-l",
            str(position_file),
            "-t",
            str(inputs.tree_newick),
            "-g",
            str(inputs.reference_genbank),
            "-d",
            str(native_dir),
            "-A",
            "-i",
        ]

        required_outputs = (
            "all_mutation_events.tsv",
            "homoplasic_events_all_calls.tsv",
            "node_labelled_newick.tre",
        )

        frozen_contract = recipe["run_contract"]

    elif method == "TreeTime":
        argv = [
            runtime["executable"],
            "ancestral",
            "--aln",
            str(inputs.alignment_fasta),
            "--tree",
            str(inputs.tree_newick),
            "--gtr",
            "JC69",
            "--method-anc",
            "probabilistic",
            "--rng-seed",
            str(scenario_seed),
            "--outdir",
            str(native_dir),
        ]

        required_outputs = (
            "ancestral_sequences.fasta",
            "annotated_tree.nexus",
        )

        frozen_contract = recipe[
            "run_contract_branch"
        ]

    else:
        raise AssertionError(
            "unreachable comparator dispatch"
        )

    if not isinstance(
        frozen_contract,
        str,
    ):
        raise RunnerError(
            f"frozen run contract for {method} is malformed"
        )

    return CommandPlan(
        method=method,
        scenario_id=inputs.scenario_id,
        scenario_seed=scenario_seed,
        argv=tuple(argv),
        cwd=native_dir,
        plan_root=plan_root,
        generated_dir=generated_dir,
        native_dir=native_dir,
        required_output_patterns=tuple(
            required_outputs
        ),
        frozen_run_contract=frozen_contract,
    )


# ---------------------------------------------------------------------------
# Runner-v3 stage 3: native-output validation and frozen normalization only.
# No comparator execution and no truth scoring occur in this section.
# ---------------------------------------------------------------------------


def required_native_outputs(
    plan: CommandPlan,
) -> dict[str, Path]:
    outputs: dict[str, Path] = {}

    for pattern in plan.required_output_patterns:
        matches = sorted(
            path
            for path in plan.native_dir.glob(pattern)
            if path.is_file()
        )

        if len(matches) != 1:
            raise RunnerError(
                f"{plan.method}: expected exactly one native output "
                f"matching {pattern!r}; observed "
                f"{[path.name for path in matches]!r}"
            )

        path = matches[0]

        if path.stat().st_size == 0:
            raise RunnerError(
                f"{plan.method}: required native output is empty: "
                f"{path.name}"
            )

        outputs[pattern] = path

    return outputs


def _sorted_branch_events(
    events: list[dict[str, str]],
) -> list[dict[str, str]]:
    return sorted(
        (dict(event) for event in events),
        key=lambda event: (
            int(event["position"]),
            event["edge_id"],
            event["ancestral_state"],
            event["derived_state"],
        ),
    )


def _sorted_recurrent_sites(
    sites: list[dict[str, str]],
) -> list[dict[str, str]]:
    return sorted(
        (dict(site) for site in sites),
        key=lambda site: (
            int(site["position"]),
            site.get(
                "reported_recurrence_count_if_available",
                "",
            ),
        ),
    )


def _validate_normalized_branch_events(
    *,
    plan: CommandPlan,
    benchmark_tree: str,
    alignment_length: int,
    events: list[dict[str, str]],
) -> None:
    valid_edges = set(
        adapters.canonical_edge_ids_by_node(
            benchmark_tree
        ).values()
    )

    required = {
        "scenario_id",
        "method",
        "edge_id",
        "position",
        "ancestral_state",
        "derived_state",
    }

    for event in events:
        if set(event) != required:
            raise RunnerError(
                f"{plan.method}: normalized branch-event "
                "schema differs"
            )

        if event["scenario_id"] != plan.scenario_id:
            raise RunnerError(
                f"{plan.method}: normalized branch event "
                "has incorrect scenario identity"
            )

        if event["method"] != plan.method:
            raise RunnerError(
                f"{plan.method}: normalized branch event "
                "has incorrect method identity"
            )

        if event["edge_id"] not in valid_edges:
            raise RunnerError(
                f"{plan.method}: normalized branch event "
                "does not use benchmark canonical edge identity"
            )

        try:
            position = int(event["position"])
        except ValueError as exc:
            raise RunnerError(
                f"{plan.method}: normalized branch event "
                "has non-integer position"
            ) from exc

        if not 1 <= position <= alignment_length:
            raise RunnerError(
                f"{plan.method}: normalized branch event "
                "position lies outside alignment"
            )

        if event["ancestral_state"] not in "ACGT":
            raise RunnerError(
                f"{plan.method}: normalized branch event "
                "has invalid ancestral state"
            )

        if event["derived_state"] not in "ACGT":
            raise RunnerError(
                f"{plan.method}: normalized branch event "
                "has invalid derived state"
            )

        if event["ancestral_state"] == event["derived_state"]:
            raise RunnerError(
                f"{plan.method}: normalized branch event "
                "does not change state"
            )


def _validate_normalized_recurrent_sites(
    *,
    plan: CommandPlan,
    alignment_length: int,
    sites: list[dict[str, str]],
) -> None:
    required = {
        "position",
        "reported_recurrence_count_if_available",
    }

    seen: set[int] = set()

    for site in sites:
        if set(site) != required:
            raise RunnerError(
                f"{plan.method}: normalized recurrent-site "
                "schema differs"
            )

        try:
            position = int(site["position"])
        except ValueError as exc:
            raise RunnerError(
                f"{plan.method}: normalized recurrent site "
                "has non-integer position"
            ) from exc

        if not 1 <= position <= alignment_length:
            raise RunnerError(
                f"{plan.method}: normalized recurrent site "
                "position lies outside alignment"
            )

        if position in seen:
            raise RunnerError(
                f"{plan.method}: duplicate normalized "
                "recurrent-site position"
            )

        seen.add(position)

        count = site[
            "reported_recurrence_count_if_available"
        ]

        if count:
            try:
                parsed_count = int(count)
            except ValueError as exc:
                raise RunnerError(
                    f"{plan.method}: normalized recurrence "
                    "count is not an integer"
                ) from exc

            if parsed_count < 2:
                raise RunnerError(
                    f"{plan.method}: normalized recurrent "
                    "site has recurrence count below two"
                )


def normalize_native_outputs(
    *,
    plan: CommandPlan,
    inputs: ScenarioInputs,
) -> dict[str, object]:
    if plan.method not in METHODS:
        raise RunnerError(
            f"unknown comparator method: {plan.method}"
        )

    if plan.scenario_id != inputs.scenario_id:
        raise RunnerError(
            "command-plan and scenario identities differ"
        )

    validated = validate_scenario_inputs(
        inputs
    )

    sequences = validated["sequences"]
    positions = validated["variable_positions"]
    benchmark_tree = validated["tree_text"]
    alignment_length = validated["alignment_length"]

    assert isinstance(sequences, dict)
    assert isinstance(positions, list)
    assert isinstance(benchmark_tree, str)
    assert isinstance(alignment_length, int)

    outputs = required_native_outputs(
        plan
    )

    branch_events: list[dict[str, str]] = []
    recurrent_sites: list[dict[str, str]] = []

    try:
        if plan.method == "ARPIP":
            ancestral_text = outputs[
                "anc.fasta"
            ].read_text()

            arpip_tree = outputs[
                "tree.nwk"
            ].read_text()

            mapped_sequences = (
                adapters.arpip_node_sequences_for_tree(
                    ancestral_text,
                    arpip_tree,
                    benchmark_tree,
                    sequences,
                )
            )

            branch_events = (
                adapters.events_from_node_sequences(
                    benchmark_tree,
                    mapped_sequences,
                    method="ARPIP",
                    scenario_id=plan.scenario_id,
                )
            )

        elif plan.method == "FastML":
            joint_text = outputs[
                "seq.joint.txt"
            ].read_text()

            fastml_tree = outputs[
                "tree.newick.txt"
            ].read_text()

            mapped_sequences = (
                adapters.fastml_node_sequences_for_tree(
                    joint_text,
                    fastml_tree,
                    benchmark_tree,
                )
            )

            branch_events = (
                adapters.events_from_node_sequences(
                    benchmark_tree,
                    mapped_sequences,
                    method="FastML",
                    scenario_id=plan.scenario_id,
                )
            )

        elif plan.method == "HomoplasyFinder":
            report = outputs[
                "consistencyIndexReport_*.txt"
            ].read_text()

            recurrent_sites = (
                adapters.parse_homoplasyfinder_report(
                    report
                )
            )

        elif plan.method == "PAML":
            rst_text = outputs[
                "rst"
            ].read_text()

            mapped_sequences = (
                adapters.paml_node_sequences_for_tree(
                    rst_text,
                    benchmark_tree,
                )
            )

            branch_events = (
                adapters.events_from_node_sequences(
                    benchmark_tree,
                    mapped_sequences,
                    method="PAML",
                    scenario_id=plan.scenario_id,
                )
            )

        elif plan.method == "PastML":
            state_text = outputs[
                "reconstructed_states.tsv"
            ].read_text()

            pastml_tree = outputs[
                "named.tree_tree.nwk"
            ].read_text()

            projected_sequences = (
                adapters.parse_tabular_node_states(
                    state_text,
                    positions,
                )
            )

            mapped_sequences = (
                adapters.map_node_sequences_by_descendant_tips(
                    pastml_tree,
                    benchmark_tree,
                    projected_sequences,
                )
            )

            branch_events = (
                adapters.events_from_projected_node_sequences(
                    benchmark_tree,
                    mapped_sequences,
                    positions,
                    method="PastML",
                    scenario_id=plan.scenario_id,
                )
            )

        elif plan.method == "POUTINE":
            recurrent_sites = (
                adapters.parse_poutine_result(
                    outputs[
                        "poutine.out"
                    ].read_text()
                )
            )

        elif plan.method == "SNPPar":
            output_tree = outputs[
                "node_labelled_newick.tre"
            ].read_text()

            all_events = (
                adapters.parse_snppar_mutation_events(
                    outputs[
                        "all_mutation_events.tsv"
                    ].read_text(),
                    output_tree,
                    scenario_id=plan.scenario_id,
                )
            )

            homoplasic_events = (
                adapters.parse_snppar_mutation_events(
                    outputs[
                        "homoplasic_events_all_calls.tsv"
                    ].read_text(),
                    output_tree,
                    scenario_id=plan.scenario_id,
                )
            )

            branch_events = all_events

            recurrent_sites = (
                adapters.snppar_recurrent_sites_from_branch_events(
                    homoplasic_events
                )
            )

        elif plan.method == "TreeTime":
            source_sequences = adapters.read_fasta(
                outputs[
                    "ancestral_sequences.fasta"
                ]
            )

            source_tree = outputs[
                "annotated_tree.nexus"
            ].read_text()

            mapped_sequences = (
                adapters.map_node_sequences_by_descendant_tips(
                    source_tree,
                    benchmark_tree,
                    source_sequences,
                )
            )

            branch_events = (
                adapters.events_from_node_sequences(
                    benchmark_tree,
                    mapped_sequences,
                    method="TreeTime",
                    scenario_id=plan.scenario_id,
                )
            )

            recurrent_sites = (
                adapters.treetime_recurrent_sites_from_branch_events(
                    branch_events
                )
            )

        else:
            raise AssertionError(
                "unreachable normalization dispatch"
            )

    except ValueError as exc:
        raise RunnerError(
            f"{plan.method}: native-output "
            f"normalization failed: {exc}"
        ) from exc

    branch_events = _sorted_branch_events(
        branch_events
    )

    recurrent_sites = _sorted_recurrent_sites(
        recurrent_sites
    )

    _validate_normalized_branch_events(
        plan=plan,
        benchmark_tree=benchmark_tree,
        alignment_length=alignment_length,
        events=branch_events,
    )

    _validate_normalized_recurrent_sites(
        plan=plan,
        alignment_length=alignment_length,
        sites=recurrent_sites,
    )

    return {
        "schema_version": 1,
        "scenario_id": plan.scenario_id,
        "method": plan.method,
        "branch_events": branch_events,
        "recurrent_sites": recurrent_sites,
    }


# ---------------------------------------------------------------------------
# Runner-v3 stage 4: generic process execution and prediction finalization.
#
# Scientific command construction and normalization remain in the frozen
# stage-2/stage-3 paths above. This layer performs only execution,
# completion-state recording and artifact preservation.
# ---------------------------------------------------------------------------


import os
import signal
import subprocess
import time
from typing import Callable


INHERITED_ENV_ALLOWLIST = {
    "HOME",
    "PATH",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TMPDIR",
    "TEMP",
    "TMP",
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
    "JAVA_HOME",
}


@dataclass(frozen=True)
class ExecutionOutcome:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool = False


Executor = Callable[
    [CommandPlan, Mapping[str, str], float],
    ExecutionOutcome,
]


def _assert_runtime_truth_blind(
    runtime: Mapping[str, str],
) -> None:
    for key, value in runtime.items():
        if "truth" in key.lower():
            raise RunnerError(
                f"truth-like runtime field is forbidden: {key}"
            )

        try:
            candidate = Path(value)
        except TypeError:
            continue

        if candidate.is_absolute() and _contains_truth_component(
            candidate
        ):
            raise RunnerError(
                f"truth path supplied as runtime field: {key}"
            )


def _environment_value_contains_truth_path(
    value: str,
) -> bool:
    for component in value.split(os.pathsep):
        if not component:
            continue

        candidate = Path(component)

        if candidate.is_absolute() and _contains_truth_component(
            candidate
        ):
            return True

    return False


def build_subprocess_environment(
    *,
    plan: CommandPlan,
    runtime_config: Mapping[str, Mapping[str, str]],
) -> dict[str, str]:
    if plan.method not in runtime_config:
        raise RunnerError(
            f"runtime configuration lacks {plan.method}"
        )

    runtime = runtime_config[plan.method]
    _assert_runtime_truth_blind(runtime)

    environment = {
        key: value
        for key, value in os.environ.items()
        if key in INHERITED_ENV_ALLOWLIST
        and "truth" not in key.lower()
    }

    recipes = load_frozen_environment_recipes()
    recipe = recipes[plan.method]

    if not isinstance(recipe, dict):
        raise RunnerError(
            f"frozen recipe for {plan.method} is malformed"
        )

    frozen_environment = recipe.get(
        "environment",
        {},
    )

    if not isinstance(
        frozen_environment,
        dict,
    ):
        raise RunnerError(
            f"frozen environment for {plan.method} is malformed"
        )

    for key, value in frozen_environment.items():
        if not isinstance(key, str):
            raise RunnerError(
                f"frozen environment key for {plan.method} "
                "is not a string"
            )

        if "truth" in key.lower():
            raise RunnerError(
                f"truth-like frozen environment key: {key}"
            )

        environment[key] = str(value)

    environment_dir = runtime.get(
        "environment_dir"
    )

    if environment_dir is not None:
        bin_dir = (
            Path(environment_dir)
            / "bin"
        )

        if not bin_dir.is_dir():
            raise RunnerError(
                f"{plan.method}: environment bin directory absent: "
                f"{bin_dir}"
            )

        inherited_path = environment.get(
            "PATH",
            "",
        )

        environment["PATH"] = (
            str(bin_dir)
            if not inherited_path
            else str(bin_dir)
            + os.pathsep
            + inherited_path
        )

    for key, value in environment.items():
        if "truth" in key.lower():
            raise RunnerError(
                f"truth-like subprocess environment key: {key}"
            )

        if _environment_value_contains_truth_path(
            value
        ):
            raise RunnerError(
                f"truth path entered subprocess environment: {key}"
            )

    return environment


def _coerce_stream(
    value: object,
) -> str:
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode(
            "utf-8",
            errors="replace",
        )

    return str(value)


def default_executor(
    plan: CommandPlan,
    environment: Mapping[str, str],
    timeout_seconds: float,
) -> ExecutionOutcome:
    try:
        process = subprocess.Popen(
            list(plan.argv),
            cwd=plan.cwd,
            env=dict(environment),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except OSError:
        raise

    try:
        stdout, stderr = process.communicate(
            timeout=timeout_seconds
        )

        return ExecutionOutcome(
            returncode=process.returncode,
            stdout=_coerce_stream(stdout),
            stderr=_coerce_stream(stderr),
            timed_out=False,
        )

    except subprocess.TimeoutExpired:
        try:
            os.killpg(
                process.pid,
                signal.SIGTERM,
            )
        except ProcessLookupError:
            pass

        try:
            stdout, stderr = process.communicate(
                timeout=5.0
            )
        except subprocess.TimeoutExpired:
            try:
                os.killpg(
                    process.pid,
                    signal.SIGKILL,
                )
            except ProcessLookupError:
                pass

            stdout, stderr = process.communicate()

        return ExecutionOutcome(
            returncode=process.returncode,
            stdout=_coerce_stream(stdout),
            stderr=_coerce_stream(stderr),
            timed_out=True,
        )


def _json_text(
    value: object,
) -> str:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _write_json(
    path: Path,
    value: object,
) -> None:
    path.write_text(
        _json_text(value)
    )


def native_output_manifest(
    directory: Path,
) -> list[dict[str, object]]:
    files = sorted(
        (
            path
            for path in directory.rglob("*")
            if path.is_file()
        ),
        key=lambda path:
            path.relative_to(
                directory
            ).as_posix(),
    )

    return [
        {
            "path":
                path.relative_to(
                    directory
                ).as_posix(),
            "size_bytes":
                path.stat().st_size,
            "sha256":
                sha256_file(path),
        }
        for path in files
    ]


def scenario_input_manifest(
    inputs: ScenarioInputs,
) -> dict[str, dict[str, object]]:
    mapping = {
        "alignment.fasta":
            inputs.alignment_fasta,
        "tree.nwk":
            inputs.tree_newick,
        "reference.gb":
            inputs.reference_genbank,
        "variable_positions.txt":
            inputs.variable_positions,
    }

    return {
        name: {
            "path":
                str(path),
            "size_bytes":
                path.stat().st_size,
            "sha256":
                sha256_file(path),
        }
        for name, path in mapping.items()
    }


def runtime_manifest(
    runtime: Mapping[str, str],
) -> dict[str, object]:
    result: dict[str, object] = {}

    for key, raw in sorted(
        runtime.items()
    ):
        path = Path(raw)

        entry: dict[str, object] = {
            "path": str(path),
        }

        if path.is_file():
            entry["sha256"] = (
                sha256_file(path)
            )
            entry["size_bytes"] = (
                path.stat().st_size
            )

        result[key] = entry

    return result


def _execution_record_base(
    *,
    plan: CommandPlan,
    inputs: ScenarioInputs,
    runtime: Mapping[str, str],
    environment: Mapping[str, str],
    timeout_seconds: float,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "authorization_id":
            AUTHORIZATION_ID,
        "status":
            "PLANNED",
        "method":
            plan.method,
        "scenario_id":
            plan.scenario_id,
        "scenario_seed":
            plan.scenario_seed,
        "argv":
            list(plan.argv),
        "cwd":
            str(plan.cwd),
        "frozen_run_contract":
            plan.frozen_run_contract,
        "required_output_patterns":
            list(
                plan.required_output_patterns
            ),
        "timeout_seconds":
            timeout_seconds,
        "subprocess_environment":
            dict(
                sorted(
                    environment.items()
                )
            ),
        "runtime":
            runtime_manifest(
                runtime
            ),
        "comparator_inputs":
            scenario_input_manifest(
                inputs
            ),
        "scoring_performed":
            False,
    }


def _write_execution_streams(
    *,
    plan: CommandPlan,
    stdout: str,
    stderr: str,
) -> None:
    (
        plan.plan_root
        / "stdout.txt"
    ).write_text(stdout)

    (
        plan.plan_root
        / "stderr.txt"
    ).write_text(stderr)


def _finalize_failure(
    *,
    plan: CommandPlan,
    record: dict[str, object],
    failure_type: str,
    failure_message: str,
) -> dict[str, object]:
    record.update(
        {
            "status":
                "FAILED",
            "failure_type":
                failure_type,
            "failure_message":
                failure_message,
            "native_outputs":
                native_output_manifest(
                    plan.native_dir
                ),
            "normalized_predictions_finalized":
                False,
            "scoring_performed":
                False,
        }
    )

    _write_json(
        plan.plan_root
        / "execution.json",
        record,
    )

    return record


def execute_command_plan(
    *,
    plan: CommandPlan,
    inputs: ScenarioInputs,
    runtime_config: Mapping[str, Mapping[str, str]],
    timeout_seconds: float,
    executor: Executor | None = None,
) -> dict[str, object]:
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(
            timeout_seconds,
            (int, float),
        )
        or timeout_seconds <= 0
    ):
        raise RunnerError(
            "timeout must be a positive number"
        )

    if plan.scenario_id != inputs.scenario_id:
        raise RunnerError(
            "command-plan and scenario identities differ"
        )

    if plan.method not in runtime_config:
        raise RunnerError(
            f"runtime configuration lacks {plan.method}"
        )

    # Re-check all pinned scientific identities immediately before
    # any process may be launched.
    verify_frozen_identities()

    environment = (
        build_subprocess_environment(
            plan=plan,
            runtime_config=runtime_config,
        )
    )

    runtime = runtime_config[
        plan.method
    ]

    record = _execution_record_base(
        plan=plan,
        inputs=inputs,
        runtime=runtime,
        environment=environment,
        timeout_seconds=float(
            timeout_seconds
        ),
    )

    _write_json(
        plan.plan_root
        / "execution.json",
        record,
    )

    run = (
        default_executor
        if executor is None
        else executor
    )

    started = time.monotonic()

    try:
        outcome = run(
            plan,
            environment,
            float(timeout_seconds),
        )

    except OSError as exc:
        elapsed = (
            time.monotonic()
            - started
        )

        _write_execution_streams(
            plan=plan,
            stdout="",
            stderr="",
        )

        record.update(
            {
                "elapsed_seconds":
                    elapsed,
                "exit_code":
                    None,
                "timed_out":
                    False,
            }
        )

        return _finalize_failure(
            plan=plan,
            record=record,
            failure_type=
                "launch_failure",
            failure_message=
                f"{type(exc).__name__}: {exc}",
        )

    elapsed = (
        time.monotonic()
        - started
    )

    _write_execution_streams(
        plan=plan,
        stdout=outcome.stdout,
        stderr=outcome.stderr,
    )

    record.update(
        {
            "elapsed_seconds":
                elapsed,
            "exit_code":
                outcome.returncode,
            "timed_out":
                outcome.timed_out,
        }
    )

    if outcome.timed_out:
        return _finalize_failure(
            plan=plan,
            record=record,
            failure_type="timeout",
            failure_message=(
                "comparator exceeded timeout "
                f"of {timeout_seconds} seconds"
            ),
        )

    if outcome.returncode != 0:
        return _finalize_failure(
            plan=plan,
            record=record,
            failure_type=
                "nonzero_exit",
            failure_message=(
                "comparator exited with status "
                f"{outcome.returncode}"
            ),
        )

    try:
        # Distinguish required-output state failures from parser/
        # normalization failures in the completion record.
        required_native_outputs(
            plan
        )

    except RunnerError as exc:
        return _finalize_failure(
            plan=plan,
            record=record,
            failure_type=
                "native_output_failure",
            failure_message=str(exc),
        )

    try:
        normalized = (
            normalize_native_outputs(
                plan=plan,
                inputs=inputs,
            )
        )

    except Exception as exc:
        return _finalize_failure(
            plan=plan,
            record=record,
            failure_type=
                "normalization_failure",
            failure_message=(
                f"{type(exc).__name__}: {exc}"
            ),
        )

    normalized_path = (
        plan.plan_root
        / "normalized_predictions.json"
    )

    _write_json(
        normalized_path,
        normalized,
    )

    normalized_sha256 = (
        sha256_file(
            normalized_path
        )
    )

    (
        plan.plan_root
        / "normalized_predictions.sha256"
    ).write_text(
        normalized_sha256
        + "  normalized_predictions.json\n"
    )

    record.update(
        {
            "status":
                "SUCCESS",
            "failure_type":
                None,
            "failure_message":
                None,
            "native_outputs":
                native_output_manifest(
                    plan.native_dir
                ),
            "normalized_predictions_finalized":
                True,
            "normalized_predictions_sha256":
                normalized_sha256,
            "scoring_performed":
                False,
        }
    )

    _write_json(
        plan.plan_root
        / "execution.json",
        record,
    )

    return record
