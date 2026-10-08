#!/usr/bin/env python3
"""Offline Git-object provenance check for Experiment 07 original implementation freeze.

This is NOT a replay of the original execution validator, an assessment of
amendment correctness, or permission to read canonical data/run comparators.
Only the eight specified source artifacts and the original freeze validator
are read through Git object identity.
"""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ORIGINAL_FREEZE = "f48bd14048866820c7a252d935ed2d26cb9407e5"
REVIEWED_ANCHOR = "017fefe32e1b86c955b8957e1be6a4bdf49e7506"
ROOT = "experiments/07_comparative_landscape"
IMPL = f"{ROOT}/comparator_benchmark_execution_v1_impl"
VALIDATOR = f"{ROOT}/comparator_benchmark_execution_v1_implementation_freeze.py"

# Counts come from the independent, read-only jynx Git-history review of the
# exact published anchor. An unreviewed artifact modification must block CI.
REVIEWED_POST_FREEZE_COMMITS = {
    "IMPLEMENTATION.md": 1,
    "adapters.py": 10,
    "environment_recipes.json": 10,
    "generator.py": 0,
    "implementation_manifest.json": 1,
    "metrics.py": 0,
    "source_pins.tsv": 0,
    "toy_validation.py": 9,
}


class ProvenanceError(RuntimeError):
    pass


def git(repo: Path, *args: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.decode("utf-8", errors="replace").strip()
        raise ProvenanceError(f"Git operation {args[0]!r} failed: {message}") from exc


def ancestry(repo: Path, ancestor: str, descendant: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, descendant],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
    )
    if result.returncode != 0:
        raise ProvenanceError(f"Required commit {ancestor[:12]} is not an ancestor of {descendant[:12]}")


def read_frozen_expected(validator_source: bytes) -> dict[str, str]:
    try:
        tree = ast.parse(validator_source.decode("utf-8"), filename=VALIDATOR)
    except (SyntaxError, UnicodeDecodeError) as exc:
        raise ProvenanceError("Original frozen validator cannot be parsed") from exc
    values = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "IMPLEMENTATION_FILES"
            for target in node.targets
        ):
            values.append(ast.literal_eval(node.value))
    if len(values) != 1 or not isinstance(values[0], dict):
        raise ProvenanceError("Expected exactly one literal original IMPLEMENTATION_FILES dictionary")
    expected = values[0]
    if set(expected) != set(REVIEWED_POST_FREEZE_COMMITS):
        raise ProvenanceError("Original freeze artifact set differs from reviewed eight-file set")
    if not all(
        isinstance(name, str) and isinstance(digest, str)
        and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)
        for name, digest in expected.items()
    ):
        raise ProvenanceError("Original freeze contains invalid artifact hash")
    return expected


def verify(
    repo: Path,
    original_freeze: str = ORIGINAL_FREEZE,
    reviewed_anchor: str = REVIEWED_ANCHOR,
    expected_counts: dict[str, int] | None = None,
) -> dict:
    counts = REVIEWED_POST_FREEZE_COMMITS if expected_counts is None else expected_counts
    repo = repo.resolve()
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    original_sha = git(repo, "rev-parse", f"{original_freeze}^{{commit}}").decode().strip()
    anchor_sha = git(repo, "rev-parse", f"{reviewed_anchor}^{{commit}}").decode().strip()
    ancestry(repo, original_sha, anchor_sha)
    ancestry(repo, anchor_sha, head)

    original_validator = git(repo, "show", f"{original_sha}:{VALIDATOR}")
    anchor_validator = git(repo, "show", f"{anchor_sha}:{VALIDATOR}")
    current_validator = git(repo, "show", f"{head}:{VALIDATOR}")
    if anchor_validator != original_validator:
        raise ProvenanceError("Original freeze validator source changed before reviewed anchor")
    if current_validator != anchor_validator:
        raise ProvenanceError("Original freeze validator source changed after reviewed anchor")
    original_expected = read_frozen_expected(original_validator)
    if set(counts) != set(original_expected):
        raise ProvenanceError("Reviewed amendment-count keys do not match original artifacts")

    results = []
    for name, expected_hash in original_expected.items():
        relative = f"{IMPL}/{name}"
        original_bytes = git(repo, "show", f"{original_sha}:{relative}")
        anchor_bytes = git(repo, "show", f"{anchor_sha}:{relative}")
        current_bytes = git(repo, "show", f"{head}:{relative}")
        if hashlib.sha256(original_bytes).hexdigest() != expected_hash:
            raise ProvenanceError(f"Original frozen artifact hash mismatch: {name}")
        if current_bytes != anchor_bytes:
            raise ProvenanceError(f"Unreviewed post-anchor change to frozen lineage: {name}")
        changed_commits = git(
            repo, "log", "--format=%H", f"{original_sha}..{anchor_sha}",
            "--", relative
        ).decode().splitlines()
        n = len(changed_commits)
        if n != counts[name]:
            raise ProvenanceError(
                f"Post-freeze change-count differs for {name}: observed={n}, reviewed={counts[name]}"
            )
        original_equals_anchor = original_bytes == anchor_bytes
        if original_equals_anchor != (n == 0):
            raise ProvenanceError(f"Unexpected revert/change history for {name}")
        results.append({
            "artifact": name,
            "original_frozen_sha256_matches": True,
            "matches_reviewed_anchor_at_head": True,
            "post_freeze_commit_count": n,
            "changed_from_original": not original_equals_anchor,
        })

    return {
        "schema": "BRANCHSNV_EXP07_HISTORICAL_IMPLEMENTATION_PROVENANCE_V1",
        "status": "PASS_ORIGINAL_FREEZE_AND_REVIEWED_ANCHOR_INTEGRITY_ONLY",
        "head": head,
        "original_freeze": original_sha,
        "reviewed_anchor": anchor_sha,
        "original_artifacts_verified": len(results),
        "artifacts": results,
        "original_validator_replayed": False,
        "amendment_authorizations_independently_verified": False,
        "canonical_execution_authorized": False,
    }


def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    try:
        result = verify(repo)
    except (ProvenanceError, OSError, ValueError) as exc:
        print(f"HISTORICAL_IMPLEMENTATION_PROVENANCE=FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    print("HISTORICAL_IMPLEMENTATION_PROVENANCE=PASS")
    print("ORIGINAL_VALIDATOR_REPLAYED=FALSE")
    print("AMENDMENT_AUTHORIZATIONS_INDEPENDENTLY_VERIFIED=FALSE")
    print("CANONICAL_EXECUTION_AUTHORIZED=FALSE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
