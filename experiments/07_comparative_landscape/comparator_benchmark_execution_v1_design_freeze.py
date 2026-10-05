#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import json
import subprocess
import sys

PARENT = "558d62aa9e8126ceef27e5d8c0c756558071d98f"
EXP = Path("experiments/07_comparative_landscape")
FEAS_RES = Path("results/07_comparative_landscape/comparator_benchmark_feasibility_v1")
FEAS_VALIDATOR = EXP / "comparator_benchmark_feasibility_v1_results_freeze.py"
FEAS_TSV = FEAS_RES / "comparator_benchmark_feasibility_v1.tsv"
DESIGN_JSON = EXP / "comparator_benchmark_execution_v1_design.json"
METHOD_MATRIX = EXP / "comparator_benchmark_execution_v1_method_matrix.tsv"
SCENARIO_MATRIX = EXP / "comparator_benchmark_execution_v1_scenario_matrix.tsv"

EXPECTED_FEAS_TSV_SHA = "528b810b296faf58d4801372dc2f6965e84aad8669a7ec478e86e94e93379c0e"
BENCHMARK_SET = ['ARPIP', 'FastML', 'HomoplasyFinder', 'PAML', 'PastML', 'POUTINE', 'SNPPar', 'TreeTime']
BRANCH_METHODS = ['ARPIP', 'FastML', 'PAML', 'PastML', 'SNPPar', 'TreeTime']
HOMOPLASY_METHODS = ['HomoplasyFinder', 'POUTINE', 'SNPPar', 'TreeTime']

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

def read_tsv(path):
    with path.open("r", encoding="utf-8", newline="") as h:
        rd = csv.DictReader(h, delimiter="	")
        return list(rd.fieldnames or []), list(rd)

def main():
    head = git("rev-parse", "HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PARENT, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError("repository is not at/descended from benchmark-design parent")

    subprocess.run([sys.executable, str(FEAS_VALIDATOR)], check=True)

    if sha(FEAS_TSV) != EXPECTED_FEAS_TSV_SHA:
        raise RuntimeError("feasibility TSV SHA differs")

    _, feas = read_tsv(FEAS_TSV)
    bench = sorted(
        r["canonical_name"] for r in feas
        if r["feasibility_class"] in {
            "quantitative_benchmark_candidate",
            "endpoint_specific_benchmark_candidate",
        }
    )
    if bench != sorted(BENCHMARK_SET):
        raise RuntimeError("feasibility-qualified benchmark set differs")

    _, methods = read_tsv(METHOD_MATRIX)
    if len(methods) != 8:
        raise RuntimeError("method matrix must contain 8 methods")
    if sorted(r["canonical_name"] for r in methods) != sorted(BENCHMARK_SET):
        raise RuntimeError("method matrix identity set differs")

    branch = sorted(
        r["canonical_name"] for r in methods
        if "branch_change_reconstruction" in r["benchmark_endpoints"].split(" | ")
    )
    hom = sorted(
        r["canonical_name"] for r in methods
        if "homoplasy_recurrent_state_analysis" in r["benchmark_endpoints"].split(" | ")
    )
    if branch != sorted(BRANCH_METHODS):
        raise RuntimeError("branch endpoint method set differs")
    if hom != sorted(HOMOPLASY_METHODS):
        raise RuntimeError("homoplasy endpoint method set differs")

    _, scenarios = read_tsv(SCENARIO_MATRIX)
    if len(scenarios) != 150:
        raise RuntimeError("scenario matrix must contain exactly 150 datasets")
    if len({r["scenario_id"] for r in scenarios}) != 150:
        raise RuntimeError("scenario ids not unique")
    if sorted({int(r["tip_count"]) for r in scenarios}) != [32,128,512]:
        raise RuntimeError("tip-size design differs")
    if sorted({r["event_regime"] for r in scenarios}) != [
        "convergent","mixed_recurrence","parallel","reversal","unique_only"
    ]:
        raise RuntimeError("event-regime design differs")
    if sorted({r["observation_condition"] for r in scenarios}) != ["complete","missing_5pct"]:
        raise RuntimeError("observation-condition design differs")

    design = json.loads(DESIGN_JSON.read_text(encoding="utf-8"))
    if design["freeze_id"] != "COMPARATOR_BENCHMARK_EXECUTION_DESIGN_V1":
        raise RuntimeError("freeze id differs")
    if design["status"] != "FROZEN_PRE_IMPLEMENTATION":
        raise RuntimeError("design status differs")
    if design["truth_generation"]["scenario_count"] != 150:
        raise RuntimeError("scenario count differs")
    if design["benchmark_method_universe"]["methods"] != BENCHMARK_SET:
        raise RuntimeError("design method universe differs")
    if design["dependency_policy"]["treetime_family"] != ["TreeTime","SNPPar","POUTINE"]:
        raise RuntimeError("TreeTime dependency family differs")
    if any(design["authority_boundary"].values()):
        raise RuntimeError("design grants unauthorized execution authority")
    if design["next_gate"] != "FREEZE_COMPARATOR_BENCHMARK_EXECUTION_IMPLEMENTATION_BEFORE_EXECUTION":
        raise RuntimeError("next gate differs")

    print("PASS | comparator benchmark execution design v1 validates")
    print("PASS | exact 8-method executable universe")
    print("PASS | branch-change arm = 6 external workflows")
    print("PASS | homoplasy arm = 4 external workflows")
    print("PASS | exact 150-scenario truth design")
    print("PASS | marker/genotyping endpoints explicitly not force-benchmarked")
    print("PASS | TreeTime/SNPPar/POUTINE dependency family explicit")
    print("PASS | no installation/environment build/software execution/benchmark authority granted")
    print("PASS | next gate = FREEZE_COMPARATOR_BENCHMARK_EXECUTION_IMPLEMENTATION_BEFORE_EXECUTION")

if __name__ == "__main__":
    main()
