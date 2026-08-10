#!/usr/bin/env python3
"""Verify integrity and headline claims of the committed publication snapshot."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_manifest(manifest: Path, base: Path) -> list[str]:
    failures: list[str] = []
    for line_no, raw in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            expected, rel = line.split(maxsplit=1)
        except ValueError:
            failures.append(f"{manifest}: malformed line {line_no}")
            continue
        rel = rel.lstrip("*")
        path = base / rel
        if not path.is_file():
            failures.append(f"missing: {path.relative_to(ROOT)}")
            continue
        observed = sha256(path)
        if observed != expected:
            failures.append(
                f"checksum mismatch: {path.relative_to(ROOT)} expected {expected} observed {observed}"
            )
    return failures


def load_summary(name: str) -> dict:
    path = ROOT / "results" / name / "summary.json"
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []

    failures.extend(check_manifest(ROOT / "inputs" / "empirical" / "checksums.sha256", ROOT / "inputs" / "empirical"))
    failures.extend(check_manifest(ROOT / "results" / "checksums.sha256", ROOT))

    s1 = load_summary("01_exact_oracle")
    require(s1.get("exact_agreement") is True, "Experiment 01 exact_agreement is not true", failures)
    require(s1.get("total_comparisons") == 128881, "Experiment 01 comparison count != 128,881", failures)
    require(s1.get("total_mismatches") == 0, "Experiment 01 mismatch count != 0", failures)
    require(s1.get("status_counts") == {
        "no_change": 85558,
        "unambiguous_change": 3605,
        "change_state_ambiguous": 814,
        "placement_ambiguous": 38904,
    }, "Experiment 01 status counts differ from publication snapshot", failures)

    s2 = load_summary("02_deliberate_faults")
    require(s2.get("all_faults_detected") is True, "Experiment 02 did not detect every fault", failures)
    require(s2.get("faults_evaluated") == 10 and s2.get("faults_detected") == 10,
            "Experiment 02 fault total != 10/10", failures)
    require(s2.get("total_challenges") == 280216, "Experiment 02 challenge count != 280,216", failures)
    require(s2.get("total_differentiating_challenges") == 118916,
            "Experiment 02 differentiating count != 118,916", failures)

    s3 = load_summary("03_published_datasets")
    t3 = s3.get("public_comparison", {}).get("totals", {})
    require(s3.get("overall_pass") is True, "Experiment 03 overall_pass is not true", failures)
    require(t3.get("branch_matrix_comparisons") == 816, "Experiment 03 branch-matrix comparisons != 816", failures)
    require(t3.get("branchsnv_unambiguous_events") == 877 and t3.get("exact_unambiguous_matches") == 877,
            "Experiment 03 exact unambiguous concordance != 877/877", failures)
    require(t3.get("snppar_events") == 943 and t3.get("snppar_only_events") == 66,
            "Experiment 03 SNPPar total/remaining != 943/66", failures)
    require(t3.get("snppar_only_supported_as_branchsnv_placement_ambiguous") == 66,
            "Experiment 03 placement-ambiguous support != 66/66", failures)
    require(t3.get("branchsnv_only_unambiguous") == 0 and t3.get("direction_differences") == 0,
            "Experiment 03 contains an unexpected unique/direction-discordant event", failures)

    s4 = load_summary("04_scalability")
    require(s4.get("status") == "complete" and s4.get("failed_runs") == 0,
            "Experiment 04 is not complete with zero failures", failures)
    require(s4.get("measured_runs") == 39, "Experiment 04 measured run count != 39", failures)
    require(s4.get("repetitions_per_configuration") == 3, "Experiment 04 repetitions != 3", failures)

    s5 = load_summary("05_published_focal_branches")
    t5 = s5.get("totals", {})
    require(s5.get("overall_pass") is True, "Experiment 05 overall_pass is not true", failures)
    require(t5.get("published_snvs") == 46 and t5.get("exact_position_direction") == 46,
            "Experiment 05 focal-branch concordance != 46/46", failures)
    require(t5.get("all_fixed_exclusive") is True and t5.get("all_unambiguous_change") is True,
            "Experiment 05 reproduced SNVs do not all satisfy both definitions", failures)
    indels = s5.get("published_non_snv_events_outside_scope", {})
    require(set(indels) == {"ak3", "st97", "oxa48"}, "Experiment 05 must record one out-of-scope indel for each focal branch", failures)
    require(indels.get("oxa48", {}).get("position") == 4871038,
            "Experiment 05 OXA-48 insertion position != 4,871,038", failures)

    s6 = load_summary("06_empirical_cross_classification")
    a6 = s6.get("analysis", {})
    t6 = a6.get("totals", {})
    q6 = s6.get("production_qc", {})
    require(s6.get("overall_pass") is True and s6.get("headline_totals_match") is True,
            "Experiment 06 overall/headline checks did not pass", failures)
    require(t6 == {
        "taxa": 912,
        "variable_sites": 31457,
        "eligible_non_root_adjacent_branches": 1804,
        "branch_site_comparisons": 16073690,
        "informative": 31644,
        "both": 30817,
        "unambiguous_not_fixed": 675,
        "placement_ambiguous": 152,
        "outside_intersection": 827,
    }, "Experiment 06 headline totals differ from publication snapshot", failures)
    require(a6.get("nonexclusivity_mechanisms") == {
        "derived_state_outside": 645,
        "descendant_not_fixed": 30,
    }, "Experiment 06 non-exclusivity mechanism counts differ", failures)
    require(a6.get("root_adjacent_sensitivity") == {
        "informative": 740,
        "fixed_plus_placement": 703,
        "not_fixed_plus_placement": 37,
    }, "Experiment 06 root-sensitivity counts differ", failures)
    require(q6.get("passed") is True and q6.get("exact_records") == 1617 and q6.get("discrepancies") == 0,
            "Experiment 06 production QC != 1,617/1,617 exact", failures)
    require(q6.get("selected_branches") == 8 and q6.get("branch_site_analyses") == 64236,
            "Experiment 06 production-QC scope differs", failures)

    versions = {
        s1.get("branchsnv_version"),
        s2.get("branchsnv_version"),
        s3.get("branchsnv_version"),
        s5.get("branchsnv_version"),
        a6.get("production_source", {}).get("branchsnv_version"),
    }
    require(versions == {"0.1.0a1"}, f"BRANCHSNV version mismatch across snapshots: {sorted(str(x) for x in versions)}", failures)

    if failures:
        print("PUBLICATION SNAPSHOT: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("PUBLICATION SNAPSHOT: PASS")
    print("- empirical input checksums: verified")
    print("- committed result checksums: verified")
    print("- Experiments 01–06 headline claims: verified")
    print("- BRANCHSNV analytical version: 0.1.0a1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
