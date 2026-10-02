#!/usr/bin/env python3

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import tempfile

from pathlib import Path

import pre_review_triage_future_review_workspace_v1 as w


ROOT = Path(
    "experiments/07_comparative_landscape"
)

OUTPUT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_review_workspace_v1"
)

LEDGER = Path(
    "results/07_comparative_landscape/"
    "baseline_scientific_screening_execution/"
    "event_ledger.tsv"
)

EXPECTED_PARENT = "d6d2d874aa61bf429767469bec34ee5b6a57e5af"

EXPECTED_AUTH_SUMS_SHA = "8eac88baadd0faac123def9c6f51be65f5707279815c41f869aa18a3afc0c09a"
EXPECTED_IMPL_SUMS_SHA = "884c8e45ac89cdcd6631579b00be02cab664b8c644c58aec9c725e4d917e7449"
EXPECTED_DESIGN_SUMS_SHA = "754288330069b576dff1e68c7c99c6fb57279c4860c3913818984bb6f57cb484"

EXPECTED_AUTH_SHA = "42fc9031cf1a684406b591fb976d6bd8cd3f3ac8d433a510f7a29f31fcf003ce"
EXPECTED_BUILDER_SHA = "b347de8b56325a56b5bb62d000d567c367b75270aed1566bdd907463992c05a0"

EXPECTED_RESULT_DESIGN_SHA = "c9eb66033589d71607fb69613a3db89bedec470f3f9d07f7aedd1316602643b4"
EXPECTED_RESULT_DOC_SHA = "65898205e952e45566e47ee6cba63ca42b3f8f87b2d4c6c2aeaf72537a7e24f9"

EXPECTED_TREE_SHA = "4dc8ede8500339a7cbe70858b842239e56cab29d5e34ada3ef54ffb55d768d6f"
EXPECTED_LEDGER_SHA = "f7175d03bb559a8996e7a2fb1aba3959abab87429b86adbd19df74f0f0cbf45e"

AUTH = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_generation_authorization.json"
)

AUTH_SUMS = (
    ROOT
    / "pre_review_triage_future_review_workspace_v1_generation_authorization.sha256"
)

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


def expected_output_relpaths():

    values = {
        "checksums.sha256",
        "packet_manifest.tsv",
        "prior_carry_forwards.tsv",
        "review_work_membership.tsv",
        "workspace_manifest.json",
        "packets/manual_001.tsv",
    }

    values |= {
        f"packets/priority_{i:03d}.tsv"
        for i in range(1, 12)
    }

    values |= {
        f"packets/residual_{i:03d}.tsv"
        for i in range(1, 14)
    }

    return values


EXPECTED_OUTPUT_RELPATHS = (
    expected_output_relpaths()
)

EXPECTED_OUTPUT_PATHS = {
    str(OUTPUT / rel)
    for rel in EXPECTED_OUTPUT_RELPATHS
}

EXPECTED_COMMIT_PATHS = (
    EXPECTED_OUTPUT_PATHS
    | {
        str(RESULT_DESIGN),
        str(RESULT_DOC),
        str(RESULT_FREEZE),
        str(RESULT_SUMS),
    }
)

EXPECTED_CHECKSUM_TARGETS = (
    EXPECTED_OUTPUT_PATHS
    | {
        str(RESULT_DESIGN),
        str(RESULT_DOC),
        str(RESULT_FREEZE),
        str(AUTH),
        str(AUTH_SUMS),
        str(IMPL_SUMS),
        str(DESIGN_SUMS),
        str(BUILDER),
    }
)


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
            "Unexpected workspace-result-freeze repository position"
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
            "Workspace-result-freeze commit path set differs"
        )

    return "COMMITTED_FREEZE"


def read_tsv(path: Path):

    with path.open(
        encoding="utf-8",
        newline="",
    ) as h:

        reader = csv.DictReader(
            h,
            delimiter="\t",
        )

        return (
            reader.fieldnames,
            list(reader),
        )


def tree_sha() -> str:

    h = hashlib.sha256()

    files = sorted(
        p for p in OUTPUT.rglob("*")
        if p.is_file()
    )

    if len(files) != 30:
        raise RuntimeError(
            "Canonical workspace file count changed"
        )

    for path in files:

        rel = str(
            path.relative_to(
                OUTPUT
            )
        )

        digest = sha(path)

        h.update(
            (
                rel
                + "\t"
                + digest
                + "\n"
            ).encode(
                "utf-8"
            )
        )

    return h.hexdigest()


def validate_result_checksum_manifest():

    entries = {}

    for line in RESULT_SUMS.read_text(
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
                "Duplicate result-freeze checksum target"
            )

        entries[rel] = digest

    if set(entries) != EXPECTED_CHECKSUM_TARGETS:
        raise RuntimeError(
            "Result-freeze checksum target set differs"
        )

    for rel, digest in entries.items():

        path = Path(rel)

        if not path.is_file():
            raise RuntimeError(
                "Result-freeze checksum target missing: "
                + rel
            )

        if sha(path) != digest:
            raise RuntimeError(
                "Result-freeze checksum mismatch: "
                + rel
            )


def validate_independent_rebuild():

    raw = w.load_real_inputs()
    bundle = w.build_workspace(raw)

    with tempfile.TemporaryDirectory(
        prefix="future-review-workspace-freeze-validator."
    ) as td:

        rebuilt = (
            Path(td)
            / "workspace"
        )

        w.write_workspace(
            rebuilt,
            bundle,
        )

        expected = sorted(
            p.relative_to(OUTPUT)
            for p in OUTPUT.rglob("*")
            if p.is_file()
        )

        actual = sorted(
            p.relative_to(rebuilt)
            for p in rebuilt.rglob("*")
            if p.is_file()
        )

        if actual != expected:
            raise RuntimeError(
                "Independent rebuild file set differs"
            )

        for rel in expected:

            if (
                OUTPUT / rel
            ).read_bytes() != (
                rebuilt / rel
            ).read_bytes():

                raise RuntimeError(
                    "Independent rebuild differs: "
                    + str(rel)
                )


def validate_semantics():

    membership_fields, membership = read_tsv(
        OUTPUT
        / "review_work_membership.tsv"
    )

    _, carry = read_tsv(
        OUTPUT
        / "prior_carry_forwards.tsv"
    )

    _, packet_manifest = read_tsv(
        OUTPUT
        / "packet_manifest.tsv"
    )

    if len(membership) != 12156:
        raise RuntimeError(
            "Review-work count changed"
        )

    if len(carry) != 6:
        raise RuntimeError(
            "Carry-forward count changed"
        )

    if len(packet_manifest) != 25:
        raise RuntimeError(
            "Packet count changed"
        )

    forbidden = {
        "continuous_score",
        "selected_candidate_id",
    }

    if forbidden & set(
        membership_fields
    ):
        raise RuntimeError(
            "Forbidden model field in membership"
        )

    human_fields = {
        "proposed_event_type",
        "proposed_record_decision",
        "proposed_exclusion_reason_code",
        "proposed_candidate_method_flag",
        "evidence_basis",
        "evidence_source_locator",
        "evidence_escalation_status",
        "notes",
    }

    packet_ids = set()

    for rel in sorted(
        x for x in EXPECTED_OUTPUT_RELPATHS
        if x.startswith("packets/")
    ):

        fields, rows = read_tsv(
            OUTPUT
            / rel
        )

        if forbidden & set(fields):
            raise RuntimeError(
                "Forbidden model field in packet"
            )

        if not human_fields <= set(fields):
            raise RuntimeError(
                "Review packet missing human-entry field"
            )

        for row in rows:

            for field in human_fields:
                if row[field] != "":
                    raise RuntimeError(
                        "Human-entry field is not blank"
                    )

            sid = row[
                "screening_entity_id"
            ]

            if sid in packet_ids:
                raise RuntimeError(
                    "Duplicate review entity across packets"
                )

            packet_ids.add(sid)

    membership_ids = {
        row[
            "screening_entity_id"
        ]
        for row in membership
    }

    carry_ids = {
        row[
            "screening_entity_id"
        ]
        for row in carry
    }

    if packet_ids != membership_ids:
        raise RuntimeError(
            "Packet universe differs from review membership"
        )

    if carry_ids & membership_ids:
        raise RuntimeError(
            "Carry-forward overlaps review universe"
        )

    for row in carry:

        if (
            row["record_decision"]
            != "retain_for_method_assessment"
        ):
            raise RuntimeError(
                "Carry-forward decision changed"
            )

        if (
            row["scientific_reassessment_performed"]
            != "false"
        ):
            raise RuntimeError(
                "Carry-forward reassessment changed"
            )

    manifest = json.loads(
        (
            OUTPUT
            / "workspace_manifest.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    if any(
        manifest[
            "scientific_boundary"
        ].values()
    ):
        raise RuntimeError(
            "Workspace scientific boundary changed"
        )

    if any(
        manifest[
            "model_information"
        ].values()
    ):
        raise RuntimeError(
            "Workspace model-information boundary changed"
        )


def validate():

    position = repository_position()

    if sha(AUTH_SUMS) != EXPECTED_AUTH_SUMS_SHA:
        raise RuntimeError(
            "Authorization freeze changed"
        )

    if sha(IMPL_SUMS) != EXPECTED_IMPL_SUMS_SHA:
        raise RuntimeError(
            "Implementation freeze changed"
        )

    if sha(DESIGN_SUMS) != EXPECTED_DESIGN_SUMS_SHA:
        raise RuntimeError(
            "Workspace design freeze changed"
        )

    if sha(AUTH) != EXPECTED_AUTH_SHA:
        raise RuntimeError(
            "Generation authorization JSON changed"
        )

    if sha(BUILDER) != EXPECTED_BUILDER_SHA:
        raise RuntimeError(
            "Active builder changed"
        )

    if sha(RESULT_DESIGN) != EXPECTED_RESULT_DESIGN_SHA:
        raise RuntimeError(
            "Result-freeze design changed"
        )

    if sha(RESULT_DOC) != EXPECTED_RESULT_DOC_SHA:
        raise RuntimeError(
            "Result-freeze document changed"
        )

    actual_output_paths = {
        str(path)
        for path in OUTPUT.rglob("*")
        if path.is_file()
    }

    if actual_output_paths != EXPECTED_OUTPUT_PATHS:
        raise RuntimeError(
            "Canonical workspace artifact set changed"
        )

    validate_result_checksum_manifest()

    w.validate_materialized_workspace(
        OUTPUT
    )

    if tree_sha() != EXPECTED_TREE_SHA:
        raise RuntimeError(
            "Canonical workspace tree identity changed"
        )

    validate_semantics()

    if sha(LEDGER) != EXPECTED_LEDGER_SHA:
        raise RuntimeError(
            "Production ledger changed before result freeze"
        )

    _, ledger_rows = read_tsv(
        LEDGER
    )

    if len(ledger_rows) != 2011:
        raise RuntimeError(
            "Production ledger row count changed before result freeze"
        )

    future_ids = {
        row["screening_entity_id"]
        for row in read_tsv(
            OUTPUT
            / "review_work_membership.tsv"
        )[1]
    }

    future_ids |= {
        row["screening_entity_id"]
        for row in read_tsv(
            OUTPUT
            / "prior_carry_forwards.tsv"
        )[1]
    }

    if any(
        row.get(
            "screening_entity_id",
            ""
        ) in future_ids
        for row in ledger_rows
    ):
        raise RuntimeError(
            "Future workspace entity has accepted event before result freeze"
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
            "Result-freeze status changed"
        )

    if value["freeze_parent_commit"] != EXPECTED_PARENT:
        raise RuntimeError(
            "Result-freeze parent changed"
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
            "One-use generation not recorded consumed"
        )

    if (
        generation[
            "generation_success"
        ]
        is not True
    ):
        raise RuntimeError(
            "Successful generation state changed"
        )

    if (
        generation[
            "rerun_authorized"
        ]
        is not False
    ):
        raise RuntimeError(
            "Rerun unexpectedly authorized"
        )

    contract = value[
        "result_contract"
    ]

    if (
        contract[
            "canonical_file_count"
        ]
        != 30
        or contract[
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
            "Frozen result contract changed"
        )

    if any(
        value[
            "scientific_boundary"
        ].values()
    ):
        raise RuntimeError(
            "Scientific authority leaked into result freeze"
        )

    if value["next_gate"] is not None:
        raise RuntimeError(
            "Result freeze unexpectedly grants downstream gate"
        )

    validate_independent_rebuild()

    print(
        "PASS | repository position =",
        position,
    )
    print(
        "PASS | future review-workspace result freeze validates"
    )
    print(
        "PASS | exact 30 canonical artifacts bound"
    )
    print(
        "PASS | canonical tree SHA exact"
    )
    print(
        "PASS | independent rebuild byte-identical"
    )
    print(
        "PASS | 12,156 new review + 6 carry-forward exact"
    )
    print(
        "PASS | 25 lane-local packets exact"
    )
    print(
        "PASS | all human-entry fields remain blank"
    )
    print(
        "PASS | model fields remain excluded"
    )
    print(
        "PASS | one-use GENERATION_001 consumed; rerun unauthorized"
    )
    print(
        "PASS | production ledger unchanged by generation"
    )
    print(
        "PASS | scientific boundary remains pre-review"
    )
    print(
        "PASS | downstream gate remains unresolved"
    )


if __name__ == "__main__":
    validate()
