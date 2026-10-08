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

EXPECTED_PARENT = (
    "1f39f2cae2ffb8816cbd770afc0874e0c4fba834"
)

ORIGINAL_FREEZE_COMMIT = (
    "e628e47112a7c714b6a7820b875a1dda0e3a2b8f"
)

EXPECTED_BLANK_SHA = (
    "665edd7eb4c00535ce1fb531460faa1e7c8193e6ef86814cad40fa0772435f05"
)

EXPECTED_LEDGER_ROWS_AT_BOUNDARY = 2011

EXPECTED_LEDGER_SHA_AT_BOUNDARY = (
    "f7175d03bb559a8996e7a2fb1aba3959abab87429b86adbd19df74f0f0cbf45e"
)

IMPL = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1.py"
)

ORIGINAL_FREEZE = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_freeze.py"
)

ORIGINAL_FREEZE_SUMS = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation.sha256"
)

AMD1_JSON = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_amendment_001_design.json"
)

AMD1_MD = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_"
      "IMPLEMENTATION_AMENDMENT_001.md"
)

AMD1_FREEZE = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_amendment_001_freeze.py"
)

AMD1_SUMS = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_amendment_001.sha256"
)

AMD2_JSON = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_amendment_002_design.json"
)

AMD2_MD = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_"
      "IMPLEMENTATION_AMENDMENT_002.md"
)

AMD2_FREEZE = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_amendment_002_freeze.py"
)

AMD2_SUMS = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "implementation_amendment_002.sha256"
)

EXPECTED_AMENDMENT_PATHS = {
    str(
        AMD2_JSON
    ),
    str(
        AMD2_MD
    ),
    str(
        AMD2_FREEZE
    ),
    str(
        AMD2_SUMS
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
            AMD2_JSON
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
            "Implementation Amendment 002 is not committed"
        )

    if (
        git(
            "rev-parse",
            intro + "^",
        )
        != EXPECTED_PARENT
    ):
        raise RuntimeError(
            "Amendment002 introduction parent differs"
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
            "Amendment002 commit path set differs"
        )

    if not is_ancestor(
        intro,
        head,
    ):
        raise RuntimeError(
            "HEAD not descended from Amendment002"
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
            "Empty checksum manifest"
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


def validate_amendment001_immutable():

    value = json.loads(
        AMD2_JSON.read_text(
            encoding="utf-8"
        )
    )

    binding = value[
        "amendment_001_binding"
    ]

    expected = {
        AMD1_JSON:
            binding[
                "design_sha256"
            ],

        AMD1_MD:
            binding[
                "document_sha256"
            ],

        AMD1_FREEZE:
            binding[
                "validator_sha256"
            ],

        AMD1_SUMS:
            binding[
                "checksum_manifest_sha256"
            ],
    }

    for path, digest in expected.items():

        if sha(
            path
        ) != digest:
            raise RuntimeError(
                "Amendment001 artifact changed: "
                + str(
                    path
                )
            )

        committed = git_bytes(
            "show",
            f"{EXPECTED_PARENT}:{path}",
        )

        if (
            path.read_bytes()
            != committed
        ):
            raise RuntimeError(
                "Amendment001 differs from Amendment002 parent"
            )

    validate_manifest(
        AMD1_SUMS
    )

    validate_manifest(
        ORIGINAL_FREEZE_SUMS
    )


def validate_amendment002_immutability(
    intro,
):

    if intro is None:
        return

    for path in (
        AMD2_JSON,
        AMD2_MD,
        AMD2_FREEZE,
        AMD2_SUMS,
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
                "Amendment002 changed after introduction"
            )


def validate_semantics():

    value = json.loads(
        AMD2_JSON.read_text(
            encoding="utf-8"
        )
    )

    if (
        value[
            "amendment_id"
        ]
        !=
        "PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_IMPLEMENTATION_AMENDMENT_002"
    ):
        raise RuntimeError(
            "Amendment002 identity changed"
        )

    if (
        value[
            "status"
        ]
        != "FROZEN_IMPLEMENTATION_AMENDMENT_002"
    ):
        raise RuntimeError(
            "Amendment002 status changed"
        )

    if (
        value[
            "amendment_parent_commit"
        ]
        != EXPECTED_PARENT
    ):
        raise RuntimeError(
            "Amendment002 parent changed"
        )

    lifecycle = value[
        "normative_lifecycle_correction"
    ]

    true_fields = (
        "amendment_001_blank_packet_snapshot_is_historical_boundary_evidence",
        "amendment_001_ledger_count_is_historical_boundary_evidence",
        "amendment_001_ledger_sha_is_historical_boundary_evidence",
        "amendment_001_exact_review_file_set_is_historical_boundary_evidence",
        "current_ledger_must_validate_semantically",
        "immutable_upstream_contracts_must_validate",
        "frozen_unit_and_hostile_suites_are_pre_review_freeze_evidence",
    )

    for field in true_fields:

        if lifecycle[
            field
        ] is not True:
            raise RuntimeError(
                "Required lifecycle correction changed: "
                + field
            )

    false_fields = (
        "downstream_review_packet_mutation_invalidates_amendment_001",
        "downstream_review_packet_materialization_invalidates_original_freeze",
        "valid_unrelated_ledger_advancement_invalidates_freeze",
        "frozen_unit_and_hostile_suites_are_required_live_review_runtime_checks",
        "frozen_test_files_may_be_rewritten",
        "frozen_implementation_may_be_rewritten",
    )

    for field in false_fields:

        if lifecycle[
            field
        ] is not False:
            raise RuntimeError(
                "Forbidden lifecycle claim changed: "
                + field
            )

    if any(
        value[
            "scientific_effect"
        ].values()
    ):
        raise RuntimeError(
            "Amendment002 unexpectedly changes scientific state"
        )


def load_implementation():

    spec = (
        importlib.util.spec_from_file_location(
            "future_human_review_protocol_amendment002",
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


def validate_current_runtime():

    impl = load_implementation()

    runtime = (
        impl.validate_upstream_contract()
    )

    workspace = (
        impl.validate_frozen_workspace_contract()
    )

    ledger = runtime[
        "current_ledger"
    ]

    if (
        ledger[
            "status"
        ]
        != "EVENT_LEDGER_VALID"
    ):
        raise RuntimeError(
            "Current ledger invalid"
        )

    if (
        ledger[
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
            "Mutable ledger unexpectedly pinned"
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

    return (
        impl,
        runtime,
    )


def validate_boundary_evidence_only_precommit(
    *,
    position: str,
    impl,
    runtime,
):

    # CRITICAL LIFECYCLE RULE:
    # Mutable review state is checked only before Amendment002 is committed.
    # COMMITTED_AMENDMENT and descendants deliberately do not require the
    # packet to remain blank or the ledger to retain this snapshot.
    if position != "PRE_COMMIT_PARENT":
        return

    if sha(
        SOURCE
    ) != EXPECTED_BLANK_SHA:
        raise RuntimeError(
            "Frozen priority_001 source changed"
        )

    if not WORKING.is_file():
        raise RuntimeError(
            "priority_001 working packet missing"
        )

    if sha(
        WORKING
    ) != EXPECTED_BLANK_SHA:
        raise RuntimeError(
            "Amendment002 boundary packet not blank"
        )

    if (
        WORKING.read_bytes()
        != SOURCE.read_bytes()
    ):
        raise RuntimeError(
            "Amendment002 boundary packet differs from source"
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
            "Amendment002 boundary review state differs"
        )

    ledger = runtime[
        "current_ledger"
    ]

    if (
        ledger[
            "event_count"
        ]
        != EXPECTED_LEDGER_ROWS_AT_BOUNDARY
    ):
        raise RuntimeError(
            "Amendment002 boundary event count differs"
        )

    if (
        ledger[
            "ledger_sha256"
        ]
        != EXPECTED_LEDGER_SHA_AT_BOUNDARY
    ):
        raise RuntimeError(
            "Amendment002 boundary ledger SHA differs"
        )

    files = {
        path
        for path in REVIEW_ROOT.rglob(
            "*"
        )
        if path.is_file()
    }

    if files != {
        WORKING
    }:
        raise RuntimeError(
            "Unexpected review artifact at Amendment002 boundary"
        )


def validate_prior_validators(
    position: str,
):

    subprocess.check_call(
        [
            sys.executable,
            str(
                ORIGINAL_FREEZE
            ),
        ]
    )

    # Before Amendment002 commit Amendment001 is still at its exact
    # COMMITTED_AMENDMENT state and the blank boundary has already been
    # verified above. After commit it becomes DESCENDANT_OF_AMENDMENT and
    # therefore behaves archivally.
    subprocess.check_call(
        [
            sys.executable,
            str(
                AMD1_FREEZE
            ),
        ]
    )


def validate():

    position, intro = (
        repository_position()
    )

    validate_manifest(
        AMD2_SUMS
    )

    validate_amendment001_immutable()

    validate_amendment002_immutability(
        intro
    )

    validate_semantics()

    impl, runtime = (
        validate_current_runtime()
    )

    validate_boundary_evidence_only_precommit(
        position=
            position,

        impl=
            impl,

        runtime=
            runtime,
    )

    validate_prior_validators(
        position
    )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | implementation Amendment 002 validates"
    )

    print(
        "PASS | Amendment001 remains byte-identical and checksum-valid"
    )

    print(
        "PASS | original implementation freeze remains checksum-valid"
    )

    print(
        "PASS | mutable review snapshot is historical boundary evidence only"
    )

    print(
        "PASS | mutable ledger snapshot is historical boundary evidence only"
    )

    print(
        "PASS | frozen unit/hostile suites classified as pre-review evidence"
    )

    print(
        "PASS | current ledger still validated semantically"
    )

    print(
        "PASS | no scientific or production authority granted"
    )


if __name__ == "__main__":

    validate()
