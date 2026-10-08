from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(
    "experiments/07_comparative_landscape"
)

RESULTS = Path(
    "results/07_comparative_landscape"
)

OUT = (
    RESULTS
    / "pre_review_triage_future_text_retrieval_v1"
)


INPUT = (
    OUT
    / "input_manifest.tsv"
)

BASE_MANIFEST = (
    OUT
    / "live_wave_a_request_manifest.tsv"
)

AMENDED_MANIFEST = (
    OUT
    / "live_wave_a_request_manifest_amendment_001.tsv"
)

OFFLINE_RESOLUTION = (
    OUT
    / "offline_cache_resolution.tsv"
)

OFFLINE_NORMALIZED = (
    OUT
    / "offline_cached_normalized_text.tsv"
)

OFFLINE_NETWORK = (
    OUT
    / "offline_network_requirements.tsv"
)

OFFLINE_SUMMARY = (
    OUT
    / "offline_cache_summary.json"
)

OFFLINE_PROVENANCE = (
    OUT
    / "offline_selected_cache_provenance.tsv"
)

CACHE_ROOT = (
    RESULTS
    / "metadata_resolution_retrieval"
)

CACHE_CHECKSUMS = (
    CACHE_ROOT
    / "checksums.sha256"
)

BASE_DESIGN = (
    ROOT
    / "pre_review_triage_future_text_live_retrieval_v1_design.json"
)

OFFLINE_RUNNER = (
    ROOT
    / "pre_review_triage_future_text_offline_runner_v1.py"
)

NORMALIZER = (
    ROOT
    / "triage_pre_review_text_normalizer_v1.py"
)

AMEND_FREEZE = (
    ROOT
    / "pre_review_triage_future_text_live_retrieval_v1_"
      "amendment_001_freeze.py"
)

AMEND_DESIGN = (
    ROOT
    / "pre_review_triage_future_text_live_retrieval_v1_"
      "amendment_001_design.json"
)

AMEND_DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_TEXT_LIVE_RETRIEVAL_V1_"
      "AMENDMENT_001.md"
)

AMEND_SHA = (
    ROOT
    / "pre_review_triage_future_text_live_retrieval_v1_"
      "amendment_001.sha256"
)


EXPECTED_HEAD = (
    "54e1b0404bf6ed87315b55f320495360e7ce1524"
)

EXPECTED_INPUT_SHA256 = (
    "345c90522a44f9f548fb164618943cac24"
    "fb87f7820d52a9048bcfe7a4eec6cf"
)

EXPECTED_BASE_DESIGN_SHA256 = (
    "826e400faccf7481219cd04661a4e7e"
    "785903ec2876e1384ef5cfda3b10dd9e5"
)

EXPECTED_BASE_MANIFEST_SHA256 = (
    "90a5bc130b51305ff88b020a90a7fd9"
    "dc5c88f6dde190cf8752f630905facbec"
)

EXPECTED_OFFLINE_RUNNER_SHA256 = (
    "47773112682532ef473c33ef28db276dede01d115961f50f699c46a283d1d018"
)

EXPECTED_OFFLINE_RESOLUTION_SHA256 = (
    "72ac4012dc1643b56a9d0f0fd089f3c7"
    "8fd8d272aca8775447c85105c7a49ed0"
)

EXPECTED_OFFLINE_NORMALIZED_SHA256 = (
    "971cd9df8ea9e945922bbaca4f0747ae"
    "014fc20930efd9079dcd3d412cfb63ab"
)

EXPECTED_OFFLINE_NETWORK_SHA256 = (
    "19d0c9ce7049c35e10cfbb9e56be8b0"
    "c012256d9329a39300f94f5584b8ed25f"
)

EXPECTED_OFFLINE_SUMMARY_SHA256 = (
    "262498d1159f7dbe24f0daf200801034"
    "a134f50fdf17d4dae6cbcc570bc811e7"
)

EXPECTED_OFFLINE_PROVENANCE_SHA256 = (
    "0b053cfbdc189e1000a8307eb3a88cd6"
    "d7560ccae1bb55d033bbf6d549d77165"
)

EXPECTED_CACHE_CHECKSUMS_SHA256 = (
    "f51080de3383cae1981e19c57687e4c8"
    "ea0e7f9832316a3936728a23995e8b86"
)

EXPECTED_NORMALIZER_SHA256 = (
    "cbe66fc9ab406fa5ee3745e099c16250"
    "c404a949c0f301e40a7397c285dc459d"
)

EXPECTED_TRANSPORT_SOURCES = [
    {
        "path":
            (
                "experiments/07_comparative_landscape/"
                "retrieve_metadata_resolution_queue.py"
            ),

        "sha256":
            (
                "9c8c11edbbec86e5cbf857f25c1bf576"
                "a0638ba5cdcf69d1fa2a8b8bfc1a994f"
            ),
    },
    {
        "path":
            (
                "experiments/07_comparative_landscape/"
                "t000002_authoritative_source_network_transport.py"
            ),

        "sha256":
            (
                "cc68579ff66af7633b7dd79520f748cfb"
                "e09cf8f95eaaf5cc927b833c4a7d962"
            ),
    },
]

EXPECTED_ADAPTER_SHA256 = (
    "30a311626b3e99e6520601585b87df3b6"
    "00991094d7724cd358b52159d902bac"
)

WAVE_ID = (
    "TRIAGE_FUTURE_TEXT_LIVE_WAVE_A"
)


ROUTE_MAP = {
    (
        "pubmed",
        "exact_pmid_efetch",
    ): {
        "transport_route":
            "record_by_pmid",

        "identifier_namespace":
            "pmid",
    },

    (
        "openalex",
        "exact_work_id",
    ): {
        "transport_route":
            "work_by_openalex_id",

        "identifier_namespace":
            "openalex",
    },

    (
        "openalex",
        "exact_doi",
    ): {
        "transport_route":
            "work_by_doi",

        "identifier_namespace":
            "doi",
    },
}


def sha256_file(
    path: Path,
) -> str:

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def canonical_hash(
    value,
) -> str:

    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode(
            "utf-8"
        )
    ).hexdigest()


def read_tsv(
    path: Path,
):

    with path.open(
        encoding="utf-8",
        newline="",
    ) as fh:

        reader = csv.DictReader(
            fh,
            delimiter="\t",
        )

        if reader.fieldnames is None:
            raise RuntimeError(
                f"missing TSV header: {path}"
            )

        return (
            list(
                reader.fieldnames
            ),
            list(
                reader
            ),
        )


def write_tsv(
    path: Path,
    fields,
    rows,
):

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:

        writer = csv.DictWriter(
            fh,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(
            rows
        )


def write_json(
    path: Path,
    value,
):

    path.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


# ============================================================
# Repository / source preconditions.
# ============================================================

head = subprocess.check_output(
    [
        "git",
        "rev-parse",
        "HEAD",
    ],
    text=True,
).strip()

if head != EXPECTED_HEAD:
    raise RuntimeError(
        "wrong amendment parent HEAD: "
        + head
    )


if subprocess.run(
    [
        "git",
        "diff",
        "--quiet",
    ],
).returncode != 0:

    raise RuntimeError(
        "tracked working tree dirty"
    )


if subprocess.run(
    [
        "git",
        "diff",
        "--cached",
        "--quiet",
    ],
).returncode != 0:

    raise RuntimeError(
        "staging area not empty"
    )


expected_hashes = {
    INPUT:
        EXPECTED_INPUT_SHA256,

    BASE_DESIGN:
        EXPECTED_BASE_DESIGN_SHA256,

    BASE_MANIFEST:
        EXPECTED_BASE_MANIFEST_SHA256,

    OFFLINE_RUNNER:
        EXPECTED_OFFLINE_RUNNER_SHA256,

    OFFLINE_RESOLUTION:
        EXPECTED_OFFLINE_RESOLUTION_SHA256,

    OFFLINE_NORMALIZED:
        EXPECTED_OFFLINE_NORMALIZED_SHA256,

    OFFLINE_NETWORK:
        EXPECTED_OFFLINE_NETWORK_SHA256,

    OFFLINE_SUMMARY:
        EXPECTED_OFFLINE_SUMMARY_SHA256,

    OFFLINE_PROVENANCE:
        EXPECTED_OFFLINE_PROVENANCE_SHA256,

    CACHE_CHECKSUMS:
        EXPECTED_CACHE_CHECKSUMS_SHA256,

    NORMALIZER:
        EXPECTED_NORMALIZER_SHA256,
}


for path, expected in expected_hashes.items():

    observed = sha256_file(
        path
    )

    if observed != expected:

        raise RuntimeError(
            f"hash mismatch: {path}: "
            f"{observed} != {expected}"
        )


base_design = json.loads(
    BASE_DESIGN.read_text(
        encoding="utf-8"
    )
)


if (
    base_design[
        "authorization_contract"
    ][
        "maximum_request_count"
    ]
    != 12162
):
    raise RuntimeError(
        "unexpected base request ceiling"
    )


if (
    base_design[
        "wave_a"
    ][
        "request_manifest"
    ][
        "sha256"
    ]
    != EXPECTED_BASE_MANIFEST_SHA256
):
    raise RuntimeError(
        "unexpected base Wave A manifest binding"
    )


if (
    base_design[
        "transport_contract"
    ][
        "transport_sources"
    ]
    != EXPECTED_TRANSPORT_SOURCES
):
    raise RuntimeError(
        "base transport source contract differs"
    )


if (
    base_design[
        "frozen_source_hashes"
    ][
        "transport_evidence_adapter"
    ][
        "sha256"
    ]
    != EXPECTED_ADAPTER_SHA256
):
    raise RuntimeError(
        "base adapter hash differs"
    )


# ============================================================
# Verify historical cache checksum boundary using the actual
# checksum-root-relative path convention.
# ============================================================

checksum_entries = {}

for raw in CACHE_CHECKSUMS.read_text(
    encoding="utf-8"
).splitlines():

    raw = raw.strip()

    if not raw:
        continue

    digest, value = raw.split(
        None,
        1,
    )

    value = value.strip()

    if value.startswith("*"):
        value = value[1:]

    while value.startswith("./"):
        value = value[2:]

    if value in checksum_entries:
        raise RuntimeError(
            "duplicate historical checksum path: "
            + value
        )

    checksum_entries[
        value
    ] = digest


if len(checksum_entries) != 8666:
    raise RuntimeError(
        "historical checksum entry count != 8666"
    )


_, provenance_rows = read_tsv(
    OFFLINE_PROVENANCE
)

if len(provenance_rows) != 15:
    raise RuntimeError(
        "offline provenance count != 15"
    )


for row in provenance_rows:

    if row[
        "provider"
    ] != "openalex":
        raise RuntimeError(
            "unexpected cached provider"
        )

    if row[
        "matching_archive_count"
    ] != "1":
        raise RuntimeError(
            "offline archive selection not unique"
        )

    if (
        row[
            "source_body_sha256"
        ]
        != row[
            "selected_body_sha256"
        ]
    ):
        raise RuntimeError(
            "selected source/body SHA mismatch"
        )

    for path_field, hash_field in (
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

        path = Path(
            row[
                path_field
            ]
        )

        expected = row[
            hash_field
        ]

        if not path.is_file():
            raise RuntimeError(
                "missing selected historical cache file: "
                + str(
                    path
                )
            )

        if (
            sha256_file(
                path
            )
            != expected
        ):
            raise RuntimeError(
                "selected historical cache file hash mismatch: "
                + str(
                    path
                )
            )

        resolved = path.resolve()

        try:
            relative = resolved.relative_to(
                CACHE_ROOT.resolve()
            )
        except ValueError as exc:
            raise RuntimeError(
                "selected historical cache file outside "
                "metadata-resolution archive: "
                + str(
                    path
                )
            ) from exc

        manifest_key = str(
            relative
        )

        if manifest_key not in checksum_entries:
            raise RuntimeError(
                "selected historical cache file absent "
                "from checksum manifest: "
                + manifest_key
            )

        if (
            checksum_entries[
                manifest_key
            ]
            != expected
        ):
            raise RuntimeError(
                "historical checksum manifest disagreement: "
                + manifest_key
            )

        if (
            "triage_validation_v1"
            in path.parts
        ):
            raise RuntimeError(
                "blind-validation archive entered cache provenance"
            )

        if (
            "pre_review_triage_future_text_retrieval_v1"
            in path.parts
        ):
            raise RuntimeError(
                "future retrieval archive entered cache provenance"
            )


# ============================================================
# Validate exact offline / network partition.
# ============================================================

_, input_rows = read_tsv(
    INPUT
)

_, base_rows = read_tsv(
    BASE_MANIFEST
)

_, resolution_rows = read_tsv(
    OFFLINE_RESOLUTION
)

_, normalized_rows = read_tsv(
    OFFLINE_NORMALIZED
)

_, network_rows = read_tsv(
    OFFLINE_NETWORK
)


if len(input_rows) != 12162:
    raise RuntimeError(
        "input count != 12162"
    )

if len(base_rows) != 12162:
    raise RuntimeError(
        "base Wave A count != 12162"
    )

if len(resolution_rows) != 12162:
    raise RuntimeError(
        "offline resolution count != 12162"
    )

if len(normalized_rows) != 14:
    raise RuntimeError(
        "offline normalized count != 14"
    )

if len(network_rows) != 12147:
    raise RuntimeError(
        "network requirement count != 12147"
    )


resolution_counts = Counter(
    row[
        "offline_resolution_status"
    ]
    for row in resolution_rows
)

expected_resolution_counts = Counter({
    "cached_sources_no_usable_abstract":
        1,

    "requires_openalex_lookup":
        3608,

    "requires_pubmed_lookup":
        8539,

    "resolved_cached_openalex":
        14,
})

if (
    resolution_counts
    != expected_resolution_counts
):
    raise RuntimeError(
        "offline resolution counts differ"
    )


route_counts = Counter(
    (
        row[
            "provider"
        ],
        row[
            "route"
        ],
    )
    for row in network_rows
)

expected_route_counts = Counter({
    (
        "openalex",
        "exact_doi",
    ):
        34,

    (
        "openalex",
        "exact_work_id",
    ):
        3574,

    (
        "pubmed",
        "exact_pmid_efetch",
    ):
        8539,
})

if route_counts != expected_route_counts:
    raise RuntimeError(
        "network route counts differ"
    )


base_by_index = {
    row[
        "retrieval_record_index"
    ]:
        row
    for row in base_rows
}

if len(base_by_index) != 12162:
    raise RuntimeError(
        "base retrieval indices not unique"
    )


network_indices = {
    row[
        "retrieval_record_index"
    ]
    for row in network_rows
}

if len(network_indices) != 12147:
    raise RuntimeError(
        "network retrieval indices not unique"
    )


terminal_offline_rows = [
    row
    for row in resolution_rows
    if not row[
        "next_network_route"
    ].strip()
]

terminal_offline_indices = {
    row[
        "retrieval_record_index"
    ]
    for row in terminal_offline_rows
}

if len(terminal_offline_indices) != 15:
    raise RuntimeError(
        "terminal offline count != 15"
    )


if (
    network_indices
    & terminal_offline_indices
):
    raise RuntimeError(
        "offline/network partition overlaps"
    )


if (
    network_indices
    | terminal_offline_indices
) != set(
    base_by_index
):
    raise RuntimeError(
        "offline/network partition does not cover "
        "the 12,162-row base manifest"
    )


# Network row ordering must be exactly base-manifest ordering
# with the 15 terminal-offline rows removed.
network_signature = [
    (
        row[
            "retrieval_record_index"
        ],
        row[
            "screening_entity_id"
        ],
        row[
            "provider"
        ],
        row[
            "route"
        ],
        row[
            "identifier"
        ],
    )
    for row in network_rows
]

filtered_base_signature = [
    (
        row[
            "retrieval_record_index"
        ],
        row[
            "screening_entity_id"
        ],
        row[
            "provider"
        ],
        row[
            "frozen_route"
        ],
        row[
            "identifier"
        ],
    )
    for row in base_rows
    if row[
        "retrieval_record_index"
    ] in network_indices
]

if (
    network_signature
    != filtered_base_signature
):
    raise RuntimeError(
        "network requirements are not the exact "
        "ordered base-manifest subset"
    )


provenance_by_index = {
    row[
        "retrieval_record_index"
    ]:
        row
    for row in provenance_rows
}

if set(
    provenance_by_index
) != terminal_offline_indices:
    raise RuntimeError(
        "selected cache provenance does not exactly "
        "cover terminal-offline rows"
    )


for row in terminal_offline_rows:

    index = row[
        "retrieval_record_index"
    ]

    provenance = provenance_by_index[
        index
    ]

    for left, right in (
        (
            row[
                "offline_resolution_status"
            ],
            provenance[
                "offline_resolution_status"
            ],
        ),
        (
            row[
                "chosen_provider"
            ],
            provenance[
                "provider"
            ],
        ),
        (
            row[
                "chosen_lookup_type"
            ],
            provenance[
                "chosen_lookup_type"
            ],
        ),
        (
            row[
                "chosen_logical_lookup_id"
            ],
            provenance[
                "logical_lookup_id"
            ],
        ),
        (
            row[
                "chosen_source_body_sha256"
            ],
            provenance[
                "source_body_sha256"
            ],
        ),
    ):

        if left != right:
            raise RuntimeError(
                "resolution/provenance disagreement "
                "at retrieval index "
                + index
            )


resolved_usable_indices = {
    row[
        "retrieval_record_index"
    ]
    for row in resolution_rows
    if row[
        "offline_resolution_status"
    ] == "resolved_cached_openalex"
}

normalized_indices = {
    row[
        "retrieval_record_index"
    ]
    for row in normalized_rows
}

if (
    normalized_indices
    != resolved_usable_indices
):
    raise RuntimeError(
        "cached normalized rows do not exactly equal "
        "resolved cached OpenAlex rows"
    )


# ============================================================
# Build corrected Wave A manifest from the frozen network
# requirements, preserving order and regenerating sequence-
# dependent request identities.
# ============================================================

wave_fields = [
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


wave_rows = []

for sequence, row in enumerate(
    network_rows,
    start=1,
):

    key = (
        row[
            "provider"
        ],
        row[
            "route"
        ],
    )

    mapping = ROUTE_MAP.get(
        key
    )

    if mapping is None:
        raise RuntimeError(
            "unsupported corrected Wave A route: "
            + repr(
                key
            )
        )


    identity = {
        "wave_id":
            WAVE_ID,

        "request_sequence":
            sequence,

        "retrieval_record_index":
            int(
                row[
                    "retrieval_record_index"
                ]
            ),

        "screening_entity_id":
            row[
                "screening_entity_id"
            ],

        "provider":
            row[
                "provider"
            ],

        "frozen_route":
            row[
                "route"
            ],

        "transport_route":
            mapping[
                "transport_route"
            ],

        "identifier_namespace":
            mapping[
                "identifier_namespace"
            ],

        "identifier":
            row[
                "identifier"
            ],
    }


    wave_rows.append({
        "wave_id":
            identity[
                "wave_id"
            ],

        "request_sequence":
            str(
                identity[
                    "request_sequence"
                ]
            ),

        "retrieval_record_index":
            str(
                identity[
                    "retrieval_record_index"
                ]
            ),

        "screening_entity_id":
            identity[
                "screening_entity_id"
            ],

        "provider":
            identity[
                "provider"
            ],

        "frozen_route":
            identity[
                "frozen_route"
            ],

        "transport_route":
            identity[
                "transport_route"
            ],

        "identifier_namespace":
            identity[
                "identifier_namespace"
            ],

        "identifier":
            identity[
                "identifier"
            ],

        "request_identity_sha256":
            canonical_hash(
                identity
            ),
    })


if len(wave_rows) != 12147:
    raise RuntimeError(
        "corrected Wave A count != 12147"
    )


if [
    int(
        row[
            "request_sequence"
        ]
    )
    for row in wave_rows
] != list(
    range(
        1,
        12148,
    )
):
    raise RuntimeError(
        "corrected request sequence not contiguous"
    )


if len({
    row[
        "request_identity_sha256"
    ]
    for row in wave_rows
}) != 12147:
    raise RuntimeError(
        "corrected request identities not unique"
    )


write_tsv(
    AMENDED_MANIFEST,
    wave_fields,
    wave_rows,
)

amended_manifest_sha256 = sha256_file(
    AMENDED_MANIFEST
)


# ============================================================
# Freeze Amendment 001.
# ============================================================

amendment = {
    "amendment_id":
        (
            "PRE_REVIEW_TRIAGE_FUTURE_TEXT_"
            "LIVE_RETRIEVAL_V1_AMENDMENT_001"
        ),

    "schema_version":
        1,

    "status":
        "FROZEN_PRE_IMPLEMENTATION",

    "parent_commit":
        EXPECTED_HEAD,

    "amends": {
        "commit":
            EXPECTED_HEAD,

        "design_path":
            str(
                BASE_DESIGN
            ),

        "design_sha256":
            EXPECTED_BASE_DESIGN_SHA256,
    },

    "reason":
        (
            "The base future live-retrieval freeze promoted "
            "all 12,162 supported future records directly "
            "into live Wave A and omitted the pre-Wave-A "
            "offline-cache partition used by the frozen "
            "development retrieval workflow. Reapplying "
            "the same exact-cache semantics resolves 15 "
            "records without live network and leaves "
            "12,147 exact Wave A requests."
        ),

    "historical_base_wave_a": {
        "path":
            str(
                BASE_MANIFEST
            ),

        "rows":
            12162,

        "sha256":
            EXPECTED_BASE_MANIFEST_SHA256,

        "execution_status":
            "SUPERSEDED_BY_AMENDMENT_001",
    },

    "offline_partition": {
        "input_rows":
            12162,

        "terminal_without_network":
            15,

        "cached_usable_openalex":
            14,

        "cached_sources_no_usable_abstract":
            1,

        "network_requirement_rows":
            12147,

        "resolution_status_counts":
            dict(
                sorted(
                    resolution_counts.items()
                )
            ),

        "network_route_counts": {
            "openalex_exact_doi":
                34,

            "openalex_exact_work_id":
                3574,

            "pubmed_exact_pmid_efetch":
                8539,
        },
    },

    "historical_cache_dependency": {
        "root":
            str(
                CACHE_ROOT
            ),

        "checksum_path_convention":
            "checksum_root_relative",

        "checksum_manifest": {
            "path":
                str(
                    CACHE_CHECKSUMS
                ),

            "entry_count":
                8666,

            "sha256":
                EXPECTED_CACHE_CHECKSUMS_SHA256,
        },

        "selected_lookup_count":
            15,

        "selected_archive_file_count":
            45,

        "selected_cache_provenance": {
            "path":
                str(
                    OFFLINE_PROVENANCE
                ),

            "sha256":
                EXPECTED_OFFLINE_PROVENANCE_SHA256,
        },

        "multiple_equivalent_archive_matches":
            0,
    },

    "corrected_wave_a": {
        "wave_id":
            WAVE_ID,

        "maximum_request_count":
            12147,

        "request_counts": {
            "openalex_exact_doi":
                34,

            "openalex_exact_work_id":
                3574,

            "pubmed_exact_pmid_efetch":
                8539,

            "total":
                12147,
        },

        "request_manifest": {
            "path":
                str(
                    AMENDED_MANIFEST
                ),

            "rows":
                12147,

            "sha256":
                amended_manifest_sha256,
        },

        "execution_order":
            "ascending request_sequence",

        "execution_output_root":
            (
                "results/07_comparative_landscape/"
                "pre_review_triage_future_text_retrieval_v1/"
                "live_wave_a"
            ),
    },

    "frozen_source_hashes": {
        "input_manifest": {
            "path":
                str(
                    INPUT
                ),

            "sha256":
                EXPECTED_INPUT_SHA256,
        },

        "future_offline_runner": {
            "path":
                str(
                    OFFLINE_RUNNER
                ),

            "sha256":
                EXPECTED_OFFLINE_RUNNER_SHA256,
        },

        "normalizer": {
            "path":
                str(
                    NORMALIZER
                ),

            "sha256":
                EXPECTED_NORMALIZER_SHA256,
        },

        "transport_evidence_adapter": {
            "path":
                base_design[
                    "frozen_source_hashes"
                ][
                    "transport_evidence_adapter"
                ][
                    "path"
                ],

            "sha256":
                EXPECTED_ADAPTER_SHA256,
        },

        "transport_sources":
            EXPECTED_TRANSPORT_SOURCES,

        "offline_cache_resolution": {
            "path":
                str(
                    OFFLINE_RESOLUTION
                ),

            "sha256":
                EXPECTED_OFFLINE_RESOLUTION_SHA256,
        },

        "offline_cached_normalized_text": {
            "path":
                str(
                    OFFLINE_NORMALIZED
                ),

            "sha256":
                EXPECTED_OFFLINE_NORMALIZED_SHA256,
        },

        "offline_network_requirements": {
            "path":
                str(
                    OFFLINE_NETWORK
                ),

            "sha256":
                EXPECTED_OFFLINE_NETWORK_SHA256,
        },

        "offline_cache_summary": {
            "path":
                str(
                    OFFLINE_SUMMARY
                ),

            "sha256":
                EXPECTED_OFFLINE_SUMMARY_SHA256,
        },

        "offline_selected_cache_provenance": {
            "path":
                str(
                    OFFLINE_PROVENANCE
                ),

            "sha256":
                EXPECTED_OFFLINE_PROVENANCE_SHA256,
        },
    },

    "replaces": {
        "authorization_contract.maximum_request_count": {
            "base":
                12162,

            "amended":
                12147,
        },

        "implementation_gate.request_count_ceiling": {
            "base":
                12162,

            "amended":
                12147,
        },

        "wave_a.request_counts": {
            "base": {
                "openalex_exact_doi":
                    47,

                "openalex_exact_work_id":
                    3576,

                "pubmed_exact_pmid_efetch":
                    8539,

                "total":
                    12162,
            },

            "amended": {
                "openalex_exact_doi":
                    34,

                "openalex_exact_work_id":
                    3574,

                "pubmed_exact_pmid_efetch":
                    8539,

                "total":
                    12147,
            },
        },

        "wave_a.request_manifest": {
            "base_path":
                str(
                    BASE_MANIFEST
                ),

            "base_sha256":
                EXPECTED_BASE_MANIFEST_SHA256,

            "amended_path":
                str(
                    AMENDED_MANIFEST
                ),

            "amended_sha256":
                amended_manifest_sha256,
        },

        "offline_partition": {
            "base":
                "OMITTED",

            "amended":
                "REQUIRED_AND_FROZEN",
        },
    },

    "authorization_contract_amendment": {
        "explicit_human_authorization_required":
            True,

        "authorization_created_by_this_amendment":
            False,

        "network_authority_created_by_this_amendment":
            False,

        "execution_authority_created_by_this_amendment":
            False,

        "maximum_request_count":
            12147,

        "future_authorization_must_bind": [
            "wave_id",
            "amended_wave_a_request_manifest_sha256",
            "amendment_design_sha256",
            "base_design_sha256",
            "design_parent_commit",
            "authorized_execution_commit",
            "normalizer_sha256",
            "transport_source_hashes",
            "maximum_request_count",
            "execution_output_root",
        ],
    },

    "unchanged_base_contract": {
        "supported_future_input_rows":
            12162,

        "input_manifest_sha256":
            EXPECTED_INPUT_SHA256,

        "wave_id":
            WAVE_ID,

        "transport_semantics_changed":
            False,

        "normalizer_semantics_changed":
            False,

        "execution_output_root_changed":
            False,

        "wave_b_authorized":
            False,
    },

    "implementation_gate": {
        "next_gate":
            (
                "REGENERATE_AND_HOSTILE_TEST_FUTURE_WAVE_A_"
                "GUARD_RUNNER_AND_ENTRYPOINT_AGAINST_"
                "AMENDMENT_001_WITHOUT_NETWORK"
            ),

        "requirements": [
            (
                "future guard binds Amendment 001 rather than "
                "the superseded base design as execution authority"
            ),
            (
                "future guard binds the amended 12,147-row "
                "request manifest"
            ),
            (
                "future guard maximum request count is exactly "
                "12,147"
            ),
            (
                "future guard verifies the frozen offline "
                "partition and selected-cache provenance"
            ),
            (
                "request outside amended manifest fails closed"
            ),
            (
                "authorization absent fails closed before network"
            ),
            (
                "all hostile implementation tests perform zero "
                "real network requests"
            ),
            (
                "completed development retrieval artifacts "
                "remain untouched"
            ),
        ],
    },

    "human_gate_after_implementation": {
        "next_gate":
            (
                "COMMIT_CORRECTED_FUTURE_WAVE_A_IMPLEMENTATION_"
                "THEN_STOP_FOR_EXPLICIT_HUMAN_AUTHORIZATION"
            ),

        "real_authorization_creation_permitted_before_that_gate":
            False,

        "real_network_execution_permitted_before_that_gate":
            False,
    },

    "scientific_boundary": {
        "automated_exclusion_authorized":
            False,

        "blind_validation_sample_in_scope":
            False,

        "blind_validation_scientific_content_authorized":
            False,

        "future_universe_scoring_authorized":
            False,

        "model_fitting_authorized":
            False,

        "production_screening_protocol_changed":
            False,

        "scientific_screening_decisions_authorized":
            False,

        "threshold_selection_authorized":
            False,
    },
}


write_json(
    AMEND_DESIGN,
    amendment,
)


AMEND_DOC.write_text(
    f"""# Pre-review triage future text live retrieval v1 — Amendment 001

Status: `FROZEN_PRE_IMPLEMENTATION`

This amendment corrects the pre-Wave-A authority boundary frozen in
commit `{EXPECTED_HEAD}`.

The supported future input manifest remains unchanged at 12,162 rows.

The base freeze incorrectly promoted all 12,162 records directly into
live Wave A. Reapplication of the frozen development offline-cache
semantics gives the exact partition:

- 14 records resolved from cached usable OpenAlex abstracts
- 1 record terminal from cached sources with no usable abstract
- 12,147 records requiring live Wave A lookup

The original 12,162-row Wave A manifest is retained byte-identically
as historical evidence but is superseded for execution authority.

Corrected Wave A:

- PubMed exact PMID EFetch: 8,539
- OpenAlex exact Work ID: 3,574
- OpenAlex exact DOI: 34
- Total live requests: 12,147

Corrected request manifest:

`{AMENDED_MANIFEST}`

SHA256:

`{amended_manifest_sha256}`

The 15 terminal-offline records are pinned through
`offline_selected_cache_provenance.tsv`. Their 45 selected terminal,
response-metadata and response-body files were independently verified
against the frozen 8,666-entry historical metadata-resolution checksum
manifest using paths relative to that checksum-manifest root.

This amendment creates no network authority and no execution authority.
It authorizes no model fitting, future scoring, threshold selection,
scientific screening decision, blind-validation scientific-content use,
or production mutation.

The next gate is to regenerate and hostile-test the future Wave A guard,
runner core and live entrypoint against Amendment 001 with real network
access disabled. A separate explicit human authorization may be created
only after that corrected implementation is committed.
""",
    encoding="utf-8",
    newline="\n",
)


checksum_paths = [
    AMEND_FREEZE,
    AMEND_DESIGN,
    AMEND_DOC,
    OFFLINE_RUNNER,
    INPUT,
    OFFLINE_RESOLUTION,
    OFFLINE_NORMALIZED,
    OFFLINE_NETWORK,
    OFFLINE_SUMMARY,
    OFFLINE_PROVENANCE,
    AMENDED_MANIFEST,
    BASE_DESIGN,
    BASE_MANIFEST,
    CACHE_CHECKSUMS,
    NORMALIZER,
]


with AMEND_SHA.open(
    "w",
    encoding="utf-8",
    newline="\n",
) as fh:

    for path in checksum_paths:

        fh.write(
            sha256_file(
                path
            )
            + "  "
            + str(
                path
            )
            + "\n"
        )


print(
    "PASS | Amendment 001 frozen"
)

print(
    "corrected_wave_a_rows =",
    len(
        wave_rows
    ),
)

print(
    "corrected_wave_a_sha256 =",
    amended_manifest_sha256,
)

print(
    "amendment_design_sha256 =",
    sha256_file(
        AMEND_DESIGN
    ),
)

print(
    "future_offline_runner_sha256 =",
    EXPECTED_OFFLINE_RUNNER_SHA256,
)

print(
    "NO NETWORK AUTHORITY CREATED"
)

print(
    "NO EXECUTION AUTHORITY CREATED"
)
