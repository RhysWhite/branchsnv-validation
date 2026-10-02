#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import subprocess

from pathlib import Path


ROOT = Path(
    "experiments/07_comparative_landscape"
)

EXPECTED_PARENT = "b6f2c6a6179e77a8931caa433ae01ede36b32ae6"

EXPECTED_IMPL_SUMS_SHA = "884c8e45ac89cdcd6631579b00be02cab664b8c644c58aec9c725e4d917e7449"
EXPECTED_DESIGN_SUMS_SHA = "754288330069b576dff1e68c7c99c6fb57279c4860c3913818984bb6f57cb484"
EXPECTED_BUILDER_SHA = "b347de8b56325a56b5bb62d000d567c367b75270aed1566bdd907463992c05a0"
EXPECTED_AUTH_SHA = "42fc9031cf1a684406b591fb976d6bd8cd3f3ac8d433a510f7a29f31fcf003ce"
EXPECTED_AUTH_DESIGN_SHA = "9443731b66667612d2a776fcbea897cfddb9e6062a83967cbf5081fa6b45eb2f"
EXPECTED_AUTH_DOC_SHA = "876860555fdd5fef9090b507fa2486befba22250ff5a803baf44a8552c6b0c4d"

IMPL_SUMS = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_implementation.sha256"
)

DESIGN_SUMS = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_design.sha256"
)

BUILDER = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1.py"
)

AUTH = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_generation_authorization.json"
)

AUTH_DESIGN = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_generation_authorization_design.json"
)

AUTH_DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_GENERATION_AUTHORIZATION.md"
)

AUTH_FREEZE = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_generation_authorization_freeze.py"
)

AUTH_SUMS = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_generation_authorization.sha256"
)

OUTPUT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_review_workspace_v1"
)

EXPECTED_MANIFEST_TARGETS = {
    str(AUTH),
    str(AUTH_DESIGN),
    str(AUTH_DOC),
    str(AUTH_FREEZE),
    str(IMPL_SUMS),
    str(DESIGN_SUMS),
    str(BUILDER),
}

EXPECTED_COMMIT_PATHS = {
    str(AUTH),
    str(AUTH_DESIGN),
    str(AUTH_DOC),
    str(AUTH_FREEZE),
    str(AUTH_SUMS),
}


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
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
            "Unexpected authorization-freeze repository position"
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
            "Authorization-freeze commit path set differs"
        )

    return "COMMITTED_FREEZE"


def validate_checksum_manifest() -> None:

    if not AUTH_SUMS.is_file():
        raise RuntimeError(
            "Authorization checksum manifest missing"
        )

    entries = {}

    for line in AUTH_SUMS.read_text(
        encoding="utf-8"
    ).splitlines():

        if not line.strip():
            continue

        digest, rel = line.split(
            None,
            1,
        )

        rel = rel.strip()

        if rel.startswith("*"):
            rel = rel[1:]

        if rel in entries:
            raise RuntimeError(
                "Duplicate authorization checksum target"
            )

        entries[rel] = digest

    if set(entries) != EXPECTED_MANIFEST_TARGETS:
        raise RuntimeError(
            "Authorization checksum target set differs"
        )

    for rel, digest in entries.items():

        path = Path(rel)

        if not path.is_file():
            raise RuntimeError(
                "Authorization checksum target missing: "
                + rel
            )

        if sha(path) != digest:
            raise RuntimeError(
                "Authorization checksum mismatch: "
                + rel
            )


def validate() -> None:

    position = repository_position()

    if sha(IMPL_SUMS) != EXPECTED_IMPL_SUMS_SHA:
        raise RuntimeError(
            "Implementation freeze changed"
        )

    if sha(DESIGN_SUMS) != EXPECTED_DESIGN_SUMS_SHA:
        raise RuntimeError(
            "Workspace design freeze changed"
        )

    if sha(BUILDER) != EXPECTED_BUILDER_SHA:
        raise RuntimeError(
            "Active workspace builder changed"
        )

    if sha(AUTH) != EXPECTED_AUTH_SHA:
        raise RuntimeError(
            "Authorization JSON changed"
        )

    if sha(AUTH_DESIGN) != EXPECTED_AUTH_DESIGN_SHA:
        raise RuntimeError(
            "Authorization design changed"
        )

    if sha(AUTH_DOC) != EXPECTED_AUTH_DOC_SHA:
        raise RuntimeError(
            "Authorization document changed"
        )

    validate_checksum_manifest()

    auth = json.loads(
        AUTH.read_text(
            encoding="utf-8"
        )
    )

    expected_auth = {
        "schema_version": 1,
        "status": "AUTHORIZED_ONE_USE",
        "authorization_id":
            (
                "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_"
                "GENERATION_001"
            ),
        "generation_authorized": True,
        "one_use": True,
        "workspace_design_checksum_manifest_sha256":
            EXPECTED_DESIGN_SUMS_SHA,
        "expected_triage_rows": 12162,
        "expected_review_work_rows": 12156,
        "expected_prior_carry_forward_rows": 6,
        "expected_packet_count": 25,
        "output_root":
            (
                "results/07_comparative_landscape/"
                "pre_review_triage_future_review_workspace_v1"
            ),
        "scientific_decision_authorized": False,
        "carry_forward_reassessment_authorized": False,
        "new_scientific_batch_membership_authorized": False,
        "production_ledger_mutation_authorized": False,
        "cross_lane_priority_inference_authorized": False,
        "confirmation":
            "GENERATE-FROZEN-FUTURE-REVIEW-WORKSPACE-V1",
    }

    if auth != expected_auth:
        raise RuntimeError(
            "Authorization payload contract changed"
        )

    design = json.loads(
        AUTH_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if (
        design["freeze_id"]
        !=
        "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_GENERATION_AUTHORIZATION"
    ):
        raise RuntimeError(
            "Authorization freeze identity changed"
        )

    if design["freeze_parent_commit"] != EXPECTED_PARENT:
        raise RuntimeError(
            "Authorization freeze parent changed"
        )

    if (
        design["status"]
        != "FROZEN_ONE_USE_GENERATION_AUTHORIZATION_PRE_EXECUTION"
    ):
        raise RuntimeError(
            "Authorization freeze status changed"
        )

    binding = design[
        "implementation_binding"
    ]

    if (
        binding[
            "implementation_checksum_manifest_sha256"
        ]
        != EXPECTED_IMPL_SUMS_SHA
    ):
        raise RuntimeError(
            "Implementation binding changed"
        )

    if (
        binding[
            "workspace_design_checksum_manifest_sha256"
        ]
        != EXPECTED_DESIGN_SUMS_SHA
    ):
        raise RuntimeError(
            "Design binding changed"
        )

    if (
        binding[
            "active_builder_sha256"
        ]
        != EXPECTED_BUILDER_SHA
    ):
        raise RuntimeError(
            "Builder binding changed"
        )

    authorization = design[
        "authorization"
    ]

    if (
        authorization[
            "one_time_generation_consumed"
        ]
        is not False
    ):
        raise RuntimeError(
            "Authorization unexpectedly consumed"
        )

    if (
        authorization[
            "rerun_authorized"
        ]
        is not False
    ):
        raise RuntimeError(
            "Rerun unexpectedly authorized"
        )

    if (
        authorization[
            "exact_confirmation"
        ]
        != "GENERATE-FROZEN-FUTURE-REVIEW-WORKSPACE-V1"
    ):
        raise RuntimeError(
            "Exact confirmation changed"
        )

    if any(
        design[
            "scientific_boundary"
        ].values()
    ):
        raise RuntimeError(
            "Scientific or production authority leaked into authorization"
        )

    if (
        design["next_gate"]
        != (
            "EXECUTE_ONCE_FROZEN_"
            "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_"
            "GENERATION_001"
        )
    ):
        raise RuntimeError(
            "Authorization next gate changed"
        )

    if OUTPUT.exists():
        raise RuntimeError(
            "Canonical workspace unexpectedly exists before execution"
        )

    print(
        "PASS | repository position =",
        position,
    )
    print(
        "PASS | one-use workspace generation authorization freeze validates"
    )
    print(
        "PASS | authorization ID = "
        "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_GENERATION_001"
    )
    print(
        "PASS | exact implementation and builder identities bound"
    )
    print(
        "PASS | 12,156 + 6 / 25-packet generation scope exact"
    )
    print(
        "PASS | authorization remains unconsumed"
    )
    print(
        "PASS | rerun remains unauthorized"
    )
    print(
        "PASS | scientific and production-ledger authority remain false"
    )
    print(
        "PASS | canonical workspace remains absent"
    )


if __name__ == "__main__":
    validate()
