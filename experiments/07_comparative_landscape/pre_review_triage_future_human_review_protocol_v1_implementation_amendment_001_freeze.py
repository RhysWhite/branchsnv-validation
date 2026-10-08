#!/usr/bin/env python3

from __future__ import annotations

import csv
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

SOURCE = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_review_workspace_v1/"
    "packets/priority_001.tsv"
)

WORKING = (
    REVIEW_ROOT
    / "packets"
    / "priority_001.tsv"
)

EXPECTED_FREEZE_COMMIT = (
    "e628e47112a7c714b6a7820b875a1dda0e3a2b8f"
)

EXPECTED_FREEZE_PARENT = (
    "0097bbc5c343f4e824bb56221d4fbb4a4b90df94"
)

EXPECTED_BLANK_SHA = (
    "665edd7eb4c00535ce1fb531460faa1e7c8193e6ef86814cad40fa0772435f05"
)

EXPECTED_LEDGER_SHA_AT_AMENDMENT = (
    "f7175d03bb559a8996e7a2fb1aba3959abab87429b86adbd19df74f0f0cbf45e"
)

EXPECTED_LEDGER_ROWS_AT_AMENDMENT = 2011

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

ORIGINAL_FREEZE_DESIGN = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_design.json"
)

ORIGINAL_FREEZE_DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_"
      "IMPLEMENTATION.md"
)

ORIGINAL_FREEZE_VALIDATOR = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_freeze.py"
)

ORIGINAL_FREEZE_SUMS = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation.sha256"
)

AMD_JSON = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_amendment_001_design.json"
)

AMD_MD = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_"
      "IMPLEMENTATION_AMENDMENT_001.md"
)

AMD_FREEZE = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_amendment_001_freeze.py"
)

AMD_SUMS = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_amendment_001.sha256"
)

ORIGINAL_SEVEN = {
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
        ORIGINAL_FREEZE_DESIGN
    ),
    str(
        ORIGINAL_FREEZE_DOC
    ),
    str(
        ORIGINAL_FREEZE_VALIDATOR
    ),
    str(
        ORIGINAL_FREEZE_SUMS
    ),
}

EXPECTED_AMENDMENT_PATHS = {
    str(
        AMD_JSON
    ),
    str(
        AMD_MD
    ),
    str(
        AMD_FREEZE
    ),
    str(
        AMD_SUMS
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
            AMD_JSON
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

    if head == EXPECTED_FREEZE_COMMIT:

        return (
            "PRE_COMMIT_PARENT",
            None,
        )

    intro = (
        introduction_commit()
    )

    if intro is None:
        raise RuntimeError(
            "Implementation Amendment 001 is not committed"
        )

    if (
        git(
            "rev-parse",
            intro + "^",
        )
        != EXPECTED_FREEZE_COMMIT
    ):
        raise RuntimeError(
            "Implementation amendment introduction parent differs"
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
        != EXPECTED_AMENDMENT_PATHS
    ):
        raise RuntimeError(
            "Implementation amendment commit path set differs"
        )

    if not is_ancestor(
        intro,
        head,
    ):
        raise RuntimeError(
            "HEAD is not descended from implementation amendment"
        )

    if head == intro:

        return (
            "COMMITTED_AMENDMENT",
            intro,
        )

    return (
        "DESCENDANT_OF_AMENDMENT",
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


def validate_manifest(
    path: Path,
):

    entries = parse_manifest(
        path
    )

    if not entries:
        raise RuntimeError(
            "Checksum manifest empty: "
            + str(
                path
            )
        )

    for rel, expected in entries.items():

        target = Path(
            rel
        )

        if not target.is_file():
            raise RuntimeError(
                "Checksum target missing: "
                + rel
            )

        if sha(
            target
        ) != expected:
            raise RuntimeError(
                "Checksum target changed: "
                + rel
            )


def validate_original_freeze_commit():

    if (
        git(
            "rev-parse",
            EXPECTED_FREEZE_COMMIT + "^",
        )
        != EXPECTED_FREEZE_PARENT
    ):
        raise RuntimeError(
            "Original implementation-freeze parent changed"
        )

    changed = {
        x
        for x in git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            EXPECTED_FREEZE_COMMIT,
        ).splitlines()
        if x
    }

    if changed != ORIGINAL_SEVEN:
        raise RuntimeError(
            "Original seven-file freeze path set changed"
        )

    for rel in ORIGINAL_SEVEN:

        path = Path(
            rel
        )

        committed = git_bytes(
            "show",
            f"{EXPECTED_FREEZE_COMMIT}:{rel}",
        )

        if (
            path.read_bytes()
            != committed
        ):
            raise RuntimeError(
                "Original frozen implementation artifact changed: "
                + rel
            )

    validate_manifest(
        ORIGINAL_FREEZE_SUMS
    )


def validate_amendment_immutability(
    intro,
):

    if intro is None:
        return

    for path in (
        AMD_JSON,
        AMD_MD,
        AMD_FREEZE,
        AMD_SUMS,
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
                "Implementation amendment changed after introduction"
            )


def load_implementation():

    spec = (
        importlib.util.spec_from_file_location(
            "future_human_review_protocol_amendment_validation",
            IMPL,
        )
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "Unable to load frozen human-review implementation"
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


def validate_amendment_semantics():

    value = json.loads(
        AMD_JSON.read_text(
            encoding="utf-8"
        )
    )

    if (
        value[
            "amendment_id"
        ]
        !=
        "PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_IMPLEMENTATION_AMENDMENT_001"
    ):
        raise RuntimeError(
            "Implementation amendment identity changed"
        )

    if (
        value[
            "status"
        ]
        != "FROZEN_IMPLEMENTATION_AMENDMENT_001"
    ):
        raise RuntimeError(
            "Implementation amendment status changed"
        )

    if (
        value[
            "amendment_parent_commit"
        ]
        != EXPECTED_FREEZE_COMMIT
    ):
        raise RuntimeError(
            "Implementation amendment parent changed"
        )

    correction = value[
        "correction"
    ]

    required_true = (
        "original_freeze_evidence_remains_historical",
        "downstream_review_artifacts_do_not_invalidate_original_freeze",
        "later_valid_append_only_ledger_advancement_does_not_invalidate_original_freeze",
        "current_ledger_must_still_validate_semantically",
        "immutable_upstream_contracts_must_still_validate",
        "original_seven_freeze_files_remain_immutable",
        "original_freeze_checksum_closure_remains_required",
        "review_artifacts_remain_subject_to_frozen_review_protocol",
    )

    for key in required_true:

        if correction[
            key
        ] is not True:
            raise RuntimeError(
                "Required lifecycle correction changed: "
                + key
            )

    if correction[
        "production_authority_granted"
    ] is not False:
        raise RuntimeError(
            "Implementation amendment unexpectedly grants production authority"
        )

    defect = value[
        "defect"
    ]

    for key in (
        "scientific_logic_defect",
        "implementation_runtime_defect",
        "event_semantics_defect",
        "operator_validation_defect",
    ):

        if defect[
            key
        ] is not False:
            raise RuntimeError(
                "Defect classification changed: "
                + key
            )

    if any(
        value[
            "scientific_effect"
        ].values()
    ):
        raise RuntimeError(
            "Implementation amendment unexpectedly changes scientific state"
        )


def validate_current_runtime():

    impl = load_implementation()

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
            "Current append-only ledger no longer validates"
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
            "Read-only ledger validation reported mutation"
        )

    if (
        runtime[
            "mutable_ledger_sha_pinned"
        ]
        is not False
    ):
        raise RuntimeError(
            "Mutable ledger became permanent implementation identity"
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
            "Frozen review-workspace semantics changed"
        )

    return (
        impl,
        runtime,
    )


def validate_amendment_time_recovery(
    *,
    position: str,
    impl,
    runtime,
):

    if position not in {
        "PRE_COMMIT_PARENT",
        "COMMITTED_AMENDMENT",
    }:
        return

    if sha(
        SOURCE
    ) != EXPECTED_BLANK_SHA:
        raise RuntimeError(
            "Frozen source packet changed"
        )

    if not WORKING.is_file():
        raise RuntimeError(
            "Materialized priority_001 working packet missing"
        )

    if sha(
        WORKING
    ) != EXPECTED_BLANK_SHA:
        raise RuntimeError(
            "Failed-mutation rollback packet is not exact blank bytes"
        )

    if (
        SOURCE.read_bytes()
        != WORKING.read_bytes()
    ):
        raise RuntimeError(
            "Failed-mutation rollback differs from frozen source"
        )

    summary = (
        impl.validate_reviewed_packet(
            packet_id="priority_001",
            reviewed_path=WORKING,
            require_complete=False,
        )
    )

    if (
        summary[
            "completed_review_rows"
        ]
        != 0
        or summary[
            "blank_review_rows"
        ]
        != 500
        or summary[
            "review_complete"
        ]
        is not False
    ):
        raise RuntimeError(
            "Failed-mutation review state not fully rolled back"
        )

    ledger = runtime[
        "current_ledger"
    ]

    if (
        ledger[
            "event_count"
        ]
        != EXPECTED_LEDGER_ROWS_AT_AMENDMENT
    ):
        raise RuntimeError(
            "Amendment-time event count differs"
        )

    if (
        ledger[
            "ledger_sha256"
        ]
        != EXPECTED_LEDGER_SHA_AT_AMENDMENT
    ):
        raise RuntimeError(
            "Amendment-time ledger SHA differs"
        )

    files = {
        p
        for p in REVIEW_ROOT.rglob(
            "*"
        )
        if p.is_file()
    }

    if files != {
        WORKING
    }:
        raise RuntimeError(
            "Unexpected real review artifact exists at amendment boundary"
        )


def validate_original_validator_as_archival(
    position: str,
):

    if position == "PRE_COMMIT_PARENT":
        return

    subprocess.check_call(
        [
            sys.executable,
            str(
                ORIGINAL_FREEZE_VALIDATOR
            ),
        ]
    )


def validate():

    position, intro = (
        repository_position()
    )

    validate_manifest(
        AMD_SUMS
    )

    validate_original_freeze_commit()

    validate_amendment_immutability(
        intro
    )

    validate_amendment_semantics()

    impl, runtime = (
        validate_current_runtime()
    )

    validate_amendment_time_recovery(
        position=
            position,

        impl=
            impl,

        runtime=
            runtime,
    )

    validate_original_validator_as_archival(
        position
    )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | implementation Amendment 001 validates"
    )

    print(
        "PASS | original seven-file implementation freeze remains byte-identical"
    )

    print(
        "PASS | original implementation checksum closure remains valid"
    )

    print(
        "PASS | downstream review artifacts no longer invalidate archival freeze"
    )

    print(
        "PASS | valid future ledger advancement no longer invalidates archival freeze"
    )

    print(
        "PASS | current ledger still validates semantically"
    )

    print(
        "PASS | failed first review mutation rollback is clean at amendment boundary"
    )

    print(
        "PASS | scientific and production authority remain false"
    )


if __name__ == "__main__":

    validate()
