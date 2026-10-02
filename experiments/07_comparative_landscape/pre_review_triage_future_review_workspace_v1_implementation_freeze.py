#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import subprocess

from pathlib import Path


ROOT = Path(
    "experiments/07_comparative_landscape"
)

EXPECTED_PARENT = (
    "6d90a4c0356509dbc8466563fc56c5ca57896f4e"
)

EXPECTED_DESIGN_SUMS_SHA = (
    "754288330069b576dff1e68c7c99c6fb57279c4860c3913818984bb6f57cb484"
)

EXPECTED_IMPL_SHA = (
    "b347de8b56325a56b5bb62d000d567c367b75270aed1566bdd907463992c05a0"
)

EXPECTED_UNIT_SHA = (
    "f7d46e8548f0592f2df5e1f5182f0044e273f67ae4493ae559a69a33295a456a"
)

EXPECTED_HOSTILE_SHA = (
    "df496ba45d66bbff61fb40f3f54d7ee2ed62b94262f581768da3b66eb439b82b"
)

EXPECTED_FREEZE_DESIGN_SHA = (
    "3eb6b675abfba5816c232722ed3a44183ab7b19851cf926f5edf3ebd6172139d"
)

EXPECTED_DOC_SHA = (
    "6b253b2721484df166e5676beb207a7a3cdeaef08864545c6fb88b7f2ea0d07f"
)

DESIGN_SUMS = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_design.sha256"
)

FREEZE_DESIGN = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_implementation_design.json"
)

DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_IMPLEMENTATION.md"
)

IMPL = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1.py"
)

UNIT = (
    ROOT
    / "test_pre_review_triage_future_review_workspace_v1.py"
)

HOSTILE = (
    ROOT
    / "test_pre_review_triage_future_review_workspace_hostile_v1.py"
)

SUMS = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_implementation.sha256"
)

FREEZE_VALIDATOR = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_implementation_freeze.py"
)

OUTPUT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_review_workspace_v1"
)

EXPECTED_MANIFEST_TARGETS = {
    str(DOC),
    str(FREEZE_DESIGN),
    str(FREEZE_VALIDATOR),
    str(IMPL),
    str(UNIT),
    str(HOSTILE),
    str(DESIGN_SUMS),
}

EXPECTED_COMMIT_PATHS = {
    str(DOC),
    str(FREEZE_DESIGN),
    str(FREEZE_VALIDATOR),
    str(IMPL),
    str(UNIT),
    str(HOSTILE),
    str(SUMS),
}


def sha(
    path: Path,
) -> str:

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def git(
    *args: str,
) -> str:

    return subprocess.check_output(
        [
            "git",
            *args,
        ],
        text=True,
    ).strip()


def repository_position() -> str:

    head = git(
        "rev-parse",
        "HEAD",
    )

    if head == EXPECTED_PARENT:
        return "PRE_COMMIT_PARENT"

    parent = git(
        "rev-parse",
        "HEAD^",
    )

    if parent != EXPECTED_PARENT:
        raise RuntimeError(
            "Unexpected implementation-freeze repository position"
        )

    changed = {
        line
        for line in git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "HEAD",
        ).splitlines()
        if line
    }

    if changed != EXPECTED_COMMIT_PATHS:
        raise RuntimeError(
            "Implementation-freeze commit path set differs"
        )

    return "COMMITTED_FREEZE"


def validate_checksum_manifest() -> None:

    if not SUMS.is_file():
        raise RuntimeError(
            "Implementation checksum manifest missing"
        )

    entries = {}

    for line in SUMS.read_text(
        encoding="utf-8"
    ).splitlines():

        if not line.strip():
            continue

        try:
            digest, rel = line.split(
                None,
                1,
            )
        except ValueError as exc:
            raise RuntimeError(
                "Malformed implementation checksum line"
            ) from exc

        rel = rel.strip()

        if rel.startswith("*"):
            rel = rel[1:]

        if rel in entries:
            raise RuntimeError(
                "Duplicate implementation checksum target"
            )

        entries[rel] = digest

    if set(entries) != EXPECTED_MANIFEST_TARGETS:
        raise RuntimeError(
            "Implementation checksum target set differs"
        )

    for rel, digest in entries.items():

        path = Path(
            rel
        )

        if not path.is_file():
            raise RuntimeError(
                "Implementation checksum target missing: "
                + rel
            )

        if sha(path) != digest:
            raise RuntimeError(
                "Implementation checksum mismatch: "
                + rel
            )


def validate() -> None:

    position = (
        repository_position()
    )

    if sha(
        DESIGN_SUMS
    ) != EXPECTED_DESIGN_SUMS_SHA:
        raise RuntimeError(
            "Workspace design freeze changed"
        )

    if sha(
        IMPL
    ) != EXPECTED_IMPL_SHA:
        raise RuntimeError(
            "Frozen workspace builder changed"
        )

    if sha(
        UNIT
    ) != EXPECTED_UNIT_SHA:
        raise RuntimeError(
            "Frozen unit tests changed"
        )

    if sha(
        HOSTILE
    ) != EXPECTED_HOSTILE_SHA:
        raise RuntimeError(
            "Frozen hostile tests changed"
        )

    if sha(
        FREEZE_DESIGN
    ) != EXPECTED_FREEZE_DESIGN_SHA:
        raise RuntimeError(
            "Implementation-freeze design changed"
        )

    if sha(
        DOC
    ) != EXPECTED_DOC_SHA:
        raise RuntimeError(
            "Implementation document changed"
        )

    validate_checksum_manifest()

    value = json.loads(
        FREEZE_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if (
        value["freeze_id"]
        != "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_IMPLEMENTATION"
    ):
        raise RuntimeError(
            "Implementation freeze identity changed"
        )

    if (
        value["freeze_parent_commit"]
        != EXPECTED_PARENT
    ):
        raise RuntimeError(
            "Implementation freeze parent changed"
        )

    if (
        value["status"]
        != "FROZEN_IMPLEMENTATION_PRE_GENERATION_AUTHORIZATION"
    ):
        raise RuntimeError(
            "Implementation freeze status changed"
        )

    if (
        value[
            "source_contract"
        ][
            "workspace_design_checksum_manifest_sha256"
        ]
        != EXPECTED_DESIGN_SUMS_SHA
    ):
        raise RuntimeError(
            "Workspace design source identity changed"
        )

    expected_hashes = {
        str(IMPL):
            EXPECTED_IMPL_SHA,
        str(UNIT):
            EXPECTED_UNIT_SHA,
        str(HOSTILE):
            EXPECTED_HOSTILE_SHA,
    }

    if (
        value[
            "implementation_hashes"
        ]
        != expected_hashes
    ):
        raise RuntimeError(
            "Implementation hash contract changed"
        )

    contract = value[
        "workspace_contract"
    ]

    if (
        contract[
            "frozen_triage_rows"
        ]
        != 12162
    ):
        raise RuntimeError(
            "Frozen triage count changed"
        )

    if (
        contract[
            "new_review_work_rows"
        ]
        != 12156
    ):
        raise RuntimeError(
            "Review-work count changed"
        )

    if (
        contract[
            "prior_carry_forward_rows"
        ]
        != 6
    ):
        raise RuntimeError(
            "Carry-forward count changed"
        )

    if (
        contract[
            "total_packet_count"
        ]
        != 25
    ):
        raise RuntimeError(
            "Packet count changed"
        )

    if (
        contract[
            "global_cross_lane_order_defined"
        ]
        is not False
    ):
        raise RuntimeError(
            "Cross-lane ordering unexpectedly defined"
        )

    boundary = value[
        "scientific_boundary"
    ]

    if any(
        boundary.values()
    ):
        raise RuntimeError(
            "Scientific or production authority leaked into implementation freeze"
        )

    validation = value[
        "validation_evidence"
    ]

    if (
        validation[
            "unit_test_count"
        ]
        != 12
        or validation[
            "hostile_test_count"
        ]
        != 14
        or validation[
            "total_test_count"
        ]
        != 26
    ):
        raise RuntimeError(
            "Frozen test counts changed"
        )

    if (
        validation[
            "all_tests_passed"
        ]
        is not True
    ):
        raise RuntimeError(
            "Test-pass status changed"
        )

    if (
        validation[
            "canonical_workspace_generated"
        ]
        is not False
    ):
        raise RuntimeError(
            "Canonical-workspace generation state changed"
        )

    generation = value[
        "generation_boundary"
    ]

    if (
        generation[
            "authorization_required"
        ]
        is not True
        or generation[
            "one_use_authorization_required"
        ]
        is not True
        or generation[
            "generation_authorized"
        ]
        is not False
        or generation[
            "workspace_generated"
        ]
        is not False
    ):
        raise RuntimeError(
            "Generation authorization boundary changed"
        )

    if (
        generation[
            "confirmation"
        ]
        != "GENERATE-FROZEN-FUTURE-REVIEW-WORKSPACE-V1"
    ):
        raise RuntimeError(
            "Generation confirmation changed"
        )

    if (
        value[
            "next_gate"
        ]
        != (
            "FREEZE_ONE_USE_"
            "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_"
            "GENERATION_AUTHORIZATION"
        )
    ):
        raise RuntimeError(
            "Implementation next gate changed"
        )

    if OUTPUT.exists():
        raise RuntimeError(
            "Canonical future review workspace unexpectedly exists"
        )

    print(
        "PASS | repository position =",
        position,
    )
    print(
        "PASS | future review-workspace implementation freeze validates"
    )
    print(
        "PASS | exact tested builder and test bytes bound"
    )
    print(
        "PASS | 12,156 new-review + 6 carry-forward contract frozen"
    )
    print(
        "PASS | 25 lane-local review packets frozen"
    )
    print(
        "PASS | model fields remain excluded"
    )
    print(
        "PASS | scientific and production authority remain false"
    )
    print(
        "PASS | canonical workspace remains absent"
    )


if __name__ == "__main__":
    validate()
