#!/usr/bin/env python3

from __future__ import annotations

import csv
import hashlib
import json
import re
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
    "5acedcdd340523a92dfb626287197a2b177e1aad"
)

AMD_DESIGN = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_"
      "terminology_amendment_001_design.json"
)

AMD_DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_"
      "TERMINOLOGY_AMENDMENT_001.md"
)

AMD_FREEZE = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_"
      "terminology_amendment_001_freeze.py"
)

AMD_SUMS = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_"
      "terminology_amendment_001.sha256"
)

DESIGN_MD = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_DESIGN.md"
)

DESIGN_JSON = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_design.json"
)

IMPL_MD = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_IMPLEMENTATION.md"
)

AUTH_MD = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_"
      "GENERATION_AUTHORIZATION.md"
)

RESULTS_MD = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_RESULTS.md"
)

CARRY = (
    WORK
    / "prior_carry_forwards.tsv"
)

EXPECTED_COMMIT_PATHS = {
    str(AMD_DESIGN),
    str(AMD_DOC),
    str(AMD_FREEZE),
    str(AMD_SUMS),
}

LEGACY_RX = re.compile(
    r"prior[\s_-]*wave[\s_-]*0"
    r"|wave[\s_-]*0[\s_-]*carry"
    r"|prior_wave0",
    re.IGNORECASE,
)


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
        ["git", *args],
        text=True,
    ).strip()


def git_bytes(
    *args: str,
) -> bytes:

    return subprocess.check_output(
        ["git", *args]
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

    return result.returncode == 0


def introduction_commit():

    value = git(
        "log",
        "--diff-filter=A",
        "-1",
        "--format=%H",
        "--",
        str(AMD_DESIGN),
    )

    return value or None


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

    intro = introduction_commit()

    if intro is None:
        raise RuntimeError(
            "Terminology amendment is not committed"
        )

    if (
        git(
            "rev-parse",
            intro + "^",
        )
        != EXPECTED_PARENT
    ):
        raise RuntimeError(
            "Terminology amendment introduction parent differs"
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

    if changed != EXPECTED_COMMIT_PATHS:
        raise RuntimeError(
            "Terminology amendment commit path set differs"
        )

    if not is_ancestor(
        intro,
        head,
    ):
        raise RuntimeError(
            "HEAD is not descended from terminology amendment"
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

        entries[
            rel
        ] = digest

    return entries


def validate_checksum_closure():

    entries = parse_checksum_manifest(
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

        if sha(path) != expected:
            raise RuntimeError(
                "Checksum target changed: "
                + rel
            )


def validate_amendment_immutability(
    intro,
):

    if intro is None:
        return

    for path in (
        AMD_DESIGN,
        AMD_DOC,
        AMD_FREEZE,
        AMD_SUMS,
    ):

        committed = git_bytes(
            "show",
            f"{intro}:{path}",
        )

        if path.read_bytes() != committed:
            raise RuntimeError(
                "Terminology amendment changed after introduction: "
                + str(path)
            )


def validate_original_frozen_bytes():

    value = json.loads(
        AMD_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    expected = value[
        "affected_frozen_paths"
    ]

    for rel, digest in expected.items():

        path = Path(
            rel
        )

        if sha(path) != digest:
            raise RuntimeError(
                "Previously frozen terminology-bearing file changed: "
                + rel
            )

        parent_bytes = git_bytes(
            "show",
            f"{EXPECTED_PARENT}:{rel}",
        )

        if (
            path.read_bytes()
            != parent_bytes
        ):
            raise RuntimeError(
                "Previously frozen file differs from amendment parent: "
                + rel
            )


def validate_legacy_footprint():

    paths = [
        DESIGN_MD,
        DESIGN_JSON,
        IMPL_MD,
        AUTH_MD,
        RESULTS_MD,
    ]

    counts = {}

    for path in paths:

        count = 0

        for line in path.read_text(
            encoding="utf-8"
        ).splitlines():

            if LEGACY_RX.search(
                line
            ):
                count += 1

        counts[
            str(path)
        ] = count

    expected = {
        str(path):
            1
        for path in paths
    }

    if counts != expected:
        raise RuntimeError(
            "Historical terminology footprint changed: "
            + repr(
                counts
            )
        )


def validate_carry_forwards():

    value = json.loads(
        AMD_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    contract = value[
        "authoritative_carry_forward_source"
    ]

    if sha(CARRY) != contract[
        "sha256"
    ]:
        raise RuntimeError(
            "Prior carry-forward source changed"
        )

    with CARRY.open(
        encoding="utf-8",
        newline="",
    ) as handle:

        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    if len(rows) != 6:
        raise RuntimeError(
            "Prior carry-forward count changed"
        )

    ids = set()

    for row in rows:

        entity = row[
            "screening_entity_id"
        ]

        if entity in ids:
            raise RuntimeError(
                "Duplicate prior carry-forward entity"
            )

        ids.add(
            entity
        )

        if (
            row[
                "prior_anchor_decision"
            ]
            != "include_as_anchor"
        ):
            raise RuntimeError(
                "Prior-anchor decision changed"
            )

        if (
            row[
                "record_decision"
            ]
            != "retain_for_method_assessment"
        ):
            raise RuntimeError(
                "Carry-forward record decision changed"
            )

        if (
            row[
                "scientific_reassessment_performed"
            ].strip().lower()
            != "false"
        ):
            raise RuntimeError(
                "Carry-forward scientific reassessment changed"
            )


def validate_amendment_semantics():

    value = json.loads(
        AMD_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if (
        value[
            "amendment_id"
        ]
        !=
        "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_TERMINOLOGY_AMENDMENT_001"
    ):
        raise RuntimeError(
            "Terminology amendment identity changed"
        )

    if (
        value[
            "status"
        ]
        != "FROZEN_TERMINOLOGY_AMENDMENT_001"
    ):
        raise RuntimeError(
            "Terminology amendment status changed"
        )

    if (
        value[
            "amendment_parent_commit"
        ]
        != EXPECTED_PARENT
    ):
        raise RuntimeError(
            "Terminology amendment parent changed"
        )

    normative = value[
        "normative_terminology"
    ]

    if (
        normative[
            "preferred_category_label"
        ]
        != "prior-anchor carry-forwards"
    ):
        raise RuntimeError(
            "Normative carry-forward terminology changed"
        )

    if (
        normative[
            "preferred_machine_key_for_future_contracts"
        ]
        != "prior_anchor_carry_forwards"
    ):
        raise RuntimeError(
            "Normative machine key changed"
        )

    effect = value[
        "scientific_effect"
    ]

    if any(
        effect.values()
    ):
        raise RuntimeError(
            "Terminology amendment unexpectedly changes scientific state"
        )

    if any(
        value[
            "scientific_boundary"
        ].values()
    ):
        raise RuntimeError(
            "Terminology amendment grants scientific authority"
        )


def validate():

    position, intro = (
        repository_position()
    )

    validate_checksum_closure()
    validate_amendment_immutability(
        intro
    )
    validate_original_frozen_bytes()
    validate_legacy_footprint()
    validate_carry_forwards()
    validate_amendment_semantics()

    print(
        "PASS | repository position =",
        position,
    )
    print(
        "PASS | terminology amendment 001 validates"
    )
    print(
        "PASS | exact five historical occurrences preserved"
    )
    print(
        "PASS | normative term = prior-anchor carry-forwards"
    )
    print(
        "PASS | normative future key = prior_anchor_carry_forwards"
    )
    print(
        "PASS | exactly six frozen prior adjudication carry-forwards"
    )
    print(
        "PASS | no prior scientific decision changed"
    )
    print(
        "PASS | no scientific reassessment authorized"
    )
    print(
        "PASS | original frozen files remain byte-identical"
    )


if __name__ == "__main__":
    validate()
