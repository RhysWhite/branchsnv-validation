#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys

from pathlib import Path


ROOT = Path(
    "experiments/07_comparative_landscape"
)

REVIEW_ROOT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_human_review_v1"
)

EXPECTED_PARENT = (
    "0097bbc5c343f4e824bb56221d4fbb4a4b90df94"
)

IMPL = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1.py"
)

TEST = (
    ROOT
    / "test_pre_review_triage_future_human_review_protocol_v1.py"
)

HOSTILE = (
    ROOT
    / "test_pre_review_triage_future_human_review_protocol_hostile_v1.py"
)

FREEZE_DESIGN = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_design.json"
)

FREEZE_DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_"
      "IMPLEMENTATION.md"
)

FREEZE_VALIDATOR = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_freeze.py"
)

FREEZE_SUMS = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation.sha256"
)

DESIGN_AMEND_FREEZE = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "design_amendment_001_freeze.py"
)

TERM_AMEND_FREEZE = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_"
      "terminology_amendment_001_freeze.py"
)

EXPECTED_COMMIT_PATHS = {
    str(
        IMPL
    ),
    str(
        TEST
    ),
    str(
        HOSTILE
    ),
    str(
        FREEZE_DESIGN
    ),
    str(
        FREEZE_DOC
    ),
    str(
        FREEZE_VALIDATOR
    ),
    str(
        FREEZE_SUMS
    ),
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


def git_bytes(
    *args: str,
) -> bytes:

    return subprocess.check_output(
        [
            "git",
            *args,
        ]
    )


def is_ancestor(
    ancestor: str,
    descendant: str,
) -> bool:

    result = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            ancestor,
            descendant,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return (
        result.returncode
        == 0
    )


def introduction_commit():

    value = git(
        "log",
        "--diff-filter=A",
        "-1",
        "--format=%H",
        "--",
        str(
            FREEZE_DESIGN
        ),
    )

    return (
        value
        or None
    )


def repository_position():

    head = git(
        "rev-parse",
        "HEAD",
    )

    if head == EXPECTED_PARENT:

        return (
            "PRE_COMMIT_PARENT",
            None,
        )

    intro = (
        introduction_commit()
    )

    if intro is None:
        raise RuntimeError(
            "Implementation freeze is not committed"
        )

    if (
        git(
            "rev-parse",
            intro + "^",
        )
        != EXPECTED_PARENT
    ):
        raise RuntimeError(
            "Implementation freeze introduction parent differs"
        )

    changed = {
        x
        for x in git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            intro,
        ).splitlines()
        if x
    }

    if (
        changed
        != EXPECTED_COMMIT_PATHS
    ):
        raise RuntimeError(
            "Implementation-freeze commit path set differs"
        )

    if not is_ancestor(
        intro,
        head,
    ):
        raise RuntimeError(
            "HEAD is not descended from implementation freeze"
        )

    if head == intro:

        return (
            "COMMITTED_FREEZE",
            intro,
        )

    return (
        "DESCENDANT_OF_FREEZE",
        intro,
    )


def parse_manifest(
    path: Path,
):

    entries = {}

    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():

        if not line.strip():
            continue

        digest, rel = line.split(
            None,
            1,
        )

        rel = rel.strip()

        if rel.startswith(
            "*"
        ):
            rel = rel[
                1:
            ]

        if rel in entries:
            raise RuntimeError(
                "Duplicate checksum target: "
                + rel
            )

        entries[
            rel
        ] = digest

    return entries


def validate_checksum_closure():

    entries = parse_manifest(
        FREEZE_SUMS
    )

    if not entries:
        raise RuntimeError(
            "Implementation checksum closure empty"
        )

    for rel, expected in entries.items():

        path = Path(
            rel
        )

        if not path.is_file():
            raise RuntimeError(
                "Implementation checksum target missing: "
                + rel
            )

        if sha(
            path
        ) != expected:
            raise RuntimeError(
                "Implementation checksum target changed: "
                + rel
            )


def validate_frozen_files_immutable(
    intro,
):

    if intro is None:
        return

    for path in (
        IMPL,
        TEST,
        HOSTILE,
        FREEZE_DESIGN,
        FREEZE_DOC,
        FREEZE_VALIDATOR,
        FREEZE_SUMS,
    ):

        committed = git_bytes(
            "show",
            f"{intro}:{path}",
        )

        if (
            path.read_bytes()
            != committed
        ):
            raise RuntimeError(
                "Implementation-freeze artifact changed "
                "after introduction: "
                + str(
                    path
                )
            )


def validate_bound_amendments():

    subprocess.check_call(
        [
            sys.executable,
            str(
                TERM_AMEND_FREEZE
            ),
        ]
    )

    subprocess.check_call(
        [
            sys.executable,
            str(
                DESIGN_AMEND_FREEZE
            ),
        ]
    )


def load_implementation():

    spec = (
        importlib.util.spec_from_file_location(
            "frozen_future_human_review_protocol",
            IMPL,
        )
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "Unable to load frozen implementation"
        )

    module = (
        importlib.util.module_from_spec(
            spec
        )
    )

    spec.loader.exec_module(
        module
    )

    return module


def validate_design_metadata():

    value = json.loads(
        FREEZE_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if (
        value[
            "freeze_id"
        ]
        !=
        "PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_IMPLEMENTATION"
    ):
        raise RuntimeError(
            "Implementation freeze identity changed"
        )

    if (
        value[
            "status"
        ]
        != "FROZEN_IMPLEMENTATION_PRE_HUMAN_REVIEW"
    ):
        raise RuntimeError(
            "Implementation freeze status changed"
        )

    if (
        value[
            "freeze_parent_commit"
        ]
        != EXPECTED_PARENT
    ):
        raise RuntimeError(
            "Implementation freeze parent changed"
        )

    tested = value[
        "tested_implementation"
    ]

    expected = {
        IMPL:
            tested[
                "implementation_sha256"
            ],

        TEST:
            tested[
                "unit_test_sha256"
            ],

        HOSTILE:
            tested[
                "hostile_test_sha256"
            ],
    }

    for path, digest in expected.items():

        if sha(
            path
        ) != digest:
            raise RuntimeError(
                "Exact tested candidate bytes changed: "
                + str(
                    path
                )
            )

    if (
        value[
            "review_universe"
        ][
            "new_human_review_rows"
        ]
        != 12156
    ):
        raise RuntimeError(
            "Frozen review row count changed"
        )

    if (
        value[
            "review_universe"
        ][
            "prior_anchor_carry_forward_rows"
        ]
        != 6
    ):
        raise RuntimeError(
            "Frozen prior-anchor carry-forward count changed"
        )

    if (
        value[
            "review_universe"
        ][
            "packet_count"
        ]
        != 25
    ):
        raise RuntimeError(
            "Frozen packet count changed"
        )

    capabilities = value[
        "implemented_capabilities"
    ]

    required_true = (
        "frozen_workspace_validation",
        "upstream_checksum_validation",
        "immutable_execution_package_validation",
        "current_append_only_ledger_semantic_validation",
        "canonical_packet_identity_validation",
        "deterministic_blank_working_copy_materialization",
        "working_copy_fail_closed_if_destination_exists",
        "reviewed_packet_identity_and_order_validation",
        "row_wise_reuse_of_frozen_event_semantics",
        "complete_packet_approval_payload_construction",
        "approval_payload_revalidation",
    )

    for key in required_true:

        if (
            capabilities[
                key
            ]
            is not True
        ):
            raise RuntimeError(
                "Required implementation capability changed: "
                + key
            )

    required_false = (
        "approval_payload_persistence",
        "production_proposal_persistence",
        "live_production_authorization",
        "production_transaction_shape_projection",
    )

    for key in required_false:

        if (
            capabilities[
                key
            ]
            is not False
        ):
            raise RuntimeError(
                "Forbidden implementation capability changed: "
                + key
            )

    runtime = value[
        "runtime_integrity_contract"
    ]

    if (
        runtime[
            "current_ledger_sha_is_permanent_protocol_identity"
        ]
        is not False
    ):
        raise RuntimeError(
            "Mutable ledger SHA unexpectedly frozen as permanent identity"
        )

    if (
        runtime[
            "production_transaction_shape_deferred_to_later_frozen_contract"
        ]
        is not True
    ):
        raise RuntimeError(
            "Production transaction shape is no longer deferred"
        )

    if any(
        value[
            "scientific_boundary"
        ].values()
    ):
        raise RuntimeError(
            "Implementation freeze grants scientific or production authority"
        )

    return value


def validate_runtime(
    *,
    position: str,
    design: dict,
):

    impl = load_implementation()

    required = (
        "validate_upstream_contract",
        "validate_frozen_workspace_contract",
        "materialize_blank_review_packet",
        "validate_reviewed_packet",
        "build_packet_approval_payload",
        "validate_packet_approval_payload",
    )

    for name in required:

        if not callable(
            getattr(
                impl,
                name,
                None,
            )
        ):
            raise RuntimeError(
                "Frozen implementation capability missing: "
                + name
            )

    runtime = (
        impl.validate_upstream_contract()
    )

    workspace = (
        impl.validate_frozen_workspace_contract()
    )

    if (
        runtime[
            "current_ledger"
        ][
            "status"
        ]
        != "EVENT_LEDGER_VALID"
    ):
        raise RuntimeError(
            "Current ledger no longer validates"
        )

    if (
        runtime[
            "current_ledger"
        ][
            "mutation_performed"
        ]
        is not False
    ):
        raise RuntimeError(
            "Read-only runtime validation reported mutation"
        )

    if (
        runtime[
            "mutable_ledger_sha_pinned"
        ]
        is not False
    ):
        raise RuntimeError(
            "Runtime now permanently pins mutable ledger SHA"
        )

    if (
        workspace[
            "review_rows"
        ]
        != 12156
        or workspace[
            "packet_count"
        ]
        != 25
        or workspace[
            "prior_carry_forward_rows"
        ]
        != 6
    ):
        raise RuntimeError(
            "Frozen workspace semantics changed"
        )

    # These are freeze-time conditions, not archival invariants.
    if position in {
        "PRE_COMMIT_PARENT",
        "COMMITTED_FREEZE",
    }:

        if REVIEW_ROOT.exists():
            raise RuntimeError(
                "Real human-review output exists at implementation freeze"
            )

        overlap = (
            impl.current_target_event_overlap()
        )

        if overlap:
            raise RuntimeError(
                "Future-review target event overlap nonzero at implementation freeze"
            )

        evidence = design[
            "freeze_time_evidence"
        ]

        if (
            runtime[
                "current_ledger"
            ][
                "event_count"
            ]
            != evidence[
                "current_event_count"
            ]
        ):
            raise RuntimeError(
                "Freeze-time event count changed"
            )

        if (
            runtime[
                "current_ledger"
            ][
                "ledger_sha256"
            ]
            != evidence[
                "observed_current_ledger_sha256"
            ]
        ):
            raise RuntimeError(
                "Freeze-time observed ledger SHA changed"
            )


def validate():

    position, intro = (
        repository_position()
    )

    validate_checksum_closure()

    validate_frozen_files_immutable(
        intro
    )

    validate_bound_amendments()

    design = (
        validate_design_metadata()
    )

    validate_runtime(
        position=
            position,

        design=
            design,
    )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | future human-review protocol implementation freeze validates"
    )

    print(
        "PASS | exact tested implementation and test bytes bound"
    )

    print(
        "PASS | design + amendment + terminology contracts bound"
    )

    print(
        "PASS | frozen appender/event-entry semantics bound"
    )

    print(
        "PASS | 12,156 review rows + 6 prior-anchor carry-forwards bound"
    )

    print(
        "PASS | 25 packet review protocol bound"
    )

    print(
        "PASS | mutable ledger validated semantically, not permanently SHA-pinned"
    )

    print(
        "PASS | production transaction shape remains deferred"
    )

    print(
        "PASS | scientific and production authority remain false"
    )


if __name__ == "__main__":

    validate()
