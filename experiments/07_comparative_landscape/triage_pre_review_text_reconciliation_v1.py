from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Iterable

import retrieve_metadata_resolution_queue as transport
import triage_pre_review_text_normalizer_v1 as normalizer
import triage_pre_review_text_wave_a_guard_v1 as wave_a_guard
import triage_pre_review_text_wave_a_transport_evidence_adapter_v1 as wave_a_adapter
import triage_pre_review_text_wave_b_guard_v1 as wave_b_guard
import triage_pre_review_text_wave_b_transport_evidence_adapter_v1 as wave_b_adapter


class ReconciliationError(RuntimeError):
    pass


REPO_ROOT = Path(
    subprocess.check_output(
        [
            "git",
            "rev-parse",
            "--show-toplevel",
        ],
        text=True,
    ).strip()
).resolve()

ROOT = (
    REPO_ROOT
    / "experiments/07_comparative_landscape"
)

RROOT = (
    REPO_ROOT
    / "results/07_comparative_landscape/"
      "triage_pre_review_text_retrieval_v1"
)

HROOT = (
    REPO_ROOT
    / "results/07_comparative_landscape/"
      "metadata_resolution_retrieval"
)

WAVE_A_ROOT = (
    RROOT
    / "live_wave_a"
)

WAVE_B_ROOT = (
    RROOT
    / "live_wave_b"
)

DESIGN_PATH = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1_design.json"
)

AMENDMENT_PATH = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1_amendment_001_design.json"
)

HISTORICAL_CHECKSUM_PATH = (
    HROOT
    / "checksums.sha256"
)

EXPECTED_DESIGN_COMMIT = (
    "1aa32f02387e4c5638b18b951bd5bc7a231c0b5f"
)

EXPECTED_AMENDMENT_COMMIT = (
    "53644804724a064acdc4a7b04870497091ed0c8f"
)

EXPECTED_HISTORICAL_CHECKSUM_SHA = (
    "f51080de3383cae1981e19c57687e4c8"
    "ea0e7f9832316a3936728a23995e8b86"
)

CANONICAL_CONFIRMATION = (
    "WRITE-FROZEN-RECONCILIATION-V1"
)

OUTPUT_FILENAMES = (
    "reconciled_resolution.tsv",
    "reconciled_normalized_text.tsv",
    "reconciliation_summary.json",
    "reconciliation_outputs.sha256",
)


def sha256_bytes(
    data: bytes,
) -> str:

    return hashlib.sha256(
        data
    ).hexdigest()


def sha256_file(
    path: Path,
) -> str:

    return sha256_bytes(
        path.read_bytes()
    )


def load_json(
    path: Path,
) -> dict:

    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception as exc:
        raise ReconciliationError(
            "Cannot parse JSON: "
            + str(path)
        ) from exc

    if not isinstance(
        value,
        dict,
    ):
        raise ReconciliationError(
            "Expected JSON object: "
            + str(path)
        )

    return value


def read_tsv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:

    try:
        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as handle:

            reader = csv.DictReader(
                handle,
                delimiter="\t",
            )

            rows = list(
                reader
            )

            header = list(
                reader.fieldnames
                or []
            )

    except Exception as exc:
        raise ReconciliationError(
            "Cannot read TSV: "
            + str(path)
        ) from exc

    return (
        header,
        rows,
    )


def git_is_ancestor(
    ancestor: str,
) -> bool:

    result = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            ancestor,
            "HEAD",
        ],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    return (
        result.returncode
        == 0
    )


def parse_checksum_manifest(
    path: Path,
) -> dict[str, str]:

    mapping: dict[str, str] = {}

    for number, line in enumerate(
        path.read_text(
            encoding="utf-8"
        ).splitlines(),
        start=1,
    ):

        if not line.strip():
            continue

        try:
            digest, relative = line.split(
                None,
                1,
            )
        except ValueError as exc:
            raise ReconciliationError(
                f"Malformed checksum line {number}"
            ) from exc

        relative = (
            relative.strip()
        )

        if (
            len(digest) != 64
            or any(
                character
                not in "0123456789abcdef"
                for character in digest
            )
        ):
            raise ReconciliationError(
                f"Invalid checksum digest at line {number}"
            )

        if not relative:
            raise ReconciliationError(
                f"Empty checksum path at line {number}"
            )

        if relative in mapping:
            raise ReconciliationError(
                "Duplicate checksum path: "
                + relative
            )

        mapping[
            relative
        ] = digest

    return mapping


def canonical_provider_id(
    provider: str,
    value: str,
) -> str:

    value = (
        value
        or ""
    ).strip()

    if provider == "pubmed":

        lower = value.lower()

        if lower.startswith(
            "https://pubmed.ncbi.nlm.nih.gov/"
        ):
            value = (
                value.rstrip("/")
                .rsplit(
                    "/",
                    1,
                )[-1]
            )

        elif lower.startswith(
            "pmid:"
        ):
            value = value[5:]

        return value.strip()

    if provider == "openalex":

        upper = value.upper()

        if upper.startswith(
            "HTTPS://OPENALEX.ORG/"
        ) or upper.startswith(
            "HTTP://OPENALEX.ORG/"
        ):
            value = value.rsplit(
                "/",
                1,
            )[-1]

        return value.strip().upper()

    raise ReconciliationError(
        "Unexpected provider: "
        + provider
    )


def assert_frozen_contract() -> dict:

    if not git_is_ancestor(
        EXPECTED_AMENDMENT_COMMIT
    ):
        raise ReconciliationError(
            "Current HEAD does not descend from "
            "the frozen reconciliation amendment"
        )

    design = load_json(
        DESIGN_PATH
    )

    amendment = load_json(
        AMENDMENT_PATH
    )

    if (
        design.get(
            "status"
        )
        != "FROZEN_PRE_IMPLEMENTATION"
    ):
        raise ReconciliationError(
            "Reconciliation design status changed"
        )

    if (
        design.get(
            "design_parent_commit"
        )
        != "c767211bec514e3b5396e202aa2a40ccfb1dc138"
    ):
        raise ReconciliationError(
            "Original design parent changed"
        )

    if (
        amendment.get(
            "status"
        )
        != "FROZEN_PRE_IMPLEMENTATION"
    ):
        raise ReconciliationError(
            "Amendment status changed"
        )

    if (
        amendment.get(
            "amends_design_commit"
        )
        != EXPECTED_DESIGN_COMMIT
    ):
        raise ReconciliationError(
            "Amendment design-commit binding changed"
        )

    dependency_hashes = (
        amendment.get(
            "dependency_hashes",
            {},
        )
    )

    if (
        dependency_hashes.get(
            "original_reconciliation_design_sha256"
        )
        != sha256_file(
            DESIGN_PATH
        )
    ):
        raise ReconciliationError(
            "Original reconciliation design SHA mismatch"
        )

    original_doc = (
        ROOT
        / "TRIAGE_PRE_REVIEW_TEXT_RECONCILIATION_V1.md"
    )

    if (
        dependency_hashes.get(
            "original_reconciliation_document_sha256"
        )
        != sha256_file(
            original_doc
        )
    ):
        raise ReconciliationError(
            "Original reconciliation document SHA mismatch"
        )

    if (
        sha256_file(
            HISTORICAL_CHECKSUM_PATH
        )
        != EXPECTED_HISTORICAL_CHECKSUM_SHA
    ):
        raise ReconciliationError(
            "Historical checksum manifest SHA mismatch"
        )

    historical = amendment[
        "historical_cache_dependency"
    ]

    if (
        historical[
            "checksum_manifest_sha256"
        ]
        != EXPECTED_HISTORICAL_CHECKSUM_SHA
    ):
        raise ReconciliationError(
            "Amendment historical SHA changed"
        )

    if (
        historical[
            "checksum_manifest_entry_count"
        ]
        != 8666
    ):
        raise ReconciliationError(
            "Historical checksum entry count changed"
        )

    if (
        historical[
            "selected_lookup_count"
        ]
        != 9
    ):
        raise ReconciliationError(
            "Selected historical lookup count changed"
        )

    expected = (
        design[
            "expected_reconciliation"
        ]
    )

    if (
        expected[
            "total_records"
        ]
        != 4499
        or expected[
            "usable_abstract_total"
        ]
        != 4190
        or expected[
            "abstract_absent_total"
        ]
        != 309
    ):
        raise ReconciliationError(
            "Frozen reconciliation counts changed"
        )

    # Revalidate every source file already frozen by the design.
    for path_text, expected_sha in sorted(
        design[
            "source_hashes"
        ].items()
    ):

        path = (
            REPO_ROOT
            / path_text
        )

        if not path.is_file():
            raise ReconciliationError(
                "Frozen source missing: "
                + path_text
            )

        if (
            sha256_file(
                path
            )
            != expected_sha
        ):
            raise ReconciliationError(
                "Frozen source SHA mismatch: "
                + path_text
            )

    return {
        "design":
            design,

        "amendment":
            amendment,
    }


def validate_historical_selected_dependency(
    contract: dict,
) -> dict[str, str]:

    amendment = contract[
        "amendment"
    ]

    checksum_map = (
        parse_checksum_manifest(
            HISTORICAL_CHECKSUM_PATH
        )
    )

    if len(
        checksum_map
    ) != 8666:
        raise ReconciliationError(
            "Historical checksum manifest cardinality changed"
        )

    selected = (
        amendment[
            "historical_cache_dependency"
        ][
            "selected_lookups"
        ]
    )

    for item in selected:

        logical = item[
            "logical_lookup_id"
        ]

        if not logical.startswith(
            "lookup:"
        ):
            raise ReconciliationError(
                "Invalid historical logical lookup ID"
            )

        token = logical.split(
            ":",
            1,
        )[1]

        prefix = (
            "raw/lookup_"
            + token
            + "/"
        )

        required = (
            prefix
            + "attempt_01/attempt.json",

            prefix
            + "attempt_01/hop_00_body.bin",

            prefix
            + "attempt_01/hop_00_response.json",

            prefix
            + "attempt_01/request.json",

            prefix
            + "terminal.json",
        )

        for relative in required:

            expected_sha = (
                checksum_map.get(
                    relative
                )
            )

            if expected_sha is None:
                raise ReconciliationError(
                    "Selected historical file is not "
                    "checksum-covered: "
                    + relative
                )

            path = (
                HROOT
                / relative
            )

            if not path.is_file():
                raise ReconciliationError(
                    "Selected historical file missing: "
                    + relative
                )

            if (
                sha256_file(
                    path
                )
                != expected_sha
            ):
                raise ReconciliationError(
                    "Selected historical file checksum mismatch: "
                    + relative
                )

        body_path = (
            HROOT
            / (
                prefix
                + "attempt_01/hop_00_body.bin"
            )
        )

        if (
            sha256_file(
                body_path
            )
            != item[
                "source_body_sha256"
            ]
        ):
            raise ReconciliationError(
                "Selected historical body SHA mismatch "
                f"for index {item['retrieval_record_index']}"
            )

    return checksum_map


def normalized_text_columns(
    contract: dict,
) -> list[str]:

    return list(
        contract[
            "design"
        ][
            "output_contract"
        ][
            "normalized_text"
        ][
            "columns"
        ]
    )


def resolution_columns(
    contract: dict,
) -> list[str]:

    return list(
        contract[
            "design"
        ][
            "output_contract"
        ][
            "resolution"
        ][
            "columns"
        ]
    )


def _normalizer_result_checks(
    *,
    result: dict,
    expected_body_sha: str,
) -> None:

    if not isinstance(
        result,
        dict,
    ):
        raise ReconciliationError(
            "Normalizer result is not an object"
        )

    if (
        result.get(
            "source_body_sha256"
        )
        != expected_body_sha
    ):
        raise ReconciliationError(
            "Normalizer source-body SHA mismatch"
        )

    if (
        result.get(
            "parser_status"
        )
        != "ok"
    ):
        raise ReconciliationError(
            "Normalizer parser status is not ok"
        )

    if result.get(
        "error",
        "",
    ):
        raise ReconciliationError(
            "Normalizer returned an error"
        )

    status = result.get(
        "abstract_status"
    )

    if status not in {
        "usable_abstract_pubmed",
        "usable_abstract_openalex",
        "abstract_absent",
    }:
        raise ReconciliationError(
            "Unexpected abstract status: "
            + repr(status)
        )

    for key in (
        "provider_record_id",
        "provider_identity_status",
    ):

        value = result.get(
            key
        )

        if (
            not isinstance(
                value,
                str,
            )
            or not value.strip()
        ):
            raise ReconciliationError(
                "Normalizer lacks "
                + key
            )


def _normalize_live_success(
    *,
    manifest_row: dict[str, str],
    evidence: dict,
    body: bytes,
) -> dict:

    provider = manifest_row[
        "provider"
    ]

    if provider == "pubmed":

        result = (
            normalizer.normalize_pubmed(
                body,
                manifest_row[
                    "identifier"
                ],
            )
        )

    elif provider == "openalex":

        result = (
            normalizer.normalize_openalex(
                body
            )
        )

    else:
        raise ReconciliationError(
            "Unexpected live provider: "
            + provider
        )

    _normalizer_result_checks(
        result=result,
        expected_body_sha=evidence[
            "terminal_body_sha256"
        ],
    )

    if (
        canonical_provider_id(
            provider,
            result[
                "provider_record_id"
            ],
        )
        != canonical_provider_id(
            provider,
            evidence[
                "provider_record_id"
            ],
        )
    ):
        raise ReconciliationError(
            "Normalizer/live-evidence provider "
            "record identity mismatch"
        )

    return result


def _verify_live_record(
    *,
    manifest_row: dict[str, str],
    sequence: int,
    execution_root: Path,
    adapter,
) -> tuple[
    dict,
    bytes | None,
]:

    transport_row = (
        adapter.manifest_to_transport_row(
            manifest_row
        )
    )

    lookup_root = (
        adapter.transport_lookup_root(
            execution_root,
            transport_row,
        )
    )

    durable = adapter.read_evidence(
        execution_root=execution_root,
        sequence=sequence,
    )

    reconstructed = (
        adapter.verified_evidence(
            manifest_row=manifest_row,
            archive_root=execution_root,
            transport_module=transport,
        )
    )

    if durable != reconstructed:
        raise ReconciliationError(
            f"Durable evidence does not reproduce "
            f"for request {sequence}"
        )

    if (
        durable.get(
            "request_sequence"
        )
        != sequence
    ):
        raise ReconciliationError(
            "Durable evidence sequence mismatch"
        )

    if (
        durable.get(
            "request_identity_sha256"
        )
        != manifest_row[
            "request_identity_sha256"
        ]
    ):
        raise ReconciliationError(
            "Durable evidence request identity mismatch"
        )

    terminal_path = (
        lookup_root
        / "terminal.json"
    )

    if (
        sha256_file(
            terminal_path
        )
        != durable[
            "transport_terminal_json_sha256"
        ]
    ):
        raise ReconciliationError(
            "Terminal JSON SHA mismatch"
        )

    terminal = load_json(
        terminal_path
    )

    adapter_status = durable.get(
        "adapter_status"
    )

    if adapter_status == "verified_not_found":

        if (
            durable.get(
                "checkpoint_eligible"
            )
            is not True
        ):
            raise ReconciliationError(
                "Verified not-found is not checkpoint eligible"
            )

        return (
            durable,
            None,
        )

    if adapter_status != "verified_success":
        raise ReconciliationError(
            "Unexpected adapter status: "
            + repr(
                adapter_status
            )
        )

    if (
        durable.get(
            "provider_identity_status"
        )
        != "matched"
    ):
        raise ReconciliationError(
            "Live provider identity is not matched"
        )

    body = (
        adapter.read_verified_final_body(
            lookup_root=lookup_root,
            terminal=terminal,
        )
    )

    if not isinstance(
        body,
        bytes,
    ):
        raise ReconciliationError(
            "Verified live body is not bytes"
        )

    if (
        sha256_bytes(
            body
        )
        != durable[
            "terminal_body_sha256"
        ]
    ):
        raise ReconciliationError(
            "Verified live body SHA mismatch"
        )

    return (
        durable,
        body,
    )


def _historical_normalized_record(
    *,
    offline_resolution_row: dict[str, str],
    selected_item: dict,
    checksum_map: dict[str, str],
    amendment: dict,
) -> dict:

    idx = int(
        offline_resolution_row[
            "retrieval_record_index"
        ]
    )

    if (
        offline_resolution_row[
            "chosen_logical_lookup_id"
        ]
        != selected_item[
            "logical_lookup_id"
        ]
    ):
        raise ReconciliationError(
            f"Historical logical lookup mismatch at {idx}"
        )

    if (
        offline_resolution_row[
            "chosen_source_body_sha256"
        ]
        != selected_item[
            "source_body_sha256"
        ]
    ):
        raise ReconciliationError(
            f"Historical selected body SHA mismatch at {idx}"
        )

    logical = selected_item[
        "logical_lookup_id"
    ]

    token = logical.split(
        ":",
        1,
    )[1]

    prefix = (
        "raw/lookup_"
        + token
        + "/"
    )

    required = (
        prefix
        + "attempt_01/attempt.json",

        prefix
        + "attempt_01/hop_00_body.bin",

        prefix
        + "attempt_01/hop_00_response.json",

        prefix
        + "attempt_01/request.json",

        prefix
        + "terminal.json",
    )

    for relative in required:

        path = (
            HROOT
            / relative
        )

        expected_sha = (
            checksum_map.get(
                relative
            )
        )

        if expected_sha is None:
            raise ReconciliationError(
                "Historical file not checksum-covered: "
                + relative
            )

        if (
            sha256_file(
                path
            )
            != expected_sha
        ):
            raise ReconciliationError(
                "Historical archive checksum mismatch: "
                + relative
            )

    lookup_root = (
        HROOT
        / (
            "raw/lookup_"
            + token
        )
    )

    terminal = (
        transport.verify_terminal_archive(
            lookup_root
        )
    )

    if (
        terminal.get(
            "terminal_status"
        )
        != "success"
    ):
        raise ReconciliationError(
            f"Historical terminal is not success at {idx}"
        )

    body = (
        lookup_root
        / "attempt_01"
        / "hop_00_body.bin"
    ).read_bytes()

    if (
        sha256_bytes(
            body
        )
        != selected_item[
            "source_body_sha256"
        ]
    ):
        raise ReconciliationError(
            f"Historical body SHA mismatch at {idx}"
        )

    result = (
        normalizer.normalize_openalex(
            body
        )
    )

    _normalizer_result_checks(
        result=result,
        expected_body_sha=selected_item[
            "source_body_sha256"
        ],
    )

    if (
        result[
            "abstract_status"
        ]
        != selected_item[
            "abstract_status"
        ]
    ):
        raise ReconciliationError(
            f"Historical abstract status mismatch at {idx}"
        )

    if (
        result[
            "abstract_status"
        ]
        == "abstract_absent"
    ):

        pinned = (
            amendment[
                "offline_cache_semantics"
            ][
                "abstract_absent_rows"
            ][
                "derived_provenance"
            ].get(
                str(idx)
            )
        )

        if pinned is None:
            raise ReconciliationError(
                f"Missing pinned absent provenance at {idx}"
            )

        if (
            result[
                "provider_record_id"
            ]
            != pinned[
                "provider_record_id"
            ]
        ):
            raise ReconciliationError(
                f"Pinned provider record mismatch at {idx}"
            )

        if (
            result[
                "provider_identity_status"
            ]
            != pinned[
                "provider_identity_status"
            ]
        ):
            raise ReconciliationError(
                f"Pinned provider identity status mismatch at {idx}"
            )

    return result


def _text_row(
    *,
    retrieval_record_index: str,
    screening_entity_id: str,
    provider_used: str,
    provider_lookup_type: str,
    normalized: dict,
    columns: list[str],
) -> dict[str, str]:

    row = {
        "retrieval_record_index":
            str(
                retrieval_record_index
            ),

        "screening_entity_id":
            screening_entity_id,

        "provider_used":
            provider_used,

        "provider_lookup_type":
            provider_lookup_type,

        "provider_record_id":
            normalized[
                "provider_record_id"
            ],

        "source_body_sha256":
            normalized[
                "source_body_sha256"
            ],

        "provider_identity_status":
            normalized[
                "provider_identity_status"
            ],

        "parser_status":
            normalized[
                "parser_status"
            ],

        "abstract_status":
            normalized[
                "abstract_status"
            ],

        "title_text":
            normalized.get(
                "title_text",
                "",
            )
            or "",

        "abstract_text":
            normalized.get(
                "abstract_text",
                "",
            )
            or "",

        "abstract_section_metadata_json":
            normalized.get(
                "abstract_section_metadata_json",
                "",
            )
            or "",
    }

    if (
        list(
            row
        )
        != columns
    ):
        raise ReconciliationError(
            "Normalized-text row schema mismatch"
        )

    if (
        row[
            "abstract_status"
        ]
        not in {
            "usable_abstract_pubmed",
            "usable_abstract_openalex",
        }
    ):
        raise ReconciliationError(
            "Non-usable row offered to normalized-text output"
        )

    if not row[
        "abstract_text"
    ].strip():
        raise ReconciliationError(
            "Usable abstract row has empty abstract text"
        )

    return row


def _resolution_row(
    *,
    retrieval_record_index: str,
    screening_entity_id: str,
    resolution_lane: str,
    provider_used: str,
    provider_lookup_type: str,
    normalized: dict,
    wave_a_request_sequence: str,
    wave_a_request_identity_sha256: str,
    wave_b_request_sequence: str,
    wave_b_request_identity_sha256: str,
    fallback_reason: str,
    normalized_text_present: bool,
    columns: list[str],
) -> dict[str, str]:

    row = {
        "retrieval_record_index":
            str(
                retrieval_record_index
            ),

        "screening_entity_id":
            screening_entity_id,

        "resolution_lane":
            resolution_lane,

        "provider_used":
            provider_used,

        "provider_lookup_type":
            provider_lookup_type,

        "provider_record_id":
            normalized[
                "provider_record_id"
            ],

        "source_body_sha256":
            normalized[
                "source_body_sha256"
            ],

        "provider_identity_status":
            normalized[
                "provider_identity_status"
            ],

        "parser_status":
            normalized[
                "parser_status"
            ],

        "abstract_status":
            normalized[
                "abstract_status"
            ],

        "wave_a_request_sequence":
            wave_a_request_sequence,

        "wave_a_request_identity_sha256":
            wave_a_request_identity_sha256,

        "wave_b_request_sequence":
            wave_b_request_sequence,

        "wave_b_request_identity_sha256":
            wave_b_request_identity_sha256,

        "fallback_reason":
            fallback_reason,

        "normalized_text_present":
            (
                "1"
                if normalized_text_present
                else "0"
            ),
    }

    if (
        list(
            row
        )
        != columns
    ):
        raise ReconciliationError(
            "Resolution row schema mismatch"
        )

    return row


def _record_counts(
    *,
    status_counts: Counter,
    source_counts: Counter,
    source_status_counts: dict[
        str,
        Counter,
    ],
    source_name: str,
    abstract_status: str,
) -> None:

    status_counts[
        abstract_status
    ] += 1

    source_counts[
        source_name
    ] += 1

    source_status_counts.setdefault(
        source_name,
        Counter(),
    )[
        abstract_status
    ] += 1


def build_reconciliation() -> dict:

    contract = (
        assert_frozen_contract()
    )

    design = contract[
        "design"
    ]

    amendment = contract[
        "amendment"
    ]

    checksum_map = (
        validate_historical_selected_dependency(
            contract
        )
    )

    resolution_header = (
        resolution_columns(
            contract
        )
    )

    text_header = (
        normalized_text_columns(
            contract
        )
    )

    input_header, input_rows = read_tsv(
        RROOT
        / "input_manifest.tsv"
    )

    _cache_header, cache_resolution = read_tsv(
        RROOT
        / "offline_cache_resolution.tsv"
    )

    cached_text_header, cached_text_rows = read_tsv(
        RROOT
        / "offline_cached_normalized_text.tsv"
    )

    _network_header, network_rows = read_tsv(
        RROOT
        / "offline_network_requirements.tsv"
    )

    _derivation_header, b_derivation = read_tsv(
        RROOT
        / "live_wave_b_derivation.tsv"
    )

    if len(
        input_rows
    ) != 4499:
        raise ReconciliationError(
            "Input manifest cardinality changed"
        )

    if len(
        cache_resolution
    ) != 4499:
        raise ReconciliationError(
            "Offline cache resolution cardinality changed"
        )

    if len(
        cached_text_rows
    ) != 3:
        raise ReconciliationError(
            "Cached normalized-text cardinality changed"
        )

    if len(
        network_rows
    ) != 4490:
        raise ReconciliationError(
            "Network-requirement cardinality changed"
        )

    if len(
        b_derivation
    ) != 25:
        raise ReconciliationError(
            "Wave B derivation cardinality changed"
        )

    if (
        cached_text_header
        != text_header
    ):
        raise ReconciliationError(
            "Existing cached normalized-text schema "
            "differs from reconciliation text schema"
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

    cache_by_index = {
        int(
            row[
                "retrieval_record_index"
            ]
        ):
            row
        for row in cache_resolution
    }

    network_indices = {
        int(
            row[
                "retrieval_record_index"
            ]
        )
        for row in network_rows
    }

    cached_text_by_index = {
        int(
            row[
                "retrieval_record_index"
            ]
        ):
            row
        for row in cached_text_rows
    }

    if len(
        input_by_index
    ) != 4499:
        raise ReconciliationError(
            "Input retrieval indices are not unique"
        )

    if len(
        cache_by_index
    ) != 4499:
        raise ReconciliationError(
            "Offline cache retrieval indices are not unique"
        )

    if len(
        network_indices
    ) != 4490:
        raise ReconciliationError(
            "Network retrieval indices are not unique"
        )

    offline_indices = (
        set(
            input_by_index
        )
        - network_indices
    )

    if len(
        offline_indices
    ) != 9:
        raise ReconciliationError(
            "Offline-only index count changed"
        )

    a_manifest = (
        wave_a_guard.read_manifest()
    )

    b_manifest = (
        wave_b_guard.read_manifest()
    )

    if len(
        a_manifest
    ) != 4490:
        raise ReconciliationError(
            "Wave A manifest cardinality changed"
        )

    if len(
        b_manifest
    ) != 25:
        raise ReconciliationError(
            "Wave B manifest cardinality changed"
        )

    if {
        int(
            row[
                "retrieval_record_index"
            ]
        )
        for row in a_manifest
    } != network_indices:
        raise ReconciliationError(
            "Wave A no longer exactly covers "
            "network-required indices"
        )

    b_by_sequence = {
        int(
            row[
                "request_sequence"
            ]
        ):
            row
        for row in b_manifest
    }

    if len(
        b_by_sequence
    ) != 25:
        raise ReconciliationError(
            "Wave B request sequences are not unique"
        )

    b_for_a: dict[int, int] = {}

    for row in b_derivation:

        a_sequence = int(
            row[
                "wave_a_request_sequence"
            ]
        )

        b_sequence = int(
            row[
                "wave_b_request_sequence"
            ]
        )

        if a_sequence in b_for_a:
            raise ReconciliationError(
                "Duplicate Wave A fallback mapping"
            )

        b_row = b_by_sequence.get(
            b_sequence
        )

        if b_row is None:
            raise ReconciliationError(
                "Wave B derivation references "
                "missing Wave B request"
            )

        if (
            row[
                "retrieval_record_index"
            ]
            != b_row[
                "retrieval_record_index"
            ]
            or row[
                "screening_entity_id"
            ]
            != b_row[
                "screening_entity_id"
            ]
        ):
            raise ReconciliationError(
                "Wave B derivation identity mismatch"
            )

        b_for_a[
            a_sequence
        ] = b_sequence

    if len(
        b_for_a
    ) != 25:
        raise ReconciliationError(
            "Wave B fallback mapping cardinality changed"
        )

    # --------------------------------------------------------
    # Reconstruct all Wave B terminal normalized records first.
    # --------------------------------------------------------

    b_results: dict[int, dict] = {}

    for sequence in range(
        1,
        26,
    ):

        row = b_by_sequence[
            sequence
        ]

        wave_b_guard.validate_manifest_row(
            row
        )

        if (
            wave_b_guard.expected_request_identity(
                row
            )
            != row[
                "request_identity_sha256"
            ]
        ):
            raise ReconciliationError(
                "Wave B request identity does not reproduce"
            )

        evidence, body = (
            _verify_live_record(
                manifest_row=row,
                sequence=sequence,
                execution_root=WAVE_B_ROOT,
                adapter=wave_b_adapter,
            )
        )

        if body is None:
            raise ReconciliationError(
                "Wave B contains unexpected not-found"
            )

        normalized = (
            _normalize_live_success(
                manifest_row=row,
                evidence=evidence,
                body=body,
            )
        )

        b_results[
            sequence
        ] = {
            "manifest_row":
                row,

            "evidence":
                evidence,

            "normalized":
                normalized,
        }

    b_status_counts = Counter(
        value[
            "normalized"
        ][
            "abstract_status"
        ]
        for value in b_results.values()
    )

    if (
        b_status_counts
        != Counter({
            "usable_abstract_openalex":
                8,
            "abstract_absent":
                17,
        })
    ):
        raise ReconciliationError(
            "Wave B normalized status counts changed"
        )

    # --------------------------------------------------------
    # Reconcile Wave A, invoking Wave B only at frozen slots.
    # --------------------------------------------------------

    resolution_rows: list[
        dict[str, str]
    ] = []

    text_rows: list[
        dict[str, str]
    ] = []

    status_counts = Counter()
    source_counts = Counter()
    source_status_counts: dict[
        str,
        Counter,
    ] = {}

    fallback_counts = Counter()
    actual_fallback_a_sequences: set[
        int
    ] = set()

    for sequence, row in enumerate(
        a_manifest,
        start=1,
    ):

        if (
            int(
                row[
                    "request_sequence"
                ]
            )
            != sequence
        ):
            raise ReconciliationError(
                "Wave A manifest order changed"
            )

        wave_a_guard.validate_manifest_row(
            row
        )

        if (
            wave_a_guard.expected_request_identity(
                row
            )
            != row[
                "request_identity_sha256"
            ]
        ):
            raise ReconciliationError(
                "Wave A request identity does not reproduce"
            )

        evidence, body = (
            _verify_live_record(
                manifest_row=row,
                sequence=sequence,
                execution_root=WAVE_A_ROOT,
                adapter=wave_a_adapter,
            )
        )

        provider = row[
            "provider"
        ]

        adapter_status = evidence[
            "adapter_status"
        ]

        final_normalized: dict
        final_provider: str
        final_lookup_type: str
        final_source: str
        resolution_lane: str
        fallback_reason = ""
        b_sequence_text = ""
        b_identity = ""

        if adapter_status == "verified_success":

            if body is None:
                raise ReconciliationError(
                    "Successful Wave A record lacks body"
                )

            primary_normalized = (
                _normalize_live_success(
                    manifest_row=row,
                    evidence=evidence,
                    body=body,
                )
            )

            primary_status = (
                primary_normalized[
                    "abstract_status"
                ]
            )

            if (
                provider == "pubmed"
                and primary_status
                == "abstract_absent"
            ):

                actual_fallback_a_sequences.add(
                    sequence
                )

                b_sequence = (
                    b_for_a.get(
                        sequence
                    )
                )

                if b_sequence is None:
                    raise ReconciliationError(
                        "PubMed abstract absence lacks "
                        "frozen Wave B fallback"
                    )

                fallback = (
                    b_results[
                        b_sequence
                    ]
                )

                b_row = fallback[
                    "manifest_row"
                ]

                final_normalized = (
                    fallback[
                        "normalized"
                    ]
                )

                final_provider = "openalex"

                final_lookup_type = (
                    b_row[
                        "frozen_route"
                    ]
                )

                final_source = (
                    "wave_b_openalex_after_"
                    "pubmed_abstract_absent"
                )

                resolution_lane = (
                    "wave_b_fallback"
                )

                fallback_reason = (
                    "pubmed_abstract_absent"
                )

                fallback_counts[
                    fallback_reason
                ] += 1

                b_sequence_text = str(
                    b_sequence
                )

                b_identity = (
                    b_row[
                        "request_identity_sha256"
                    ]
                )

            else:

                if sequence in b_for_a:
                    raise ReconciliationError(
                        "Wave A record has frozen fallback "
                        "but primary result terminates cascade"
                    )

                final_normalized = (
                    primary_normalized
                )

                final_provider = (
                    provider
                )

                final_lookup_type = (
                    row[
                        "frozen_route"
                    ]
                )

                resolution_lane = (
                    "wave_a_primary"
                )

                if provider == "pubmed":

                    if (
                        primary_status
                        != "usable_abstract_pubmed"
                    ):
                        raise ReconciliationError(
                            "Unexpected terminal PubMed status"
                        )

                    final_source = (
                        "wave_a_pubmed"
                    )

                elif provider == "openalex":

                    if primary_status not in {
                        "usable_abstract_openalex",
                        "abstract_absent",
                    }:
                        raise ReconciliationError(
                            "Unexpected direct OpenAlex status"
                        )

                    final_source = (
                        "wave_a_openalex"
                    )

                else:
                    raise ReconciliationError(
                        "Unexpected Wave A provider"
                    )

        elif adapter_status == "verified_not_found":

            if provider != "pubmed":
                raise ReconciliationError(
                    "Unexpected non-PubMed verified not-found"
                )

            actual_fallback_a_sequences.add(
                sequence
            )

            b_sequence = (
                b_for_a.get(
                    sequence
                )
            )

            if b_sequence is None:
                raise ReconciliationError(
                    "Verified PubMed not-found lacks "
                    "frozen Wave B fallback"
                )

            fallback = (
                b_results[
                    b_sequence
                ]
            )

            b_row = fallback[
                "manifest_row"
            ]

            final_normalized = (
                fallback[
                    "normalized"
                ]
            )

            final_provider = (
                "openalex"
            )

            final_lookup_type = (
                b_row[
                    "frozen_route"
                ]
            )

            final_source = (
                "wave_b_openalex_after_"
                "pubmed_verified_not_found"
            )

            resolution_lane = (
                "wave_b_fallback"
            )

            fallback_reason = (
                "pubmed_verified_not_found"
            )

            fallback_counts[
                fallback_reason
            ] += 1

            b_sequence_text = str(
                b_sequence
            )

            b_identity = (
                b_row[
                    "request_identity_sha256"
                ]
            )

        else:
            raise ReconciliationError(
                "Unexpected Wave A adapter status"
            )

        idx = row[
            "retrieval_record_index"
        ]

        entity = row[
            "screening_entity_id"
        ]

        usable = (
            final_normalized[
                "abstract_status"
            ]
            in {
                "usable_abstract_pubmed",
                "usable_abstract_openalex",
            }
        )

        resolution_rows.append(
            _resolution_row(
                retrieval_record_index=idx,
                screening_entity_id=entity,
                resolution_lane=resolution_lane,
                provider_used=final_provider,
                provider_lookup_type=final_lookup_type,
                normalized=final_normalized,
                wave_a_request_sequence=str(
                    sequence
                ),
                wave_a_request_identity_sha256=row[
                    "request_identity_sha256"
                ],
                wave_b_request_sequence=b_sequence_text,
                wave_b_request_identity_sha256=b_identity,
                fallback_reason=fallback_reason,
                normalized_text_present=usable,
                columns=resolution_header,
            )
        )

        if usable:

            text_rows.append(
                _text_row(
                    retrieval_record_index=idx,
                    screening_entity_id=entity,
                    provider_used=final_provider,
                    provider_lookup_type=final_lookup_type,
                    normalized=final_normalized,
                    columns=text_header,
                )
            )

        _record_counts(
            status_counts=status_counts,
            source_counts=source_counts,
            source_status_counts=source_status_counts,
            source_name=final_source,
            abstract_status=final_normalized[
                "abstract_status"
            ],
        )

    if (
        actual_fallback_a_sequences
        != set(
            b_for_a
        )
    ):
        raise ReconciliationError(
            "Observed Wave A fallback population differs "
            "from frozen Wave B derivation"
        )

    # --------------------------------------------------------
    # Reconcile the nine historical cache rows.
    # --------------------------------------------------------

    selected_by_index = {
        int(
            item[
                "retrieval_record_index"
            ]
        ):
            item
        for item in amendment[
            "historical_cache_dependency"
        ][
            "selected_lookups"
        ]
    }

    if (
        set(
            selected_by_index
        )
        != offline_indices
    ):
        raise ReconciliationError(
            "Amendment historical lookup set differs "
            "from nine offline-only records"
        )

    for idx in sorted(
        offline_indices
    ):

        input_row = (
            input_by_index[
                idx
            ]
        )

        cache_row = (
            cache_by_index[
                idx
            ]
        )

        if (
            cache_row[
                "screening_entity_id"
            ]
            != input_row[
                "screening_entity_id"
            ]
        ):
            raise ReconciliationError(
                f"Offline entity mismatch at index {idx}"
            )

        normalized = (
            _historical_normalized_record(
                offline_resolution_row=cache_row,
                selected_item=selected_by_index[
                    idx
                ],
                checksum_map=checksum_map,
                amendment=amendment,
            )
        )

        provider = (
            cache_row[
                "chosen_provider"
            ]
        )

        lookup_type = (
            cache_row[
                "chosen_lookup_type"
            ]
        )

        if provider != "openalex":
            raise ReconciliationError(
                "Frozen offline cache contains "
                "unexpected non-OpenAlex provider"
            )

        usable = (
            normalized[
                "abstract_status"
            ]
            == "usable_abstract_openalex"
        )

        expected_text_row = None

        if usable:

            expected_text_row = (
                _text_row(
                    retrieval_record_index=str(
                        idx
                    ),
                    screening_entity_id=input_row[
                        "screening_entity_id"
                    ],
                    provider_used=provider,
                    provider_lookup_type=lookup_type,
                    normalized=normalized,
                    columns=text_header,
                )
            )

            cached = (
                cached_text_by_index.get(
                    idx
                )
            )

            if cached is None:
                raise ReconciliationError(
                    f"Usable cached record missing "
                    f"normalized-text row at index {idx}"
                )

            # The three usable historical-cache rows predate the
            # current provider-provenance representation.  Their
            # scientific text and retrieval state must reproduce
            # exactly from the checksum-verified historical body, but
            # the already-frozen cached row itself remains authoritative
            # for provider_record_id and provider_identity_status.
            #
            # No other field is permitted to differ.
            allowed_historical_provenance_differences = {
                "provider_record_id",
                "provider_identity_status",
            }

            differing_fields = {
                key
                for key in text_header
                if (
                    cached[
                        key
                    ]
                    != expected_text_row[
                        key
                    ]
                )
            }

            unexpected_differences = (
                differing_fields
                - allowed_historical_provenance_differences
            )

            if unexpected_differences:
                raise ReconciliationError(
                    f"Existing usable cached normalized "
                    f"scientific/retrieval fields do not reproduce "
                    f"at index {idx}: "
                    f"{sorted(unexpected_differences)}"
                )

            if (
                not cached[
                    "provider_record_id"
                ].strip()
            ):
                raise ReconciliationError(
                    f"Existing usable cached provider_record_id "
                    f"is empty at index {idx}"
                )

            if (
                cached[
                    "provider_identity_status"
                ]
                != "matched_or_transport_validated"
            ):
                raise ReconciliationError(
                    f"Unexpected historical cached provider "
                    f"identity status at index {idx}"
                )

            # Preserve the exact previously frozen cached row.
            text_rows.append(
                dict(
                    cached
                )
            )

        else:

            if (
                normalized[
                    "abstract_status"
                ]
                != "abstract_absent"
            ):
                raise ReconciliationError(
                    f"Unexpected offline abstract state at {idx}"
                )

            if idx in cached_text_by_index:
                raise ReconciliationError(
                    f"Abstract-absent cached record unexpectedly "
                    f"has normalized-text row at index {idx}"
                )

        resolution_rows.append(
            _resolution_row(
                retrieval_record_index=str(
                    idx
                ),
                screening_entity_id=input_row[
                    "screening_entity_id"
                ],
                resolution_lane="offline_cache",
                provider_used=provider,
                provider_lookup_type=lookup_type,
                normalized=normalized,
                wave_a_request_sequence="",
                wave_a_request_identity_sha256="",
                wave_b_request_sequence="",
                wave_b_request_identity_sha256="",
                fallback_reason="",
                normalized_text_present=usable,
                columns=resolution_header,
            )
        )

        _record_counts(
            status_counts=status_counts,
            source_counts=source_counts,
            source_status_counts=source_status_counts,
            source_name="offline_cache_openalex",
            abstract_status=normalized[
                "abstract_status"
            ],
        )

    # --------------------------------------------------------
    # Global deterministic reconciliation assertions.
    # --------------------------------------------------------

    resolution_rows.sort(
        key=lambda row: int(
            row[
                "retrieval_record_index"
            ]
        )
    )

    text_rows.sort(
        key=lambda row: int(
            row[
                "retrieval_record_index"
            ]
        )
    )

    if len(
        resolution_rows
    ) != 4499:
        raise ReconciliationError(
            "Final resolution cardinality is not 4499"
        )

    if len(
        text_rows
    ) != 4190:
        raise ReconciliationError(
            "Final normalized-text cardinality is not 4190"
        )

    observed_indices = [
        int(
            row[
                "retrieval_record_index"
            ]
        )
        for row in resolution_rows
    ]

    if (
        observed_indices
        != sorted(
            input_by_index
        )
    ):
        raise ReconciliationError(
            "Resolution table does not exactly cover "
            "input manifest indices"
        )

    text_indices = {
        int(
            row[
                "retrieval_record_index"
            ]
        )
        for row in text_rows
    }

    if len(
        text_indices
    ) != 4190:
        raise ReconciliationError(
            "Normalized-text indices are not unique"
        )

    for row in resolution_rows:

        idx = int(
            row[
                "retrieval_record_index"
            ]
        )

        expected_present = (
            "1"
            if idx in text_indices
            else "0"
        )

        if (
            row[
                "normalized_text_present"
            ]
            != expected_present
        ):
            raise ReconciliationError(
                f"normalized_text_present mismatch at {idx}"
            )

        if (
            row[
                "abstract_status"
            ]
            == "abstract_absent"
            and idx in text_indices
        ):
            raise ReconciliationError(
                f"Abstract-absent record promoted to text at {idx}"
            )

    expected = (
        design[
            "expected_reconciliation"
        ]
    )

    if (
        dict(
            status_counts
        )
        != expected[
            "abstract_status_counts"
        ]
    ):
        raise ReconciliationError(
            "Final abstract-status counts differ "
            "from frozen design"
        )

    if (
        dict(
            source_counts
        )
        != expected[
            "terminal_source_counts"
        ]
    ):
        raise ReconciliationError(
            "Final terminal-source counts differ "
            "from frozen design"
        )

    observed_matrix = {
        source:
            dict(
                counts
            )
        for source, counts in (
            source_status_counts.items()
        )
    }

    if (
        observed_matrix
        != expected[
            "terminal_source_status_counts"
        ]
    ):
        raise ReconciliationError(
            "Final source/status matrix differs "
            "from frozen design"
        )

    if (
        dict(
            fallback_counts
        )
        != expected[
            "wave_b_fallback_reason_counts"
        ]
    ):
        raise ReconciliationError(
            "Final Wave B fallback counts differ "
            "from frozen design"
        )

    parser_or_gap_count = sum(
        1
        for row in resolution_rows
        if (
            row[
                "parser_status"
            ]
            != "ok"
            or row[
                "abstract_status"
            ]
            == "openalex_position_gap"
        )
    )

    if (
        parser_or_gap_count
        != expected[
            "parser_or_position_gap_count"
        ]
    ):
        raise ReconciliationError(
            "Parser/position-gap count differs "
            "from frozen design"
        )

    return {
        "contract":
            contract,

        "resolution_columns":
            resolution_header,

        "normalized_text_columns":
            text_header,

        "resolution_rows":
            resolution_rows,

        "normalized_text_rows":
            text_rows,

        "abstract_status_counts":
            dict(
                status_counts
            ),

        "terminal_source_counts":
            dict(
                source_counts
            ),

        "terminal_source_status_counts":
            observed_matrix,

        "fallback_reason_counts":
            dict(
                fallback_counts
            ),

        "parser_or_position_gap_count":
            parser_or_gap_count,
    }


def write_tsv(
    *,
    path: Path,
    columns: list[str],
    rows: Iterable[
        dict[str, str]
    ],
) -> None:

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                row
            )


def validate_output_destination(
    output_root: Path,
    *,
    canonical_confirmation: str | None,
) -> Path:

    output_root = (
        output_root.resolve()
    )

    if (
        output_root
        == RROOT.resolve()
        and canonical_confirmation
        != CANONICAL_CONFIRMATION
    ):
        raise ReconciliationError(
            "Canonical output requires exact confirmation"
        )

    for filename in OUTPUT_FILENAMES:

        path = (
            output_root
            / filename
        )

        if path.exists():
            raise ReconciliationError(
                "Refusing to overwrite reconciliation output: "
                + str(path)
            )

    return output_root


def build_source_hash_summary(
    contract: dict,
) -> dict[str, str]:

    source_hashes = dict(
        contract[
            "design"
        ][
            "source_hashes"
        ]
    )

    source_hashes.update({
        str(
            DESIGN_PATH.relative_to(
                REPO_ROOT
            )
        ):
            sha256_file(
                DESIGN_PATH
            ),

        str(
            AMENDMENT_PATH.relative_to(
                REPO_ROOT
            )
        ):
            sha256_file(
                AMENDMENT_PATH
            ),

        str(
            HISTORICAL_CHECKSUM_PATH.relative_to(
                REPO_ROOT
            )
        ):
            sha256_file(
                HISTORICAL_CHECKSUM_PATH
            ),
    })

    return dict(
        sorted(
            source_hashes.items()
        )
    )


def write_reconciliation(
    *,
    output_root: Path,
    canonical_confirmation: str | None = None,
) -> dict:

    output_root = (
        validate_output_destination(
            output_root,
            canonical_confirmation=canonical_confirmation,
        )
    )

    result = (
        build_reconciliation()
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    resolution_path = (
        output_root
        / "reconciled_resolution.tsv"
    )

    text_path = (
        output_root
        / "reconciled_normalized_text.tsv"
    )

    summary_path = (
        output_root
        / "reconciliation_summary.json"
    )

    checksum_path = (
        output_root
        / "reconciliation_outputs.sha256"
    )

    write_tsv(
        path=resolution_path,
        columns=result[
            "resolution_columns"
        ],
        rows=result[
            "resolution_rows"
        ],
    )

    write_tsv(
        path=text_path,
        columns=result[
            "normalized_text_columns"
        ],
        rows=result[
            "normalized_text_rows"
        ],
    )

    output_hashes = {
        "reconciled_resolution.tsv":
            sha256_file(
                resolution_path
            ),

        "reconciled_normalized_text.tsv":
            sha256_file(
                text_path
            ),
    }

    summary = {
        "schema_version":
            1,

        "design_name":
            "triage_pre_review_text_reconciliation_v1",

        "amendment":
            "triage_pre_review_text_reconciliation_v1_amendment_001",

        "source_hashes":
            build_source_hash_summary(
                result[
                    "contract"
                ]
            ),

        "output_hashes":
            output_hashes,

        "row_counts": {
            "resolution":
                len(
                    result[
                        "resolution_rows"
                    ]
                ),

            "normalized_text":
                len(
                    result[
                        "normalized_text_rows"
                    ]
                ),
        },

        "abstract_status_counts":
            result[
                "abstract_status_counts"
            ],

        "terminal_source_counts":
            result[
                "terminal_source_counts"
            ],

        "terminal_source_status_counts":
            result[
                "terminal_source_status_counts"
            ],

        "fallback_reason_counts":
            result[
                "fallback_reason_counts"
            ],

        "parser_or_position_gap_count":
            result[
                "parser_or_position_gap_count"
            ],

        "safety_boundaries": {
            "network_used":
                False,

            "production_ledger_modified":
                False,

            "raw_archive_modified":
                False,

            "scientific_decisions_made":
                False,

            "scientific_labels_added":
                False,

            "model_fit":
                False,

            "threshold_selected":
                False,

            "blind_validation_content_used":
                False,

            "abstract_absence_used_as_exclusion_evidence":
                False,
        },
    }

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    checksum_lines = []

    for path in (
        resolution_path,
        text_path,
        summary_path,
    ):

        checksum_lines.append(
            f"{sha256_file(path)}  {path.name}"
        )

    checksum_path.write_text(
        "\n".join(
            checksum_lines
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "resolution_path":
            resolution_path,

        "normalized_text_path":
            text_path,

        "summary_path":
            summary_path,

        "checksum_path":
            checksum_path,

        "resolution_sha256":
            sha256_file(
                resolution_path
            ),

        "normalized_text_sha256":
            sha256_file(
                text_path
            ),

        "summary_sha256":
            sha256_file(
                summary_path
            ),

        "checksum_manifest_sha256":
            sha256_file(
                checksum_path
            ),
    }


def dry_run() -> dict:

    result = (
        build_reconciliation()
    )

    return {
        "resolution_rows":
            len(
                result[
                    "resolution_rows"
                ]
            ),

        "normalized_text_rows":
            len(
                result[
                    "normalized_text_rows"
                ]
            ),

        "abstract_status_counts":
            result[
                "abstract_status_counts"
            ],

        "terminal_source_counts":
            result[
                "terminal_source_counts"
            ],

        "fallback_reason_counts":
            result[
                "fallback_reason_counts"
            ],
    }


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(
        required=True
    )

    group.add_argument(
        "--dry-run",
        action="store_true",
    )

    group.add_argument(
        "--output-root",
        type=Path,
    )

    parser.add_argument(
        "--confirm-canonical",
        default=None,
    )

    return parser.parse_args()


def main() -> int:

    args = parse_args()

    if args.dry_run:

        result = dry_run()

        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    written = write_reconciliation(
        output_root=args.output_root,
        canonical_confirmation=args.confirm_canonical,
    )

    print(
        json.dumps(
            {
                key:
                    str(value)
                if isinstance(
                    value,
                    Path,
                )
                else value
                for key, value
                in written.items()
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
