#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import json
import subprocess
import sys

PARENT = "51771f3766d34794b6eab124fa6b53eed6905017"
EXP = Path("experiments/07_comparative_landscape")
IMPL = EXP / "comparator_benchmark_execution_v1_impl"
DESIGN_VALIDATOR = EXP / "comparator_benchmark_execution_v1_design_freeze.py"
AUTH_VALIDATOR = EXP / "comparator_benchmark_execution_v1_implementation_authorization_freeze.py"
DESIGN_JSON = EXP / "comparator_benchmark_execution_v1_design.json"
AUTH_JSON = EXP / "comparator_benchmark_execution_v1_implementation_authorization.json"

EXPECTED_DESIGN_JSON_SHA = "1306af08f69d27a80990203bd7d803d2c907a1cdeb56bfd2fe0174bf4a416cde"
EXPECTED_AUTH_JSON_SHA = "c7ed262cf99239bb29e1b11d28788e50302de37f78d643b4f488139b8975b5a3"
IMPLEMENTATION_FILES = {'IMPLEMENTATION.md': 'd9faee06aaebfe5ace4cb0564bbb7761308f236bf55468550c9d2f6167d8fbac', 'adapters.py': 'b5b6dae15008d403d8e408ea44220651b390c12f24a3902dfb7c5312daa01b16', 'environment_recipes.json': '743af4effea96e8afbba6be87b9796ee89471f024789c60fc74487d4ad6f9921', 'generator.py': '229ed49c541023d6d439967ca184dd82430a4b3592d42657131fac08c9f3f560', 'implementation_manifest.json': 'd5249be8aa0e751f1f1b564dbc1a6cd7f1345cb485c36b07d32a8ce0731a51d7', 'metrics.py': 'b6d3ca91702e79a8a1b2dc36591616fa1519f59bd342a005e9cf646c8e8475de', 'source_pins.tsv': 'b1f5d81a33ac407e9cdf3d15dfa6bcd6e45c676808e3f5232bab9d9c1dcf1365', 'toy_validation.py': '646cd346931ccbe8f988c5ee17ffb4302fa5e2cf2c8d84cd1037621ae46ed3eb'}
EXPECTED_PINS = {'ARPIP': 'ee32c10b49407728b1ab00b5f98f792ca6dc2e1a', 'FastML': 'c78ce0ccc1ace2855ae0449c15b8bd8e2d766ba0', 'HomoplasyFinder': 'faed16f2ff1602a2a939663a942e0b8640b9bc50', 'PAML': '4c7902fe972737ef5e80bb18f159a6e6acace3d3', 'POUTINE': '8faeeb243a0f3ddc6f8274c81ce5ee79e8845f7d', 'PastML': '1654471801c8104b51ac45eda625c289d8e3f1ac', 'SNPPar': '0386df8edcff26faf242bc268c5f8865b09c9de9', 'TreeTime': '17da461f9299706b99a90e622183772f00c5076d'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

def main():
    head = git("rev-parse", "HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PARENT, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError("repository is not at/descended from implementation parent")

    subprocess.run([sys.executable, str(DESIGN_VALIDATOR)], check=True)
    subprocess.run([sys.executable, str(AUTH_VALIDATOR)], check=True)

    if sha(DESIGN_JSON) != EXPECTED_DESIGN_JSON_SHA:
        raise RuntimeError("benchmark design JSON SHA differs")
    if sha(AUTH_JSON) != EXPECTED_AUTH_JSON_SHA:
        raise RuntimeError("implementation authorization JSON SHA differs")

    for name, expected in IMPLEMENTATION_FILES.items():
        p = IMPL / name
        if not p.is_file() or sha(p) != expected:
            raise RuntimeError(f"implementation artifact differs: {name}")

    manifest = json.loads((IMPL / "implementation_manifest.json").read_text(encoding="utf-8"))
    if manifest["freeze_id"] != "COMPARATOR_BENCHMARK_EXECUTION_IMPLEMENTATION_V1":
        raise RuntimeError("implementation freeze id differs")
    if manifest["status"] != "FROZEN_PRE_ENVIRONMENT_BUILD":
        raise RuntimeError("implementation status differs")
    if manifest["master_seed"] != 20261005012417:
        raise RuntimeError("master seed differs")
    if manifest["canonical_scenario_count"] != 150:
        raise RuntimeError("canonical scenario count differs")
    if manifest["canonical_dataset_generated"] is not False:
        raise RuntimeError("canonical datasets unexpectedly generated")
    if manifest["third_party_software_installed"] is not False:
        raise RuntimeError("third-party installation boundary violated")
    if manifest["comparator_software_executed"] is not False:
        raise RuntimeError("comparator execution boundary violated")
    if manifest["authorization"]["one_time_implementation_consumed"] is not True:
        raise RuntimeError("implementation authorization consumption absent")
    if manifest["authorization"]["rerun_authorized"] is not False:
        raise RuntimeError("implementation rerun unexpectedly authorized")
    if manifest["next_gate"] != "AUTHORIZE_COMPARATOR_BENCHMARK_ENVIRONMENT_BUILD_AND_SMOKE_TEST_V1":
        raise RuntimeError("implementation next gate differs")

    with (IMPL / "source_pins.tsv").open("r", encoding="utf-8", newline="") as h:
        rows = list(csv.DictReader(h, delimiter="\t"))
    pins = {r["canonical_name"]: r["selected_commit_sha"] for r in rows}
    if pins != EXPECTED_PINS:
        raise RuntimeError("source pin set differs")

    recipes = json.loads((IMPL / "environment_recipes.json").read_text(encoding="utf-8"))
    if recipes["status"] != "STATIC_RECIPES_ONLY_NOT_EXECUTED":
        raise RuntimeError("environment recipe status differs")
    if recipes["global_policy"]["canonical_execution_authorized"] is not False:
        raise RuntimeError("recipe grants canonical execution")
    if recipes["methods"]["POUTINE"]["build_status"] != "HELP_CAPTURE_REQUIRED_DURING_AUTHORIZED_SMOKE":
        raise RuntimeError("POUTINE unresolved CLI boundary differs")
    if "smoke_resolution_required" not in recipes["methods"]["PastML"]:
        raise RuntimeError("PastML machine-readable output smoke gate absent")

    cp = subprocess.run(
        [sys.executable, "toy_validation.py"],
        cwd=IMPL,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    sys.stdout.write(cp.stdout)
    if cp.returncode != 0 or "TOY_IMPLEMENTATION_VALIDATION=PASS" not in cp.stdout:
        raise RuntimeError("toy-only implementation validation failed")

    print("PASS | comparator benchmark execution implementation v1 validates")
    print("PASS | exact 8 comparator source pins frozen")
    print("PASS | master seed = 20261005012417")
    print("PASS | canonical generator remains fail-closed")
    print("PASS | independent generator/adapters/metrics toy validation")
    print("PASS | POUTINE/PastML smoke-resolution boundaries explicit")
    print("PASS | no third-party install, comparator execution, or canonical generation")
    print("PASS | next gate = AUTHORIZE_COMPARATOR_BENCHMARK_ENVIRONMENT_BUILD_AND_SMOKE_TEST_V1")

if __name__ == "__main__":
    main()
