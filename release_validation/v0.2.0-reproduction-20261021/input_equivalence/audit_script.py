#!/usr/bin/env python3
"""Independent representation-equivalence audit of BRANCHSNV 0.2.0.

Generate deterministic synthetic nucleotide alignments in distinct supported NEXUS
representations. Compare parser-normalised sites and exact CLI positive-call outputs
in all three modes. Writes evidence ONLY to a new, caller-specified directory.
This tests input representation invariance, not phylogenetic truth accuracy.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import csv
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

TAXA = ("Outgroup", "A", "B", "C", "D", "E", "F", "G", "H")
TREE = "(Outgroup:0.1,((A:0.1,B:0.1):0.2,((C:0.05,D:0.05):0.04,(E:0.06,(F:0.03,(G:0.02,H:0.01):0.02):0.01):0.07):0.08):0.04);\n"
SYMBOLS = "ACGTRYSWKMBDHVN?-"
MODES = ("fixed-exclusive", "parsimony", "both")
VARIANTS = ("transposed_tokens", "transposed_compact", "conventional_compact", "conventional_tokens", "conventional_no_taxlabels", "conventional_reordered")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_states(seed: int, n: int) -> list[str]:
    rng = random.Random(seed)
    sites = []
    for i in range(n):
        if i % 9 == 0:
            states = ["A"] * len(TAXA)
            states[1] = states[2] = "G"
        elif i % 9 == 1:
            states = ["C"] * len(TAXA)
            states[1] = "T"
            states[2] = "N"
        elif i % 9 == 2:
            states = [rng.choice("ACGT") for _ in TAXA]
            states[3] = "?"
        elif i % 9 == 3:
            states = [rng.choice("ACGT") for _ in TAXA]
            states[2] = "-"
        elif i % 9 == 4:
            states = [rng.choice("ACGT") for _ in TAXA]
            states[6] = rng.choice("RYSWKMBDHV")
        else:
            states = [rng.choice(SYMBOLS) for _ in TAXA]
        sites.append("".join(states))
    return sites


def nexus_text(sites: list[str], variant: str) -> str:
    n = len(sites)
    is_transposed = variant.startswith("transposed")
    is_compact = variant.endswith("compact")
    if is_transposed:
        transpose = "TRANSPOSE=YES" if is_compact else "TRANSPOSE"
    elif variant == "conventional_tokens":
        transpose = "TRANSPOSE=NO"
    else:
        transpose = ""
    h = ["#NEXUS", "BEGIN DATA;", f"  DIMENSIONS NTAX={len(TAXA)} NCHAR={n};", f'  FORMAT DATATYPE=DNA SYMBOLS="ACGT" MISSING=? GAP=- {transpose};']
    if variant != "conventional_no_taxlabels":
        h.append("  TAXLABELS " + " ".join(TAXA) + ";")
    if not is_transposed:
        h.append("  CHARLABELS " + " ".join(f"ref_{i+1}" for i in range(n)) + ";")
    h.append("  MATRIX")
    if is_transposed:
        for i, state in enumerate(sites, 1):
            tokens = state if is_compact else " ".join(state)
            h.append(f"    ref_{i} {tokens}")
    else:
        order = tuple(reversed(TAXA)) if variant == "conventional_reordered" else TAXA
        for taxon in order:
            idx = TAXA.index(taxon)
            state = "".join(site[idx] for site in sites)
            tokens = " ".join(state) if variant == "conventional_tokens" else state
            h.append(f"    {taxon} {tokens}")
    return "\n".join(h + ["  ;", "END;", ""])


def execute_cli(cli_main, alignment: Path, tree: Path, tips: Path, folder: Path, mode: str) -> dict:
    folder.mkdir(parents=True, exist_ok=False)
    cmd = ["find", "--alignment", str(alignment), "--tree", str(tree),
           "--accept-existing-root", "--clade-tips", str(tips), "--mode", mode,
           "--include-ambiguous", "--output", str(folder / "results.tsv"),
           "--members-output", str(folder / "members.txt"), "--report", str(folder / "report.json")]
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cli_main(cmd)
    if code:
        raise RuntimeError(f"CLI failure: {mode}, {alignment.name}: {code}: {stderr.getvalue()[-500:]}")
    report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
    return {"results": sha(folder / "results.tsv"), "members": sha(folder / "members.txt"),
            "reported_sites": report["results"]["reported_sites"],
            "sites_examined": report["results"]["sites_examined"],
            "format": report["inputs"]["alignment"]["format"]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--production", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--cases", type=int, default=30)
    a = p.parse_args()
    source, out = a.production.resolve(strict=True), a.output.absolute()
    if a.cases < 2 or a.cases > 200:
        p.error("--cases must be 2..200")
    if out.exists():
        p.error("output exists; use a fresh location")
    init = (source / "src/branchsnv/__init__.py").read_text()
    if '__version__ = "0.2.0"' not in init and "__version__ = '0.2.0'" not in init:
        p.error("exact BRANCHSNV 0.2.0 source required")
    sys.path.insert(0, str(source / "src"))
    from branchsnv.cli import main as cli_main
    from branchsnv import cli as cli_module
    if Path(cli_module.__file__).resolve() != (source / "src/branchsnv/cli.py").resolve():
        raise RuntimeError("CLI module is not loaded from requested production source")
    out.mkdir(parents=True)
    git = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True)
    source_hashes = {p.relative_to(source).as_posix():sha(p) for p in sorted((source/"src/branchsnv").glob("*.py"))}
    records = []
    for i in range(a.cases):
        case = out / f"case_{i+1:03}"
        case.mkdir()
        nchar = (12, 29, 67)[i % 3]
        sites = generate_states(20261020 + 9973 * i, nchar)
        tree = case / "rooted.nwk"
        tree.write_text(TREE, encoding="utf-8")
        tips = case / "selected.txt"
        tips.write_text("A\nB\n", encoding="utf-8")
        checks = {}
        for variant in VARIANTS:
            alignment = case / f"{variant}.nex"
            alignment.write_text(nexus_text(sites, variant), encoding="utf-8")
            checks[variant] = sha(alignment)
        for mode in MODES:
            outputs = {}
            for variant in VARIANTS:
                outputs[variant] = execute_cli(cli_main,case/f"{variant}.nex",tree,tips,
                                               case / f"{mode}_{variant}",mode)
            reference = outputs[VARIANTS[0]]
            for variant, result in outputs.items():
                for field in ("results", "members", "reported_sites", "sites_examined"):
                    if result[field] != reference[field]:
                        raise AssertionError(f"mismatch case={i+1} mode={mode} variant={variant} field={field}")
                fmt = "transposed_nexus" if variant.startswith("transposed") else "conventional_nexus"
                if result["format"] != fmt:
                    raise AssertionError(f"incorrect format declaration: {variant}: {result['format']}")
                records.append({"case":i+1,"mode":mode,"variant":variant,"nchar":nchar,
                                "input_sha256":checks[variant],"results_sha256":result["results"],
                                "members_sha256":result["members"],"reported_sites":result["reported_sites"]})
        print(f"NEXUS_EQUIVALENCE_PASS case={i+1}/{a.cases}",flush=True)
    with (out / "equivalence_records.tsv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]),delimiter="\t",lineterminator="\n")
        w.writeheader();w.writerows(records)
    report = {"schema":"BRANCHSNV_V020_INPUT_ORIENTATION_EQUIVALENCE_AUDIT_V1",
              "status":"INPUT_ORIENTATION_EQUIVALENCE_PASS", "source_commit":git.stdout.strip() if git.returncode==0 else None,
              "source_python_sha256":source_hashes,"generator_seed_rule":"20261020 + 9973 * case_index",
              "independent_cases":a.cases,"variants":list(VARIANTS),"cli_modes":list(MODES),
              "actual_cli_main_invocations":len(records),"mismatches":0,
              "limitations":"Representation equivalence is not an independent ancestral-reconstruction accuracy proof."}
    (out / "audit_summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    with (out / "SHA256SUMS").open("w",encoding="utf-8") as f:
        for path in sorted(out.rglob("*")):
            if path.is_file() and path.name != "SHA256SUMS":
                f.write(f"{sha(path)}  {path.relative_to(out)}\n")
    print(f"BRANCHSNV_V020_INPUT_ORIENTATION_EQUIVALENCE_PASS cases={a.cases} cli_main_calls={len(records)} output={out}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"INPUT_EQUIVALENCE_AUDIT_FAILED: {type(exc).__name__}: {exc}",file=sys.stderr)
        raise SystemExit(2)
