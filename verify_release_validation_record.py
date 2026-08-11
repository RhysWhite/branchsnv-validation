#!/usr/bin/env python3
"""Verify an archived BRANCHSNV stable-release validation record."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RECORD_TYPE = "BRANCHSNV stable release validation"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"RELEASE VALIDATION RECORD: FAIL\n- {message}")


def parse_manifest(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        try:
            digest, relpath = raw_line.split("  ", 1)
        except ValueError:
            fail(f"{path}: malformed checksum line {line_number}")
        if not SHA256_RE.fullmatch(digest):
            fail(f"{path}: invalid SHA-256 on line {line_number}")
        pure = PurePosixPath(relpath)
        if (
            pure.is_absolute()
            or ".." in pure.parts
            or not pure.parts
            or pure.parts[0] != "results"
        ):
            fail(f"{path}: unsafe or out-of-scope path on line {line_number}: {relpath}")
        normalized = pure.as_posix()
        if normalized in entries:
            fail(f"{path}: duplicate path on line {line_number}: {normalized}")
        entries[normalized] = digest
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify an archived BRANCHSNV stable-release validation record."
    )
    parser.add_argument("--record-dir", required=True, type=Path)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--expected-production-commit", required=True)
    parser.add_argument("--expected-validation-framework-commit", required=True)
    args = parser.parse_args()

    root = args.record_dir.resolve()
    record_path = root / "record.json"
    manifest_path = root / "checksums.sha256"
    results_dir = root / "results"

    for required in (record_path, manifest_path):
        if not required.is_file():
            fail(f"missing required file: {required}")
    if not results_dir.is_dir():
        fail(f"missing results directory: {results_dir}")

    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {record_path}: {exc}")

    expected_fields = {
        "schema_version": 1,
        "record_type": RECORD_TYPE,
        "branchsnv_version": args.expected_version,
        "overall_pass": True,
        "production_commit_at_run": args.expected_production_commit,
        "validation_framework_commit": args.expected_validation_framework_commit,
    }
    for key, expected in expected_fields.items():
        actual = record.get(key)
        if actual != expected:
            fail(f"{key} is {actual!r}; expected {expected!r}")

    for commit_key in ("production_commit_at_run", "validation_framework_commit"):
        if not re.fullmatch(r"[0-9a-f]{40}", str(record.get(commit_key, ""))):
            fail(f"{commit_key} is not a full 40-character lowercase Git commit")

    expected_manifest_digest = record.get("results_checksum_manifest_sha256")
    if not SHA256_RE.fullmatch(str(expected_manifest_digest or "")):
        fail("results_checksum_manifest_sha256 is missing or malformed")
    actual_manifest_digest = sha256_file(manifest_path)
    if actual_manifest_digest != expected_manifest_digest:
        fail(
            "checksums.sha256 digest does not match "
            "record.json results_checksum_manifest_sha256"
        )

    manifest = parse_manifest(manifest_path)
    actual_files = {
        "results/" + path.relative_to(results_dir).as_posix()
        for path in results_dir.rglob("*")
        if path.is_file()
    }

    if set(manifest) != actual_files:
        missing = sorted(actual_files - set(manifest))
        extra = sorted(set(manifest) - actual_files)
        detail = []
        if missing:
            detail.append(f"unlisted result files: {missing}")
        if extra:
            detail.append(f"manifest paths without files: {extra}")
        fail("; ".join(detail))

    recorded_count = record.get("result_file_count")
    if recorded_count != len(actual_files):
        fail(
            f"result_file_count is {recorded_count!r}; "
            f"actual result file count is {len(actual_files)}"
        )

    for relpath, expected_digest in sorted(manifest.items()):
        actual_digest = sha256_file(root / relpath)
        if actual_digest != expected_digest:
            fail(
                f"checksum mismatch for {relpath}: "
                f"{actual_digest} != {expected_digest}"
            )

    original_capture = record.get("original_capture")
    if not isinstance(original_capture, dict):
        fail("original_capture is missing or not an object")
    for key in ("zip_sha256", "external_manifest_sha256"):
        if not SHA256_RE.fullmatch(str(original_capture.get(key, ""))):
            fail(f"original_capture.{key} is missing or malformed")

    verification = record.get("verification")
    if not isinstance(verification, dict):
        fail("verification is missing or not an object")
    required_verification = {
        "production_source_identity": "verified (13 Python files)",
        "validation_script_identity": "verified",
        "deterministic_analytical_outputs": "exact match to canonical scientific snapshot",
        "experiments_01_to_06_headline_and_exact_pass_criteria": "verified",
        "experiment_04_protocol": "3 repetitions; 39 measured runs",
    }
    for key, expected in required_verification.items():
        actual = verification.get(key)
        if actual != expected:
            fail(f"verification.{key} is {actual!r}; expected {expected!r}")

    print("RELEASE VALIDATION RECORD: PASS")
    print(f"- record directory: {root}")
    print(f"- BRANCHSNV version: {args.expected_version}")
    print(f"- result files: {len(actual_files)}")
    print("- checksum manifest identity: verified")
    print("- archived result checksums: verified")
    print("- production and validation-framework provenance: verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
