#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import subprocess

from pathlib import Path


ROOT = Path(
    "experiments/07_comparative_landscape"
)

OUTPUT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_review_workspace_v1"
)

EXPECTED_PARENT = "40dace8c545cfe2433571f65b789a0a7f72a3c15"

EXPECTED_RESULT_SUMS_SHA = "305510cf32496327ff9637792d5d316072de2bf520666c18165bca43e7271c17"
EXPECTED_RESULT_DESIGN_SHA = "c9eb66033589d71607fb69613a3db89bedec470f3f9d07f7aedd1316602643b4"
EXPECTED_RESULT_DOC_SHA = "65898205e952e45566e47ee6cba63ca42b3f8f87b2d4c6c2aeaf72537a7e24f9"
EXPECTED_RESULT_FREEZE_SHA = "e8d8056ad9cf5b7ef30d23ffcf979cf24469a6bdbda25b4a6467d02f85b0e97f"

EXPECTED_AMD_DESIGN_SHA = "fd179662774a262c18ffbd7f02d77339bcddff1aacdbfd9b51c68425e1180bb6"
EXPECTED_AMD_DOC_SHA = "bc7e85c8eb982075568623c812cda8d920be8d114a6fd037485c88d1dbec68db"

EXPECTED_TREE_SHA = (
    "4dc8ede8500339a7cbe70858b842239e56cab29d5e34ada3ef54ffb55d768d6f"
)

GENERATION_LEDGER_SHA = (
    "f7175d03bb559a8996e7a2fb1aba3959abab87429b86adbd19df74f0f0cbf45e"
)

RESULT_DESIGN = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_results_design.json"
)

RESULT_DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_RESULTS.md"
)

RESULT_FREEZE = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_results_freeze.py"
)

RESULT_SUMS = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_results.sha256"
)

AMD_DESIGN = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_results_amendment_001_design.json"
)

AMD_DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_RESULTS_AMENDMENT_001.md"
)

AMD_FREEZE = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_results_amendment_001_freeze.py"
)

AMD_SUMS = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_results_amendment_001.sha256"
)

EXPECTED_AMENDMENT_COMMIT_PATHS = {
    str(AMD_DESIGN),
    str(AMD_DOC),
    str(AMD_FREEZE),
    str(AMD_SUMS),
}

EXPECTED_AMENDMENT_SUM_TARGETS = {
    str(AMD_DESIGN),
    str(AMD_DOC),
    str(AMD_FREEZE),
    str(RESULT_SUMS),
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

    return result.returncode == 0


def amendment_introduction_commit():
    try:
        value = git(
            "log",
            "--diff-filter=A",
            "-1",
            "--format=%H",
            "--",
            str(AMD_DESIGN),
        )
    except subprocess.CalledProcessError:
        return None

    return value or None


def repository_position() -> str:

    head = git(
        "rev-parse",
        "HEAD",
    )

    if head == EXPECTED_PARENT:
        return "PRE_COMMIT_PARENT"

    intro = amendment_introduction_commit()

    if intro is None:
        raise RuntimeError(
            "Amendment files are not committed from expected parent"
        )

    intro_parent = git(
        "rev-parse",
        intro + "^",
    )

    if intro_parent != EXPECTED_PARENT:
        raise RuntimeError(
            "Amendment introduction parent differs"
        )

    changed = {
        line
        for line in git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            intro,
        ).splitlines()
        if line
    }

    if changed != EXPECTED_AMENDMENT_COMMIT_PATHS:
        raise RuntimeError(
            "Amendment introduction path set differs"
        )

    if not is_ancestor(
        intro,
        head,
    ):
        raise RuntimeError(
            "Current HEAD is not descended from amendment commit"
        )

    if head == intro:
        return "COMMITTED_AMENDMENT"

    return "DESCENDANT_OF_AMENDMENT"


def parse_checksum_manifest(
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

        if rel.startswith("*"):
            rel = rel[1:]

        if rel in entries:
            raise RuntimeError(
                "Duplicate checksum target: "
                + rel
            )

        entries[rel] = digest

    return entries


def validate_original_result_checksum_closure():

    if sha(RESULT_SUMS) != EXPECTED_RESULT_SUMS_SHA:
        raise RuntimeError(
            "Original result checksum manifest changed"
        )

    entries = parse_checksum_manifest(
        RESULT_SUMS
    )

    for rel, expected in entries.items():

        path = Path(rel)

        if not path.is_file():
            raise RuntimeError(
                "Original frozen result target missing: "
                + rel
            )

        if sha(path) != expected:
            raise RuntimeError(
                "Original frozen result target changed: "
                + rel
            )


def validate_amendment_checksum_closure():

    entries = parse_checksum_manifest(
        AMD_SUMS
    )

    if set(entries) != EXPECTED_AMENDMENT_SUM_TARGETS:
        raise RuntimeError(
            "Amendment checksum target set differs"
        )

    for rel, expected in entries.items():

        path = Path(rel)

        if not path.is_file():
            raise RuntimeError(
                "Amendment checksum target missing: "
                + rel
            )

        if sha(path) != expected:
            raise RuntimeError(
                "Amendment checksum mismatch: "
                + rel
            )


def validate_original_result_metadata():

    if sha(RESULT_DESIGN) != EXPECTED_RESULT_DESIGN_SHA:
        raise RuntimeError(
            "Original result design changed"
        )

    if sha(RESULT_DOC) != EXPECTED_RESULT_DOC_SHA:
        raise RuntimeError(
            "Original result document changed"
        )

    if sha(RESULT_FREEZE) != EXPECTED_RESULT_FREEZE_SHA:
        raise RuntimeError(
            "Original result validator changed"
        )

    value = json.loads(
        RESULT_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if (
        value["status"]
        != "FROZEN_FUTURE_REVIEW_WORKSPACE_V1_RESULTS"
    ):
        raise RuntimeError(
            "Original result status changed"
        )

    if (
        value["freeze_parent_commit"]
        != "d6d2d874aa61bf429767469bec34ee5b6a57e5af"
    ):
        raise RuntimeError(
            "Original result parent changed"
        )

    if (
        value[
            "completion"
        ][
            "canonical_result_set_complete"
        ]
        is not True
    ):
        raise RuntimeError(
            "Original result completion changed"
        )

    if (
        value[
            "completion"
        ][
            "canonical_result_set_frozen"
        ]
        is not True
    ):
        raise RuntimeError(
            "Original result frozen state changed"
        )

    contract = value[
        "result_contract"
    ]

    if (
        contract[
            "canonical_file_count"
        ]
        != 30
    ):
        raise RuntimeError(
            "Canonical file count changed"
        )

    if (
        contract[
            "canonical_tree_sha256"
        ]
        != EXPECTED_TREE_SHA
    ):
        raise RuntimeError(
            "Canonical tree identity changed"
        )

    if (
        contract[
            "new_review_work_rows"
        ]
        != 12156
        or contract[
            "prior_carry_forward_rows"
        ]
        != 6
        or contract[
            "total_packet_count"
        ]
        != 25
    ):
        raise RuntimeError(
            "Frozen workspace result contract changed"
        )

    generation = value[
        "generation"
    ]

    if (
        generation[
            "one_time_generation_consumed"
        ]
        is not True
    ):
        raise RuntimeError(
            "Generation consumption state changed"
        )

    if (
        generation[
            "generation_success"
        ]
        is not True
    ):
        raise RuntimeError(
            "Generation success state changed"
        )

    if (
        generation[
            "rerun_authorized"
        ]
        is not False
    ):
        raise RuntimeError(
            "Rerun authorization changed"
        )

    observation = value[
        "production_ledger_observation_at_generation"
    ]

    if observation != {
        "event_count": 2011,
        "future_entity_event_rows": 0,
        "ledger_sha256": GENERATION_LEDGER_SHA,
        "production_ledger_mutated_by_generation": False,
    }:
        raise RuntimeError(
            "Frozen generation-time ledger observation changed"
        )

    if any(
        value[
            "scientific_boundary"
        ].values()
    ):
        raise RuntimeError(
            "Original scientific boundary changed"
        )

    if value["next_gate"] is not None:
        raise RuntimeError(
            "Original result freeze unexpectedly grants downstream gate"
        )


def validate_amendment_metadata():

    if sha(AMD_DESIGN) != EXPECTED_AMD_DESIGN_SHA:
        raise RuntimeError(
            "Amendment design changed"
        )

    if sha(AMD_DOC) != EXPECTED_AMD_DOC_SHA:
        raise RuntimeError(
            "Amendment document changed"
        )

    value = json.loads(
        AMD_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if (
        value["amendment_id"]
        !=
        "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_RESULTS_AMENDMENT_001"
    ):
        raise RuntimeError(
            "Amendment identity changed"
        )

    if (
        value["status"]
        != "FROZEN_RESULT_VALIDATION_AMENDMENT_001"
    ):
        raise RuntimeError(
            "Amendment status changed"
        )

    if (
        value["amendment_parent_commit"]
        != EXPECTED_PARENT
    ):
        raise RuntimeError(
            "Amendment parent changed"
        )

    correction = value[
        "correction"
    ]

    if (
        correction[
            "original_34_result_freeze_paths_modified"
        ]
        is not False
    ):
        raise RuntimeError(
            "Original result paths unexpectedly authorized for modification"
        )

    if (
        correction[
            "canonical_workspace_modified"
        ]
        is not False
    ):
        raise RuntimeError(
            "Canonical workspace unexpectedly authorized for modification"
        )

    if (
        correction[
            "generation_time_ledger_evidence_preserved"
        ]
        is not True
    ):
        raise RuntimeError(
            "Generation-time ledger evidence not preserved"
        )

    for key in (
        "current_live_ledger_sha_required_for_static_result_validation",
        "current_live_ledger_row_count_required_for_static_result_validation",
        "current_live_future_entity_event_overlap_required_for_static_result_validation",
    ):
        if correction[key] is not False:
            raise RuntimeError(
                "Mutable-ledger validation requirement reintroduced: "
                + key
            )

    scope = value[
        "validation_scope"
    ]

    if (
        scope[
            "validates_historical_result_artifacts"
        ]
        is not True
    ):
        raise RuntimeError(
            "Historical-result validation disabled"
        )

    if (
        scope[
            "validates_generation_time_ledger_observation_from_frozen_metadata"
        ]
        is not True
    ):
        raise RuntimeError(
            "Generation-time ledger metadata validation disabled"
        )

    if (
        scope[
            "validates_current_mutable_event_ledger"
        ]
        is not False
    ):
        raise RuntimeError(
            "Current mutable ledger entered archival validator scope"
        )

    if any(
        value[
            "scientific_boundary"
        ].values()
    ):
        raise RuntimeError(
            "Scientific authority leaked into amendment"
        )

    if value["next_gate"] is not None:
        raise RuntimeError(
            "Amendment unexpectedly grants downstream gate"
        )


def validate():

    position = repository_position()

    validate_original_result_checksum_closure()
    validate_amendment_checksum_closure()
    validate_original_result_metadata()
    validate_amendment_metadata()

    # Deliberately no access to current mutable production-ledger state.
    # The historical generation-time ledger identity is validated only
    # through the immutable original result metadata above.

    print(
        "PASS | repository position =",
        position,
    )
    print(
        "PASS | results validation amendment 001 validates"
    )
    print(
        "PASS | original result checksum closure exact"
    )
    print(
        "PASS | canonical 30-file workspace remains exact"
    )
    print(
        "PASS | generation-time ledger evidence preserved historically"
    )
    print(
        "PASS | current mutable ledger is outside archival result validation"
    )
    print(
        "PASS | original result paths remain unmodified"
    )
    print(
        "PASS | scientific authority remains false"
    )
    print(
        "PASS | downstream human-review gate remains unresolved"
    )


if __name__ == "__main__":
    validate()
