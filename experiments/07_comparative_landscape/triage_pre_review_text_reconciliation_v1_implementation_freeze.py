from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "53644804724a064acdc4a7b04870497091ed0c8f"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

IMPL_REL = (
    ROOT_REL
    + "/triage_pre_review_text_reconciliation_v1.py"
)

TEST_REL = (
    ROOT_REL
    + "/test_triage_pre_review_text_reconciliation_v1.py"
)

HOSTILE_REL = (
    ROOT_REL
    + "/test_triage_pre_review_text_reconciliation_hostile_v1.py"
)

FREEZE_REL = (
    ROOT_REL
    + "/triage_pre_review_text_reconciliation_v1_implementation_freeze.py"
)

DESIGN_REL = (
    ROOT_REL
    + "/triage_pre_review_text_reconciliation_v1_implementation_design.json"
)

DOC_REL = (
    ROOT_REL
    + "/TRIAGE_PRE_REVIEW_TEXT_RECONCILIATION_V1_IMPLEMENTATION.md"
)

SUMS_REL = (
    ROOT_REL
    + "/triage_pre_review_text_reconciliation_v1_implementation.sha256"
)

EXPECTED_COMMIT_PATHS = {
    IMPL_REL,
    TEST_REL,
    HOSTILE_REL,
    FREEZE_REL,
    DESIGN_REL,
    DOC_REL,
    SUMS_REL,
}

CANONICAL_ROOT_REL = (
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1"
)

EXPECTED_OUTPUT_HASHES = {
    "reconciled_resolution.tsv":
        "cb2a5d32d6eabcde6ba7aa5db52bfcc813fc52e45a897cac7ec13a632ce016d5",

    "reconciled_normalized_text.tsv":
        "8c897444fe1a4d26226c8ecb798cd9d08bd3acc362aead972fdbee80d326785b",

    "reconciliation_summary.json":
        "c43385e506a7d37c5290fdb3842c2991c0398efcf944f57be68ffadd51d5c802",

    "reconciliation_outputs.sha256":
        "62aa1bed45d5bfc77b190247d94a1a9e4bb7be772d14fb55f2cbf03f3ab3f5cf",
}


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
        design[
            "status"
        ]
        != "FROZEN_IMPLEMENTATION_PRE_OUTPUT"
    ):
        raise FreezeError(
            "Implementation freeze status changed"
        )

    if (
        design[
            "freeze_parent_commit"
        ]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Freeze parent changed"
        )

    expected_candidates = {
        IMPL_REL,
        TEST_REL,
        HOSTILE_REL,
    }

    if (
        set(
            design[
                "candidate_file_hashes"
            ]
        )
        != expected_candidates
    ):
        raise FreezeError(
            "Candidate file set changed"
        )

    for relative, expected_sha in (
        design[
            "candidate_file_hashes"
        ].items()
    ):

        path = repo / relative

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

        path = repo / relative

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
        design[
            "expected_canonical_output_sha256"
        ]
        != EXPECTED_OUTPUT_HASHES
    ):
        raise FreezeError(
            "Expected output hashes changed"
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

    expected_checksum_targets = {
        IMPL_REL,
        TEST_REL,
        HOSTILE_REL,
        FREEZE_REL,
        DESIGN_REL,
        DOC_REL,
    }

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
                repo / relative
            )
            != expected_sha
        ):
            raise FreezeError(
                "Implementation checksum mismatch: "
                + relative
            )

    source = (
        repo
        / IMPL_REL
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
        for name, path in (
            output_paths.items()
        )
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
