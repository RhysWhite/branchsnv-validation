#!/usr/bin/env python3
"""Verify a freshly reproduced BRANCHSNV validation result tree.

Unlike ``verify_publication_snapshot.py``, which verifies the immutable committed
v0.1.0a1 manuscript snapshot, this verifier operates on a caller-supplied result
directory.  When a production source checkout is supplied it also checks that the
recorded BRANCHSNV version and source hashes correspond to that exact checkout.
"""
from __future__ import annotations

import argparse
import csv
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_ANALYSIS_SOFTWARE = {
    "numpy": "2.3.5",
    "pandas": "2.2.3",
    "numba": "0.65.1",
}
EXPECTED_STATUS_COUNTS = {
    "no_change": 85558,
    "unambiguous_change": 3605,
    "change_state_ambiguous": 814,
    "placement_ambiguous": 38904,
}
EXPECTED_SNP_PAR_TOTALS = {
    "datasets": 4,
    "organisms": 2,
    "branch_matrix_comparisons": 816,
    "exact_edge_comparisons": 783,
    "method_difference_edge_comparisons": 33,
    "snppar_events": 943,
    "branchsnv_unambiguous_events": 877,
    "exact_unambiguous_matches": 877,
    "snppar_only_events": 66,
    "snppar_only_supported_as_branchsnv_placement_ambiguous": 66,
    "branchsnv_only_unambiguous": 0,
    "direction_differences": 0,
}
EXPECTED_EMPIRICAL_TOTALS = {
    "taxa": 912,
    "variable_sites": 31457,
    "eligible_non_root_adjacent_branches": 1804,
    "branch_site_comparisons": 16073690,
    "informative": 31644,
    "both": 30817,
    "unambiguous_not_fixed": 675,
    "placement_ambiguous": 152,
    "outside_intersection": 827,
}
EXPECTED_MECHANISMS = {
    "derived_state_outside": 645,
    "descendant_not_fixed": 30,
}
EXPECTED_ROOT_SENSITIVITY = {
    "informative": 740,
    "fixed_plus_placement": 703,
    "not_fixed_plus_placement": 37,
}


DETERMINISTIC_FILES = [
    "01_exact_oracle/mismatches.tsv",
    "01_exact_oracle/status_summary.tsv",
    "01_exact_oracle/topology_summary.tsv",
    "02_deliberate_faults/fault_summary.tsv",
    "02_deliberate_faults/witnesses.tsv",
    "03_published_datasets/branch_summary.tsv",
    "03_published_datasets/dataset_summary.tsv",
    "03_published_datasets/event_comparison.tsv",
    "03_published_datasets/placement_ambiguous_snppar_events.tsv",
    "03_published_datasets/public_input_checksums.tsv",
    "05_published_focal_branches/focal_branch_comparison.tsv",
    "05_published_focal_branches/ak3_members.txt",
    "05_published_focal_branches/ak3_results.tsv",
    "05_published_focal_branches/st97_members.txt",
    "05_published_focal_branches/st97_results.tsv",
    "05_published_focal_branches/oxa48_members.txt",
    "05_published_focal_branches/oxa48_results.tsv",
    "06_empirical_cross_classification/branch_cross_classification.tsv",
    "06_empirical_cross_classification/branch_stratification.tsv",
    "06_empirical_cross_classification/dataset_summary.tsv",
    "06_empirical_cross_classification/informative_events.tsv",
    "06_empirical_cross_classification/input_checksums.tsv",
    "06_empirical_cross_classification/mechanism_summary.tsv",
    "06_empirical_cross_classification/production_qc.tsv",
    "06_empirical_cross_classification/production_qc_discrepancies.tsv",
    "06_empirical_cross_classification/root_adjacent.tsv",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path, failures: list[str]) -> dict:
    if not path.is_file():
        failures.append(f"missing: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        failures.append(f"cannot read JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        failures.append(f"expected JSON object: {path}")
        return {}
    return value


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def branchsnv_version(root: Path) -> str:
    init_path = root / "src" / "branchsnv" / "__init__.py"
    text = init_path.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    if not match:
        raise ValueError(f"Unable to read BRANCHSNV version from {init_path}")
    return match.group(1)


def production_hashes(root: Path) -> dict[str, str]:
    package = root / "src" / "branchsnv"
    paths = sorted(package.glob("*.py"))
    if not paths:
        raise ValueError(f"No BRANCHSNV Python source files found under {package}")
    return {str(path.relative_to(root)): sha256(path) for path in paths}


def script_hash(relative: str) -> str:
    return sha256(ROOT / relative)




def normalized_summary(experiment: str, value: dict) -> dict:
    data = copy.deepcopy(value)
    if experiment == "01":
        for key in ("branchsnv_version", "branchsnv_parsimony_sha256", "validation_script_sha256"):
            data.pop(key, None)
    elif experiment == "02":
        data.pop("branchsnv_version", None)
        data.pop("source_sha256", None)
    elif experiment == "03":
        for key in ("branchsnv_version", "branchsnv_analysis_sha256", "branchsnv_parsimony_sha256", "validation_script_sha256"):
            data.pop(key, None)
    elif experiment == "05":
        data.pop("branchsnv_version", None)
    elif experiment == "06":
        analysis = data.get("analysis")
        if isinstance(analysis, dict):
            source = analysis.get("production_source")
            if isinstance(source, dict):
                for key in ("branchsnv_version", "branchsnv_analysis_sha256", "branchsnv_parsimony_sha256"):
                    source.pop(key, None)
        qc = data.get("production_qc")
        if isinstance(qc, dict):
            for key in ("branchsnv_analysis_sha256", "branchsnv_parsimony_sha256"):
                qc.pop(key, None)
    return data


def compare_deterministic_outputs(results: Path, summaries: dict[str, dict], failures: list[str]) -> None:
    canonical = ROOT / "results"
    canonical_summary_paths = {
        "01": canonical / "01_exact_oracle" / "summary.json",
        "02": canonical / "02_deliberate_faults" / "summary.json",
        "03": canonical / "03_published_datasets" / "summary.json",
        "05": canonical / "05_published_focal_branches" / "summary.json",
        "06": canonical / "06_empirical_cross_classification" / "summary.json",
    }
    for experiment, path in canonical_summary_paths.items():
        expected = load_json(path, failures)
        if normalized_summary(experiment, summaries[experiment]) != normalized_summary(experiment, expected):
            failures.append(
                f"Experiment {experiment} deterministic summary differs from the canonical scientific snapshot after provenance fields are removed"
            )

    for relative in DETERMINISTIC_FILES:
        observed = results / relative
        expected = canonical / relative
        if not observed.is_file():
            failures.append(f"missing deterministic result: {observed}")
            continue
        if not expected.is_file():
            failures.append(f"missing canonical deterministic result: {expected}")
            continue
        if sha256(observed) != sha256(expected):
            failures.append(f"deterministic result differs from canonical snapshot: {relative}")

    # Benchmark timing and memory values are environment-specific, but the benchmark
    # configurations and reported-site counts are deterministic.
    observed_benchmark = results / "04_scalability" / "benchmark_summary.tsv"
    expected_benchmark = canonical / "04_scalability" / "benchmark_summary.tsv"
    if not observed_benchmark.is_file() or not expected_benchmark.is_file():
        failures.append("Experiment 04 benchmark_summary.tsv is missing")
        return

    static_fields = [
        "dataset_id", "ntax", "nchar", "focal_descendants", "alignment_bytes",
        "mode", "reported_sites",
    ]
    def static_rows(path: Path) -> list[tuple[str, ...]]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = csv.DictReader(handle, delimiter="\t")
            return sorted(tuple(row[field] for field in static_fields) for row in rows)
    try:
        observed_rows = static_rows(observed_benchmark)
        expected_rows = static_rows(expected_benchmark)
    except (OSError, KeyError, csv.Error) as exc:
        failures.append(f"cannot compare Experiment 04 benchmark design: {exc}")
    else:
        if observed_rows != expected_rows:
            failures.append("Experiment 04 deterministic benchmark configurations differ from the canonical design")


def check_recorded_source_identity(
    *,
    expected_version: str,
    source_hashes: dict[str, str] | None,
    summaries: dict[str, dict],
    metadata: dict[str, dict],
    failures: list[str],
) -> None:
    s1 = summaries["01"]
    s2 = summaries["02"]
    s3 = summaries["03"]
    s5 = summaries["05"]
    a6 = summaries["06"].get("analysis", {})
    q6 = summaries["06"].get("production_qc", {})
    m4 = metadata["04"]
    m5 = metadata["05"]
    m6a = metadata["06_analysis"]
    m6q = metadata["06_qc"]

    versions = {
        s1.get("branchsnv_version"),
        s2.get("branchsnv_version"),
        s3.get("branchsnv_version"),
        m4.get("branchsnv_version"),
        s5.get("branchsnv_version"),
        m5.get("branchsnv_version"),
        a6.get("production_source", {}).get("branchsnv_version"),
        m6a.get("branchsnv_version"),
    }
    require(
        versions == {expected_version},
        f"BRANCHSNV version mismatch across reproduced results: expected {expected_version!r}, observed {sorted(str(x) for x in versions)}",
        failures,
    )

    # Historical snapshots can be checked in headline-only mode with --expected-version.
    # Fresh release reruns supply --branchsnv-root; in that mode bind the outputs to
    # both the production source and the validation scripts in this checkout.
    if source_hashes is None:
        return

    require(
        s1.get("validation_script_sha256") == script_hash("experiments/01_exact_oracle/run.py"),
        "Experiment 01 validation-script hash does not match this validation checkout",
        failures,
    )
    source2 = s2.get("source_sha256", {})
    require(
        source2.get("experiment_01_oracle") == script_hash("experiments/01_exact_oracle/run.py"),
        "Experiment 02 recorded Experiment 01 oracle hash does not match this validation checkout",
        failures,
    )
    require(
        source2.get("experiment_02_runner") == script_hash("experiments/02_deliberate_faults/run.py"),
        "Experiment 02 validation-script hash does not match this validation checkout",
        failures,
    )
    require(
        s3.get("validation_script_sha256") == script_hash("experiments/03_published_datasets/run.py"),
        "Experiment 03 validation-script hash does not match this validation checkout",
        failures,
    )
    require(
        m5.get("validation_script_sha256") == script_hash("experiments/05_published_focal_branches/run.py"),
        "Experiment 05 validation-script hash does not match this validation checkout",
        failures,
    )
    require(
        m6a.get("validation_script_sha256") == script_hash("experiments/06_empirical_cross_classification/run.py"),
        "Experiment 06 analysis-script hash does not match this validation checkout",
        failures,
    )
    require(
        m6q.get("validation_script_sha256") == script_hash("experiments/06_empirical_cross_classification/production_qc.py"),
        "Experiment 06 production-QC script hash does not match this validation checkout",
        failures,
    )

    def expected(rel: str) -> str | None:
        return source_hashes.get(f"src/branchsnv/{rel}")

    require(
        s1.get("branchsnv_parsimony_sha256") == expected("parsimony.py"),
        "Experiment 01 parsimony hash does not match supplied BRANCHSNV source",
        failures,
    )
    require(
        source2.get("branchsnv_analysis") == expected("analysis.py")
        and source2.get("branchsnv_newick") == expected("newick.py")
        and source2.get("branchsnv_parsimony") == expected("parsimony.py"),
        "Experiment 02 production-source hashes do not match supplied BRANCHSNV source",
        failures,
    )
    require(
        s3.get("branchsnv_analysis_sha256") == expected("analysis.py")
        and s3.get("branchsnv_parsimony_sha256") == expected("parsimony.py"),
        "Experiment 03 production-source hashes do not match supplied BRANCHSNV source",
        failures,
    )
    require(
        m4.get("branchsnv_source_files_sha256") == source_hashes,
        "Experiment 04 full production-source hash map does not match supplied BRANCHSNV source",
        failures,
    )
    require(
        m5.get("branchsnv_analysis_sha256") == expected("analysis.py")
        and m5.get("branchsnv_parsimony_sha256") == expected("parsimony.py"),
        "Experiment 05 production-source hashes do not match supplied BRANCHSNV source",
        failures,
    )
    p6 = a6.get("production_source", {})
    require(
        p6.get("branchsnv_analysis_sha256") == expected("analysis.py")
        and p6.get("branchsnv_parsimony_sha256") == expected("parsimony.py"),
        "Experiment 06 analysis production-source hashes do not match supplied BRANCHSNV source",
        failures,
    )
    require(
        q6.get("branchsnv_analysis_sha256") == expected("analysis.py")
        and q6.get("branchsnv_parsimony_sha256") == expected("parsimony.py"),
        "Experiment 06 production-QC source hashes do not match supplied BRANCHSNV source",
        failures,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--branchsnv-root", type=Path)
    parser.add_argument("--expected-version")
    parser.add_argument("--benchmark-repetitions", type=int, default=3)
    args = parser.parse_args()

    if args.branchsnv_root is None and args.expected_version is None:
        parser.error("provide --branchsnv-root and/or --expected-version")
    if args.benchmark_repetitions < 1:
        parser.error("--benchmark-repetitions must be at least 1")

    failures: list[str] = []
    results = args.results_dir.resolve()
    require(results.is_dir(), f"results directory does not exist: {results}", failures)

    source_hashes: dict[str, str] | None = None
    inferred_version: str | None = None
    if args.branchsnv_root is not None:
        production = args.branchsnv_root.resolve()
        try:
            inferred_version = branchsnv_version(production)
            source_hashes = production_hashes(production)
        except (OSError, UnicodeError, ValueError) as exc:
            failures.append(str(exc))
    expected_version = args.expected_version or inferred_version
    if expected_version is None:
        failures.append("unable to determine expected BRANCHSNV version")
        expected_version = "<unknown>"
    if args.expected_version is not None and inferred_version is not None:
        require(
            args.expected_version == inferred_version,
            f"supplied --expected-version {args.expected_version!r} does not match production source version {inferred_version!r}",
            failures,
        )

    summaries = {
        "01": load_json(results / "01_exact_oracle" / "summary.json", failures),
        "02": load_json(results / "02_deliberate_faults" / "summary.json", failures),
        "03": load_json(results / "03_published_datasets" / "summary.json", failures),
        "04": load_json(results / "04_scalability" / "summary.json", failures),
        "05": load_json(results / "05_published_focal_branches" / "summary.json", failures),
        "06": load_json(results / "06_empirical_cross_classification" / "summary.json", failures),
    }
    metadata = {
        "04": load_json(results / "04_scalability" / "run_metadata.json", failures),
        "05": load_json(results / "05_published_focal_branches" / "run_metadata.json", failures),
        "06_analysis": load_json(results / "06_empirical_cross_classification" / "analysis_run_metadata.json", failures),
        "06_qc": load_json(results / "06_empirical_cross_classification" / "production_qc_run_metadata.json", failures),
    }

    s1 = summaries["01"]
    require(s1.get("exact_agreement") is True, "Experiment 01 exact_agreement is not true", failures)
    require(s1.get("total_comparisons") == 128881, "Experiment 01 comparison count != 128,881", failures)
    require(s1.get("total_mismatches") == 0, "Experiment 01 mismatch count != 0", failures)
    require(s1.get("status_counts") == EXPECTED_STATUS_COUNTS, "Experiment 01 status counts differ", failures)

    s2 = summaries["02"]
    require(s2.get("all_faults_detected") is True, "Experiment 02 did not detect every fault", failures)
    require(s2.get("faults_evaluated") == 10 and s2.get("faults_detected") == 10, "Experiment 02 fault total != 10/10", failures)
    require(s2.get("total_challenges") == 280216, "Experiment 02 challenge count != 280,216", failures)
    require(s2.get("total_differentiating_challenges") == 118916, "Experiment 02 differentiating count != 118,916", failures)

    s3 = summaries["03"]
    require(s3.get("overall_pass") is True, "Experiment 03 overall_pass is not true", failures)
    public3 = s3.get("public_comparison", {})
    require(public3.get("passed") is True, "Experiment 03 public comparison did not pass", failures)
    require(public3.get("totals") == EXPECTED_SNP_PAR_TOTALS, "Experiment 03 totals differ", failures)

    s4 = summaries["04"]
    expected_runs = 13 * args.benchmark_repetitions
    require(s4.get("status") == "complete" and s4.get("failed_runs") == 0, "Experiment 04 is not complete with zero failures", failures)
    require(s4.get("datasets") == 11, "Experiment 04 dataset count != 11", failures)
    require(s4.get("repetitions_per_configuration") == args.benchmark_repetitions, "Experiment 04 repetition count differs from requested protocol", failures)
    require(s4.get("measured_runs") == expected_runs, f"Experiment 04 measured run count != {expected_runs}", failures)
    require(metadata["04"].get("repetitions") == args.benchmark_repetitions, "Experiment 04 metadata repetition count differs", failures)

    s5 = summaries["05"]
    t5 = s5.get("totals", {})
    require(s5.get("overall_pass") is True, "Experiment 05 overall_pass is not true", failures)
    require(t5.get("published_snvs") == 46 and t5.get("exact_position_direction") == 46, "Experiment 05 focal-branch concordance != 46/46", failures)
    require(t5.get("all_fixed_exclusive") is True and t5.get("all_unambiguous_change") is True, "Experiment 05 reproduced SNVs do not all satisfy both definitions", failures)
    datasets5 = {item.get("dataset"): item for item in s5.get("datasets", []) if isinstance(item, dict)}
    require(
        {key: (datasets5.get(key, {}).get("published_snvs"), datasets5.get(key, {}).get("exact_position_direction")) for key in ("ak3", "st97", "oxa48")}
        == {"ak3": (23, 23), "st97": (10, 10), "oxa48": (13, 13)},
        "Experiment 05 dataset-level focal-branch counts differ",
        failures,
    )
    indels = s5.get("published_non_snv_events_outside_scope", {})
    require(set(indels) == {"ak3", "st97", "oxa48"}, "Experiment 05 out-of-scope indel record is incomplete", failures)
    require(indels.get("oxa48", {}).get("position") == 4871038, "Experiment 05 OXA-48 insertion position != 4,871,038", failures)

    s6 = summaries["06"]
    a6 = s6.get("analysis", {})
    t6 = a6.get("totals", {})
    q6 = s6.get("production_qc", {})
    require(s6.get("overall_pass") is True and s6.get("headline_totals_match") is True, "Experiment 06 overall/headline checks did not pass", failures)
    require(t6 == EXPECTED_EMPIRICAL_TOTALS, "Experiment 06 headline totals differ", failures)
    require(a6.get("nonexclusivity_mechanisms") == EXPECTED_MECHANISMS, "Experiment 06 non-exclusivity mechanism counts differ", failures)
    require(a6.get("root_adjacent_sensitivity") == EXPECTED_ROOT_SENSITIVITY, "Experiment 06 root-sensitivity counts differ", failures)
    require(a6.get("software") == EXPECTED_ANALYSIS_SOFTWARE, "Experiment 06 analysis dependency versions differ from the locked publication environment", failures)
    require(q6.get("passed") is True and q6.get("exact_records") == 1617 and q6.get("discrepancies") == 0, "Experiment 06 production QC != 1,617/1,617 exact", failures)
    require(q6.get("selected_branches") == 8 and q6.get("branch_site_analyses") == 64236, "Experiment 06 production-QC scope differs", failures)

    check_recorded_source_identity(
        expected_version=expected_version,
        source_hashes=source_hashes,
        summaries=summaries,
        metadata=metadata,
        failures=failures,
    )
    compare_deterministic_outputs(results, summaries, failures)

    # Bind Experiment 04 to the deterministic benchmark-input manifest used for the
    # publication design. A fresh full run also leaves the generated ignored manifest
    # in place, which must have the same hash.
    canonical_manifest = ROOT / "results" / "04_scalability" / "input_manifest.json"
    require(canonical_manifest.is_file(), "canonical Experiment 04 input manifest is missing", failures)
    if canonical_manifest.is_file():
        require(
            metadata["04"].get("input_manifest_sha256") == sha256(canonical_manifest),
            "Experiment 04 input-manifest hash differs from the canonical deterministic design",
            failures,
        )
    if source_hashes is not None:
        generated_manifest = ROOT / "experiments" / "04_scalability" / "inputs" / "manifest.json"
        require(generated_manifest.is_file(), "Experiment 04 generated input manifest is missing", failures)
        if generated_manifest.is_file():
            require(
                metadata["04"].get("input_manifest_sha256") == sha256(generated_manifest),
                "Experiment 04 input-manifest hash does not match the freshly generated inputs",
                failures,
            )

    if failures:
        print("REPRODUCED RESULTS: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("REPRODUCED RESULTS: PASS")
    print(f"- results directory: {results}")
    print(f"- BRANCHSNV version: {expected_version}")
    if source_hashes is not None:
        print(f"- production source identity: verified ({len(source_hashes)} Python files)")
        print("- validation-script identity: verified")
    else:
        print("- production and validation-script identity: not checked (no --branchsnv-root supplied)")
    print("- deterministic analytical outputs: exact match to canonical scientific snapshot")
    print("- Experiments 01–06 headline and exact pass criteria: verified")
    print(f"- Experiment 04 benchmark protocol: {args.benchmark_repetitions} repetitions, {13 * args.benchmark_repetitions} measured runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
