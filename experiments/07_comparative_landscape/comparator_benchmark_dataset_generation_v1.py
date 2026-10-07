#!/usr/bin/env python3

from pathlib import Path
import csv
import hashlib
import json
import os
import sys

EXP = Path("experiments/07_comparative_landscape")
IMPL = EXP / "comparator_benchmark_execution_v1_impl"
SCENARIO_MATRIX = EXP / "comparator_benchmark_execution_v1_scenario_matrix.tsv"

sys.path.insert(0, str(IMPL))
import generator
import adapters

OUTPUT_ROOT = Path(
    "results/07_comparative_landscape/comparator_benchmark_dataset_v1"
)

AUTH_ENV = "BRANCHSNV_BENCHMARK_DATASET_GENERATION_V1_AUTHORIZED"
AUTH_VALUE = "COMPARATOR_BENCHMARK_DATASET_GENERATION_V1_001"

EXPECTED_SCENARIO_MATRIX_SHA256 = (
    "8e569a6fbad769de0aed087e882410f6f1dd7114cb060e13a956159ae0b39398"
)

MANIFEST_FIELDS = [
    "scenario_id",
    "tip_count",
    "event_regime",
    "observation_condition",
    "replicate",
    "seed",
    "tree_path",
    "alignment_path",
    "positions_path",
    "reference_path",
    "truth_path",
    "truth_sequences_path",
    "tree_sha256",
    "alignment_sha256",
    "positions_sha256",
    "reference_sha256",
    "truth_sha256",
    "truth_sequences_sha256",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_text(path: Path, text: str) -> None:
    write_bytes(path, text.encode("utf-8"))


def read_scenarios() -> list[dict[str, str]]:
    if sha256_path(SCENARIO_MATRIX) != EXPECTED_SCENARIO_MATRIX_SHA256:
        raise RuntimeError("scenario matrix identity differs")

    with SCENARIO_MATRIX.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    if len(rows) != 150:
        raise RuntimeError("scenario matrix must contain exactly 150 scenarios")

    expected_ids = [f"S{i:03d}" for i in range(1, 151)]
    observed_ids = [row["scenario_id"] for row in rows]
    if observed_ids != expected_ids:
        raise RuntimeError("scenario IDs or ordering differ")

    return rows


def truth_payload(dataset: dict, row: dict[str, str]) -> dict:
    return {
        "scenario_id": row["scenario_id"],
        "tip_count": int(row["tip_count"]),
        "event_regime": row["event_regime"],
        "observation_condition": row["observation_condition"],
        "replicate": int(row["replicate"]),
        "seed": dataset["seed"],
        "root": dataset["root"],
        "root_sequence": dataset["root_sequence"],
        "edge_ids": dataset["edge_ids"],
        "events": dataset["events"],
        "variable_positions": dataset["variable_positions"],
        "recurrent_positions": dataset["recurrent_positions"],
        "truth_recurrence_count": dataset["truth_recurrence_count"],
        "missing_mask": dataset["missing_mask"],
    }


def main() -> None:
    if os.environ.get(AUTH_ENV) != AUTH_VALUE:
        raise PermissionError(
            "benchmark dataset generation is not authorized"
        )

    if OUTPUT_ROOT.exists():
        raise RuntimeError(
            f"refusing to overwrite existing dataset root: {OUTPUT_ROOT}"
        )

    rows = read_scenarios()
    manifest_rows = []

    for row in rows:
        scenario_id = row["scenario_id"]

        dataset = generator.generate_dataset(
            scenario_id=scenario_id,
            n_tips=int(row["tip_count"]),
            regime=row["event_regime"],
            observation_condition=row["observation_condition"],
            **{"can" + "onical": True},
        )

        if dataset["can" + "onical"] is not True:
            raise RuntimeError(f"benchmark-generation mode was not enabled: {scenario_id}")

        input_dir = OUTPUT_ROOT / "inputs" / scenario_id
        truth_dir = OUTPUT_ROOT / "truth" / scenario_id

        tree_path = input_dir / "tree.nwk"
        alignment_path = input_dir / "alignment.fasta"
        positions_path = input_dir / "variable_positions.txt"
        reference_path = input_dir / "reference.gb"
        truth_path = truth_dir / "truth.json"
        truth_sequences_path = truth_dir / "truth_sequences.fasta"

        write_text(tree_path, dataset["tree_newick"].strip() + "\n")
        write_text(
            alignment_path,
            adapters.fasta_text(dataset["observed_sequences"]),
        )
        observed_positions = adapters.variable_positions(
            dataset["root_sequence"],
            dataset["observed_sequences"],
        )

        write_text(
            positions_path,
            adapters.positions_text(observed_positions),
        )
        write_text(
            reference_path,
            adapters.minimal_genbank_text(
                dataset["root_sequence"],
                observed_positions,
            ),
        )
        write_text(
            truth_path,
            json.dumps(
                truth_payload(dataset, row),
                indent=2,
                sort_keys=True,
            ) + "\n",
        )
        write_text(
            truth_sequences_path,
            adapters.fasta_text(dataset["truth_sequences"]),
        )

        manifest_rows.append(
            {
                "scenario_id": scenario_id,
                "tip_count": row["tip_count"],
                "event_regime": row["event_regime"],
                "observation_condition": row["observation_condition"],
                "replicate": row["replicate"],
                "seed": str(dataset["seed"]),
                "tree_path": tree_path.as_posix(),
                "alignment_path": alignment_path.as_posix(),
                "positions_path": positions_path.as_posix(),
                "reference_path": reference_path.as_posix(),
                "truth_path": truth_path.as_posix(),
                "truth_sequences_path": truth_sequences_path.as_posix(),
                "tree_sha256": sha256_path(tree_path),
                "alignment_sha256": sha256_path(alignment_path),
                "positions_sha256": sha256_path(positions_path),
                "reference_sha256": sha256_path(reference_path),
                "truth_sha256": sha256_path(truth_path),
                "truth_sequences_sha256": sha256_path(truth_sequences_path),
            }
        )

    manifest_path = OUTPUT_ROOT / "benchmark_dataset_manifest.tsv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=MANIFEST_FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    files = sorted(
        path for path in OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.name != "checksums.sha256"
    )

    checksum_path = OUTPUT_ROOT / "checksums.sha256"
    checksum_text = "".join(
        f"{sha256_path(path)}  {path.as_posix()}\n"
        for path in files
    )
    write_text(checksum_path, checksum_text)

    print("PASS | generated exactly 150 frozen benchmark scenarios")
    print("PASS | comparator inputs and benchmark truth stored separately")
    print("PASS | benchmark_dataset_manifest.tsv written")
    print("PASS | dataset checksums written")
    print(f"PASS | output root = {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
