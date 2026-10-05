#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import subprocess
import sys

PARENT = "e31ae97a8b230b4f94cf9bac17768168b639b528"
EXP = Path("experiments/07_comparative_landscape")
DESIGN_VALIDATOR = EXP / "comparator_benchmark_feasibility_v1_design_freeze.py"
DESIGN_JSON = EXP / "comparator_benchmark_feasibility_v1_design.json"
AUTH_JSON = EXP / "comparator_benchmark_feasibility_v1_assessment_authorization.json"

EXPECTED_DESIGN_JSON_SHA = "9775615d3f3fbbe9b2e935fe1a9f44d2f53e4262d34c176241058b7f3d0baf9d"
AUTHORIZATION_ID = "COMPARATOR_BENCHMARK_FEASIBILITY_ASSESSMENT_V1_EXECUTION_001"

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
        raise RuntimeError("repository is not at/descended from authorization parent")

    subprocess.run([sys.executable, str(DESIGN_VALIDATOR)], check=True)

    if sha(DESIGN_JSON) != EXPECTED_DESIGN_JSON_SHA:
        raise RuntimeError("design JSON SHA differs")

    auth = json.loads(AUTH_JSON.read_text(encoding="utf-8"))
    if auth["authorization_id"] != AUTHORIZATION_ID:
        raise RuntimeError("authorization id differs")
    if auth["status"] not in {"AUTHORIZED_NOT_YET_CONSUMED", "AUTHORIZED_CONSUMED"}:
        raise RuntimeError("authorization status differs")
    if auth["scope"]["method_family_count"] != 29:
        raise RuntimeError("authorized method-family count differs")

    for key in [
        "source_research_authorized",
        "authoritative_source_retrieval_authorized",
        "official_repository_and_documentation_research_authorized",
        "public_web_research_authorized",
        "feasibility_classification_authorized",
        "assessment_artifact_generation_authorized",
    ]:
        if auth["scope"][key] is not True:
            raise RuntimeError(f"required assessment authority false: {key}")

    if not all(auth["explicitly_not_authorized"].values()):
        raise RuntimeError("one or more forbidden activities not explicitly blocked")

    if auth["one_time_assessment_write"] is not True:
        raise RuntimeError("one-time assessment write not enforced")
    if auth["rerun_authorized"] is not False:
        raise RuntimeError("rerun unexpectedly authorized")

    print("PASS | comparator benchmark feasibility assessment authorization validates")
    print("PASS | source-backed assessment authorized for all 29 frozen method families")
    print("PASS | feasibility classification + assessment artifact generation authorized")
    print("PASS | software installation/execution remains unauthorized")
    print("PASS | benchmark execution remains unauthorized")
    print("PASS | frozen direct/near scientific classifications remain immutable")
    print("PASS | production bridge and production ledger mutation remain unauthorized")

if __name__ == "__main__":
    main()
