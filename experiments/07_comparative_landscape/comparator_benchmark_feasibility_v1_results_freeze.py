#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import json
import subprocess
import sys

FREEZE_PARENT = "2b4a7131c98283da65af79846d694cd147d0dda5"
EXP = Path("experiments/07_comparative_landscape")
OUT = Path("results/07_comparative_landscape/comparator_benchmark_feasibility_v1")
SOURCE_RES = Path("results/07_comparative_landscape/comparative_landscape_v1")

LANDSCAPE_VALIDATOR = EXP / "comparative_landscape_v1_results_freeze.py"
DESIGN_VALIDATOR = EXP / "comparator_benchmark_feasibility_v1_design_freeze.py"
AUTH_VALIDATOR = EXP / "comparator_benchmark_feasibility_v1_assessment_authorization_freeze.py"
FROZEN_DIRECT_NEAR = SOURCE_RES / "branchsnv_direct_near_comparators_v1.tsv"

EXPECTED_RESULT_FILES = {'comparator_benchmark_feasibility_v1.tsv': '528b810b296faf58d4801372dc2f6965e84aad8669a7ec478e86e94e93379c0e', 'comparator_benchmark_feasibility_v1_manifest.json': '92c0f514c35bd6373878e7c35b6673147f0471843b99cf8c3a8719b3cebe400c', 'comparator_benchmark_feasibility_v1_summary.md': '0689deaac7d3e2ac8f19f5f044a46874bbb185e7ceafb11ab163984df7465e31', 'checksums.sha256': 'e01b1533d9cb99beaa6a4727589ad138d491794662015abdcff5ad42dac898e9'}
EXPECTED_BENCHMARK_SET = ['ARPIP', 'FastML', 'HomoplasyFinder', 'PAML', 'PastML', 'POUTINE', 'SNPPar', 'TreeTime']
EXPECTED_QUANT = ["SNPPar", "TreeTime"]
EXPECTED_ENDPOINT = ["ARPIP", "FastML", "HomoplasyFinder", "PAML", "PastML", "POUTINE"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

def read_tsv(path):
    with path.open("r", encoding="utf-8", newline="") as h:
        rd = csv.DictReader(h, delimiter="\t")
        return list(rd.fieldnames or []), list(rd)

def main():
    head = git("rev-parse", "HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", FREEZE_PARENT, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError("repository is not at/descended from feasibility authorization")

    for validator in [LANDSCAPE_VALIDATOR, DESIGN_VALIDATOR, AUTH_VALIDATOR]:
        subprocess.run([sys.executable, str(validator)], check=True)

    for name, expected in EXPECTED_RESULT_FILES.items():
        p = OUT / name
        if not p.is_file() or sha(p) != expected:
            raise RuntimeError(f"canonical feasibility artifact differs: {name}")

    subprocess.run(["sha256sum", "-c", "checksums.sha256"], cwd=OUT, check=True)

    _, rows = read_tsv(OUT / "comparator_benchmark_feasibility_v1.tsv")
    _, frozen = read_tsv(FROZEN_DIRECT_NEAR)
    if len(rows) != 29:
        raise RuntimeError("method count differs")

    if {r["canonical_name"]:r["final_comparator_class"] for r in rows} != {r["canonical_name"]:r["final_comparator_class"] for r in frozen}:
        raise RuntimeError("scientific class changed")

    counts = {}
    for r in rows:
        counts[r["feasibility_class"]] = counts.get(r["feasibility_class"],0)+1
    if counts != {
        "quantitative_benchmark_candidate":2,
        "endpoint_specific_benchmark_candidate":6,
        "contextual_comparator_only":21,
    }:
        raise RuntimeError("feasibility count differs")

    bench = sorted(r["canonical_name"] for r in rows if r["feasibility_class"] in {"quantitative_benchmark_candidate","endpoint_specific_benchmark_candidate"})
    if bench != sorted(EXPECTED_BENCHMARK_SET):
        raise RuntimeError("benchmark candidate set differs")

    quant = sorted(r["canonical_name"] for r in rows if r["feasibility_class"]=="quantitative_benchmark_candidate")
    endpoint = sorted(r["canonical_name"] for r in rows if r["feasibility_class"]=="endpoint_specific_benchmark_candidate")
    if quant != sorted(EXPECTED_QUANT) or endpoint != sorted(EXPECTED_ENDPOINT):
        raise RuntimeError("candidate subclass set differs")

    if any(r["small_validation_run_status"] != "not_run_pre_execution" for r in rows):
        raise RuntimeError("pre-execution status violated")

    manifest = json.loads((OUT/"comparator_benchmark_feasibility_v1_manifest.json").read_text(encoding="utf-8"))
    if any(manifest["execution_boundary"].values()):
        raise RuntimeError("execution boundary violated")
    if manifest["authorization"]["one_time_execution_consumed"] is not True:
        raise RuntimeError("authorization not consumed in result record")
    if manifest["authorization"]["rerun_authorized"] is not False:
        raise RuntimeError("rerun unexpectedly authorized")

    design = json.loads((EXP/"comparator_benchmark_feasibility_v1_results_design.json").read_text(encoding="utf-8"))
    if design["freeze_id"] != "COMPARATOR_BENCHMARK_FEASIBILITY_RESULTS_V1":
        raise RuntimeError("result freeze id differs")
    if design["next_gate"] != "FREEZE_COMPARATOR_BENCHMARK_EXECUTION_DESIGN_BEFORE_EXECUTION":
        raise RuntimeError("next gate differs")

    print("PASS | comparator benchmark feasibility v1 result freeze validates")
    print("PASS | 29 method families complete")
    print("PASS | 2 quantitative / 6 endpoint-specific / 21 contextual")
    print("PASS | benchmark candidate set = 8 methods")
    print("PASS | frozen direct/near comparator status unchanged")
    print("PASS | authorization consumed exactly once; rerun unauthorized")
    print("PASS | no installation/software execution/benchmark execution occurred")
    print("PASS | next gate = FREEZE_COMPARATOR_BENCHMARK_EXECUTION_DESIGN_BEFORE_EXECUTION")

if __name__ == "__main__":
    main()
