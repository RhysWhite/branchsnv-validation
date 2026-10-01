#!/usr/bin/env python3

from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json
import subprocess

import pre_review_triage_future_text_wave_a_runner_core_v1 as core
import triage_pre_review_text_normalizer_v1 as normalizer


ROOT = Path(
    "experiments/07_comparative_landscape"
)

FUT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_text_retrieval_v1"
)

PROD = FUT / "live_wave_a"

INPUT = FUT / "input_manifest.tsv"

WAVE_A_MANIFEST = (
    FUT
    / "live_wave_a_request_manifest_amendment_001.tsv"
)

WAVE_B_MANIFEST = (
    FUT
    / "live_wave_b_request_manifest.tsv"
)

WAVE_B_DERIVATION = (
    FUT
    / "live_wave_b_derivation.tsv"
)

DESIGN = (
    ROOT
    / "pre_review_triage_future_text_wave_b_manifest_v1_design.json"
)

DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_TEXT_WAVE_B_MANIFEST_V1.md"
)

CHECKSUMS = (
    ROOT
    / "pre_review_triage_future_text_wave_b_manifest_v1.sha256"
)

FREEZE_SCRIPT = (
    ROOT
    / "pre_review_triage_future_text_wave_b_manifest_v1_freeze.py"
)

FUTURE_RETRIEVAL_DESIGN = (
    ROOT
    / "pre_review_triage_future_text_live_retrieval_v1_design.json"
)

FUTURE_RETRIEVAL_AMENDMENT = (
    ROOT
    / "pre_review_triage_future_text_live_retrieval_v1_amendment_001_design.json"
)

RETRIEVAL_COMPLETION = (
    ROOT
    / "pre_review_triage_future_text_wave_a_retrieval_completion.json"
)

NORMALIZER_PATH = (
    ROOT
    / "triage_pre_review_text_normalizer_v1.py"
)

FUTURE_GUARD_PATH = (
    ROOT
    / "pre_review_triage_future_text_wave_a_guard_v1.py"
)

FUTURE_CORE_PATH = (
    ROOT
    / "pre_review_triage_future_text_wave_a_runner_core_v1.py"
)

ADAPTER_PATH = (
    ROOT
    / "triage_pre_review_text_wave_a_transport_evidence_adapter_v1.py"
)

TRANSPORT_PATH = (
    ROOT
    / "retrieve_metadata_resolution_queue.py"
)


EXPECTED_PARENT = (
    "6bf6fff82bd03b36317dfb369947fd7d29e732fd"
)

EXPECTED_SHA256 = {
    INPUT:
        "345c90522a44f9f548fb164618943cac24fb87f7820d52a9048bcfe7a4eec6cf",

    WAVE_A_MANIFEST:
        "9c5a1b7cda465f0f4a88fc06c612c979af3093f0cecabbe4d8b42576cac30e73",

    FUT / "manifest.json":
        "021942963bce5afd5ada74ad3f2a097ce0c9f0a7f971eec198a665bb0b8ca106",

    FUT / "checksums.sha256":
        "6d79c99c164c6d5b1db0cfb6168a8fb4211fa02cbf1866737b953767d7756c3c",

    RETRIEVAL_COMPLETION:
        "034140d5e6aecc10eb3b1f04f1e6dbc93c857b5cefc9796814345e424cac95ab",

    FUTURE_RETRIEVAL_DESIGN:
        "826e400faccf7481219cd04661a4e7e785903ec2876e1384ef5cfda3b10dd9e5",

    FUTURE_RETRIEVAL_AMENDMENT:
        "576c45e6294031980e56f63bd1f9c272701f11c89ec1afa7dd8aad999ddaf968",

    NORMALIZER_PATH:
        "cbe66fc9ab406fa5ee3745e099c16250c404a949c0f301e40a7397c285dc459d",

    FUTURE_GUARD_PATH:
        "79300875f7620afde503f70b27a78449d11fcda35c23b11dc44d2fe538bcb28c",

    FUTURE_CORE_PATH:
        "c4775bfcef700ee7df35c32dafbeb97f546ff6c14b935f675ae2f745ba8144cd",

    ADAPTER_PATH:
        "30a311626b3e99e6520601585b87df3b600991094d7724cd358b52159d902bac",

    TRANSPORT_PATH:
        "9c8c11edbbec86e5cbf857f25c1bf576a0638ba5cdcf69d1fa2a8b8bfc1a994f",
}

EXPECTED_MANIFEST_SHA = (
    "e6b79c2fff3f31a8155dd7c37188d0ea"
    "2c4bd786c7e7de9950570288a2c62d11"
)

EXPECTED_DERIVATION_SHA = (
    "7fc3bd6fee6c5a3539587223ef6459df"
    "1ecce41ad670de3929836eef7a6c4474"
)

TOTAL_INPUT = 12162
TOTAL_WAVE_A = 12147
PUBMED_WAVE_A = 8539
SPECIAL_SEQ = 10083

EXECUTION_ID = (
    "FUTURE-WAVE-A-EXEC-20260930-01"
)

WAVE_B_ID = (
    "TRIAGE_FUTURE_TEXT_LIVE_WAVE_B"
)

adapter = core.adapter
transport = core.transport
guard = core.guard


class FreezeError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(
        path.read_bytes()
    )


def canonical_json_bytes(value) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode(
        "utf-8"
    )


def read_tsv(path: Path):
    with path.open(
        newline="",
        encoding="utf-8",
    ) as handle:

        return list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


def tsv_bytes(
    fields: list[str],
    rows: list[dict[str, str]],
) -> bytes:

    buffer = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        buffer,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )

    writer.writeheader()

    for row in rows:
        writer.writerow({
            field:
                str(
                    row.get(
                        field,
                        "",
                    )
                )
            for field in fields
        })

    return buffer.getvalue().encode(
        "utf-8"
    )


def verify_sidecar(path: Path) -> str:

    sidecar = Path(
        str(path) + ".sha256"
    )

    if not sidecar.is_file():
        raise FreezeError(
            f"missing checksum sidecar: {path}"
        )

    recorded = (
        sidecar.read_text(
            encoding="utf-8"
        )
        .strip()
        .split()[0]
    )

    actual = sha256_file(
        path
    )

    if actual != recorded:
        raise FreezeError(
            f"checksum mismatch: {path}"
        )

    return actual


def require_exact_source_hashes() -> None:

    for path, expected in (
        EXPECTED_SHA256.items()
    ):
        if not path.is_file():
            raise FreezeError(
                f"missing frozen source: {path}"
            )

        actual = sha256_file(
            path
        )

        if actual != expected:
            raise FreezeError(
                "frozen source hash mismatch: "
                f"{path}\n"
                f"expected={expected}\n"
                f"actual={actual}"
            )


def prohibit_network(
    *args,
    **kwargs,
):
    raise FreezeError(
        "NETWORK FORBIDDEN DURING "
        "FUTURE WAVE-B MANIFEST DERIVATION"
    )


if hasattr(
    transport,
    "default_http_executor",
):
    transport.default_http_executor = (
        prohibit_network
    )


def derive():

    head = subprocess.check_output(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        text=True,
    ).strip()

    if head != EXPECTED_PARENT:
        raise FreezeError(
            "wrong parent commit: "
            f"{head}"
        )

    require_exact_source_hashes()

    input_rows = read_tsv(
        INPUT
    )

    wave_a_rows = read_tsv(
        WAVE_A_MANIFEST
    )

    if len(
        input_rows
    ) != TOTAL_INPUT:
        raise FreezeError(
            "future input count drift"
        )

    if len(
        wave_a_rows
    ) != TOTAL_WAVE_A:
        raise FreezeError(
            "Wave A request count drift"
        )

    input_by_index = {
        int(
            row[
                "retrieval_record_index"
            ]
        ):
            row
        for row in input_rows
    }

    if len(
        input_by_index
    ) != TOTAL_INPUT:
        raise FreezeError(
            "duplicate retrieval_record_index"
        )

    wave_a_by_seq = {
        int(
            row[
                "request_sequence"
            ]
        ):
            row
        for row in wave_a_rows
    }

    if set(
        wave_a_by_seq
    ) != set(
        range(
            1,
            TOTAL_WAVE_A + 1,
        )
    ):
        raise FreezeError(
            "Wave A request sequences not contiguous"
        )

    provider_counts = Counter(
        row["provider"]
        for row in wave_a_rows
    )

    if provider_counts != Counter({
        "openalex": 3608,
        "pubmed": 8539,
    }):
        raise FreezeError(
            "Wave A provider population drift"
        )

    # --------------------------------------------------------
    # Request 10083 explicit completed recovery.
    # --------------------------------------------------------

    special_root = (
        FUT
        / "manifest_defect_exceptions"
        / EXECUTION_ID
        / "request_10083"
    )

    recovery_evidence_path = (
        special_root
        / "recovery_evidence.json"
    )

    recovery_terminal_path = (
        special_root
        / "recovery_terminal.json"
    )

    recovery_completion_path = (
        special_root
        / "recovery_completion.json"
    )

    selected_record_path = (
        special_root
        / "selected_pubmed_record_37878119.xml"
    )

    for path in (
        recovery_evidence_path,
        recovery_terminal_path,
        recovery_completion_path,
        selected_record_path,
    ):
        verify_sidecar(
            path
        )

    recovery_evidence = json.loads(
        recovery_evidence_path.read_text(
            encoding="utf-8"
        )
    )

    recovery_terminal = json.loads(
        recovery_terminal_path.read_text(
            encoding="utf-8"
        )
    )

    recovery_completion = json.loads(
        recovery_completion_path.read_text(
            encoding="utf-8"
        )
    )

    special_row = (
        wave_a_by_seq[
            SPECIAL_SEQ
        ]
    )

    if (
        recovery_evidence[
            "request_identity_sha256"
        ]
        != special_row[
            "request_identity_sha256"
        ]
    ):
        raise FreezeError(
            "request 10083 recovery identity mismatch"
        )

    if (
        recovery_evidence[
            "checkpoint_eligible"
        ]
        is not True
        or recovery_evidence[
            "network_reissued"
        ]
        is not False
        or recovery_terminal[
            "terminal_status"
        ]
        != "success"
        or recovery_completion[
            "status"
        ]
        != "CONSUMED"
        or recovery_completion[
            "network_reissued"
        ]
        is not False
    ):
        raise FreezeError(
            "request 10083 recovery state mismatch"
        )

    selected_body = (
        selected_record_path
        .read_bytes()
    )

    if (
        sha256_bytes(
            selected_body
        )
        != recovery_evidence[
            "selected_record_body_sha256"
        ]
    ):
        raise FreezeError(
            "request 10083 selected body mismatch"
        )

    special_normalized = (
        normalizer.normalize_pubmed(
            selected_body,
            "37878119",
        )
    )

    if (
        special_normalized[
            "provider_identity_status"
        ]
        != "matched"
        or special_normalized[
            "parser_status"
        ]
        != "ok"
        or special_normalized[
            "abstract_status"
        ]
        != "usable_abstract_pubmed"
    ):
        raise FreezeError(
            "request 10083 no longer reproduces "
            "usable PubMed abstract"
        )

    # --------------------------------------------------------
    # Derive eligible Wave-B parent requests.
    # --------------------------------------------------------

    fallback = []

    pubmed_adapter_status = Counter()
    pubmed_abstract_status = Counter()

    for seq in range(
        1,
        TOTAL_WAVE_A + 1,
    ):

        row = wave_a_by_seq[
            seq
        ]

        if row["provider"] != "pubmed":
            continue

        if seq == SPECIAL_SEQ:

            pubmed_adapter_status[
                "recovered_verified_success"
            ] += 1

            pubmed_abstract_status[
                "usable_abstract_pubmed"
            ] += 1

            continue

        evidence_path = (
            adapter.evidence_path(
                PROD,
                seq,
            )
        )

        durable = (
            adapter.read_evidence_path(
                evidence_path
            )
        )

        regenerated = (
            adapter.verified_evidence(
                manifest_row=row,
                archive_root=PROD,
                transport_module=transport,
            )
        )

        if regenerated != durable:
            raise FreezeError(
                "durable evidence mismatch at "
                f"request {seq}"
            )

        status = durable[
            "adapter_status"
        ]

        pubmed_adapter_status[
            status
        ] += 1

        if status == "verified_not_found":

            if (
                durable[
                    "provider_identity_status"
                ]
                != "not_applicable_not_found"
            ):
                raise FreezeError(
                    "not-found identity-state drift "
                    f"at request {seq}"
                )

            fallback.append({
                "wave_a_request_sequence":
                    seq,

                "fallback_reason":
                    "verified_not_found",

                "wave_a_request_identity_sha256":
                    row[
                        "request_identity_sha256"
                    ],

                "wave_a_adapter_evidence_sha256":
                    sha256_file(
                        evidence_path
                    ),

                "wave_a_terminal_body_sha256":
                    "",
            })

            continue

        if status != "verified_success":
            raise FreezeError(
                "ineligible unresolved PubMed "
                f"transport state at request {seq}: "
                f"{status}"
            )

        transport_row = (
            adapter.manifest_to_transport_row(
                row
            )
        )

        lookup_root = (
            adapter.transport_lookup_root(
                PROD,
                transport_row,
            )
        )

        terminal_path = (
            lookup_root
            / "terminal.json"
        )

        if not terminal_path.is_file():
            raise FreezeError(
                "missing ordinary PubMed terminal: "
                f"{seq}"
            )

        terminal = json.loads(
            terminal_path.read_text(
                encoding="utf-8"
            )
        )

        if (
            terminal[
                "terminal_status"
            ]
            != "success"
        ):
            raise FreezeError(
                "unexpected PubMed terminal status "
                f"at request {seq}"
            )

        body_sha = (
            terminal[
                "terminal_body_sha256"
            ]
        )

        bodies = []

        for body_path in (
            lookup_root.rglob(
                "*.bin"
            )
        ):
            body = (
                body_path
                .read_bytes()
            )

            if (
                sha256_bytes(
                    body
                )
                == body_sha
            ):
                bodies.append(
                    body
                )

        if len(
            bodies
        ) != 1:
            raise FreezeError(
                "terminal body multiplicity at "
                f"request {seq}: {len(bodies)}"
            )

        normalized = (
            normalizer.normalize_pubmed(
                bodies[0],
                row["identifier"],
            )
        )

        if (
            normalized[
                "provider_identity_status"
            ]
            != "matched"
            or normalized[
                "parser_status"
            ]
            != "ok"
        ):
            raise FreezeError(
                "PubMed normalization integrity "
                f"failure at request {seq}"
            )

        abstract_status = (
            normalized[
                "abstract_status"
            ]
        )

        pubmed_abstract_status[
            abstract_status
        ] += 1

        if (
            abstract_status
            == "usable_abstract_pubmed"
        ):
            continue

        if (
            abstract_status
            != "abstract_absent"
        ):
            raise FreezeError(
                "unexpected PubMed abstract status "
                f"at request {seq}: "
                f"{abstract_status}"
            )

        fallback.append({
            "wave_a_request_sequence":
                seq,

            "fallback_reason":
                "abstract_absent",

            "wave_a_request_identity_sha256":
                row[
                    "request_identity_sha256"
                ],

            "wave_a_adapter_evidence_sha256":
                sha256_file(
                    evidence_path
                ),

            "wave_a_terminal_body_sha256":
                body_sha,
        })

    fallback.sort(
        key=lambda row:
            row[
                "wave_a_request_sequence"
            ]
    )

    if (
        pubmed_adapter_status
        != Counter({
            "verified_success": 8536,
            "verified_not_found": 2,
            "recovered_verified_success": 1,
        })
    ):
        raise FreezeError(
            "PubMed adapter-state counts drift"
        )

    if (
        pubmed_abstract_status
        != Counter({
            "usable_abstract_pubmed": 8499,
            "abstract_absent": 38,
        })
    ):
        raise FreezeError(
            "PubMed abstract-state counts drift"
        )

    if len(
        fallback
    ) != 40:
        raise FreezeError(
            "Future Wave-B population != 40"
        )

    if (
        Counter(
            row[
                "fallback_reason"
            ]
            for row in fallback
        )
        != Counter({
            "abstract_absent": 38,
            "verified_not_found": 2,
        })
    ):
        raise FreezeError(
            "fallback reason counts drift"
        )

    # --------------------------------------------------------
    # Bind each fallback to exact frozen input record.
    # --------------------------------------------------------

    manifest_rows = []
    derivation_rows = []

    for wave_b_seq, item in enumerate(
        fallback,
        start=1,
    ):

        a_seq = item[
            "wave_a_request_sequence"
        ]

        a_row = (
            wave_a_by_seq[
                a_seq
            ]
        )

        index = int(
            a_row[
                "retrieval_record_index"
            ]
        )

        source = input_by_index[
            index
        ]

        if (
            source[
                "screening_entity_id"
            ]
            != a_row[
                "screening_entity_id"
            ]
        ):
            raise FreezeError(
                "input/Wave-A entity mismatch "
                f"at record {index}"
            )

        openalex_id = (
            source.get(
                "openalex_id",
                "",
            )
            or ""
        ).strip()

        doi = (
            source.get(
                "doi",
                "",
            )
            or ""
        ).strip()

        pmid = (
            source.get(
                "pmid",
                "",
            )
            or ""
        ).strip()

        frozen_route = (
            source.get(
                "openalex_route",
                "",
            )
            or ""
        ).strip()

        frozen_lookup = (
            source.get(
                "openalex_lookup_value",
                "",
            )
            or ""
        ).strip()

        if openalex_id:

            expected_route = (
                "exact_work_id"
            )

            identifier = openalex_id

            transport_route = (
                "work_by_openalex_id"
            )

            namespace = "openalex"

        elif doi:

            expected_route = (
                "exact_doi"
            )

            identifier = doi

            transport_route = (
                "work_by_doi"
            )

            namespace = "doi"

        else:

            if not pmid:
                raise FreezeError(
                    "Wave-B candidate lacks "
                    "OpenAlex fallback identifier"
                )

            expected_route = (
                "exact_pmid"
            )

            identifier = pmid

            transport_route = (
                "work_by_pmid"
            )

            namespace = "pmid"

        if (
            frozen_route
            != expected_route
            or frozen_lookup
            != identifier
        ):
            raise FreezeError(
                "frozen OpenAlex routing mismatch "
                f"at record {index}"
            )

        request = {
            "wave_id":
                WAVE_B_ID,

            "request_sequence":
                str(
                    wave_b_seq
                ),

            "retrieval_record_index":
                str(
                    index
                ),

            "screening_entity_id":
                source[
                    "screening_entity_id"
                ],

            "provider":
                "openalex",

            "frozen_route":
                frozen_route,

            "transport_route":
                transport_route,

            "identifier_namespace":
                namespace,

            "identifier":
                identifier,
        }

        request[
            "request_identity_sha256"
        ] = (
            guard.expected_request_identity(
                request
            )
        )

        manifest_rows.append(
            request
        )

        derivation_rows.append({
            "wave_b_request_sequence":
                str(
                    wave_b_seq
                ),

            "wave_a_request_sequence":
                str(
                    a_seq
                ),

            "retrieval_record_index":
                str(
                    index
                ),

            "screening_entity_id":
                source[
                    "screening_entity_id"
                ],

            "pmid":
                pmid,

            "fallback_reason":
                item[
                    "fallback_reason"
                ],

            "wave_a_request_identity_sha256":
                item[
                    "wave_a_request_identity_sha256"
                ],

            "wave_a_adapter_evidence_sha256":
                item[
                    "wave_a_adapter_evidence_sha256"
                ],

            "wave_a_terminal_body_sha256":
                item[
                    "wave_a_terminal_body_sha256"
                ],

            "openalex_route":
                frozen_route,

            "openalex_lookup_value":
                identifier,
        })

    if [
        int(
            row[
                "request_sequence"
            ]
        )
        for row in manifest_rows
    ] != list(
        range(
            1,
            41,
        )
    ):
        raise FreezeError(
            "Wave-B request sequence drift"
        )

    route_counts = Counter(
        row[
            "frozen_route"
        ]
        for row in manifest_rows
    )

    if route_counts != Counter({
        "exact_work_id": 31,
        "exact_doi": 8,
        "exact_pmid": 1,
    }):
        raise FreezeError(
            "Wave-B route counts drift"
        )

    if len({
        row[
            "request_identity_sha256"
        ]
        for row in manifest_rows
    }) != 40:
        raise FreezeError(
            "Wave-B request identities not unique"
        )

    if any(
        row[
            "wave_a_request_sequence"
        ]
        == str(
            SPECIAL_SEQ
        )
        for row in derivation_rows
    ):
        raise FreezeError(
            "request 10083 unexpectedly "
            "entered Wave B"
        )

    manifest_fields = [
        "wave_id",
        "request_sequence",
        "retrieval_record_index",
        "screening_entity_id",
        "provider",
        "frozen_route",
        "transport_route",
        "identifier_namespace",
        "identifier",
        "request_identity_sha256",
    ]

    derivation_fields = [
        "wave_b_request_sequence",
        "wave_a_request_sequence",
        "retrieval_record_index",
        "screening_entity_id",
        "pmid",
        "fallback_reason",
        "wave_a_request_identity_sha256",
        "wave_a_adapter_evidence_sha256",
        "wave_a_terminal_body_sha256",
        "openalex_route",
        "openalex_lookup_value",
    ]

    manifest_body = tsv_bytes(
        manifest_fields,
        manifest_rows,
    )

    derivation_body = tsv_bytes(
        derivation_fields,
        derivation_rows,
    )

    manifest_sha = sha256_bytes(
        manifest_body
    )

    derivation_sha = sha256_bytes(
        derivation_body
    )

    if (
        manifest_sha
        != EXPECTED_MANIFEST_SHA
    ):
        raise FreezeError(
            "Wave-B manifest does not "
            "match prior independent dry run"
        )

    if (
        derivation_sha
        != EXPECTED_DERIVATION_SHA
    ):
        raise FreezeError(
            "Wave-B derivation does not "
            "match prior independent dry run"
        )

    # --------------------------------------------------------
    # Freeze metadata.
    # --------------------------------------------------------

    recovery_bindings = {
        "recovery_evidence_sha256":
            sha256_file(
                recovery_evidence_path
            ),

        "recovery_terminal_sha256":
            sha256_file(
                recovery_terminal_path
            ),

        "recovery_completion_sha256":
            sha256_file(
                recovery_completion_path
            ),

        "selected_pubmed_record_sha256":
            sha256_file(
                selected_record_path
            ),
    }

    source_bindings = {
        str(path): sha256_file(
            path
        )
        for path in (
            INPUT,
            WAVE_A_MANIFEST,
            FUT / "manifest.json",
            FUT / "checksums.sha256",
            RETRIEVAL_COMPLETION,
            FUTURE_RETRIEVAL_DESIGN,
            FUTURE_RETRIEVAL_AMENDMENT,
            NORMALIZER_PATH,
            FUTURE_GUARD_PATH,
            FUTURE_CORE_PATH,
            ADAPTER_PATH,
            TRANSPORT_PATH,
        )
    }

    design = {
        "design_id":
            "PRE_REVIEW_TRIAGE_FUTURE_TEXT_WAVE_B_MANIFEST_V1",

        "schema_version":
            1,

        "status":
            "FROZEN_PRE_IMPLEMENTATION",

        "design_parent_commit":
            EXPECTED_PARENT,

        "purpose":
            (
                "Freeze the deterministic OpenAlex "
                "fallback request population derived "
                "from completed Future Wave A PubMed "
                "terminal outcomes."
            ),

        "candidate_population": {
            "rows": 40,

            "fallback_reason_counts": {
                "abstract_absent": 38,
                "verified_not_found": 2,
            },

            "openalex_route_counts": {
                "exact_work_id": 31,
                "exact_doi": 8,
                "exact_pmid": 1,
            },

            "wave_a_pubmed_requests":
                8539,

            "wave_a_pubmed_usable_abstract":
                8499,

            "request_10083_wave_b_candidate":
                False,
        },

        "eligibility_contract": {
            "eligible": [
                (
                    "Future Wave A PubMed terminal "
                    "outcome is verified_not_found"
                ),
                (
                    "Future Wave A PubMed terminal "
                    "outcome is verified_success and "
                    "the pinned normalizer returns "
                    "provider_identity_status=matched, "
                    "parser_status=ok, and "
                    "abstract_status=abstract_absent"
                ),
            ],

            "not_eligible": [
                "usable_abstract_pubmed",
                "provider identity mismatch",
                "parser failure",
                (
                    "retrieval failure or unresolved "
                    "transport fault"
                ),
                "unverifiable evidence",
            ],

            "scientific_exclusion_inference":
                False,
        },

        "routing_contract": {
            "provider":
                "openalex",

            "precedence": [
                "exact_work_id",
                "exact_doi",
                "exact_pmid",
            ],

            "transport_route_mapping": {
                "exact_work_id":
                    "work_by_openalex_id",

                "exact_doi":
                    "work_by_doi",

                "exact_pmid":
                    "work_by_pmid",
            },

            "actual_routes_in_manifest": [
                "exact_work_id",
                "exact_doi",
                "exact_pmid",
            ],
        },

        "request_identity_contract": {
            "fields": [
                "wave_id",
                "request_sequence",
                "retrieval_record_index",
                "screening_entity_id",
                "provider",
                "frozen_route",
                "transport_route",
                "identifier_namespace",
                "identifier",
            ],

            "implementation":
                (
                    "pre_review_triage_future_text_"
                    "wave_a_guard_v1."
                    "expected_request_identity"
                ),
        },

        "request_10083": {
            "canonical_fault_evidence_preserved":
                True,

            "recovery_used_for_terminal_normalization":
                True,

            "selected_pmid":
                "37878119",

            "normalized_abstract_status":
                "usable_abstract_pubmed",

            "wave_b_candidate":
                False,

            "network_reissued":
                False,

            "bindings":
                recovery_bindings,
        },

        "outputs": {
            "request_manifest": {
                "path":
                    str(
                        WAVE_B_MANIFEST
                    ),

                "rows":
                    40,

                "sha256":
                    manifest_sha,
            },

            "derivation_evidence": {
                "path":
                    str(
                        WAVE_B_DERIVATION
                    ),

                "rows":
                    40,

                "sha256":
                    derivation_sha,
            },
        },

        "source_bindings":
            source_bindings,

        "authority_boundary": {
            "authorization_created":
                False,

            "network_authorized":
                False,

            "wave_b_execution_permitted":
                False,

            "separate_human_authorization_required":
                True,

            "wave_a_archive_modification_permitted":
                False,

            "blind_validation_content_used":
                False,

            "future_scoring_performed":
                False,

            "model_fit_permitted":
                False,

            "threshold_selection_permitted":
                False,

            "scientific_screening_permitted":
                False,
        },

        "implementation_requirements": {
            "maximum_request_count":
                40,

            "allowed_routes": [
                "exact_work_id",
                "exact_doi",
                "exact_pmid",
            ],

            "exact_pmid_route_must_be_hostile_tested":
                True,

            "halt_on_unresolved_fault":
                True,

            "no_ad_hoc_probe":
                True,

            "no_search_or_list_endpoint":
                True,

            "raw_evidence_must_be_preserved":
                True,

            "authorization_must_be_separate":
                True,
        },

        "next_gate":
            (
                "IMPLEMENT_AND_HOSTILE_TEST_"
                "FUTURE_WAVE_B_EXECUTION_BEFORE_"
                "SEPARATE_HUMAN_AUTHORIZATION"
            ),
    }

    design_body = canonical_json_bytes(
        design
    )

    design_sha = sha256_bytes(
        design_body
    )

    doc_text = f"""# Pre-review triage future text Wave B manifest v1

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This freeze defines the deterministic Future Wave B OpenAlex fallback
population derived from the completed and frozen Future Wave A retrieval.

It does not authorize network access.

It does not create a Wave B execution authorization.

It does not perform reconciliation, future scoring, model fitting, threshold
selection, blind-validation scientific inspection, or scientific screening.

## Frozen candidate population

Exactly 40 Future Wave A PubMed records require OpenAlex fallback:

- 38 because the verified PubMed record normalized as `abstract_absent`;
- 2 because the exact PubMed route ended `verified_not_found`.

The OpenAlex routes are:

- 31 `exact_work_id`;
- 8 `exact_doi`;
- 1 `exact_pmid`.

The route precedence is:

`exact_work_id -> exact_doi -> exact_pmid`

## Request 10083

Request 10083 is not a Wave B candidate.

Its explicitly authorized no-network recovery selected PMID 37878119 from
the already archived PubMed response. The selected focal record reproduces
`usable_abstract_pubmed`, so the retrieval cascade terminates at Future
Wave A.

The original request-10083 canonical fault evidence remains preserved.

## Frozen outputs

Request manifest:

`{WAVE_B_MANIFEST}`

Rows: 40

SHA-256:

`{manifest_sha}`

Derivation evidence:

`{WAVE_B_DERIVATION}`

Rows: 40

SHA-256:

`{derivation_sha}`

No title text or abstract text is stored in either Wave B manifest artifact.

## Authority boundary

This freeze creates no network authority.

Future Wave B requires a separate explicit human authorization after the
execution guard, transport adapter, runner core and live entrypoint have been
implemented, hostile-tested and frozen.

The Future Wave A authorization cannot authorize Future Wave B.

## Implementation requirement

The future execution layer must support all three frozen exact OpenAlex
routes.

In particular, the manifest contains one `exact_pmid` request using
`work_by_pmid`. This route must be explicitly implemented and hostile-tested;
the historical development Wave B population did not exercise that route.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_FUTURE_WAVE_B_EXECUTION_BEFORE_SEPARATE_HUMAN_AUTHORIZATION`
"""

    doc_body = doc_text.encode(
        "utf-8"
    )

    doc_sha = sha256_bytes(
        doc_body
    )

    generator_sha = sha256_file(
        FREEZE_SCRIPT
    )

    checksum_rows = {
        str(
            FREEZE_SCRIPT
        ):
            generator_sha,

        str(
            DESIGN
        ):
            design_sha,

        str(
            DOC
        ):
            doc_sha,

        str(
            WAVE_B_MANIFEST
        ):
            manifest_sha,

        str(
            WAVE_B_DERIVATION
        ):
            derivation_sha,
    }

    for path, digest in (
        source_bindings.items()
    ):
        checksum_rows[
            path
        ] = digest

    for path in (
        recovery_evidence_path,
        recovery_terminal_path,
        recovery_completion_path,
        selected_record_path,
    ):
        checksum_rows[
            str(path)
        ] = sha256_file(
            path
        )

    checksum_body = "".join(
        digest
        + "  "
        + path
        + "\n"
        for path, digest
        in sorted(
            checksum_rows.items()
        )
    ).encode(
        "utf-8"
    )

    return {
        WAVE_B_MANIFEST:
            manifest_body,

        WAVE_B_DERIVATION:
            derivation_body,

        DESIGN:
            design_body,

        DOC:
            doc_body,

        CHECKSUMS:
            checksum_body,
    }, {
        "manifest_sha256":
            manifest_sha,

        "derivation_sha256":
            derivation_sha,

        "design_sha256":
            design_sha,

        "document_sha256":
            doc_sha,

        "generator_sha256":
            generator_sha,
    }


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--verify-only",
        action="store_true",
    )

    args = parser.parse_args()

    outputs, hashes = derive()

    if args.verify_only:

        for path, expected in (
            outputs.items()
        ):
            if not path.is_file():
                raise FreezeError(
                    f"missing frozen output: {path}"
                )

            actual = path.read_bytes()

            if actual != expected:
                raise FreezeError(
                    "frozen output byte mismatch: "
                    f"{path}"
                )

        print(
            "PASS | future Wave-B manifest "
            "freeze reproduces byte-identically"
        )

    else:

        for path in outputs:
            if path.exists():
                raise FreezeError(
                    f"refusing overwrite: {path}"
                )

        for path, body in (
            outputs.items()
        ):
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with path.open(
                "xb"
            ) as handle:
                handle.write(
                    body
                )

        print(
            "PASS | future Wave-B manifest "
            "freeze created"
        )

    print(
        "candidate_count = 40"
    )

    print(
        "fallback_reason_counts = "
        "{'abstract_absent': 38, "
        "'verified_not_found': 2}"
    )

    print(
        "openalex_route_counts = "
        "{'exact_doi': 8, "
        "'exact_pmid': 1, "
        "'exact_work_id': 31}"
    )

    print(
        "request_10083_wave_b_candidate = False"
    )

    for key in sorted(
        hashes
    ):
        print(
            key,
            "=",
            hashes[
                key
            ],
        )

    print(
        "NETWORK_AUTHORIZED=NO"
    )

    print(
        "WAVE_B_EXECUTION_PERMITTED=NO"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
