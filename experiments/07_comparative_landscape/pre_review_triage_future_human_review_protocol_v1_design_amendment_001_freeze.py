#!/usr/bin/env python3

from __future__ import annotations

from collections import defaultdict
import csv
import hashlib
import json
import subprocess

from pathlib import Path


ROOT = Path(
    "experiments/07_comparative_landscape"
)

WORK = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_review_workspace_v1"
)

EXPECTED_PARENT = (
    "560615fb8ab8549b69ea76d4b92c9efc69ac9ed8"
)

DESIGN_MD = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_DESIGN.md"
)

DESIGN_JSON = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_design.json"
)

DESIGN_SUMS = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_design.sha256"
)

TERM_SUMS = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_"
      "terminology_amendment_001.sha256"
)

MEMBERSHIP = (
    WORK
    / "review_work_membership.tsv"
)

TRANCHE_GUARD = (
    ROOT
    / "baseline_scientific_screening_tranche_guard_v3.py"
)

CAMPAIGN_SUMS = (
    ROOT
    / "baseline_scientific_screening_campaign_orchestration_v4_design.sha256"
)

AMD_JSON = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "design_amendment_001.json"
)

AMD_MD = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_"
      "DESIGN_AMENDMENT_001.md"
)

AMD_FREEZE = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "design_amendment_001_freeze.py"
)

AMD_SUMS = (
    ROOT
    / "pre_review_triage_future_human_review_protocol_v1_"
      "design_amendment_001.sha256"
)

EXPECTED_COMMIT_PATHS = {
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
            "Design amendment is not committed"
        )

    if (
        git(
            "rev-parse",
            intro + "^",
        )
        != EXPECTED_PARENT
    ):
        raise RuntimeError(
            "Design amendment introduction parent differs"
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
            "Design amendment commit path set differs"
        )

    if not is_ancestor(
        intro,
        head,
    ):
        raise RuntimeError(
            "HEAD is not descended from design amendment"
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
                "Duplicate checksum target"
            )

        entries[
            rel
        ] = digest

    return entries


def validate_checksum_closure():

    entries = parse_manifest(
        AMD_SUMS
    )

    for rel, expected in entries.items():

        path = Path(
            rel
        )

        if not path.is_file():
            raise RuntimeError(
                "Checksum target missing: "
                + rel
            )

        if sha(
            path
        ) != expected:
            raise RuntimeError(
                "Checksum target changed: "
                + rel
            )


def validate_original_design_unchanged():

    value = json.loads(
        AMD_JSON.read_text(
            encoding="utf-8"
        )
    )

    original = value[
        "original_design"
    ]

    expected = {
        DESIGN_MD:
            original[
                "design_md_sha256"
            ],

        DESIGN_JSON:
            original[
                "design_json_sha256"
            ],

        DESIGN_SUMS:
            original[
                "design_checksum_manifest_sha256"
            ],
    }

    for path, digest in expected.items():

        if sha(
            path
        ) != digest:
            raise RuntimeError(
                "Original design artifact changed: "
                + str(
                    path
                )
            )

        parent_bytes = git_bytes(
            "show",
            f"{EXPECTED_PARENT}:{path}",
        )

        if (
            path.read_bytes()
            != parent_bytes
        ):
            raise RuntimeError(
                "Original design artifact differs from amendment parent"
            )


def find_key(
    value,
    target,
    path=(),
):

    found = []

    if isinstance(
        value,
        dict,
    ):

        for key, child in value.items():

            next_path = (
                *path,
                key,
            )

            if key == target:

                found.append(
                    (
                        ".".join(
                            next_path
                        ),
                        child,
                    )
                )

            found.extend(
                find_key(
                    child,
                    target,
                    next_path,
                )
            )

    elif isinstance(
        value,
        list,
    ):

        for index, child in enumerate(
            value
        ):

            found.extend(
                find_key(
                    child,
                    target,
                    (
                        *path,
                        str(
                            index
                        ),
                    ),
                )
            )

    return found


def validate_superseded_claims():

    original = json.loads(
        DESIGN_JSON.read_text(
            encoding="utf-8"
        )
    )

    keys = (
        "later_bridge_must_satisfy_current_contiguous_transaction_contract",
        "one_production_transaction_per_existing_batch_or_valid_contiguous_tranche",
    )

    for key in keys:

        found = find_key(
            original,
            key,
        )

        if len(
            found
        ) != 1:
            raise RuntimeError(
                f"Superseded claim occurrence differs: {key}"
            )

        if (
            found[
                0
            ][
                1
            ]
            is not True
        ):
            raise RuntimeError(
                f"Superseded original claim changed: {key}"
            )


def validate_review_distribution():

    with MEMBERSHIP.open(
        encoding="utf-8",
        newline="",
    ) as handle:

        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    if len(
        rows
    ) != 12156:
        raise RuntimeError(
            "Review membership count changed"
        )

    by_batch = defaultdict(
        list
    )

    for row in rows:

        by_batch[
            row[
                "baseline_batch_id"
            ]
        ].append(
            int(
                row[
                    "baseline_position_in_batch"
                ]
            )
        )

    if len(
        by_batch
    ) != 155:
        raise RuntimeError(
            "Review B-batch coverage changed"
        )

    contiguous = 0
    noncontiguous = 0
    full_500 = 0

    for positions in (
        by_batch.values()
    ):

        positions = sorted(
            positions
        )

        if len(
            positions
        ) != len(
            set(
                positions
            )
        ):
            raise RuntimeError(
                "Duplicate review position"
            )

        is_contiguous = (
            positions
            ==
            list(
                range(
                    positions[
                        0
                    ],
                    positions[
                        -1
                    ]
                    + 1,
                )
            )
        )

        if is_contiguous:
            contiguous += 1
        else:
            noncontiguous += 1

        if (
            len(
                positions
            )
            == 500
            and positions
            == list(
                range(
                    1,
                    501,
                )
            )
        ):
            full_500 += 1

    if (
        contiguous
        != 3
        or noncontiguous
        != 152
        or full_500
        != 0
    ):
        raise RuntimeError(
            "Review distribution evidence changed"
        )


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
        "PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_DESIGN_AMENDMENT_001"
    ):
        raise RuntimeError(
            "Amendment identity changed"
        )

    if (
        value[
            "status"
        ]
        != "FROZEN_DESIGN_AMENDMENT_001"
    ):
        raise RuntimeError(
            "Amendment status changed"
        )

    if (
        value[
            "amendment_parent_commit"
        ]
        != EXPECTED_PARENT
    ):
        raise RuntimeError(
            "Amendment parent changed"
        )

    bridge = value[
        "normative_production_bridge_contract"
    ]

    required_true = (
        "existing_B_membership_remains_authoritative",
        "later_bridge_must_use_explicit_reviewed_decisions_only",
        "additional_nontriage_positions_may_require_human_review",
        "later_bridge_must_conform_to_then_applicable_separately_frozen_production_contract",
        "production_transaction_shape_is_deferred_to_later_gate",
    )

    for key in required_true:

        if (
            bridge[
                key
            ]
            is not True
        ):
            raise RuntimeError(
                "Required bridge constraint changed: "
                + key
            )

    required_false = (
        "review_protocol_authorizes_transaction_shape",
        "review_protocol_authorizes_live_production",
        "cross_batch_transaction_authorized",
        "direct_triage_packet_to_production_proposal_projection_authorized",
        "unreviewed_nontriage_positions_may_be_inferred",
        "scientific_review_approval_is_live_production_authorization",
    )

    for key in required_false:

        if (
            bridge[
                key
            ]
            is not False
        ):
            raise RuntimeError(
                "Forbidden bridge authority changed: "
                + key
            )

    if any(
        value[
            "review_protocol_effect"
        ].values()
    ):
        raise RuntimeError(
            "Design amendment unexpectedly changes review protocol"
        )

    if any(
        value[
            "scientific_effect"
        ].values()
    ):
        raise RuntimeError(
            "Design amendment unexpectedly changes scientific state"
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
                "Design amendment changed after introduction"
            )


def validate():

    position, intro = (
        repository_position()
    )

    validate_checksum_closure()
    validate_amendment_immutability(
        intro
    )
    validate_original_design_unchanged()
    validate_superseded_claims()
    validate_review_distribution()
    validate_amendment_semantics()

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | human-review protocol design amendment 001 validates"
    )

    print(
        "PASS | original human-review design remains byte-identical"
    )

    print(
        "PASS | 12,156 review rows remain an ordering overlay"
    )

    print(
        "PASS | 155 existing B batches retained"
    )

    print(
        "PASS | 3 contiguous and 152 non-contiguous review subsets confirmed"
    )

    print(
        "PASS | future review protocol does not authorize transaction shape"
    )

    print(
        "PASS | later production shape deferred to separately frozen contract"
    )

    print(
        "PASS | no scientific or production authority granted"
    )


if __name__ == "__main__":

    validate()
