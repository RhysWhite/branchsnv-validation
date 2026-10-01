from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "7a793f5a6b8aa3e0e99c1b0b3c49b1e4af46a4b7"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

CANDIDATE_RELS = {
    "experiments/07_comparative_landscape/pre_review_triage_future_text_reconciliation_v1.py",
    "experiments/07_comparative_landscape/test_pre_review_triage_future_text_reconciliation_v1.py",
    "experiments/07_comparative_landscape/test_pre_review_triage_future_text_reconciliation_hostile_v1.py",
    "experiments/07_comparative_landscape/test_pre_review_triage_future_text_reconciliation_amendment_001_v1.py",
    "experiments/07_comparative_landscape/test_pre_review_triage_future_text_reconciliation_amendment_002_v1.py",
    "experiments/07_comparative_landscape/test_pre_review_triage_future_text_reconciliation_request_10083_v1.py",
}

FREEZE_REL = (
    "experiments/07_comparative_landscape/pre_review_triage_future_text_reconciliation_v1_implementation_freeze.py"
)

DESIGN_REL = (
    "experiments/07_comparative_landscape/pre_review_triage_future_text_reconciliation_v1_implementation_design.json"
)

DOC_REL = (
    "experiments/07_comparative_landscape/PRE_REVIEW_TRIAGE_FUTURE_TEXT_RECONCILIATION_V1_IMPLEMENTATION.md"
)

SUMS_REL = (
    "experiments/07_comparative_landscape/pre_review_triage_future_text_reconciliation_v1_implementation.sha256"
)

EXPECTED_COMMIT_PATHS = (
    CANDIDATE_RELS
    | {
        FREEZE_REL,
        DESIGN_REL,
        DOC_REL,
        SUMS_REL,
    }
)

CANONICAL_ROOT_REL = (
    "results/07_comparative_landscape/pre_review_triage_future_text_retrieval_v1"
)

EXPECTED_OUTPUT_HASHES = {
    "reconciled_normalized_text.tsv": "8ee30e1bbd94140710e943fc2227805819fa88e84e31207ff64965d67489a1d3",
    "reconciled_resolution.tsv": "437f21bde9c29ddc2ef531a356bd56491fb088f3a37e35ee5aa9be1609ec31f7",
    "reconciliation_outputs.sha256": "237fd7080a3ff0617a486673ab122234edfbd6bfe12dc1734e5e16ea9e153279",
    "reconciliation_summary.json": "14b8099cecff8787a3a62efe5c796beebddf8635a66a38588f089435fdd14209"
}

EXPECTED_COUNTS = {
    "abstract_absent": 246,
    "normalized_text_rows": 11905,
    "openalex_position_gap": 1,
    "provider_not_found": 10,
    "total_records": 12162,
    "usable_abstract_openalex": 3406,
    "usable_abstract_pubmed": 8499,
    "wave_b_fallback_total": 40,
}

EXPECTED_NEXT_GATE = (
    "CONTROLLED_CANONICAL_RECONCILIATION_OUTPUT_GENERATION_"
    "WITH_EXACT_FROZEN_HASH_MATCH"
)


class FreezeError(RuntimeError):
    pass


def repo_root() -> Path:

    return Path(
        subprocess.check_output(
            [
                "git",
                "rev-parse",
                "--show-toplevel",
            ],
            text=True,
        ).strip()
    ).resolve()


def sha256_file(
    path: Path,
) -> str:

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def git_output(
    *args: str,
) -> str:

    return subprocess.check_output(
        [
            "git",
            *args,
        ],
        cwd=repo_root(),
        text=True,
    ).strip()


def repository_position() -> str:

    head = git_output(
        "rev-parse",
        "HEAD",
    )

    if head == EXPECTED_PARENT:
        return "PRE_COMMIT_PARENT"

    parent = git_output(
        "rev-parse",
        "HEAD^",
    )

    if parent != EXPECTED_PARENT:
        raise FreezeError(
            "HEAD is neither the expected parent nor "
            "its implementation-freeze child"
        )

    changed = set(
        line
        for line in git_output(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "HEAD",
        ).splitlines()
        if line
    )

    if changed != EXPECTED_COMMIT_PATHS:
        raise FreezeError(
            "Committed implementation-freeze path set differs"
        )

    return "COMMITTED_FREEZE"


def parse_checksum_manifest(
    path: Path,
) -> dict[str, str]:

    values = {}

    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():

        if not line.strip():
            continue

        digest, relative = line.split(
            None,
            1,
        )

        relative = relative.strip()

        if relative in values:
            raise FreezeError(
                "Duplicate checksum target"
            )

        values[
            relative
        ] = digest

    return values


def call_names(
    tree: ast.AST,
) -> set[str]:

    names = set()

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        fn = node.func

        if isinstance(
            fn,
            ast.Name,
        ):
            names.add(
                fn.id
            )

        elif isinstance(
            fn,
            ast.Attribute,
        ):
            parts = [
                fn.attr
            ]

            value = fn.value

            while isinstance(
                value,
                ast.Attribute,
            ):
                parts.append(
                    value.attr
                )

                value = value.value

            if isinstance(
                value,
                ast.Name,
            ):
                parts.append(
                    value.id
                )

            names.add(
                ".".join(
                    reversed(
                        parts
                    )
                )
            )

    return names


def validate() -> str:

    repo = repo_root()

    position = (
        repository_position()
    )

    design_path = (
        repo
        / DESIGN_REL
    )

    if not design_path.is_file():
        raise FreezeError(
            "Implementation design missing"
        )

    design = json.loads(
        design_path.read_text(
            encoding="utf-8"
        )
    )

    if (
        design.get(
            "schema_version"
        )
        != 1
        or design.get(
            "status"
        )
        != "FROZEN_IMPLEMENTATION_PRE_OUTPUT"
        or design.get(
            "freeze_parent_commit"
        )
        != EXPECTED_PARENT
        or design.get(
            "next_gate"
        )
        != EXPECTED_NEXT_GATE
    ):
        raise FreezeError(
            "Implementation freeze design state mismatch"
        )

    if (
        set(
            design.get(
                "candidate_file_hashes",
                {},
            )
        )
        != CANDIDATE_RELS
    ):
        raise FreezeError(
            "Candidate file set changed"
        )

    for relative, expected_sha in (
        design[
            "candidate_file_hashes"
        ].items()
    ):
        path = (
            repo
            / relative
        )

        if (
            not path.is_file()
            or sha256_file(
                path
            )
            != expected_sha
        ):
            raise FreezeError(
                "Candidate hash mismatch: "
                + relative
            )

    for relative, expected_sha in (
        design[
            "dependency_hashes"
        ].items()
    ):
        path = (
            repo
            / relative
        )

        if (
            not path.is_file()
            or sha256_file(
                path
            )
            != expected_sha
        ):
            raise FreezeError(
                "Dependency hash mismatch: "
                + relative
            )

    if (
        design.get(
            "expected_canonical_output_sha256"
        )
        != EXPECTED_OUTPUT_HASHES
    ):
        raise FreezeError(
            "Expected output hashes changed"
        )

    if (
        design.get(
            "validated_reconciliation_counts"
        )
        != EXPECTED_COUNTS
    ):
        raise FreezeError(
            "Validated reconciliation counts changed"
        )

    for key, value in (
        design[
            "safety_boundaries"
        ].items()
    ):
        if value is not False:
            raise FreezeError(
                "Unsafe freeze boundary: "
                + key
            )

    checksum_path = (
        repo
        / SUMS_REL
    )

    checksum_map = (
        parse_checksum_manifest(
            checksum_path
        )
    )

    expected_checksum_targets = (
        EXPECTED_COMMIT_PATHS
        - {
            SUMS_REL
        }
    )

    if (
        set(
            checksum_map
        )
        != expected_checksum_targets
    ):
        raise FreezeError(
            "Implementation checksum target set changed"
        )

    for relative, expected_sha in (
        checksum_map.items()
    ):
        if (
            sha256_file(
                repo
                / relative
            )
            != expected_sha
        ):
            raise FreezeError(
                "Implementation checksum mismatch: "
                + relative
            )

    implementation_rel = (
        ROOT_REL
        + "/pre_review_triage_future_text_reconciliation_v1.py"
    )

    source = (
        repo
        / implementation_rel
    ).read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source
    )

    imports = []

    for node in ast.walk(
        tree
    ):
        if isinstance(
            node,
            ast.Import,
        ):
            imports.extend(
                alias.name
                for alias in node.names
            )

        elif isinstance(
            node,
            ast.ImportFrom,
        ):
            imports.append(
                node.module
                or ""
            )

    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
    ):
        if any(
            item == forbidden
            or item.startswith(
                forbidden
                + "."
            )
            for item in imports
        ):
            raise FreezeError(
                "Independent network import present: "
                + forbidden
            )

    calls = call_names(
        tree
    )

    for forbidden in (
        "transport.request_with_redirects",
        "transport.build_request",
        "requests.get",
        "requests.post",
        "urllib.request.urlopen",
        "httpx.get",
        "httpx.post",
    ):
        if forbidden in calls:
            raise FreezeError(
                "Live request call present: "
                + forbidden
            )

    canonical_root = (
        repo
        / CANONICAL_ROOT_REL
    )

    output_paths = {
        name:
            canonical_root
            / name
        for name in EXPECTED_OUTPUT_HASHES
    }

    existing = {
        name:
            path
        for name, path
        in output_paths.items()
        if path.exists()
    }

    if existing and (
        len(
            existing
        )
        != len(
            EXPECTED_OUTPUT_HASHES
        )
    ):
        raise FreezeError(
            "Partial canonical reconciliation output set"
        )

    if existing:

        for name, expected_sha in (
            EXPECTED_OUTPUT_HASHES.items()
        ):
            if (
                sha256_file(
                    output_paths[
                        name
                    ]
                )
                != expected_sha
            ):
                raise FreezeError(
                    "Canonical output hash mismatch: "
                    + name
                )

        output_state = (
            "CANONICAL_OUTPUTS_EXACT"
        )

    else:

        output_state = (
            "CANONICAL_OUTPUTS_ABSENT"
        )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | implementation freeze validates"
    )

    print(
        "PASS | canonical output state =",
        output_state,
    )

    return position


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--validate",
        action="store_true",
        required=True,
    )

    parser.parse_args()

    validate()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
