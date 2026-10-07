#!/usr/bin/env python3

from pathlib import Path
import csv
import hashlib
import json
import subprocess
import sys

EXP = Path("experiments/07_comparative_landscape")
RESULTS = Path("results/07_comparative_landscape")
DATASET = RESULTS / "comparator_benchmark_dataset_v1"
EXECUTION = RESULTS / "comparator_benchmark_dataset_generation_v1_execution"

AUTH_COMMIT = "e79d47fce7e60fc1af1c36a45904a23b272b3055"

DESIGN = EXP / "comparator_benchmark_dataset_generation_v1_results_design.json"
RECORD = EXP / "COMPARATOR_BENCHMARK_DATASET_GENERATION_V1_RESULTS.md"

EXPECTED_DESIGN_SHA = "3d364079e25065a55410e471f0f2378696c06ac3772afc8ff9dc86c1f1392ae5"
EXPECTED_RECORD_SHA = "03ba3a3602d09f3e1dcb3b74cb7ad45287023798c46011c15a2f9f5231ce5810"

EXPECTED_ARTIFACTS = {
    DATASET / "benchmark_dataset_manifest.tsv": (
        149900,
        "e24b9eac940da5db304c2855698d2969974b7102d4dad8bda5120996a315e310",
    ),
    DATASET / "checksums.sha256": (
        142662,
        "893216511f5e77bf7fd78671cd9c02f6878ebda88a4462fc3ebc773b2a6dd233",
    ),
    EXECUTION / "run.stdout.txt": (
        284,
        "7ae3648efcd501caccdc655ebef30b2609dc14e17bbe99b2956075a8c4191a59",
    ),
    EXECUTION / "run.stderr.txt": (
        0,
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    ),
    EXECUTION / "run.exit.txt": (
        2,
        "9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa",
    ),
}

AUTH_PATHS = [
    EXP / "comparator_benchmark_dataset_generation_v1.py",
    EXP / "comparator_benchmark_dataset_generation_v1_authorization.json",
    EXP / "COMPARATOR_BENCHMARK_DATASET_GENERATION_V1_AUTHORIZATION.md",
    EXP / "comparator_benchmark_dataset_generation_v1_authorization.sha256",
    EXP / "comparator_benchmark_dataset_generation_v1_authorization_freeze.py",
]

SCENARIOS = EXP / "comparator_benchmark_execution_v1_scenario_matrix.tsv"
MASTER_SEED = 20261005012417

EXPECTED_RECURRENT = {
    "unique_only": 0,
    "parallel": 20,
    "convergent": 20,
    "reversal": 20,
    "mixed_recurrence": 30,
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def read_fasta(path):
    records = {}
    name = None
    parts = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(">"):
            if name is not None:
                records[name] = "".join(parts)
            name = line[1:].split()[0]
            parts = []
        else:
            parts.append(line.strip())
    if name is not None:
        records[name] = "".join(parts)
    return records


def reference_sequence(path):
    text = path.read_text(encoding="utf-8")
    origin = text.split("ORIGIN\n", 1)[1].split("//", 1)[0]
    return "".join(c for c in origin.upper() if c in "ACGT")


def observed_variable_positions(root, sequences):
    length = len(root)
    positions = []
    for index in range(length):
        ref = root[index]
        if any(
            seq[index] in "ACGT" and seq[index] != ref
            for seq in sequences.values()
        ):
            positions.append(index + 1)
    return positions


def main():
    head = git("rev-parse", "HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", AUTH_COMMIT, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError("repository is not descended from dataset-generation authorization")

    if sha(DESIGN) != EXPECTED_DESIGN_SHA:
        raise RuntimeError("dataset-generation result design differs")
    if sha(RECORD) != EXPECTED_RECORD_SHA:
        raise RuntimeError("dataset-generation result record differs")

    for path, (expected_bytes, expected_sha) in EXPECTED_ARTIFACTS.items():
        if not path.is_file():
            raise RuntimeError(f"result artifact absent: {path}")
        if path.stat().st_size != expected_bytes:
            raise RuntimeError(f"result artifact byte count differs: {path}")
        if sha(path) != expected_sha:
            raise RuntimeError(f"result artifact identity differs: {path}")

    print("PASS | repository descends from dataset-generation authorization")
    print("PASS | result design and freeze record identities match")
    print("PASS | five frozen result artifact identities match")

    upstream = subprocess.run(
        [
            sys.executable,
            str(EXP / "comparator_benchmark_dataset_generation_v1_authorization_freeze.py"),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if upstream.returncode != 0:
        raise RuntimeError(
            "dataset-generation authorization freeze no longer validates: "
            + upstream.stderr.strip()
        )

    for path in AUTH_PATHS:
        frozen = subprocess.check_output(
            ["git", "show", f"{AUTH_COMMIT}:{path.as_posix()}"]
        )
        if path.read_bytes() != frozen:
            raise RuntimeError(f"dataset-generation authorization artifact changed: {path}")

    authorization = json.loads(
        (EXP / "comparator_benchmark_dataset_generation_v1_authorization.json")
        .read_text(encoding="utf-8")
    )
    if authorization["authorization_id"] != \
       "COMPARATOR_BENCHMARK_DATASET_GENERATION_V1_001":
        raise RuntimeError("dataset-generation authorization id differs")
    if authorization["one_time_dataset_generation_authorization"] is not True:
        raise RuntimeError("one-use dataset-generation authorization absent")
    if authorization["rerun_authorized"] is not False:
        raise RuntimeError("dataset-generation rerun unexpectedly authorized")

    print("PASS | upstream dataset-generation authorization freeze validates")
    print("PASS | original one-use authorization artifacts remain unchanged")
    print("PASS | generation authorization consumed; rerun remains blocked")

    result_design = json.loads(DESIGN.read_text(encoding="utf-8"))
    if result_design["freeze_id"] != \
       "COMPARATOR_BENCHMARK_DATASET_GENERATION_RESULTS_V1":
        raise RuntimeError("result freeze id differs")
    if result_design["status"] != "FROZEN_PRE_BENCHMARK_EXECUTION":
        raise RuntimeError("result status differs")
    if result_design["authorization_commit"] != AUTH_COMMIT:
        raise RuntimeError("result authorization commit differs")
    if result_design["freeze_parent_commit"] != AUTH_COMMIT:
        raise RuntimeError("result freeze parent differs")
    if result_design["authorization_consumed"] is not True:
        raise RuntimeError("authorization-consumed status differs")
    if result_design["rerun_authorized"] is not False:
        raise RuntimeError("result unexpectedly permits rerun")
    if any(result_design["execution_boundary"].values()):
        raise RuntimeError("post-generation execution boundary violated")
    if result_design["next_gate"] != "AUTHORIZE_COMPARATOR_BENCHMARK_EXECUTION_V1":
        raise RuntimeError("post-dataset next gate differs")

    print("PASS | result-design semantics and execution boundary validate")

    if EXECUTION.joinpath("run.exit.txt").read_text(encoding="utf-8") != "0\n":
        raise RuntimeError("generation exit record differs")
    if EXECUTION.joinpath("run.stderr.txt").read_bytes() != b"":
        raise RuntimeError("generation stderr is not empty")

    expected_stdout = (
        "PASS | generated exactly 150 frozen benchmark scenarios\n"
        "PASS | comparator inputs and benchmark truth stored separately\n"
        "PASS | benchmark_dataset_manifest.tsv written\n"
        "PASS | dataset checksums written\n"
        "PASS | output root = results/07_comparative_landscape/"
        "comparator_benchmark_dataset_v1\n"
    )
    if EXECUTION.joinpath("run.stdout.txt").read_text(encoding="utf-8") != expected_stdout:
        raise RuntimeError("generation stdout differs")

    print("PASS | one-use generation execution completed successfully")

    checksum_lines = DATASET.joinpath("checksums.sha256").read_text(
        encoding="utf-8"
    ).splitlines()
    if len(checksum_lines) != 901:
        raise RuntimeError("dataset checksum-entry count differs")

    subprocess.run(
        ["sha256sum", "-c", str(DATASET / "checksums.sha256")],
        check=True,
        stdout=subprocess.DEVNULL,
    )

    print("PASS | complete 901-entry generated dataset tree verifies")

    with SCENARIOS.open("r", encoding="utf-8", newline="") as handle:
        scenarios = list(csv.DictReader(handle, delimiter="\t"))
    with DATASET.joinpath("benchmark_dataset_manifest.tsv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    if len(scenarios) != 150 or len(rows) != 150:
        raise RuntimeError("scenario count differs")
    if [row["scenario_id"] for row in rows] != \
       [row["scenario_id"] for row in scenarios]:
        raise RuntimeError("manifest scenario order differs")

    for row, scenario in zip(rows, scenarios):
        sid = row["scenario_id"]

        if (
            int(row["tip_count"]) != int(scenario["tip_count"])
            or row["event_regime"] != scenario["event_regime"]
            or row["observation_condition"] != scenario["observation_condition"]
            or int(row["replicate"]) != int(scenario["replicate"])
        ):
            raise RuntimeError(f"scenario metadata differs: {sid}")

        expected_seed = int.from_bytes(
            hashlib.sha256(f"{MASTER_SEED}|{sid}".encode()).digest()[:8],
            "big",
            signed=False,
        )
        if int(row["seed"]) != expected_seed:
            raise RuntimeError(f"manifest seed differs: {sid}")

        file_pairs = (
            ("tree_path", "tree_sha256"),
            ("alignment_path", "alignment_sha256"),
            ("positions_path", "positions_sha256"),
            ("reference_path", "reference_sha256"),
            ("truth_path", "truth_sha256"),
            ("truth_sequences_path", "truth_sequences_sha256"),
        )
        for path_key, hash_key in file_pairs:
            path = Path(row[path_key])
            if not path.is_file():
                raise RuntimeError(f"manifest path absent: {sid} {path_key}")
            if sha(path) != row[hash_key]:
                raise RuntimeError(f"manifest file identity differs: {sid} {path_key}")

        truth = json.loads(Path(row["truth_path"]).read_text(encoding="utf-8"))
        if truth["seed"] != expected_seed:
            raise RuntimeError(f"truth seed differs: {sid}")
        if len(truth["variable_positions"]) != 40:
            raise RuntimeError(f"true event-site count differs: {sid}")
        if len(truth["recurrent_positions"]) != EXPECTED_RECURRENT[row["event_regime"]]:
            raise RuntimeError(f"recurrence structure differs: {sid}")

        n_tips = int(row["tip_count"])
        expected_missing = (
            0
            if row["observation_condition"] == "complete"
            else (n_tips * 40 * 5) // 100
        )
        if len(truth["missing_mask"]) != expected_missing:
            raise RuntimeError(f"truth missingness differs: {sid}")

        observed = read_fasta(Path(row["alignment_path"]))
        truth_sequences = read_fasta(Path(row["truth_sequences_path"]))

        if len(observed) != n_tips or len(truth_sequences) != n_tips:
            raise RuntimeError(f"tip count differs: {sid}")
        if set(observed) != set(truth_sequences):
            raise RuntimeError(f"tip labels differ: {sid}")
        if any(len(sequence) != 10000 for sequence in observed.values()):
            raise RuntimeError(f"observed sequence length differs: {sid}")
        if any(len(sequence) != 10000 for sequence in truth_sequences.values()):
            raise RuntimeError(f"truth sequence length differs: {sid}")
        if any(set(sequence) - set("ACGT") for sequence in truth_sequences.values()):
            raise RuntimeError(f"truth alphabet differs: {sid}")

        observed_missing = sum(sequence.count("N") for sequence in observed.values())
        if observed_missing != expected_missing:
            raise RuntimeError(f"observed missingness differs: {sid}")

        root = reference_sequence(Path(row["reference_path"]))
        recorded_positions = [
            int(value)
            for value in Path(row["positions_path"]).read_text(
                encoding="utf-8"
            ).splitlines()
            if value
        ]
        if recorded_positions != observed_variable_positions(root, observed):
            raise RuntimeError(f"input positions differ from observed alignment: {sid}")

    print("PASS | exact 150-scenario frozen matrix validates")
    print("PASS | deterministic seeds and all 900 manifest file identities validate")
    print("PASS | event-site, recurrence and missing-data contracts validate")
    print("PASS | sequence payload and observed-position contracts validate")

    input_dirs = [
        path for path in DATASET.joinpath("inputs").iterdir() if path.is_dir()
    ]
    truth_dirs = [
        path for path in DATASET.joinpath("truth").iterdir() if path.is_dir()
    ]
    input_files = [
        path for path in DATASET.joinpath("inputs").rglob("*") if path.is_file()
    ]
    truth_files = [
        path for path in DATASET.joinpath("truth").rglob("*") if path.is_file()
    ]

    if len(input_dirs) != 150 or len(truth_dirs) != 150:
        raise RuntimeError("input/truth scenario-directory count differs")
    if len(input_files) != 600 or len(truth_files) != 300:
        raise RuntimeError("input/truth file count differs")

    print("PASS | comparator inputs and benchmark truth remain physically separated")
    print("PASS | 600 input files and 300 truth files validate")

    tracked_payloads = git(
        "ls-files",
        "results/07_comparative_landscape/comparator_benchmark_dataset_v1/inputs",
        "results/07_comparative_landscape/comparator_benchmark_dataset_v1/truth",
    )
    if tracked_payloads:
        raise RuntimeError("large generated payload is unexpectedly tracked by Git")

    print("PASS | generated payload remains outside ordinary Git history")
    print("PASS | benchmark execution remains unauthorized")
    print("PASS | next gate = AUTHORIZE_COMPARATOR_BENCHMARK_EXECUTION_V1")


if __name__ == "__main__":
    main()
