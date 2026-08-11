#!/usr/bin/env python3
"""Run end-to-end BRANCHSNV scalability benchmarks with GNU time."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def branchsnv_version(branchsnv_source: Path) -> str:
    init_path = branchsnv_source / "src" / "branchsnv" / "__init__.py"
    text = init_path.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    if not match:
        raise ValueError(
            f"Unable to read BRANCHSNV version from production source: {init_path}"
        )
    return match.group(1)


def cpu_model() -> str:
    try:
        text = Path("/proc/cpuinfo").read_text(encoding="utf-8")
        match = re.search(r"^model name\s*:\s*(.+)$", text, re.MULTILINE)
        return match.group(1).strip() if match else platform.processor()
    except OSError:
        return platform.processor()


def memory_total_bytes() -> int | None:
    try:
        text = Path("/proc/meminfo").read_text(encoding="utf-8")
        match = re.search(r"^MemTotal:\s+(\d+)\s+kB$", text, re.MULTILINE)
        return int(match.group(1)) * 1024 if match else None
    except OSError:
        return None


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-root", type=Path, required=True)
    parser.add_argument("--branchsnv-source", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--results-dir", type=Path, required=True)
    args = parser.parse_args()

    experiment_dir = args.validation_root / "experiments" / "04_scalability"
    input_root = experiment_dir / "inputs"
    manifest_path = input_root / "manifest.json"
    if not manifest_path.exists():
        subprocess.run(
            [sys.executable, str(experiment_dir / "generate_inputs.py"), "--output-root", str(input_root)],
            check=True,
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    datasets = {entry["dataset_id"]: entry for entry in manifest["datasets"]}

    # Scaling uses the most comprehensive mode. A representative dataset compares all modes.
    jobs: list[tuple[str, str, int]] = []
    for dataset_id in sorted(datasets):
        for replicate in range(1, args.repetitions + 1):
            jobs.append((dataset_id, "both", replicate))
    representative = "t500_s10000"
    for mode in ("fixed-exclusive", "parsimony"):
        for replicate in range(1, args.repetitions + 1):
            jobs.append((representative, mode, replicate))
    random.Random(20260731).shuffle(jobs)

    args.results_dir.mkdir(parents=True, exist_ok=True)
    raw_rows: list[dict[str, object]] = []
    time_program = shutil.which("time") or "/usr/bin/time"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(args.branchsnv_source / "src")
    env["PYTHONHASHSEED"] = "0"

    # Warm-up excludes interpreter and filesystem cold-start peculiarities from the first measured job.
    warm = datasets["t250_s1000"]
    with tempfile.TemporaryDirectory(prefix="branchsnv_benchmark_warmup_") as tmp:
        tmp_path = Path(tmp)
        command = [
            sys.executable, "-m", "branchsnv", "find",
            "--alignment", str(experiment_dir / warm["alignment"]),
            "--tree", str(experiment_dir / warm["tree"]),
            "--accept-existing-root",
            "--clade-tips", str(experiment_dir / warm["focal_tips"]),
            "--mode", "both",
            "--output", str(tmp_path / "results.tsv"),
            "--members-output", str(tmp_path / "members.txt"),
            "--report", str(tmp_path / "report.json"),
        ]
        subprocess.run(command, env=env, check=True, stdout=subprocess.DEVNULL)

    for job_number, (dataset_id, mode, replicate) in enumerate(jobs, start=1):
        entry = datasets[dataset_id]
        with tempfile.TemporaryDirectory(prefix="branchsnv_benchmark_") as tmp:
            tmp_path = Path(tmp)
            time_path = tmp_path / "time.tsv"
            output_path = tmp_path / "results.tsv"
            members_path = tmp_path / "members.txt"
            report_path = tmp_path / "report.json"
            command = [
                time_program,
                "-f", "%e\t%U\t%S\t%M\t%P\t%x",
                "-o", str(time_path),
                sys.executable, "-m", "branchsnv", "find",
                "--alignment", str(experiment_dir / entry["alignment"]),
                "--tree", str(experiment_dir / entry["tree"]),
                "--accept-existing-root",
                "--clade-tips", str(experiment_dir / entry["focal_tips"]),
                "--mode", mode,
                "--output", str(output_path),
                "--members-output", str(members_path),
                "--report", str(report_path),
            ]
            completed = subprocess.run(command, env=env, text=True, capture_output=True)
            if completed.returncode != 0:
                raise RuntimeError(
                    f"Benchmark failed for {dataset_id}, {mode}, replicate {replicate}:\n"
                    f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )
            wall, user, system, peak_rss_kb, cpu_percent, exit_status = time_path.read_text().strip().split("\t")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            raw_rows.append({
                "job_order": job_number,
                "dataset_id": dataset_id,
                "ntax": entry["ntax"],
                "nchar": entry["nchar"],
                "focal_descendants": entry["focal_descendants"],
                "alignment_bytes": entry["alignment_bytes"],
                "mode": mode,
                "replicate": replicate,
                "wall_seconds": float(wall),
                "user_seconds": float(user),
                "system_seconds": float(system),
                "peak_rss_kb": int(peak_rss_kb),
                "peak_rss_mib": round(int(peak_rss_kb) / 1024, 3),
                "cpu_percent": cpu_percent,
                "exit_status": int(exit_status),
                "reported_sites": report["results"]["reported_sites"],
                "results_bytes": output_path.stat().st_size,
                "report_sha256": sha256(report_path),
            })
            print(f"[{job_number}/{len(jobs)}] {dataset_id} mode={mode} rep={replicate}: {wall}s, {int(peak_rss_kb)/1024:.1f} MiB", flush=True)

    raw_fields = list(raw_rows[0].keys())
    write_tsv(args.results_dir / "raw_runs.tsv", raw_rows, raw_fields)

    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in raw_rows:
        grouped[(str(row["dataset_id"]), str(row["mode"]))].append(row)
    summary_rows: list[dict[str, object]] = []
    for (dataset_id, mode), rows in sorted(grouped.items()):
        walls = [float(row["wall_seconds"]) for row in rows]
        memories = [float(row["peak_rss_mib"]) for row in rows]
        first = rows[0]
        summary_rows.append({
            "dataset_id": dataset_id,
            "ntax": first["ntax"],
            "nchar": first["nchar"],
            "focal_descendants": first["focal_descendants"],
            "alignment_bytes": first["alignment_bytes"],
            "mode": mode,
            "repetitions": len(rows),
            "reported_sites": first["reported_sites"],
            "wall_median_seconds": round(statistics.median(walls), 3),
            "wall_min_seconds": round(min(walls), 3),
            "wall_max_seconds": round(max(walls), 3),
            "peak_rss_median_mib": round(statistics.median(memories), 3),
            "peak_rss_min_mib": round(min(memories), 3),
            "peak_rss_max_mib": round(max(memories), 3),
        })
    summary_fields = list(summary_rows[0].keys())
    write_tsv(args.results_dir / "benchmark_summary.tsv", summary_rows, summary_fields)

    source_files = sorted((args.branchsnv_source / "src" / "branchsnv").glob("*.py"))
    source_hashes = {str(path.relative_to(args.branchsnv_source)): sha256(path) for path in source_files}
    metadata = {
        "experiment": "04_scalability",
        "branchsnv_version": branchsnv_version(args.branchsnv_source),
        "branchsnv_source_root": str(args.branchsnv_source),
        "branchsnv_source_files_sha256": source_hashes,
        "input_manifest_sha256": sha256(manifest_path),
        "repetitions": args.repetitions,
        "run_order_seed": 20260731,
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_model": cpu_model(),
        "logical_cpus_visible": os.cpu_count(),
        "memory_total_bytes_visible": memory_total_bytes(),
        "gnu_time": subprocess.run([time_program, "--version"], text=True, capture_output=True).stdout.splitlines()[0],
        "environment": {
            "PYTHONHASHSEED": "0",
            "PYTHONPATH": str(args.branchsnv_source / "src"),
        },
        "design": manifest["design"],
        "notes": [
            "Each invocation was a fresh Python process and included parsing, validation, analysis, and output generation.",
            "Scaling configurations used mode=both; all three modes were compared on t500_s10000.",
            "BRANCHSNV is single-process; visible logical CPU count describes the environment, not parallel execution.",
        ],
    }
    (args.results_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    summary = {
        "experiment": "04_scalability",
        "status": "complete",
        "datasets": len(datasets),
        "measured_runs": len(raw_rows),
        "repetitions_per_configuration": args.repetitions,
        "failed_runs": sum(int(row["exit_status"]) != 0 for row in raw_rows),
        "largest_taxon_configuration": max((row for row in summary_rows if row["mode"] == "both" and row["nchar"] == 10000), key=lambda row: int(row["ntax"])),
        "largest_site_configuration": max((row for row in summary_rows if row["mode"] == "both" and row["ntax"] == 250), key=lambda row: int(row["nchar"])),
        "representative_mode_comparison": [row for row in summary_rows if row["dataset_id"] == representative],
    }
    (args.results_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
