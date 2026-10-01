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
import pre_review_triage_future_text_wave_a_guard_v1 as wave_a_guard
import triage_pre_review_text_wave_a_transport_evidence_adapter_v1 as wave_a_adapter
import pre_review_triage_future_text_wave_b_guard_v1 as wave_b_guard
import pre_review_triage_future_text_wave_b_transport_evidence_adapter_v1 as wave_b_adapter


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
      "pre_review_triage_future_text_retrieval_v1"
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
    / "pre_review_triage_future_text_reconciliation_v1_design.json"
)

EXPECTED_DESIGN_SHA256 = (
    "95dd5938b9cbd4659a7f4d8fe98b4c63"
    "e8ced9c8c88efaa9e6b2656506b3395c"
)

EXPECTED_DESIGN_COMMIT = (
    "3047e7b1aef8d479bd988a8779890877d056a173"
)

HISTORICAL_CHECKSUM_PATH = (
    HROOT
    / "checksums.sha256"
)

EXPECTED_HISTORICAL_CHECKSUM_SHA256 = (
    "f51080de3383cae1981e19c57687e4c8"
    "ea0e7f9832316a3936728a23995e8b86"
)

OUTPUT_FILENAMES = (
    "reconciled_resolution.tsv",
    "reconciled_normalized_text.tsv",
    "reconciliation_summary.json",
    "reconciliation_outputs.sha256",
)

CANONICAL_CONFIRMATION = (
    "WRITE-FROZEN-RECONCILIATION-V1"
)

NORMALIZED_TEXT_COLUMNS = [
    "retrieval_record_index",
    "screening_entity_id",
    "provider_used",
    "provider_lookup_type",
    "provider_record_id",
    "source_body_sha256",
    "provider_identity_status",
    "parser_status",
    "abstract_status",
    "title_text",
    "abstract_text",
    "abstract_section_metadata_json",
]

RESOLUTION_COLUMNS = [
    "retrieval_record_index",
    "screening_entity_id",
    "resolution_lane",
    "provider_used",
    "provider_lookup_type",
    "provider_record_id",
    "source_body_sha256",
    "provider_identity_status",
    "parser_status",
    "abstract_status",
    "wave_a_request_sequence",
    "wave_a_request_identity_sha256",
    "wave_b_request_sequence",
    "wave_b_request_identity_sha256",
    "fallback_reason",
    "normalized_text_present",
]

EXTRA_FROZEN_HASHES = {
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_002_freeze.py":
        "de1ce2d32f3d9702e916b8a655ca47f197d91dac00cdc04324457449619aa780",

    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_002_design.json":
        "b9476bfacc80a4236a79e4c7238b238c8a029f103c54e91a2f04824f5e349717",

    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_TEXT_RECONCILIATION_V1_AMENDMENT_002.md":
        "421fa18292643881fe7c7b9b325cb13e87e59b6a177cfb6055bc0dd521a50d9d",

    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_002.sha256":
        "997b00e18eb249f6e5295cbba2def7dbb70217914df1bb1884a2ba5f6a43897f",

    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_001_freeze.py":
        "a47ed5b25555fbe3515220e6b76bb45de7dd85fe72c8ef16f21414e053f7df30",

    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_001_design.json":
        "538cf8fbe78129ddba34495dd489749f9a5bec2e4332cdabc243eec4a4a03309",

    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_TEXT_RECONCILIATION_V1_AMENDMENT_001.md":
        "34c4d9fd2dec6be77a86dd4c22a8fa3c5cf345d19d9349570c4d5d418c223427",

    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_001.sha256":
        "dde8e60ebd240bc2f0361dccd976fa2ca3ba9b4f621b35c0ee79f8c3e3cd7f2a",

    ROOT
    / "pre_review_triage_future_text_wave_a_guard_v1.py":
        "79300875f7620afde503f70b27a78449d11fcda35c23b11dc44d2fe538bcb28c",

    ROOT
    / "triage_pre_review_text_wave_a_transport_evidence_adapter_v1.py":
        "30a311626b3e99e6520601585b87df3b600991094d7724cd358b52159d902bac",

    RROOT
    / "offline_cache_resolution.tsv":
        "72ac4012dc1643b56a9d0f0fd089f3c78fd8d272aca8775447c85105c7a49ed0",

    RROOT
    / "offline_cached_normalized_text.tsv":
        "971cd9df8ea9e945922bbaca4f0747ae014fc20930efd9079dcd3d412cfb63ab",

    RROOT
    / "offline_network_requirements.tsv":
        "19d0c9ce7049c35e10cfbb9e56be8b0c012256d9329a39300f94f5584b8ed25f",

    RROOT
    / "offline_selected_cache_provenance.tsv":
        "0b053cfbdc189e1000a8307eb3a88cd6d7560ccae1bb55d033bbf6d549d77165",

    RROOT
    / "offline_cache_summary.json":
        "262498d1159f7dbe24f0daf200801034a134f50fdf17d4dae6cbcc570bc811e7",
}

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

def _normalizer_result_checks(
    *,
    result: dict,
    expected_body_sha: str,
    allow_openalex_position_gap: bool = False,
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

    allowed_statuses = {
        "usable_abstract_pubmed",
        "usable_abstract_openalex",
        "abstract_absent",
    }

    if allow_openalex_position_gap:
        allowed_statuses.add(
            "openalex_position_gap"
        )

    if status not in allowed_statuses:
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

        pubmed_identifier = (
            manifest_row[
                "identifier"
            ]
        )

        exact_request_10083_recovery = (
            str(
                manifest_row.get(
                    "request_sequence",
                    "",
                )
            )
            == "10083"
            and str(
                manifest_row.get(
                    "retrieval_record_index",
                    "",
                )
            )
            == "10094"
            and manifest_row.get(
                "screening_entity_id"
            )
            == (
                "publication_component:database:"
                "publication:doi:"
                "10.1007/s00285-023-02006-3"
            )
            and manifest_row.get(
                "identifier_namespace"
            )
            == "pmid"
            and manifest_row.get(
                "identifier"
            )
            == "37873002;37878119"
            and manifest_row.get(
                "request_identity_sha256"
            )
            == (
                "fc8dea356e2ab8cec741dc4e38f3feb7"
                "14915a2adaa52181000b45a89a990a13"
            )
            and evidence.get(
                "evidence_type"
            )
            == "MANIFEST_DEFECT_NO_NETWORK_RECOVERY"
            and evidence.get(
                "provider"
            )
            == "pubmed"
            and evidence.get(
                "provider_record_id"
            )
            == "37878119"
            and evidence.get(
                "request_sequence"
            )
            == 10083
            and evidence.get(
                "request_identity_sha256"
            )
            == (
                "fc8dea356e2ab8cec741dc4e38f3feb7"
                "14915a2adaa52181000b45a89a990a13"
            )
            and evidence.get(
                "network_reissued"
            )
            is False
            and evidence.get(
                "selected_record_body_sha256"
            )
            == (
                "7cffd5a4977e2b74058b3476e4d1d9bc"
                "5a85151d303f59acb8125c4f94e20e15"
            )
            and evidence.get(
                "terminal_body_sha256"
            )
            == (
                "7cffd5a4977e2b74058b3476e4d1d9bc"
                "5a85151d303f59acb8125c4f94e20e15"
            )
        )

        if exact_request_10083_recovery:
            pubmed_identifier = (
                "37878119"
            )

        result = (
            normalizer.normalize_pubmed(
                body,
                pubmed_identifier,
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

    allow_position_gap = False

    if (
        result.get(
            "abstract_status"
        )
        == "openalex_position_gap"
    ):

        exact_amendment_002_record = (
            provider == "openalex"
            and str(
                manifest_row.get(
                    "request_sequence",
                    "",
                )
            )
            == '9180'
            and str(
                manifest_row.get(
                    "retrieval_record_index",
                    "",
                )
            )
            == '9191'
            and manifest_row.get(
                "screening_entity_id"
            )
            == 'publication_component:citation:publication:doi:10.5897/ajb11.773'
            and manifest_row.get(
                "identifier_namespace"
            )
            == 'openalex'
            and manifest_row.get(
                "identifier"
            )
            == 'W2119850564'
            and manifest_row.get(
                "frozen_route"
            )
            == 'exact_work_id'
            and manifest_row.get(
                "request_identity_sha256"
            )
            == '0ce8b2384745cddbd10549afeb55642d781f067fd7d5c612b75006a1dd0bf1e2'
            and evidence.get(
                "terminal_body_sha256"
            )
            == '30228dfcd8815a4e8dfbbefc810d9033a579b2733cb7091c6314e514178943a1'
            and result.get(
                "source_body_sha256"
            )
            == '30228dfcd8815a4e8dfbbefc810d9033a579b2733cb7091c6314e514178943a1'
            and result.get(
                "provider_record_id"
            )
            == 'https://openalex.org/W2119850564'
            and evidence.get(
                "provider_identity_status"
            )
            == "matched"
            and result.get(
                "provider_identity_status"
            )
            == "transport_validated"
            and result.get(
                "parser_status"
            )
            == 'ok'
        )

        if not exact_amendment_002_record:
            raise ReconciliationError(
                "Unexpected OpenAlex position gap "
                "outside Amendment 002 exception"
            )

        allow_position_gap = True

    _normalizer_result_checks(
        result=result,
        expected_body_sha=evidence[
            "terminal_body_sha256"
        ],
        allow_openalex_position_gap=
            allow_position_gap,
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

    if allow_position_gap:
        result = dict(
            result
        )

        result[
            "provider_identity_status"
        ] = evidence[
            "provider_identity_status"
        ]

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


def git_is_ancestor(
    commit: str,
) -> bool:

    result = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            commit,
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

    result: dict[
        str,
        str,
    ] = {}

    for line_number, raw in enumerate(
        path.read_text(
            encoding="utf-8"
        ).splitlines(),
        start=1,
    ):

        if not raw.strip():
            continue

        parts = raw.split(
            maxsplit=1
        )

        if len(parts) != 2:
            raise ReconciliationError(
                f"Malformed checksum line {line_number}"
            )

        digest = parts[0]
        relative = (
            parts[1]
            .lstrip("*")
            .strip()
        )

        if (
            len(digest) != 64
            or any(
                ch not in "0123456789abcdef"
                for ch in digest
            )
        ):
            raise ReconciliationError(
                f"Invalid checksum digest at line {line_number}"
            )

        if relative in result:
            raise ReconciliationError(
                "Duplicate checksum path: "
                + relative
            )

        result[
            relative
        ] = digest

    return result


def canonical_provider_id(
    provider: str,
    value: str,
) -> str:

    text = (
        value
        or ""
    ).strip()

    if provider == "pubmed":

        lowered = text.lower()

        if lowered.startswith(
            "pmid:"
        ):
            text = text.split(
                ":",
                1,
            )[1]

        return text

    if provider == "openalex":

        lowered = (
            text.lower()
        )

        prefix = (
            "https://openalex.org/"
        )

        if lowered.startswith(
            prefix
        ):
            text = text[
                len(prefix):
            ]

        return text.upper()

    raise ReconciliationError(
        "Unexpected provider: "
        + provider
    )


def normalized_text_columns(
    contract=None,
) -> list[str]:

    return list(
        NORMALIZED_TEXT_COLUMNS
    )


def resolution_columns(
    contract=None,
) -> list[str]:

    return list(
        RESOLUTION_COLUMNS
    )


def assert_frozen_contract() -> dict:

    if not git_is_ancestor(
        EXPECTED_DESIGN_COMMIT
    ):
        raise ReconciliationError(
            "Current HEAD does not descend from "
            "the frozen future reconciliation design"
        )

    if (
        not DESIGN_PATH.is_file()
        or sha256_file(
            DESIGN_PATH
        )
        != EXPECTED_DESIGN_SHA256
    ):
        raise ReconciliationError(
            "Future reconciliation design SHA mismatch"
        )

    design = load_json(
        DESIGN_PATH
    )

    if (
        design.get(
            "status"
        )
        != "FROZEN_PRE_IMPLEMENTATION"
    ):
        raise ReconciliationError(
            "Future reconciliation design status changed"
        )

    if (
        design.get(
            "design_parent_commit"
        )
        != "1c9abbe08310cb5c914d549e6bf4c41df14befe4"
    ):
        raise ReconciliationError(
            "Future reconciliation design parent changed"
        )

    source_bindings = (
        design.get(
            "source_bindings",
            {},
        )
    )

    if not isinstance(
        source_bindings,
        dict,
    ):
        raise ReconciliationError(
            "Future source bindings are not an object"
        )

    for path_text, expected_sha in sorted(
        source_bindings.items()
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

    for path, expected_sha in sorted(
        EXTRA_FROZEN_HASHES.items(),
        key=lambda item:
            str(
                item[0]
            ),
    ):

        if (
            not path.is_file()
            or sha256_file(
                path
            )
            != expected_sha
        ):
            raise ReconciliationError(
                "Additional frozen source SHA mismatch: "
                + str(
                    path
                )
            )

    if (
        sha256_file(
            HISTORICAL_CHECKSUM_PATH
        )
        != EXPECTED_HISTORICAL_CHECKSUM_SHA256
    ):
        raise ReconciliationError(
            "Historical archive checksum manifest changed"
        )

    population = (
        design[
            "known_structural_population"
        ]
    )

    exact = {
        "future_input_rows":
            12162,

        "future_wave_a_request_rows":
            12147,

        "future_terminal_offline_rows":
            15,

        "future_wave_b_fallback_rows":
            40,
    }

    for key, expected in exact.items():

        if (
            population.get(
                key
            )
            != expected
        ):
            raise ReconciliationError(
                "Frozen structural count changed: "
                + key
            )

    if (
        population[
            "future_wave_b_fallback_reason_counts"
        ]
        != {
            "abstract_absent":
                38,

            "verified_not_found":
                2,
        }
    ):
        raise ReconciliationError(
            "Frozen Wave-B fallback reasons changed"
        )

    if (
        population[
            "future_wave_b_primary_provider_counts"
        ]
        != {
            "pubmed":
                40,
        }
    ):
        raise ReconciliationError(
            "Frozen Wave-B primary provider population changed"
        )

    if (
        design[
            "safety_boundaries"
        ][
            "production_write_permitted"
        ]
        is not False
    ):
        raise ReconciliationError(
            "Design unexpectedly permits production write"
        )

    return {
        "design":
            design,
    }


def _resolve_historical_path(
    value: str,
) -> Path:

    raw = Path(
        value
    )

    if raw.is_absolute():

        resolved = (
            raw.resolve()
        )

    elif str(
        raw
    ).startswith(
        "results/"
    ):

        resolved = (
            REPO_ROOT
            / raw
        ).resolve()

    else:

        resolved = (
            HROOT
            / raw
        ).resolve()

    try:
        resolved.relative_to(
            HROOT.resolve()
        )
    except ValueError as exc:
        raise ReconciliationError(
            "Historical selected path escapes archive root"
        ) from exc

    return resolved


def validate_historical_selected_dependency(
    contract: dict,
) -> tuple[
    dict[str, str],
    dict[int, dict[str, str]],
]:

    checksum_map = (
        parse_checksum_manifest(
            HISTORICAL_CHECKSUM_PATH
        )
    )

    if len(
        checksum_map
    ) != 8666:
        raise ReconciliationError(
            "Historical checksum entry count changed"
        )

    _header, selected_rows = (
        read_tsv(
            RROOT
            / "offline_selected_cache_provenance.tsv"
        )
    )

    if len(
        selected_rows
    ) != 15:
        raise ReconciliationError(
            "Future selected-cache provenance cardinality changed"
        )

    selected_by_index: dict[
        int,
        dict[str, str],
    ] = {}

    for row in selected_rows:

        idx = int(
            row[
                "retrieval_record_index"
            ]
        )

        if idx in selected_by_index:
            raise ReconciliationError(
                "Duplicate selected-cache retrieval index"
            )

        if (
            row[
                "provider"
            ]
            != "openalex"
        ):
            raise ReconciliationError(
                "Unexpected selected-cache provider"
            )

        for path_key, sha_key in (
            (
                "selected_terminal_path",
                "selected_terminal_sha256",
            ),
            (
                "selected_response_metadata_path",
                "selected_response_metadata_sha256",
            ),
            (
                "selected_body_path",
                "selected_body_sha256",
            ),
        ):

            path = (
                _resolve_historical_path(
                    row[
                        path_key
                    ]
                )
            )

            if not path.is_file():
                raise ReconciliationError(
                    "Selected historical file missing: "
                    + str(
                        path
                    )
                )

            actual = sha256_file(
                path
            )

            if (
                actual
                != row[
                    sha_key
                ]
            ):
                raise ReconciliationError(
                    "Selected historical provenance SHA mismatch: "
                    + str(
                        path
                    )
                )

            relative = (
                path.relative_to(
                    HROOT
                )
                .as_posix()
            )

            if (
                checksum_map.get(
                    relative
                )
                != actual
            ):
                raise ReconciliationError(
                    "Selected historical file not bound "
                    "by checksum manifest: "
                    + relative
                )

        if (
            row[
                "source_body_sha256"
            ]
            != row[
                "selected_body_sha256"
            ]
        ):
            raise ReconciliationError(
                "Selected historical body SHA fields disagree"
            )

        selected_by_index[
            idx
        ] = row

    return (
        checksum_map,
        selected_by_index,
    )


def _read_durable_evidence(
    *,
    execution_root: Path,
    sequence: int,
    adapter,
) -> tuple[
    dict,
    Path,
]:

    evidence_path_fn = getattr(
        adapter,
        "evidence_path",
        None,
    )

    if not callable(
        evidence_path_fn
    ):
        raise ReconciliationError(
            "Adapter lacks evidence_path"
        )

    evidence_path = (
        evidence_path_fn(
            execution_root,
            sequence,
        )
    )

    if not evidence_path.is_file():
        raise ReconciliationError(
            "Durable evidence file missing"
        )

    read_evidence = getattr(
        adapter,
        "read_evidence",
        None,
    )

    if callable(
        read_evidence
    ):

        durable = (
            read_evidence(
                execution_root=
                    execution_root,
                sequence=
                    sequence,
            )
        )

    else:

        read_evidence_path = getattr(
            adapter,
            "read_evidence_path",
            None,
        )

        if not callable(
            read_evidence_path
        ):
            raise ReconciliationError(
                "Adapter lacks durable evidence reader"
            )

        durable = (
            read_evidence_path(
                evidence_path
            )
        )

    return (
        durable,
        evidence_path,
    )



def _verify_wave_a_request_10083_recovery(
    *,
    manifest_row: dict[str, str],
) -> tuple[
    dict,
    bytes,
    str,
]:
    """
    Consume the already-frozen, explicitly authorised,
    no-network recovery for Future Wave-A request 10083.

    This is an exact-record exception. It does not weaken
    ordinary Wave-A transport verification.
    """

    import hashlib as _hashlib

    expected_identity = (
        "fc8dea356e2ab8cec741dc4e38f3feb7"
        "14915a2adaa52181000b45a89a990a13"
    )

    expected_selected_sha = (
        "7cffd5a4977e2b74058b3476e4d1d9bc"
        "5a85151d303f59acb8125c4f94e20e15"
    )

    expected_row = {
        "request_sequence":
            "10083",
        "retrieval_record_index":
            "10094",
        "screening_entity_id":
            (
                "publication_component:database:"
                "publication:doi:"
                "10.1007/s00285-023-02006-3"
            ),
        "provider":
            "pubmed",
        "frozen_route":
            "exact_pmid_efetch",
        "transport_route":
            "record_by_pmid",
        "identifier_namespace":
            "pmid",
        "identifier":
            "37873002;37878119",
        "request_identity_sha256":
            expected_identity,
    }

    for key, expected in (
        expected_row.items()
    ):
        observed = str(
            manifest_row.get(
                key,
                "",
            )
        )

        if observed != expected:
            raise ReconciliationError(
                "Request 10083 recovery manifest "
                f"identity mismatch for {key}: "
                f"{observed!r} != {expected!r}"
            )

    special_root = (
        WAVE_A_ROOT.parent
        / "manifest_defect_exceptions"
        / "FUTURE-WAVE-A-EXEC-20260930-01"
        / "request_10083"
    )

    expected_hashes = {
        "human_recovery_authorization.json":
            (
                "36405bbed57b8f3dbff1e57d6195b829"
                "52f16ed362ccd75889d5b1f3a2e5b94a"
            ),
        "recovery_completion.json":
            (
                "78d9627301c343b4833f734275750872a"
                "e7e3d4593fe65730d2bfa383a584f54"
            ),
        "recovery_evidence.json":
            (
                "487fc11994dceb62b169180f291e0d18"
                "a93cb23b5ecb2937871f3fdccf27d496"
            ),
        "recovery_terminal.json":
            (
                "a85c9ef24394a17206a0db9476c806a6"
                "89554872210464e66f9d6706faff3997"
            ),
        "selected_pubmed_record_37878119.xml":
            expected_selected_sha,
    }

    payloads = {}

    for name, expected_sha in (
        expected_hashes.items()
    ):
        path = (
            special_root
            / name
        )

        if not path.is_file():
            raise ReconciliationError(
                "Request 10083 frozen recovery "
                f"artifact missing: {path}"
            )

        payload = path.read_bytes()

        observed_sha = (
            _hashlib.sha256(
                payload
            ).hexdigest()
        )

        if observed_sha != expected_sha:
            raise ReconciliationError(
                "Request 10083 frozen recovery "
                f"hash mismatch for {name}"
            )

        payloads[
            name
        ] = payload

    authorization = json.loads(
        payloads[
            "human_recovery_authorization.json"
        ].decode(
            "utf-8"
        )
    )

    recovery_completion = json.loads(
        payloads[
            "recovery_completion.json"
        ].decode(
            "utf-8"
        )
    )

    recovery_evidence = json.loads(
        payloads[
            "recovery_evidence.json"
        ].decode(
            "utf-8"
        )
    )

    recovery_terminal = json.loads(
        payloads[
            "recovery_terminal.json"
        ].decode(
            "utf-8"
        )
    )

    selected_body = payloads[
        "selected_pubmed_record_37878119.xml"
    ]

    if (
        authorization.get(
            "status"
        )
        != "AUTHORIZED"
        or authorization.get(
            "authorization_type"
        )
        != (
            "HUMAN_ONE_TIME_NO_NETWORK_"
            "MANIFEST_DEFECT_RECOVERY"
        )
        or authorization.get(
            "request_sequence"
        )
        != 10083
        or authorization.get(
            "retrieval_record_index"
        )
        != 10094
        or authorization.get(
            "request_identity_sha256"
        )
        != expected_identity
        or authorization.get(
            "selected_provider_record_id"
        )
        != "37878119"
        or authorization.get(
            "target_doi"
        )
        != "10.1007/s00285-023-02006-3"
        or authorization.get(
            "network_request_performed"
        )
        is not False
        or authorization.get(
            "network_request_permitted"
        )
        is not False
        or authorization.get(
            "frozen_manifest_modified"
        )
        is not False
        or authorization.get(
            "original_raw_modified"
        )
        is not False
    ):
        raise ReconciliationError(
            "Request 10083 recovery "
            "authorization semantics changed"
        )

    if (
        recovery_completion.get(
            "status"
        )
        != "CONSUMED"
        or recovery_completion.get(
            "network_reissued"
        )
        is not False
        or recovery_completion.get(
            "request_sequence"
        )
        != 10083
        or recovery_completion.get(
            "request_identity_sha256"
        )
        != expected_identity
        or recovery_completion.get(
            "selected_provider_record_id"
        )
        != "37878119"
        or recovery_completion.get(
            "target_doi"
        )
        != "10.1007/s00285-023-02006-3"
    ):
        raise ReconciliationError(
            "Request 10083 recovery "
            "completion semantics changed"
        )

    if (
        recovery_evidence.get(
            "evidence_type"
        )
        != "MANIFEST_DEFECT_NO_NETWORK_RECOVERY"
        or recovery_evidence.get(
            "checkpoint_eligible"
        )
        is not True
        or recovery_evidence.get(
            "network_reissued"
        )
        is not False
        or recovery_evidence.get(
            "canonical_fault_evidence_preserved"
        )
        is not True
        or recovery_evidence.get(
            "canonical_raw_archive_preserved"
        )
        is not True
        or recovery_evidence.get(
            "provider"
        )
        != "pubmed"
        or recovery_evidence.get(
            "provider_record_id"
        )
        != "37878119"
        or recovery_evidence.get(
            "request_sequence"
        )
        != 10083
        or recovery_evidence.get(
            "request_identity_sha256"
        )
        != expected_identity
        or recovery_evidence.get(
            "selected_record_body_sha256"
        )
        != expected_selected_sha
        or recovery_evidence.get(
            "target_doi"
        )
        != "10.1007/s00285-023-02006-3"
        or recovery_evidence.get(
            "transport_route"
        )
        != "record_by_pmid"
    ):
        raise ReconciliationError(
            "Request 10083 recovery "
            "evidence semantics changed"
        )

    if (
        recovery_terminal.get(
            "terminal_status"
        )
        != "success"
        or recovery_terminal.get(
            "terminal_type"
        )
        != "MANIFEST_DEFECT_NO_NETWORK_RECOVERY"
        or recovery_terminal.get(
            "network_reissued"
        )
        is not False
        or recovery_terminal.get(
            "provider"
        )
        != "pubmed"
        or recovery_terminal.get(
            "provider_record_id"
        )
        != "37878119"
        or recovery_terminal.get(
            "request_sequence"
        )
        != 10083
        or recovery_terminal.get(
            "request_identity_sha256"
        )
        != expected_identity
        or recovery_terminal.get(
            "selected_record_body_sha256"
        )
        != expected_selected_sha
        or recovery_terminal.get(
            "target_doi"
        )
        != "10.1007/s00285-023-02006-3"
    ):
        raise ReconciliationError(
            "Request 10083 recovery "
            "terminal semantics changed"
        )

    reproduced = (
        normalizer.normalize_pubmed(
            selected_body,
            "37878119",
        )
    )

    if (
        reproduced.get(
            "provider_identity_status"
        )
        != "matched"
        or reproduced.get(
            "parser_status"
        )
        != "ok"
        or reproduced.get(
            "abstract_status"
        )
        != "usable_abstract_pubmed"
        or reproduced.get(
            "provider_record_id"
        )
        != "37878119"
        or reproduced.get(
            "source_body_sha256"
        )
        != expected_selected_sha
    ):
        raise ReconciliationError(
            "Request 10083 frozen recovery "
            "no longer reproduces usable PubMed text"
        )

    # Present the recovered record to the existing reconciliation
    # machinery as a verified successful Wave-A result. Preserve
    # all original recovery metadata while adding only the fields
    # expected by the ordinary normalization contract.
    evidence = dict(
        recovery_evidence
    )

    evidence[
        "adapter_status"
    ] = "verified_success"

    evidence[
        "terminal_body_sha256"
    ] = expected_selected_sha

    evidence[
        "transport_terminal_status"
    ] = "success"

    return (
        evidence,
        selected_body,
        expected_hashes[
            "recovery_evidence.json"
        ],
    )


def _verify_live_record(
    *,
    manifest_row: dict[str, str],
    sequence: int,
    execution_root: Path,
    adapter,
) -> tuple[
    dict,
    bytes | None,
    str,
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

    durable, evidence_path = (
        _read_durable_evidence(
            execution_root=
                execution_root,
            sequence=
                sequence,
            adapter=
                adapter,
        )
    )

    reconstructed = (
        adapter.verified_evidence(
            manifest_row=
                manifest_row,
            archive_root=
                execution_root,
            transport_module=
                transport,
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

    if (
        durable.get(
            "checkpoint_eligible"
        )
        is not True
    ):
        raise ReconciliationError(
            "Durable evidence is not checkpoint eligible"
        )

    terminal_path = (
        lookup_root
        / "terminal.json"
    )

    if (
        not terminal_path.is_file()
        or sha256_file(
            terminal_path
        )
        != durable[
            "transport_terminal_json_sha256"
        ]
    ):
        raise ReconciliationError(
            "Terminal JSON SHA mismatch"
        )

    terminal = (
        transport.verify_terminal_archive(
            lookup_root
        )
    )

    adapter_status = (
        durable.get(
            "adapter_status"
        )
    )

    evidence_sha = (
        sha256_file(
            evidence_path
        )
    )

    if (
        adapter_status
        == "verified_not_found"
    ):

        return (
            durable,
            None,
            evidence_sha,
        )

    if (
        adapter_status
        != "verified_success"
    ):
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
        not in {
            "matched",
            "matched_via_verified_openalex_redirect",
        }
    ):
        raise ReconciliationError(
            "Live provider identity is not verified"
        )

    body_reader = getattr(
        adapter,
        "read_verified_final_body",
        None,
    )

    if not callable(
        body_reader
    ):
        raise ReconciliationError(
            "Adapter lacks verified final-body reader"
        )

    body = (
        body_reader(
            lookup_root=
                lookup_root,
            terminal=
                terminal,
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
        evidence_sha,
    )


def _offline_normalized_record(
    *,
    offline_resolution_row: dict[str, str],
    selected_item: dict[str, str],
) -> dict:

    idx = int(
        offline_resolution_row[
            "retrieval_record_index"
        ]
    )

    if (
        offline_resolution_row[
            "screening_entity_id"
        ]
        != selected_item[
            "screening_entity_id"
        ]
    ):
        raise ReconciliationError(
            f"Offline selected entity mismatch at {idx}"
        )

    if (
        offline_resolution_row[
            "chosen_provider"
        ]
        != "openalex"
        or selected_item[
            "provider"
        ]
        != "openalex"
    ):
        raise ReconciliationError(
            f"Unexpected offline provider at {idx}"
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
            f"Offline logical lookup mismatch at {idx}"
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
            f"Offline body SHA mismatch at {idx}"
        )

    terminal_path = (
        _resolve_historical_path(
            selected_item[
                "selected_terminal_path"
            ]
        )
    )

    body_path = (
        _resolve_historical_path(
            selected_item[
                "selected_body_path"
            ]
        )
    )

    terminal = (
        transport.verify_terminal_archive(
            terminal_path.parent
        )
    )

    if (
        terminal.get(
            "terminal_status"
        )
        != "success"
    ):
        raise ReconciliationError(
            f"Historical terminal not success at {idx}"
        )

    body = (
        body_path.read_bytes()
    )

    if (
        sha256_bytes(
            body
        )
        != selected_item[
            "source_body_sha256"
        ]
    ):
        raise ReconciliationError(
            f"Historical body changed at {idx}"
        )

    result = (
        normalizer.normalize_openalex(
            body
        )
    )

    _normalizer_result_checks(
        result=
            result,
        expected_body_sha=
            selected_item[
                "source_body_sha256"
            ],
    )

    if (
        result[
            "abstract_status"
        ]
        != offline_resolution_row[
            "abstract_status"
        ]
    ):
        raise ReconciliationError(
            f"Historical abstract status mismatch at {idx}"
        )

    return result


def build_reconciliation() -> dict:

    contract = (
        assert_frozen_contract()
    )

    resolution_header = (
        resolution_columns()
    )

    text_header = (
        normalized_text_columns()
    )

    input_header, input_rows = (
        read_tsv(
            RROOT
            / "input_manifest.tsv"
        )
    )

    _cache_header, cache_resolution = (
        read_tsv(
            RROOT
            / "offline_cache_resolution.tsv"
        )
    )

    cached_text_header, cached_text_rows = (
        read_tsv(
            RROOT
            / "offline_cached_normalized_text.tsv"
        )
    )

    _network_header, network_rows = (
        read_tsv(
            RROOT
            / "offline_network_requirements.tsv"
        )
    )

    _derivation_header, b_derivation = (
        read_tsv(
            RROOT
            / "live_wave_b_derivation.tsv"
        )
    )

    if len(
        input_rows
    ) != 12162:
        raise ReconciliationError(
            "Input manifest cardinality changed"
        )

    if len(
        cache_resolution
    ) != 12162:
        raise ReconciliationError(
            "Offline cache resolution cardinality changed"
        )

    if len(
        cached_text_rows
    ) != 14:
        raise ReconciliationError(
            "Cached normalized-text cardinality changed"
        )

    if len(
        network_rows
    ) != 12147:
        raise ReconciliationError(
            "Network-requirement cardinality changed"
        )

    if len(
        b_derivation
    ) != 40:
        raise ReconciliationError(
            "Wave-B derivation cardinality changed"
        )

    if (
        cached_text_header
        != text_header
    ):
        raise ReconciliationError(
            "Frozen cached normalized-text schema changed"
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
    ) != 12162:
        raise ReconciliationError(
            "Input retrieval indices are not unique"
        )

    if len(
        cache_by_index
    ) != 12162:
        raise ReconciliationError(
            "Offline cache retrieval indices are not unique"
        )

    if len(
        network_indices
    ) != 12147:
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
    ) != 15:
        raise ReconciliationError(
            "Offline-only population is not 15"
        )

    a_manifest = (
        wave_a_guard.read_manifest()
    )

    b_manifest = (
        wave_b_guard.read_manifest()
    )

    if len(
        a_manifest
    ) != 12147:
        raise ReconciliationError(
            "Future Wave-A manifest cardinality changed"
        )

    if len(
        b_manifest
    ) != 40:
        raise ReconciliationError(
            "Future Wave-B manifest cardinality changed"
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
            "Future Wave A no longer exactly covers "
            "network-required records"
        )

    a_by_sequence = {}

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
                "Future Wave-A ordering changed"
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
                "Future Wave-A request identity "
                "does not reproduce"
            )

        a_by_sequence[
            sequence
        ] = row

    b_by_sequence = {}

    for sequence, row in enumerate(
        b_manifest,
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
                "Future Wave-B ordering changed"
            )

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
                "Future Wave-B request identity "
                "does not reproduce"
            )

        b_by_sequence[
            sequence
        ] = row

    b_for_a: dict[
        int,
        int,
    ] = {}

    derivation_by_a = {}

    fallback_source_reason_counts = Counter()

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

        if (
            a_sequence
            in b_for_a
        ):
            raise ReconciliationError(
                "Duplicate Wave-A fallback mapping"
            )

        a_row = (
            a_by_sequence.get(
                a_sequence
            )
        )

        b_row = (
            b_by_sequence.get(
                b_sequence
            )
        )

        if (
            a_row is None
            or b_row is None
        ):
            raise ReconciliationError(
                "Wave-B derivation references "
                "missing frozen request"
            )

        if (
            row[
                "retrieval_record_index"
            ]
            != a_row[
                "retrieval_record_index"
            ]
            or row[
                "screening_entity_id"
            ]
            != a_row[
                "screening_entity_id"
            ]
            or row[
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
                "Wave-B derivation identity mismatch"
            )

        if (
            row[
                "wave_a_request_identity_sha256"
            ]
            != a_row[
                "request_identity_sha256"
            ]
        ):
            raise ReconciliationError(
                "Wave-B derivation Wave-A request SHA mismatch"
            )

        reason = (
            row[
                "fallback_reason"
            ]
        )

        if reason not in {
            "abstract_absent",
            "verified_not_found",
        }:
            raise ReconciliationError(
                "Unexpected frozen fallback reason"
            )

        fallback_source_reason_counts[
            reason
        ] += 1

        b_for_a[
            a_sequence
        ] = b_sequence

        derivation_by_a[
            a_sequence
        ] = row

    if len(
        b_for_a
    ) != 40:
        raise ReconciliationError(
            "Future Wave-B fallback mapping "
            "cardinality changed"
        )

    if (
        fallback_source_reason_counts
        != Counter({
            "abstract_absent":
                38,

            "verified_not_found":
                2,
        })
    ):
        raise ReconciliationError(
            "Future Wave-B source fallback reasons changed"
        )

    # Reconstruct and normalize all Future Wave-B records first.
    b_results = {}

    for sequence in range(
        1,
        41,
    ):

        row = (
            b_by_sequence[
                sequence
            ]
        )

        evidence, body, evidence_sha = (
            _verify_live_record(
                manifest_row=
                    row,
                sequence=
                    sequence,
                execution_root=
                    WAVE_B_ROOT,
                adapter=
                    wave_b_adapter,
            )
        )

        if body is None:
            raise ReconciliationError(
                "Future Wave-B unexpectedly lacks body"
            )

        normalized = (
            _normalize_live_success(
                manifest_row=
                    row,
                evidence=
                    evidence,
                body=
                    body,
            )
        )

        if (
            normalized[
                "abstract_status"
            ]
            not in {
                "usable_abstract_openalex",
                "abstract_absent",
            }
        ):
            raise ReconciliationError(
                "Unexpected Future Wave-B normalized state"
            )

        b_results[
            sequence
        ] = {
            "manifest_row":
                row,

            "evidence":
                evidence,

            "evidence_sha256":
                evidence_sha,

            "normalized":
                normalized,
        }

    wave_b_normalized_status_counts = (
        Counter(
            value[
                "normalized"
            ][
                "abstract_status"
            ]
            for value in (
                b_results.values()
            )
        )
    )

    resolution_rows = []
    text_rows = []

    status_counts = Counter()
    source_counts = Counter()
    source_status_counts = {}
    fallback_counts = Counter()

    actual_fallback_a_sequences = set()

    for sequence in range(
        1,
        12148,
    ):

        row = (
            a_by_sequence[
                sequence
            ]
        )

        if sequence == 10083:
            evidence, body, evidence_sha = (
                _verify_wave_a_request_10083_recovery(
                    manifest_row=
                        row,
                )
            )
        else:
            evidence, body, evidence_sha = (
                _verify_live_record(
                    manifest_row=
                        row,
                    sequence=
                        sequence,
                    execution_root=
                        WAVE_A_ROOT,
                    adapter=
                        wave_a_adapter,
                )
            )

        provider = (
            row[
                "provider"
            ]
        )

        adapter_status = (
            evidence[
                "adapter_status"
            ]
        )

        final_normalized = None
        final_provider = ""
        final_lookup_type = ""
        final_source = ""
        resolution_lane = ""
        fallback_reason = ""
        b_sequence_text = ""
        b_identity = ""

        if (
            adapter_status
            == "verified_success"
        ):

            if body is None:
                raise ReconciliationError(
                    "Successful Wave-A record lacks body"
                )

            primary_normalized = (
                _normalize_live_success(
                    manifest_row=
                        row,
                    evidence=
                        evidence,
                    body=
                        body,
                )
            )

            primary_status = (
                primary_normalized[
                    "abstract_status"
                ]
            )

            if (
                provider
                == "pubmed"
                and primary_status
                == "abstract_absent"
            ):

                observed_reason = (
                    "abstract_absent"
                )

            else:

                observed_reason = None

                if (
                    sequence
                    in b_for_a
                ):
                    raise ReconciliationError(
                        "Frozen fallback exists but "
                        "Wave-A primary terminates cascade"
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
                            "Unexpected terminal PubMed state"
                        )

                    final_source = (
                        "wave_a_pubmed"
                    )

                elif provider == "openalex":

                    if (
                        primary_status
                        not in {
                            "usable_abstract_openalex",
                            "abstract_absent",
                            "openalex_position_gap",
                        }
                    ):
                        raise ReconciliationError(
                            "Unexpected direct OpenAlex state"
                        )

                    final_source = (
                        "wave_a_openalex"
                    )

                else:
                    raise ReconciliationError(
                        "Unexpected Future Wave-A provider"
                    )

        elif (
            adapter_status
            == "verified_not_found"
        ):

            if provider == "pubmed":

                observed_reason = (
                    "verified_not_found"
                )

            elif provider == "openalex":

                expected_sequence_to_index = {
                    2419: 2421,
                    2601: 2603,
                    3090: 3092,
                    3346: 3348,
                    3490: 3492,
                    3533: 3535,
                    4733: 4738,
                    4734: 4739,
                    5274: 5283,
                    11047: 11061,
                }

                current_index = int(
                    row[
                        "retrieval_record_index"
                    ]
                )

                if (
                    expected_sequence_to_index.get(
                        sequence
                    )
                    != current_index
                ):
                    raise ReconciliationError(
                        "Unexpected direct OpenAlex "
                        "verified-not-found identity"
                    )

                if sequence in b_for_a:
                    raise ReconciliationError(
                        "Direct OpenAlex verified-not-found "
                        "must not have Wave-B fallback"
                    )

                terminal_body_sha = (
                    evidence.get(
                        "terminal_body_sha256"
                    )
                )

                if (
                    terminal_body_sha
                    != "e9639e3c4681ce85f852fbac48e2eeee5ba51296dbfec57c200d59b76237ab80"
                ):
                    raise ReconciliationError(
                        "Direct OpenAlex not-found "
                        "terminal-body SHA changed"
                    )

                final_normalized = {
                    "provider_record_id":
                        "",
                    "source_body_sha256":
                        terminal_body_sha,
                    "provider_identity_status":
                        "not_applicable",
                    "parser_status":
                        "not_applicable",
                    "abstract_status":
                        "provider_not_found",
                }

                final_provider = (
                    "openalex"
                )

                final_lookup_type = (
                    row[
                        "frozen_route"
                    ]
                )

                final_source = (
                    "wave_a_openalex_verified_not_found"
                )

                resolution_lane = (
                    "wave_a_primary"
                )

            else:

                raise ReconciliationError(
                    "Unexpected Future Wave-A "
                    "verified-not-found provider"
                )

        else:
            raise ReconciliationError(
                "Unexpected Future Wave-A adapter status"
            )

        if observed_reason is not None:

            actual_fallback_a_sequences.add(
                sequence
            )

            b_sequence = (
                b_for_a.get(
                    sequence
                )
            )

            derivation = (
                derivation_by_a.get(
                    sequence
                )
            )

            if (
                b_sequence is None
                or derivation is None
            ):
                raise ReconciliationError(
                    "Observed Wave-A fallback lacks "
                    "frozen Wave-B derivation"
                )

            if (
                derivation[
                    "fallback_reason"
                ]
                != observed_reason
            ):
                raise ReconciliationError(
                    "Observed Wave-A fallback reason "
                    "differs from frozen derivation"
                )

            if (
                derivation[
                    "wave_a_adapter_evidence_sha256"
                ]
                != evidence_sha
            ):
                raise ReconciliationError(
                    "Wave-A fallback evidence SHA changed"
                )

            frozen_body_sha = (
                derivation[
                    "wave_a_terminal_body_sha256"
                ]
            )

            if frozen_body_sha:

                if (
                    evidence.get(
                        "terminal_body_sha256"
                    )
                    != frozen_body_sha
                ):
                    raise ReconciliationError(
                        "Wave-A fallback terminal-body SHA changed"
                    )

            fallback = (
                b_results[
                    b_sequence
                ]
            )

            b_row = (
                fallback[
                    "manifest_row"
                ]
            )

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
                "wave_b_openalex_after_pubmed_"
                + observed_reason
            )

            resolution_lane = (
                "wave_b_fallback"
            )

            fallback_reason = (
                "pubmed_"
                + observed_reason
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

        assert (
            final_normalized
            is not None
        )

        idx = (
            row[
                "retrieval_record_index"
            ]
        )

        entity = (
            row[
                "screening_entity_id"
            ]
        )

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
                retrieval_record_index=
                    idx,
                screening_entity_id=
                    entity,
                resolution_lane=
                    resolution_lane,
                provider_used=
                    final_provider,
                provider_lookup_type=
                    final_lookup_type,
                normalized=
                    final_normalized,
                wave_a_request_sequence=
                    str(
                        sequence
                    ),
                wave_a_request_identity_sha256=
                    row[
                        "request_identity_sha256"
                    ],
                wave_b_request_sequence=
                    b_sequence_text,
                wave_b_request_identity_sha256=
                    b_identity,
                fallback_reason=
                    fallback_reason,
                normalized_text_present=
                    usable,
                columns=
                    resolution_header,
            )
        )

        if usable:

            text_rows.append(
                _text_row(
                    retrieval_record_index=
                        idx,
                    screening_entity_id=
                        entity,
                    provider_used=
                        final_provider,
                    provider_lookup_type=
                        final_lookup_type,
                    normalized=
                        final_normalized,
                    columns=
                        text_header,
                )
            )

        _record_counts(
            status_counts=
                status_counts,
            source_counts=
                source_counts,
            source_status_counts=
                source_status_counts,
            source_name=
                final_source,
            abstract_status=
                final_normalized[
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
            "Observed Future Wave-A fallback population "
            "differs from frozen Wave-B derivation"
        )

    if (
        fallback_counts
        != Counter({
            "pubmed_abstract_absent":
                38,

            "pubmed_verified_not_found":
                2,
        })
    ):
        raise ReconciliationError(
            "Final fallback-reason counts changed"
        )

    # Reconcile the fifteen frozen offline records.
    _checksum_map, selected_by_index = (
        validate_historical_selected_dependency(
            contract
        )
    )

    if (
        set(
            selected_by_index
        )
        != offline_indices
    ):
        raise ReconciliationError(
            "Selected offline cache population differs "
            "from fifteen offline-only records"
        )

    observed_usable_offline_indices = set()

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
                f"Offline entity mismatch at {idx}"
            )

        normalized = (
            _offline_normalized_record(
                offline_resolution_row=
                    cache_row,
                selected_item=
                    selected_by_index[
                        idx
                    ],
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

        usable = (
            normalized[
                "abstract_status"
            ]
            == "usable_abstract_openalex"
        )

        if usable:

            observed_usable_offline_indices.add(
                idx
            )

            expected_text_row = (
                _text_row(
                    retrieval_record_index=
                        str(
                            idx
                        ),
                    screening_entity_id=
                        input_row[
                            "screening_entity_id"
                        ],
                    provider_used=
                        provider,
                    provider_lookup_type=
                        lookup_type,
                    normalized=
                        normalized,
                    columns=
                        text_header,
                )
            )

            cached = (
                cached_text_by_index.get(
                    idx
                )
            )

            if cached is None:
                raise ReconciliationError(
                    f"Usable offline record lacks "
                    f"frozen normalized-text row at {idx}"
                )

            allowed_provenance_differences = {
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

            unexpected = (
                differing_fields
                - allowed_provenance_differences
            )

            if unexpected:
                raise ReconciliationError(
                    f"Frozen offline scientific/retrieval "
                    f"fields do not reproduce at {idx}: "
                    f"{sorted(unexpected)}"
                )

            if (
                not cached[
                    "provider_record_id"
                ].strip()
                or not cached[
                    "provider_identity_status"
                ].strip()
            ):
                raise ReconciliationError(
                    f"Frozen offline provenance incomplete "
                    f"at {idx}"
                )

            # Preserve the exact already-frozen row.
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
                    f"Abstract-absent offline record "
                    f"unexpectedly has text at {idx}"
                )

        resolution_rows.append(
            _resolution_row(
                retrieval_record_index=
                    str(
                        idx
                    ),
                screening_entity_id=
                    input_row[
                        "screening_entity_id"
                    ],
                resolution_lane=
                    "offline_cache",
                provider_used=
                    provider,
                provider_lookup_type=
                    lookup_type,
                normalized=
                    normalized,
                wave_a_request_sequence=
                    "",
                wave_a_request_identity_sha256=
                    "",
                wave_b_request_sequence=
                    "",
                wave_b_request_identity_sha256=
                    "",
                fallback_reason=
                    "",
                normalized_text_present=
                    usable,
                columns=
                    resolution_header,
            )
        )

        _record_counts(
            status_counts=
                status_counts,
            source_counts=
                source_counts,
            source_status_counts=
                source_status_counts,
            source_name=
                "offline_cache_openalex",
            abstract_status=
                normalized[
                    "abstract_status"
                ],
        )

    if (
        observed_usable_offline_indices
        != set(
            cached_text_by_index
        )
    ):
        raise ReconciliationError(
            "Frozen offline normalized-text population "
            "does not reproduce exactly"
        )

    resolution_rows.sort(
        key=lambda row:
            int(
                row[
                    "retrieval_record_index"
                ]
            )
    )

    text_rows.sort(
        key=lambda row:
            int(
                row[
                    "retrieval_record_index"
                ]
            )
    )

    if len(
        resolution_rows
    ) != 12162:
        raise ReconciliationError(
            "Final resolution cardinality is not 12162"
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
            "Resolution output does not exactly cover "
            "future input manifest"
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
    ) != len(
        text_rows
    ):
        raise ReconciliationError(
            "Normalized-text retrieval indices are not unique"
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

    provider_not_found_rows = [
        row
        for row in resolution_rows
        if (
            row[
                "abstract_status"
            ]
            == "provider_not_found"
        )
    ]

    if (
        {
            int(
                row[
                    "retrieval_record_index"
                ]
            )
            for row in provider_not_found_rows
        }
        != {
            2421,
            2603,
            3092,
            3348,
            3492,
            3535,
            4738,
            4739,
            5283,
            11061,
        }
    ):
        raise ReconciliationError(
            "Direct OpenAlex provider-not-found "
            "population changed"
        )

    for row in provider_not_found_rows:

        if (
            row[
                "resolution_lane"
            ]
            != "wave_a_primary"
            or row[
                "provider_used"
            ]
            != "openalex"
            or row[
                "provider_record_id"
            ]
            != ""
            or row[
                "provider_identity_status"
            ]
            != "not_applicable"
            or row[
                "parser_status"
            ]
            != "not_applicable"
            or row[
                "wave_b_request_sequence"
            ]
            != ""
            or row[
                "wave_b_request_identity_sha256"
            ]
            != ""
            or row[
                "fallback_reason"
            ]
            != ""
            or row[
                "normalized_text_present"
            ]
            != "0"
        ):
            raise ReconciliationError(
                "Direct OpenAlex provider-not-found "
                "resolution semantics changed"
            )

    position_gap_rows = [
        row
        for row in resolution_rows
        if (
            row[
                "abstract_status"
            ]
            == "openalex_position_gap"
        )
    ]

    if len(
        position_gap_rows
    ) != 1:
        raise ReconciliationError(
            "Amendment 002 position-gap "
            "population is not exactly one"
        )

    position_gap_row = (
        position_gap_rows[0]
    )

    if (
        position_gap_row[
            "retrieval_record_index"
        ]
        != '9191'
        or position_gap_row[
            "screening_entity_id"
        ]
        != 'publication_component:citation:publication:doi:10.5897/ajb11.773'
        or position_gap_row[
            "resolution_lane"
        ]
        != 'wave_a_primary'
        or position_gap_row[
            "provider_used"
        ]
        != 'openalex'
        or position_gap_row[
            "provider_lookup_type"
        ]
        != 'exact_work_id'
        or position_gap_row[
            "provider_record_id"
        ]
        != 'https://openalex.org/W2119850564'
        or position_gap_row[
            "source_body_sha256"
        ]
        != '30228dfcd8815a4e8dfbbefc810d9033a579b2733cb7091c6314e514178943a1'
        or position_gap_row[
            "provider_identity_status"
        ]
        != 'matched'
        or position_gap_row[
            "parser_status"
        ]
        != 'ok'
        or position_gap_row[
            "wave_a_request_sequence"
        ]
        != '9180'
        or position_gap_row[
            "wave_a_request_identity_sha256"
        ]
        != '0ce8b2384745cddbd10549afeb55642d781f067fd7d5c612b75006a1dd0bf1e2'
        or position_gap_row[
            "wave_b_request_sequence"
        ]
        != ""
        or position_gap_row[
            "wave_b_request_identity_sha256"
        ]
        != ""
        or position_gap_row[
            "fallback_reason"
        ]
        != ""
        or position_gap_row[
            "normalized_text_present"
        ]
        != "0"
    ):
        raise ReconciliationError(
            "Amendment 002 position-gap "
            "resolution semantics changed"
        )

    if (
        9191
        in text_indices
    ):
        raise ReconciliationError(
            "Amendment 002 position-gap record "
            "entered normalized-text output"
        )

    parser_failure_count = sum(
        1
        for row in resolution_rows
        if (
            row[
                "abstract_status"
            ]
            != "provider_not_found"
            and row[
                "parser_status"
            ]
            != "ok"
        )
    )

    if parser_failure_count != 0:
        raise ReconciliationError(
            "Parser failure encountered"
        )

    position_gap_total = (
        status_counts[
            "openalex_position_gap"
        ]
    )

    if position_gap_total != 1:
        raise ReconciliationError(
            "Amendment 002 position-gap "
            "status count changed"
        )

    parser_or_gap_count = (
        parser_failure_count
        + position_gap_total
    )

    usable_total = sum(
        status_counts[
            key
        ]
        for key in (
            "usable_abstract_pubmed",
            "usable_abstract_openalex",
        )
    )

    absent_total = (
        status_counts[
            "abstract_absent"
        ]
    )

    provider_not_found_total = (
        status_counts[
            "provider_not_found"
        ]
    )

    if provider_not_found_total != 10:
        raise ReconciliationError(
            "Direct OpenAlex provider-not-found "
            "count changed"
        )

    if (
        usable_total
        + absent_total
        + provider_not_found_total
        + position_gap_total
        != 12162
    ):
        raise ReconciliationError(
            "Final abstract-state population incomplete"
        )

    if (
        len(
            text_rows
        )
        != usable_total
    ):
        raise ReconciliationError(
            "Normalized-text row count differs "
            "from usable-abstract count"
        )

    if (
        source_counts[
            "wave_a_openalex_verified_not_found"
        ]
        != 10
    ):
        raise ReconciliationError(
            "Direct OpenAlex provider-not-found "
            "terminal-source count changed"
        )

    if (
        source_counts[
            "offline_cache_openalex"
        ]
        != 15
    ):
        raise ReconciliationError(
            "Offline terminal-source count changed"
        )

    if (
        source_counts[
            "wave_b_openalex_after_pubmed_abstract_absent"
        ]
        != 38
        or source_counts[
            "wave_b_openalex_after_pubmed_verified_not_found"
        ]
        != 2
    ):
        raise ReconciliationError(
            "Wave-B terminal-source counts changed"
        )

    observed_matrix = {
        source:
            dict(
                sorted(
                    counts.items()
                )
            )
        for source, counts in sorted(
            source_status_counts.items()
        )
    }

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
                sorted(
                    status_counts.items()
                )
            ),

        "terminal_source_counts":
            dict(
                sorted(
                    source_counts.items()
                )
            ),

        "terminal_source_status_counts":
            observed_matrix,

        "fallback_reason_counts":
            dict(
                sorted(
                    fallback_counts.items()
                )
            ),

        "wave_b_normalized_status_counts":
            dict(
                sorted(
                    wave_b_normalized_status_counts.items()
                )
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
            fieldnames=
                columns,
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
    canonical_confirmation: str | None = None,
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
                + str(
                    path
                )
            )

    return output_root


def build_source_hash_summary(
    contract: dict,
) -> dict[str, str]:

    source_hashes = dict(
        contract[
            "design"
        ][
            "source_bindings"
        ]
    )

    source_hashes[
        str(
            DESIGN_PATH.relative_to(
                REPO_ROOT
            )
        )
    ] = sha256_file(
        DESIGN_PATH
    )

    for path in sorted(
        EXTRA_FROZEN_HASHES,
        key=str,
    ):

        source_hashes[
            str(
                path.relative_to(
                    REPO_ROOT
                )
            )
        ] = sha256_file(
            path
        )

    source_hashes[
        str(
            HISTORICAL_CHECKSUM_PATH.relative_to(
                REPO_ROOT
            )
        )
    ] = sha256_file(
        HISTORICAL_CHECKSUM_PATH
    )

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
            canonical_confirmation=
                canonical_confirmation,
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
        path=
            resolution_path,
        columns=
            result[
                "resolution_columns"
            ],
        rows=
            result[
                "resolution_rows"
            ],
    )

    write_tsv(
        path=
            text_path,
        columns=
            result[
                "normalized_text_columns"
            ],
        rows=
            result[
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
            "pre_review_triage_future_text_reconciliation_v1",

        "design_sha256":
            EXPECTED_DESIGN_SHA256,

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

        "wave_b_normalized_status_counts":
            result[
                "wave_b_normalized_status_counts"
            ],

        "parser_or_position_gap_count":
            result[
                "parser_or_position_gap_count"
            ],

        "safety_boundaries": {
            "network_used":
                False,

            "production_write":
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

        "terminal_source_status_counts":
            result[
                "terminal_source_status_counts"
            ],

        "fallback_reason_counts":
            result[
                "fallback_reason_counts"
            ],

        "wave_b_normalized_status_counts":
            result[
                "wave_b_normalized_status_counts"
            ],

        "parser_or_position_gap_count":
            result[
                "parser_or_position_gap_count"
            ],
    }


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser()

    group = (
        parser.add_mutually_exclusive_group(
            required=True
        )
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

        print(
            json.dumps(
                dry_run(),
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    written = (
        write_reconciliation(
            output_root=
                args.output_root,
            canonical_confirmation=
                args.confirm_canonical,
        )
    )

    print(
        json.dumps(
            {
                key:
                    str(
                        value
                    )
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
