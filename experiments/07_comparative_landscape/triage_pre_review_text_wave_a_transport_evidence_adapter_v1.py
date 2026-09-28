from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


ROOT = Path(
    "experiments/07_comparative_landscape"
)

BASE_DESIGN = (
    ROOT
    / "triage_pre_review_text_wave_a_transport_evidence_adapter_v1_design.json"
)

AMENDMENT_DESIGN = (
    ROOT
    / "triage_pre_review_text_wave_a_transport_evidence_adapter_v1_amendment_01_design.json"
)

EXPECTED_BASE_DESIGN_SHA256 = (
    "10dab25efdeb5fdbddacaef90479456af31275ab8a2d3ed5421c85592894ea48"
)

EXPECTED_AMENDMENT_SHA256 = (
    "0003aa1ad456a1a7dc25a291afe5869eed7e77309d377fb0aa3e1fa5a1d83ad0"
)

EVIDENCE_DIRECTORY = (
    "transport_evidence"
)


class AdapterError(
    RuntimeError
):
    pass


class ProviderIdentityMismatch(
    AdapterError
):
    pass


class TransportEvidenceFault(
    AdapterError
):
    pass


def canonical_json_bytes(
    value: Any,
) -> bytes:

    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    ).encode(
        "utf-8"
    )


def sha256_bytes(
    value: bytes,
) -> str:

    return hashlib.sha256(
        value
    ).hexdigest()


def sha256_file(
    path: Path,
) -> str:

    return sha256_bytes(
        path.read_bytes()
    )


def load_contract() -> tuple[
    dict,
    dict,
]:

    if (
        sha256_file(
            BASE_DESIGN
        )
        != EXPECTED_BASE_DESIGN_SHA256
    ):
        raise AdapterError(
            "Base adapter design hash mismatch"
        )

    if (
        sha256_file(
            AMENDMENT_DESIGN
        )
        != EXPECTED_AMENDMENT_SHA256
    ):
        raise AdapterError(
            "Adapter amendment hash mismatch"
        )

    base = json.loads(
        BASE_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    amendment = json.loads(
        AMENDMENT_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if (
        base.get(
            "status"
        )
        != "FROZEN_PRE_IMPLEMENTATION"
    ):
        raise AdapterError(
            "Base adapter design status changed"
        )

    if (
        amendment.get(
            "status"
        )
        != "FROZEN_PRE_IMPLEMENTATION"
    ):
        raise AdapterError(
            "Adapter amendment status changed"
        )

    if (
        amendment[
            "base_design"
        ][
            "sha256"
        ]
        != EXPECTED_BASE_DESIGN_SHA256
    ):
        raise AdapterError(
            "Amendment no longer binds base design"
        )

    for record in (
        base[
            "frozen_sources"
        ].values()
    ):

        path = Path(
            record[
                "path"
            ]
        )

        if not path.is_file():

            raise AdapterError(
                "Frozen dependency missing: "
                + str(
                    path
                )
            )

        if (
            sha256_file(
                path
            )
            != record[
                "sha256"
            ]
        ):

            raise AdapterError(
                "Frozen dependency hash mismatch: "
                + str(
                    path
                )
            )

    return (
        base,
        amendment,
    )


def normalize_openalex_work_token(
    value: str,
) -> str:

    raw = str(
        value
    ).strip()

    match = re.fullmatch(
        r"(?:https://openalex\.org/)?(W[0-9]+)",
        raw,
        flags=re.IGNORECASE,
    )

    if match is None:

        raise ProviderIdentityMismatch(
            "OpenAlex Work identifier is not canonical"
        )

    return (
        match.group(1)
        .upper()
    )


def normalize_doi(
    value: str,
) -> str:

    raw = str(
        value
    ).strip()

    lowered = raw.lower()

    prefixes = (
        "https://doi.org/",
        "http://doi.org/",
        "doi:",
    )

    for prefix in prefixes:

        if lowered.startswith(
            prefix
        ):

            raw = raw[
                len(
                    prefix
                ):
            ].strip()

            break

    if not raw:

        raise ProviderIdentityMismatch(
            "DOI is empty after normalization"
        )

    return raw.lower()


def manifest_to_transport_row(
    manifest_row: dict[str, str],
) -> dict[str, str]:

    sequence = int(
        manifest_row[
            "request_sequence"
        ]
    )

    identity = str(
        manifest_row[
            "request_identity_sha256"
        ]
    )

    if not re.fullmatch(
        r"[0-9a-f]{64}",
        identity,
    ):

        raise AdapterError(
            "Manifest request identity SHA invalid"
        )

    logical_lookup_id = (
        "triage_text_wave_a:"
        f"{sequence:04d}:"
        f"{identity[:16]}"
    )

    row = {
        "logical_lookup_id":
            logical_lookup_id,

        "provider":
            manifest_row[
                "provider"
            ],

        "route":
            manifest_row[
                "transport_route"
            ],

        "identifier_namespace":
            manifest_row[
                "identifier_namespace"
            ],

        "identifier":
            manifest_row[
                "identifier"
            ],
    }

    allowed = {
        (
            "pubmed",
            "record_by_pmid",
            "pmid",
        ),

        (
            "openalex",
            "work_by_openalex_id",
            "openalex",
        ),

        (
            "openalex",
            "work_by_doi",
            "doi",
        ),
    }

    observed = (
        row[
            "provider"
        ],
        row[
            "route"
        ],
        row[
            "identifier_namespace"
        ],
    )

    if observed not in allowed:

        raise AdapterError(
            "Transport route outside frozen adapter contract"
        )

    return row


def transport_lookup_root(
    archive_root: Path,
    transport_row: dict[str, str],
) -> Path:

    return (
        archive_root
        / "raw"
        / transport_row[
            "logical_lookup_id"
        ].replace(
            ":",
            "_",
        )
    )


def terminal_json_path(
    archive_root: Path,
    transport_row: dict[str, str],
) -> Path:

    return (
        transport_lookup_root(
            archive_root,
            transport_row,
        )
        / "terminal.json"
    )


def raw_archive_bundle_records(
    lookup_root: Path,
) -> list[dict]:

    if not lookup_root.is_dir():

        raise TransportEvidenceFault(
            "Raw transport lookup root missing"
        )

    records = []

    for path in sorted(
        (
            item
            for item in lookup_root.rglob("*")
            if item.is_file()
        ),
        key=lambda item: (
            item.relative_to(
                lookup_root
            ).as_posix()
        ),
    ):

        records.append({
            "path":
                path.relative_to(
                    lookup_root
                ).as_posix(),

            "sha256":
                sha256_file(
                    path
                ),
        })

    if not records:

        raise TransportEvidenceFault(
            "Raw transport lookup archive is empty"
        )

    return records


def raw_archive_bundle_sha256(
    lookup_root: Path,
) -> str:

    return sha256_bytes(
        canonical_json_bytes(
            raw_archive_bundle_records(
                lookup_root
            )
        )
    )


def validate_terminal_request_identity(
    *,
    terminal: dict,
    transport_row: dict[str, str],
) -> None:

    expected = {
        "logical_lookup_id":
            transport_row[
                "logical_lookup_id"
            ],

        "provider":
            transport_row[
                "provider"
            ],

        "route":
            transport_row[
                "route"
            ],

        "identifier_namespace":
            transport_row[
                "identifier_namespace"
            ],

        "identifier":
            transport_row[
                "identifier"
            ],
    }

    for key, expected_value in (
        expected.items()
    ):

        if (
            terminal.get(
                key
            )
            != expected_value
        ):

            raise TransportEvidenceFault(
                "Transport terminal request identity mismatch: "
                + key
            )


def final_attempt_root(
    *,
    lookup_root: Path,
    terminal: dict,
) -> Path:

    return (
        lookup_root
        / (
            "attempt_"
            f"{int(terminal['attempt_count']):02d}"
        )
    )


def hop_metadata(
    *,
    lookup_root: Path,
    terminal: dict,
) -> list[dict]:

    attempt_root = (
        final_attempt_root(
            lookup_root=lookup_root,
            terminal=terminal,
        )
    )

    paths = sorted(
        attempt_root.glob(
            "hop_*_response.json"
        )
    )

    if not paths:

        raise TransportEvidenceFault(
            "Terminal attempt lacks archived response metadata"
        )

    values = []

    for expected_index, path in enumerate(
        paths
    ):

        value = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if (
            int(
                value.get(
                    "hop_number",
                    -1,
                )
            )
            != expected_index
        ):

            raise TransportEvidenceFault(
                "Archived redirect hop numbering is not contiguous"
            )

        values.append(
            value
        )

    return values


def read_verified_final_body(
    *,
    lookup_root: Path,
    terminal: dict,
) -> bytes:

    hops = hop_metadata(
        lookup_root=lookup_root,
        terminal=terminal,
    )

    attempt_root = (
        final_attempt_root(
            lookup_root=lookup_root,
            terminal=terminal,
        )
    )

    final_metadata = hops[-1]

    body_path = (
        attempt_root
        / final_metadata[
            "body_file"
        ]
    )

    body = body_path.read_bytes()

    actual = sha256_bytes(
        body
    )

    if (
        actual
        != final_metadata[
            "body_sha256"
        ]
    ):

        raise TransportEvidenceFault(
            "Final archived response body SHA mismatch"
        )

    if (
        actual
        != terminal[
            "terminal_body_sha256"
        ]
    ):

        raise TransportEvidenceFault(
            "Transport terminal body SHA mismatch"
        )

    return body


def header_values(
    pairs,
    name: str,
) -> list[str]:

    target = name.lower()

    values = []

    for pair in pairs:

        if (
            isinstance(
                pair,
                (list, tuple),
            )
            and len(
                pair
            )
            == 2
            and str(
                pair[0]
            ).lower()
            == target
        ):

            values.append(
                str(
                    pair[1]
                )
            )

    return values


def work_token_from_api_url(
    value: str,
) -> str:

    raw = str(
        value
    ).strip()

    match = re.search(
        r"(?:https://api\.openalex\.org)?"
        r"/works/(W[0-9]+)"
        r"(?:[/?#]|$)",
        raw,
        flags=re.IGNORECASE,
    )

    if match is None:

        raise ProviderIdentityMismatch(
            "Archived OpenAlex request/redirect URL lacks canonical Work path"
        )

    return (
        match.group(1)
        .upper()
    )


def validate_openalex_work_redirect(
    *,
    lookup_root: Path,
    terminal: dict,
    transport_row: dict[str, str],
    requested_work: str,
    returned_work: str,
    transport_module,
) -> None:

    hops = hop_metadata(
        lookup_root=lookup_root,
        terminal=terminal,
    )

    if len(
        hops
    ) < 2:

        raise ProviderIdentityMismatch(
            "Different OpenAlex Work returned without archived redirect"
        )

    expected_initial_request = (
        transport_module.build_request(
            transport_row,
            environ={},
        )
    )

    expected_initial_url = (
        transport_module.sanitized_url(
            expected_initial_request.url
        )
    )

    first_request_url = str(
        hops[0].get(
            "request_url",
            "",
        )
    )

    if (
        first_request_url
        != expected_initial_url
    ):

        raise ProviderIdentityMismatch(
            "First archived OpenAlex request URL does not reproduce "
            "the exact frozen request"
        )

    request_tokens = []

    for hop in hops:

        request_url = str(
            hop.get(
                "request_url",
                "",
            )
        )

        response_url = str(
            hop.get(
                "response_url",
                "",
            )
        )

        request_token = (
            work_token_from_api_url(
                request_url
            )
        )

        response_token = (
            work_token_from_api_url(
                response_url
            )
        )

        if (
            response_token
            != request_token
        ):

            raise ProviderIdentityMismatch(
                "Archived OpenAlex response URL differs from "
                "its request Work"
            )

        request_tokens.append(
            request_token
        )

    if (
        request_tokens[0]
        != requested_work
    ):

        raise ProviderIdentityMismatch(
            "First archived OpenAlex request does not match requested Work"
        )

    if (
        request_tokens[-1]
        != returned_work
    ):

        raise ProviderIdentityMismatch(
            "Final archived OpenAlex request does not match returned Work"
        )

    for index in range(
        len(
            hops
        )
        - 1
    ):

        hop = hops[
            index
        ]

        status = int(
            hop.get(
                "response_status",
                -1,
            )
        )

        if (
            status
            not in transport_module.REDIRECT_STATUSES
        ):

            raise ProviderIdentityMismatch(
                "Non-final OpenAlex hop is not a frozen redirect status"
            )

        locations = header_values(
            hop.get(
                "response_headers",
                [],
            ),
            "Location",
        )

        if len(
            locations
        ) != 1:

            raise ProviderIdentityMismatch(
                "Archived OpenAlex redirect lacks exactly one Location"
            )

        current_url = str(
            hop.get(
                "request_url",
                "",
            )
        )

        try:

            target = (
                transport_module.validate_redirect_target(
                    provider="openalex",
                    current_url=current_url,
                    location=locations[0],
                )
            )

            # Re-run the frozen OpenAlex credential-preservation
            # policy against the sanitized archived request. Because
            # the archive is credential-free, a redirect that
            # introduces an api_key must fail closed.
            target = (
                transport_module.preserve_openalex_api_key_on_redirect(
                    current_url=current_url,
                    target_url=target,
                )
            )

        except Exception as exc:

            raise ProviderIdentityMismatch(
                "Archived OpenAlex redirect fails frozen transport policy"
            ) from exc

        target = (
            transport_module.sanitized_url(
                target
            )
        )

        next_request_url = str(
            hops[
                index + 1
            ].get(
                "request_url",
                "",
            )
        )

        if (
            target
            != next_request_url
        ):

            raise ProviderIdentityMismatch(
                "Archived OpenAlex redirect chain is not URL-contiguous"
            )

    final_status = int(
        hops[-1].get(
            "response_status",
            -1,
        )
    )

    if (
        final_status
        in transport_module.REDIRECT_STATUSES
    ):

        raise ProviderIdentityMismatch(
            "Final archived OpenAlex hop remains a redirect"
        )

    attempts = terminal.get(
        "attempts"
    )

    if (
        not isinstance(
            attempts,
            list,
        )
        or not attempts
    ):

        raise ProviderIdentityMismatch(
            "Transport terminal lacks attempt history"
        )

    redirect_count = attempts[-1].get(
        "redirect_hops"
    )

    if (
        redirect_count
        != len(
            hops
        )
        - 1
    ):

        raise ProviderIdentityMismatch(
            "Terminal redirect count differs from archived redirect chain"
        )

def validate_success_provider_identity(
    *,
    transport_row: dict[str, str],
    terminal: dict,
    body: bytes,
    lookup_root: Path,
    transport_module,
) -> tuple[
    str,
    str,
]:

    provider = transport_row[
        "provider"
    ]

    route = transport_row[
        "route"
    ]

    requested = transport_row[
        "identifier"
    ]

    if provider == "pubmed":

        returned = terminal.get(
            "provider_identifier"
        )

        if returned != requested:

            raise ProviderIdentityMismatch(
                "PubMed provider identifier does not match requested PMID"
            )

        return (
            returned,
            "matched",
        )

    if provider != "openalex":

        raise ProviderIdentityMismatch(
            "Unsupported successful provider"
        )

    try:

        value = json.loads(
            body.decode(
                "utf-8"
            )
        )

    except Exception as exc:

        raise ProviderIdentityMismatch(
            "OpenAlex archived body is not valid JSON"
        ) from exc

    if not isinstance(
        value,
        dict,
    ):

        raise ProviderIdentityMismatch(
            "OpenAlex archived body is not one object"
        )

    top_level_id = value.get(
        "id"
    )

    ids = value.get(
        "ids"
    )

    if not isinstance(
        ids,
        dict,
    ):

        raise ProviderIdentityMismatch(
            "OpenAlex archived body lacks ids object"
        )

    returned_work = (
        normalize_openalex_work_token(
            top_level_id
        )
    )

    terminal_provider_id = (
        terminal.get(
            "provider_identifier"
        )
    )

    if (
        terminal_provider_id
        != top_level_id
    ):

        raise ProviderIdentityMismatch(
            "Transport terminal provider identifier differs "
            "from archived OpenAlex payload"
        )

    if route == "work_by_openalex_id":

        requested_work = (
            normalize_openalex_work_token(
                requested
            )
        )

        ids_openalex = ids.get(
            "openalex"
        )

        if ids_openalex is not None:

            if (
                normalize_openalex_work_token(
                    ids_openalex
                )
                != returned_work
            ):

                raise ProviderIdentityMismatch(
                    "OpenAlex ids.openalex conflicts with top-level Work ID"
                )

        if (
            returned_work
            == requested_work
        ):

            return (
                str(
                    top_level_id
                ),
                "matched",
            )

        validate_openalex_work_redirect(
            lookup_root=lookup_root,
            terminal=terminal,
            transport_row=transport_row,
            requested_work=requested_work,
            returned_work=returned_work,
            transport_module=
                transport_module,
        )

        return (
            str(
                top_level_id
            ),
            "matched_via_verified_openalex_redirect",
        )

    if route == "work_by_doi":

        returned_doi = ids.get(
            "doi"
        )

        if (
            not isinstance(
                returned_doi,
                str,
            )
            or not returned_doi.strip()
        ):

            raise ProviderIdentityMismatch(
                "OpenAlex exact DOI response lacks ids.doi"
            )

        if (
            normalize_doi(
                returned_doi
            )
            != normalize_doi(
                requested
            )
        ):

            raise ProviderIdentityMismatch(
                "OpenAlex DOI does not match exact requested DOI"
            )

        return (
            str(
                top_level_id
            ),
            "matched",
        )

    raise ProviderIdentityMismatch(
        "Unsupported OpenAlex success route"
    )


def verified_evidence(
    *,
    manifest_row: dict[str, str],
    archive_root: Path,
    transport_module,
) -> dict:

    load_contract()

    transport_row = (
        manifest_to_transport_row(
            manifest_row
        )
    )

    lookup_root = (
        transport_lookup_root(
            archive_root,
            transport_row,
        )
    )

    terminal_path = (
        lookup_root
        / "terminal.json"
    )

    if not terminal_path.is_file():

        raise TransportEvidenceFault(
            "Transport terminal.json missing"
        )

    try:

        terminal = (
            transport_module.verify_terminal_archive(
                lookup_root
            )
        )

    except Exception as exc:

        raise TransportEvidenceFault(
            "Transport terminal archive verification failed"
        ) from exc

    validate_terminal_request_identity(
        terminal=terminal,
        transport_row=transport_row,
    )

    status = terminal.get(
        "terminal_status"
    )

    if status not in {
        "success",
        "not_found",
    }:

        raise TransportEvidenceFault(
            "Transport terminal status is not checkpoint-eligible"
        )

    body = (
        read_verified_final_body(
            lookup_root=lookup_root,
            terminal=terminal,
        )
    )

    if status == "success":

        (
            provider_record_id,
            provider_identity_status,
        ) = (
            validate_success_provider_identity(
                transport_row=
                    transport_row,
                terminal=terminal,
                body=body,
                lookup_root=
                    lookup_root,
                transport_module=
                    transport_module,
            )
        )

        adapter_status = (
            "verified_success"
        )

    else:

        provider_record_id = None

        provider_identity_status = (
            "not_applicable_not_found"
        )

        adapter_status = (
            "verified_not_found"
        )

    return {
        "schema_version":
            1,

        "wave_id":
            manifest_row[
                "wave_id"
            ],

        "request_sequence":
            int(
                manifest_row[
                    "request_sequence"
                ]
            ),

        "request_identity_sha256":
            manifest_row[
                "request_identity_sha256"
            ],

        "logical_lookup_id":
            transport_row[
                "logical_lookup_id"
            ],

        "provider":
            transport_row[
                "provider"
            ],

        "transport_route":
            transport_row[
                "route"
            ],

        "identifier_namespace":
            transport_row[
                "identifier_namespace"
            ],

        "identifier":
            transport_row[
                "identifier"
            ],

        "transport_terminal_status":
            status,

        "adapter_status":
            adapter_status,

        "checkpoint_eligible":
            True,

        "provider_record_id":
            provider_record_id,

        "provider_identity_status":
            provider_identity_status,

        "transport_terminal_json_sha256":
            sha256_file(
                terminal_path
            ),

        "terminal_body_sha256":
            terminal[
                "terminal_body_sha256"
            ],

        "raw_archive_bundle_sha256":
            raw_archive_bundle_sha256(
                lookup_root
            ),
    }


def fault_evidence(
    *,
    manifest_row: dict[str, str],
    archive_root: Path,
    transport_terminal_status: str,
    adapter_status: str,
) -> dict:

    transport_row = (
        manifest_to_transport_row(
            manifest_row
        )
    )

    lookup_root = (
        transport_lookup_root(
            archive_root,
            transport_row,
        )
    )

    terminal_path = (
        lookup_root
        / "terminal.json"
    )

    terminal_sha = None
    terminal_body_sha = None
    provider_record_id = None
    bundle_sha = None

    if lookup_root.is_dir():

        try:

            bundle_sha = (
                raw_archive_bundle_sha256(
                    lookup_root
                )
            )

        except Exception:

            bundle_sha = None

    if terminal_path.is_file():

        terminal_sha = sha256_file(
            terminal_path
        )

        try:

            terminal = json.loads(
                terminal_path.read_text(
                    encoding="utf-8"
                )
            )

            terminal_body_sha = (
                terminal.get(
                    "terminal_body_sha256"
                )
            )

            provider_record_id = (
                terminal.get(
                    "provider_identifier"
                )
            )

        except Exception:

            pass

    return {
        "schema_version":
            1,

        "wave_id":
            manifest_row[
                "wave_id"
            ],

        "request_sequence":
            int(
                manifest_row[
                    "request_sequence"
                ]
            ),

        "request_identity_sha256":
            manifest_row[
                "request_identity_sha256"
            ],

        "logical_lookup_id":
            transport_row[
                "logical_lookup_id"
            ],

        "provider":
            transport_row[
                "provider"
            ],

        "transport_route":
            transport_row[
                "route"
            ],

        "identifier_namespace":
            transport_row[
                "identifier_namespace"
            ],

        "identifier":
            transport_row[
                "identifier"
            ],

        "transport_terminal_status":
            transport_terminal_status,

        "adapter_status":
            adapter_status,

        "checkpoint_eligible":
            False,

        "provider_record_id":
            provider_record_id,

        "provider_identity_status":
            "not_evaluated",

        "transport_terminal_json_sha256":
            terminal_sha,

        "terminal_body_sha256":
            terminal_body_sha,

        "raw_archive_bundle_sha256":
            bundle_sha,
    }


def evidence_path(
    execution_root: Path,
    sequence: int,
) -> Path:

    return (
        execution_root
        / EVIDENCE_DIRECTORY
        / f"{sequence:04d}.json"
    )


def checksum_path(
    path: Path,
) -> Path:

    return Path(
        str(
            path
        )
        + ".sha256"
    )


def read_evidence_path(
    path: Path,
) -> dict:

    digest_path = (
        checksum_path(
            path
        )
    )

    if (
        not path.is_file()
        or not digest_path.is_file()
    ):

        raise TransportEvidenceFault(
            "Adapter evidence/checksum pair incomplete"
        )

    raw = path.read_bytes()

    pieces = (
        digest_path.read_text(
            encoding="utf-8"
        )
        .strip()
        .split()
    )

    if len(
        pieces
    ) != 2:

        raise TransportEvidenceFault(
            "Malformed adapter evidence checksum"
        )

    if pieces[1] != path.name:

        raise TransportEvidenceFault(
            "Adapter checksum filename mismatch"
        )

    if (
        sha256_bytes(
            raw
        )
        != pieces[0]
    ):

        raise TransportEvidenceFault(
            "Adapter evidence checksum mismatch"
        )

    value = json.loads(
        raw.decode(
            "utf-8"
        )
    )

    if not isinstance(
        value,
        dict,
    ):

        raise TransportEvidenceFault(
            "Adapter evidence must be JSON object"
        )

    return value


def read_evidence(
    *,
    execution_root: Path,
    sequence: int,
) -> dict:

    return read_evidence_path(
        evidence_path(
            execution_root,
            sequence,
        )
    )


def write_evidence(
    *,
    execution_root: Path,
    evidence: dict,
) -> Path:

    sequence = int(
        evidence[
            "request_sequence"
        ]
    )

    path = evidence_path(
        execution_root,
        sequence,
    )

    digest_path = checksum_path(
        path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if (
        path.exists()
        or digest_path.exists()
    ):

        existing = read_evidence_path(
            path
        )

        if existing != evidence:

            raise TransportEvidenceFault(
                "Existing adapter evidence differs from reconstructed evidence"
            )

        return path

    raw = canonical_json_bytes(
        evidence
    )

    digest = sha256_bytes(
        raw
    )

    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
    )

    fd = os.open(
        path,
        flags,
        0o644,
    )

    try:

        with os.fdopen(
            fd,
            "wb",
        ) as handle:

            handle.write(
                raw
            )

    except Exception:

        try:
            path.unlink()
        except FileNotFoundError:
            pass

        raise

    digest_raw = (
        digest
        + "  "
        + path.name
        + "\n"
    ).encode(
        "utf-8"
    )

    fd = os.open(
        digest_path,
        flags,
        0o644,
    )

    try:

        with os.fdopen(
            fd,
            "wb",
        ) as handle:

            handle.write(
                digest_raw
            )

    except Exception:

        raise

    return path
