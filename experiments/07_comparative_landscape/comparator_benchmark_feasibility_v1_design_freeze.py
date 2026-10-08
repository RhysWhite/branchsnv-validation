#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, json, subprocess, sys

PARENT = "836fcc816c761ccc945365fb2783e25e66edcc2b"
EXP = Path("experiments/07_comparative_landscape")
RES = Path("results/07_comparative_landscape/comparative_landscape_v1")
DESIGN_JSON = EXP / "comparator_benchmark_feasibility_v1_design.json"
DESIGN_MD = EXP / "COMPARATOR_BENCHMARK_FEASIBILITY_V1_DESIGN.md"
RESULT_VALIDATOR = EXP / "comparative_landscape_v1_results_freeze.py"
DIRECT_NEAR = RES / "branchsnv_direct_near_comparators_v1.tsv"
MANIFEST = RES / "branchsnv_comparative_landscape_v1_manifest.json"

EXPECTED_DIRECT_NEAR_SHA = "d9cb7454707fe243a6088dba309063fdfcfe3c71cf4d89ae0836a9b7adb70229"
EXPECTED_MANIFEST_SHA = "8f229c81838921edcc46d1576d3de86c6ceee9ba00b9974634430507bdba8a09"
EXPECTED_29 = ['ARPIP', 'BetaReconstruct', 'chARNement', 'ConDor', 'EREM', 'F1ALA', 'FastML', 'FireProtASR', 'FUSE-PhyloTree', 'GASP', 'GLADX', 'GRASP', 'HomoplasyFinder', 'PAML', 'PastML', 'PastView', 'PhyloBot', 'POUTINE', 'ProtASR', 'ProtParCon', 'Shine', 'SNPPar', 'SpacerPlacer', 'SubRecon', 'Topiary', 'Tree-decomposition ncRNA ASR', 'TreeProfiler', 'TreeTime', 'WGCCRR']
DIRECT_SET = ["SNPPar", "SubRecon", "TreeTime"]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

def main():
    head = git("rev-parse", "HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PARENT, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError("repository is not at/descended from frozen parent")

    subprocess.run([sys.executable, str(RESULT_VALIDATOR)], check=True)

    if sha(DIRECT_NEAR) != EXPECTED_DIRECT_NEAR_SHA:
        raise RuntimeError("direct/near input SHA differs")
    if sha(MANIFEST) != EXPECTED_MANIFEST_SHA:
        raise RuntimeError("landscape manifest SHA differs")

    with DIRECT_NEAR.open("r", encoding="utf-8", newline="") as h:
        rows = list(csv.DictReader(h, delimiter="	"))

    if len(rows) != 29:
        raise RuntimeError("direct/near method count differs")

    names = [r["canonical_name"] for r in rows]
    if sorted(names) != sorted(EXPECTED_29):
        raise RuntimeError("direct/near identity set differs")

    direct = sorted(r["canonical_name"] for r in rows if r["final_comparator_class"] == "direct")
    near = [r for r in rows if r["final_comparator_class"] == "near_direct"]

    if direct != sorted(DIRECT_SET):
        raise RuntimeError("direct set differs")
    if len(near) != 26:
        raise RuntimeError("near-direct count differs")

    design = json.loads(DESIGN_JSON.read_text(encoding="utf-8"))
    if design["freeze_id"] != "COMPARATOR_BENCHMARK_FEASIBILITY_DESIGN_V1":
        raise RuntimeError("freeze id differs")
    if design["status"] != "FROZEN_PRE_ASSESSMENT":
        raise RuntimeError("design status differs")
    if design["scientific_scope"]["method_family_count"] != 29:
        raise RuntimeError("design method count differs")
    if design["scientific_scope"]["direct_set"] != DIRECT_SET:
        raise RuntimeError("design direct set differs")

    boundary = design["execution_boundary"]
    if any(boundary.values()):
        raise RuntimeError("design freeze grants unauthorized authority")

    if design["next_gate"] != "AUTHORIZE_COMPARATOR_BENCHMARK_FEASIBILITY_ASSESSMENT_V1":
        raise RuntimeError("next gate differs")

    print("PASS | comparator benchmark feasibility design v1 validates")
    print("PASS | frozen source universe = 29 direct/near method families")
    print("PASS | direct set = SNPPar + SubRecon + TreeTime")
    print("PASS | 26 near-direct method families")
    print("PASS | feasibility separated from scientific comparator status")
    print("PASS | no installation/software execution/benchmark authority granted")
    print("PASS | no production-bridge authority granted")
    print("PASS | next gate = AUTHORIZE_COMPARATOR_BENCHMARK_FEASIBILITY_ASSESSMENT_V1")

if __name__ == "__main__":
    main()
