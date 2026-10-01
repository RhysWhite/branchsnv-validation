from __future__ import annotations

from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import subprocess
import sys


ROOT = Path("experiments/07_comparative_landscape")

RROOT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_text_retrieval_v1"
)

EXPECTED_PARENT = (
    "3047e7b1aef8d479bd988a8779890877d056a173"
)

ORIGINAL_DESIGN = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_design.json"
)

ORIGINAL_DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_TEXT_RECONCILIATION_V1.md"
)

WAVE_A_MANIFEST = (
    RROOT
    / "live_wave_a_request_manifest_amendment_001.tsv"
)

WAVE_B_MANIFEST = (
    RROOT
    / "live_wave_b_request_manifest.tsv"
)

WAVE_A_RAW = (
    RROOT
    / "live_wave_a"
    / "raw"
)

FREEZE = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_001_freeze.py"
)

DESIGN = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_001_design.json"
)

DOCUMENT = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_TEXT_RECONCILIATION_V1_AMENDMENT_001.md"
)

CHECKSUM = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_001.sha256"
)

AMENDMENT_PATHS = {
    str(FREEZE),
    str(DESIGN),
    str(DOCUMENT),
    str(CHECKSUM),
}

PLANNED_OUTPUTS = [
    RROOT / "reconciled_resolution.tsv",
    RROOT / "reconciled_normalized_text.tsv",
    RROOT / "reconciliation_summary.json",
    RROOT / "reconciliation_outputs.sha256",
]

TERMINAL_BODY_SHA = (
    "e9639e3c4681ce85f852fbac48e2eeee"
    "5ba51296dbfec57c200d59b76237ab80"
)

DIRECT_OPENALEX_NOT_FOUND = [
    {
        "request_sequence": 2419,
        "retrieval_record_index": 2421,
        "screening_entity_id":
            "publication_component:citation:publication:"
            "doi:10.1101/2021.07.06.451309",
        "provider": "openalex",
        "frozen_route": "exact_work_id",
        "transport_route": "work_by_openalex_id",
        "identifier_namespace": "openalex",
        "identifier": "W3178074861",
        "request_identity_sha256":
            "acd79717e2e4558b3f467bb1cf89b89f"
            "415e21a620c1ae532e1583729027bec9",
    },
    {
        "request_sequence": 2601,
        "retrieval_record_index": 2603,
        "screening_entity_id":
            "publication_component:citation:publication:"
            "doi:10.1101/2022.03.22.485370",
        "provider": "openalex",
        "frozen_route": "exact_work_id",
        "transport_route": "work_by_openalex_id",
        "identifier_namespace": "openalex",
        "identifier": "W4229018387",
        "request_identity_sha256":
            "fadf1cec71ce8478d07d272b051702682"
            "2cb36b18a04965ac0669a3896e52fe7",
    },
    {
        "request_sequence": 3090,
        "retrieval_record_index": 3092,
        "screening_entity_id":
            "publication_component:citation:publication:"
            "doi:10.1101/2024.09.24.614677",
        "provider": "openalex",
        "frozen_route": "exact_work_id",
        "transport_route": "work_by_openalex_id",
        "identifier_namespace": "openalex",
        "identifier": "W4402860352",
        "request_identity_sha256":
            "69ff31100bda0385812658c4492d2d9de"
            "a3e42b81bec1297963cf3fd96121b4d",
    },
    {
        "request_sequence": 3346,
        "retrieval_record_index": 3348,
        "screening_entity_id":
            "publication_component:citation:publication:"
            "doi:10.1101/289488",
        "provider": "openalex",
        "frozen_route": "exact_work_id",
        "transport_route": "work_by_openalex_id",
        "identifier_namespace": "openalex",
        "identifier": "W2951692545",
        "request_identity_sha256":
            "f770f8aa2532862481d2e775ea236b43f"
            "8937537cc49b338227db434aa3ce0e2",
    },
    {
        "request_sequence": 3490,
        "retrieval_record_index": 3492,
        "screening_entity_id":
            "publication_component:citation:publication:"
            "doi:10.1101/627182",
        "provider": "openalex",
        "frozen_route": "exact_work_id",
        "transport_route": "work_by_openalex_id",
        "identifier_namespace": "openalex",
        "identifier": "W2942922667",
        "request_identity_sha256":
            "aed68de1a6345a9087a4af384e41cfec"
            "125697a8210f6a5e0265bfb047acdd0e",
    },
    {
        "request_sequence": 3533,
        "retrieval_record_index": 3535,
        "screening_entity_id":
            "publication_component:citation:publication:"
            "doi:10.1101/735175",
        "provider": "openalex",
        "frozen_route": "exact_work_id",
        "transport_route": "work_by_openalex_id",
        "identifier_namespace": "openalex",
        "identifier": "W2967995881",
        "request_identity_sha256":
            "f37055e23f791ea5d0bd4fca1db269bb"
            "114e0b7e03f214e7d54cd6f0b1bd30bb",
    },
    {
        "request_sequence": 4733,
        "retrieval_record_index": 4738,
        "screening_entity_id":
            "publication_component:citation:publication:"
            "doi:10.11234/jsbibr.2021.7",
        "provider": "openalex",
        "frozen_route": "exact_doi",
        "transport_route": "work_by_doi",
        "identifier_namespace": "doi",
        "identifier": "10.11234/jsbibr.2021.7",
        "request_identity_sha256":
            "bd240e8a7cc2950fb78ba007b52aca5b"
            "ff4e8703c7da9f97c83ff072c27beb62",
    },
    {
        "request_sequence": 4734,
        "retrieval_record_index": 4739,
        "screening_entity_id":
            "publication_component:citation:publication:"
            "doi:10.11234/jsbibr.2023.primer2",
        "provider": "openalex",
        "frozen_route": "exact_doi",
        "transport_route": "work_by_doi",
        "identifier_namespace": "doi",
        "identifier": "10.11234/jsbibr.2023.primer2",
        "request_identity_sha256":
            "842a42e6cf9fc0cb4cbf73c0e45f3ab5"
            "1b95c2a8e911ed9948f37a0b2e9238ee",
    },
    {
        "request_sequence": 5274,
        "retrieval_record_index": 5283,
        "screening_entity_id":
            "publication_component:citation:publication:"
            "doi:10.1175/1520-0493(1950)078<0001:vofeit>2.0.co",
        "provider": "openalex",
        "frozen_route": "exact_doi",
        "transport_route": "work_by_doi",
        "identifier_namespace": "doi",
        "identifier":
            "10.1175/1520-0493(1950)078<0001:vofeit>2.0.co",
        "request_identity_sha256":
            "7009562635806d1eef211417f51d8b582"
            "e7a40999731e5dfa6cf58afd4b5150b",
    },
    {
        "request_sequence": 11047,
        "retrieval_record_index": 11061,
        "screening_entity_id":
            "publication_component:database:publication:"
            "doi:10.1101/2021.02.02.429486",
        "provider": "openalex",
        "frozen_route": "exact_work_id",
        "transport_route": "work_by_openalex_id",
        "identifier_namespace": "openalex",
        "identifier": "W3127954829",
        "request_identity_sha256":
            "7029dcc7eb15499a986d8f2640e1e573"
            "53fbfec3832675b1e8c49d148a0b7adc",
    },
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        text=True,
    ).strip()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        return list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


def repository_position() -> str:
    head = git("rev-parse", "HEAD")

    if head == EXPECTED_PARENT:
        return "PRE_COMMIT_PARENT"

    parent = git("rev-parse", "HEAD^")

    if parent != EXPECTED_PARENT:
        raise RuntimeError(
            "Repository is neither expected parent nor "
            "its direct amendment-freeze child"
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
        if line.strip()
    }

    if changed != AMENDMENT_PATHS:
        raise RuntimeError(
            "Committed amendment path set differs"
        )

    return "COMMITTED_FREEZE"


def validate_dependencies() -> dict:
    if git(
        "status",
        "--porcelain",
        "--untracked-files=no",
    ):
        raise RuntimeError(
            "Tracked working tree is not clean"
        )

    if not ORIGINAL_DESIGN.is_file():
        raise RuntimeError(
            "Original reconciliation design missing"
        )

    if not ORIGINAL_DOC.is_file():
        raise RuntimeError(
            "Original reconciliation document missing"
        )

    for path in PLANNED_OUTPUTS:
        if path.exists():
            raise RuntimeError(
                "Canonical reconciliation output already exists: "
                + str(path)
            )

    design = json.loads(
        ORIGINAL_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if design.get("status") != "FROZEN_PRE_IMPLEMENTATION":
        raise RuntimeError(
            "Original design status changed"
        )

    population = design.get(
        "known_structural_population",
        {}
    )

    if population.get("future_input_rows") != 12162:
        raise RuntimeError(
            "Future input population changed"
        )

    if population.get("future_wave_a_request_rows") != 12147:
        raise RuntimeError(
            "Wave-A request population changed"
        )

    if population.get("future_wave_b_fallback_rows") != 40:
        raise RuntimeError(
            "Wave-B fallback population changed"
        )

    if not WAVE_A_MANIFEST.is_file():
        raise RuntimeError(
            "Amended Wave-A manifest missing"
        )

    manifest_rows = read_tsv(
        WAVE_A_MANIFEST
    )

    manifest_by_sequence = {
        int(row["request_sequence"]): row
        for row in manifest_rows
    }

    if len(manifest_by_sequence) != 12147:
        raise RuntimeError(
            "Amended Wave-A manifest cardinality changed"
        )

    observed_direct_not_found = {}

    terminals = sorted(
        WAVE_A_RAW.rglob("terminal.json")
    )

    if len(terminals) != 12146:
        raise RuntimeError(
            "Ordinary Wave-A terminal count changed"
        )

    status_counts = Counter()
    provider_counts = Counter()

    for terminal_path in terminals:
        terminal = json.loads(
            terminal_path.read_text(
                encoding="utf-8"
            )
        )

        status = terminal.get(
            "terminal_status"
        )

        provider = terminal.get(
            "provider"
        )

        status_counts[
            status
        ] += 1

        provider_counts[
            provider
        ] += 1

        if (
            provider == "openalex"
            and status == "not_found"
        ):
            logical_id = terminal.get(
                "logical_lookup_id",
                "",
            )

            parts = logical_id.split(":")

            if len(parts) != 3:
                raise RuntimeError(
                    "Malformed OpenAlex not-found logical ID"
                )

            sequence = int(parts[1])

            observed_direct_not_found[
                sequence
            ] = (
                terminal_path,
                terminal,
            )

    if status_counts != Counter({
        "success": 12134,
        "not_found": 12,
    }):
        raise RuntimeError(
            "Wave-A terminal status population changed: "
            + repr(status_counts)
        )

    if provider_counts != Counter({
        "pubmed": 8538,
        "openalex": 3608,
    }):
        raise RuntimeError(
            "Wave-A provider population changed: "
            + repr(provider_counts)
        )

    expected_sequences = {
        item["request_sequence"]
        for item in DIRECT_OPENALEX_NOT_FOUND
    }

    if (
        set(observed_direct_not_found)
        != expected_sequences
    ):
        raise RuntimeError(
            "Direct OpenAlex not-found sequence set changed"
        )

    frozen_rows = []

    manifest_keys = [
        "retrieval_record_index",
        "screening_entity_id",
        "provider",
        "frozen_route",
        "transport_route",
        "identifier_namespace",
        "identifier",
        "request_identity_sha256",
    ]

    for item in DIRECT_OPENALEX_NOT_FOUND:
        sequence = item[
            "request_sequence"
        ]

        row = manifest_by_sequence.get(
            sequence
        )

        if row is None:
            raise RuntimeError(
                f"Wave-A manifest row missing: {sequence}"
            )

        for key in manifest_keys:
            expected = str(
                item[key]
            )

            if row.get(key) != expected:
                raise RuntimeError(
                    f"Wave-A manifest mismatch at "
                    f"sequence {sequence}: {key}"
                )

        terminal_path, terminal = (
            observed_direct_not_found[
                sequence
            ]
        )

        if terminal.get(
            "provider"
        ) != "openalex":
            raise RuntimeError(
                f"Provider changed at {sequence}"
            )

        if terminal.get(
            "terminal_status"
        ) != "not_found":
            raise RuntimeError(
                f"Terminal status changed at {sequence}"
            )

        if terminal.get(
            "identifier"
        ) != item[
            "identifier"
        ]:
            raise RuntimeError(
                f"Identifier changed at {sequence}"
            )

        if terminal.get(
            "identifier_namespace"
        ) != item[
            "identifier_namespace"
        ]:
            raise RuntimeError(
                f"Identifier namespace changed at {sequence}"
            )

        if terminal.get(
            "route"
        ) != item[
            "transport_route"
        ]:
            raise RuntimeError(
                f"Transport route changed at {sequence}"
            )

        if terminal.get(
            "terminal_body_sha256"
        ) != TERMINAL_BODY_SHA:
            raise RuntimeError(
                f"Terminal body SHA changed at {sequence}"
            )

        attempts = terminal.get(
            "attempts"
        )

        if (
            not isinstance(attempts, list)
            or len(attempts) < 1
        ):
            raise RuntimeError(
                f"Attempt evidence missing at {sequence}"
            )

        final_attempt = attempts[-1]

        if (
            final_attempt.get("http_status") != 404
            or final_attempt.get("outcome")
            != "not_found"
        ):
            raise RuntimeError(
                f"404 evidence changed at {sequence}"
            )

        frozen = dict(item)
        frozen[
            "terminal_status"
        ] = "not_found"
        frozen[
            "http_status"
        ] = 404
        frozen[
            "terminal_body_sha256"
        ] = TERMINAL_BODY_SHA
        frozen[
            "terminal_json_sha256"
        ] = sha256_file(
            terminal_path
        )
        frozen[
            "terminal_path"
        ] = str(
            terminal_path
        )

        frozen_rows.append(
            frozen
        )

    if not WAVE_B_MANIFEST.is_file():
        raise RuntimeError(
            "Wave-B manifest missing"
        )

    wave_b_rows = read_tsv(
        WAVE_B_MANIFEST
    )

    if len(wave_b_rows) != 40:
        raise RuntimeError(
            "Wave-B request count changed"
        )

    direct_indices = {
        str(
            item[
                "retrieval_record_index"
            ]
        )
        for item in DIRECT_OPENALEX_NOT_FOUND
    }

    wave_b_indices = {
        row[
            "retrieval_record_index"
        ]
        for row in wave_b_rows
    }

    overlap = (
        direct_indices
        & wave_b_indices
    )

    if overlap:
        raise RuntimeError(
            "Direct OpenAlex not-found unexpectedly "
            "has Wave-B fallback: "
            + repr(sorted(overlap))
        )

    return {
        "original_reconciliation_design_sha256":
            sha256_file(
                ORIGINAL_DESIGN
            ),
        "original_reconciliation_document_sha256":
            sha256_file(
                ORIGINAL_DOC
            ),
        "wave_a_amended_manifest_sha256":
            sha256_file(
                WAVE_A_MANIFEST
            ),
        "wave_b_manifest_sha256":
            sha256_file(
                WAVE_B_MANIFEST
            ),
        "direct_openalex_not_found_rows":
            frozen_rows,
    }


def expected_design(
    dependencies: dict,
) -> dict:
    frozen_rows = dependencies[
        "direct_openalex_not_found_rows"
    ]

    return {
        "schema_version": 1,
        "amendment_name":
            "pre_review_triage_future_text_"
            "reconciliation_v1_amendment_001",
        "status":
            "FROZEN_PRE_IMPLEMENTATION",
        "amends_design_commit":
            EXPECTED_PARENT,
        "scope":
            (
                "Define deterministic reconciliation "
                "semantics for the ten frozen direct "
                "OpenAlex Wave-A verified-not-found "
                "records discovered during "
                "implementation validation."
            ),
        "dependency_hashes": {
            "original_reconciliation_design_sha256":
                dependencies[
                    "original_reconciliation_design_sha256"
                ],
            "original_reconciliation_document_sha256":
                dependencies[
                    "original_reconciliation_document_sha256"
                ],
            "wave_a_amended_manifest_sha256":
                dependencies[
                    "wave_a_amended_manifest_sha256"
                ],
            "wave_b_manifest_sha256":
                dependencies[
                    "wave_b_manifest_sha256"
                ],
        },
        "direct_openalex_verified_not_found": {
            "count": 10,
            "rows": frozen_rows,
            "wave_b_fallback_permitted":
                False,
        },
        "resolution_semantics": {
            "included_in_reconciled_resolution":
                True,
            "included_in_reconciled_normalized_text":
                False,
            "resolution_lane":
                "wave_a_primary",
            "terminal_source":
                "wave_a_openalex_verified_not_found",
            "provider_used":
                "openalex",
            "provider_lookup_type_source":
                "frozen Wave-A manifest frozen_route",
            "provider_record_id":
                "",
            "source_body_sha256_source":
                "verified Wave-A terminal_body_sha256",
            "provider_identity_status":
                "not_applicable",
            "parser_status":
                "not_applicable",
            "abstract_status":
                "provider_not_found",
            "wave_b_request_sequence":
                "",
            "wave_b_request_identity_sha256":
                "",
            "fallback_reason":
                "",
            "normalized_text_present":
                False,
            "scientific_exclusion_evidence":
                False,
        },
        "validation_amendments": {
            "provider_not_found_count":
                10,
            "final_population_equation":
                (
                    "usable_abstract_total + "
                    "abstract_absent_total + "
                    "provider_not_found_total = 12162"
                ),
            "parser_or_position_gap_semantics":
                (
                    "provider_not_found rows have no "
                    "provider payload to parse and therefore "
                    "parser_status=not_applicable; they are "
                    "not parser or OpenAlex-position gaps"
                ),
            "direct_openalex_not_found_must_not_enter_"
            "fallback_population":
                True,
            "pubmed_verified_not_found_fallback_count_"
            "unchanged":
                2,
            "wave_b_total_unchanged":
                40,
        },
        "unchanged_original_contract": {
            "total_future_input_records":
                12162,
            "future_wave_a_requests":
                12147,
            "future_wave_b_fallback_rows":
                40,
            "future_wave_b_abstract_absent_fallbacks":
                38,
            "future_wave_b_verified_not_found_fallbacks":
                2,
            "network_permitted":
                False,
            "raw_retrieval_archive_modification_permitted":
                False,
            "scientific_decisions_permitted":
                False,
            "blind_validation_content_used":
                False,
            "model_fit_permitted":
                False,
        },
        "verification_requirements": [
            (
                "verify all ten rows against the frozen "
                "amended Wave-A manifest"
            ),
            (
                "verify each terminal archive is direct "
                "OpenAlex terminal_status=not_found"
            ),
            (
                "verify each final attempt is HTTP 404 "
                "with outcome=not_found"
            ),
            (
                "verify each terminal body SHA and terminal "
                "JSON SHA before reconciliation"
            ),
            (
                "fail closed if any additional direct "
                "OpenAlex verified-not-found appears"
            ),
            (
                "fail closed if any of the ten direct "
                "OpenAlex not-found rows enters Wave B"
            ),
            (
                "do not normalize a nonexistent OpenAlex "
                "provider record"
            ),
            (
                "do not reinterpret provider not-found as "
                "abstract_absent"
            ),
            (
                "do not convert provider not-found into "
                "scientific exclusion evidence"
            ),
        ],
        "next_gate":
            (
                "IMPLEMENT_AND_HOSTILE_TEST_FUTURE_TEXT_"
                "RECONCILIATION_V1_AGAINST_DESIGN_PLUS_"
                "AMENDMENT_001_WITH_TWO_INDEPENDENT_"
                "TEMPORARY_BUILDS"
            ),
    }


def write_candidate() -> None:
    if repository_position() != "PRE_COMMIT_PARENT":
        raise RuntimeError(
            "Amendment candidate may only be written "
            "at expected parent"
        )

    for path in (
        DESIGN,
        DOCUMENT,
        CHECKSUM,
    ):
        if path.exists():
            raise RuntimeError(
                "Refusing to overwrite amendment artifact: "
                + str(path)
            )

    dependencies = (
        validate_dependencies()
    )

    design = expected_design(
        dependencies
    )

    DESIGN.write_text(
        json.dumps(
            design,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    indices = ", ".join(
        str(
            item[
                "retrieval_record_index"
            ]
        )
        for item in dependencies[
            "direct_openalex_not_found_rows"
        ]
    )

    doc = f"""# Pre-review triage future text reconciliation v1 — Amendment 001

## Status

`FROZEN_PRE_IMPLEMENTATION`

This amendment supplements, but does not modify, the future reconciliation
design frozen at commit `{EXPECTED_PARENT}`.

## Reason for amendment

Implementation validation against the frozen Future Wave-A archive established
that ten direct OpenAlex requests terminate as independently verified provider
not-found responses.

The original implementation candidate inherited the historical assumption that
every Wave-A `verified_not_found` record was PubMed and therefore eligible for
the frozen PubMed-to-OpenAlex Wave-B fallback. That assumption is false for the
future population.

The affected reconciliation record indices are:

`{indices}`

Each exact request identity, retrieval-record index, screening entity,
identifier, route, terminal path, terminal JSON SHA256 and terminal-body SHA256
is pinned in the machine-readable amendment design.

## Frozen evidence

The ten records:

- are direct Future Wave-A OpenAlex requests;
- terminate with `terminal_status = not_found`;
- terminate after HTTP 404 evidence with `outcome = not_found`;
- have no frozen Future Wave-B fallback;
- are provider-level absence states, not abstract-absence states.

The frozen Future Wave-B population remains exactly 40 rows: 38 derived from
PubMed `abstract_absent` and two derived from PubMed `verified_not_found`.

## Resolution semantics

Each of the ten direct OpenAlex not-found records must remain present in
`reconciled_resolution.tsv`.

They must not enter `reconciled_normalized_text.tsv`.

They are represented as:

- `resolution_lane = wave_a_primary`
- `provider_used = openalex`
- `provider_lookup_type` from the frozen Wave-A manifest
- blank `provider_record_id`
- `source_body_sha256` from the verified terminal body
- `provider_identity_status = not_applicable`
- `parser_status = not_applicable`
- `abstract_status = provider_not_found`
- no Wave-B request identity
- no fallback reason
- `normalized_text_present = 0`

`provider_not_found` is retrieval provenance only. It is not scientific
exclusion evidence and must not be reinterpreted as `abstract_absent`.

Because no provider record exists to normalize, `parser_status =
not_applicable` is not a parser failure and must not contribute to the
parser/position-gap failure count.

Final population accounting must therefore include usable abstracts,
abstract-absent records and these ten provider-not-found records, together
covering all 12,162 future reconciliation inputs.

## Unchanged boundaries

This amendment does not change:

- the 12,162-record future reconciliation population;
- the 12,147 Future Wave-A request population;
- any Future Wave-A raw archive;
- the 40-row Future Wave-B fallback population;
- the 38 PubMed abstract-absent fallbacks;
- the two PubMed verified-not-found fallbacks;
- scientific eligibility rules;
- the blind-validation boundary;
- model fitting or thresholds.

No network access is authorized.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_FUTURE_TEXT_RECONCILIATION_V1_AGAINST_DESIGN_PLUS_AMENDMENT_001_WITH_TWO_INDEPENDENT_TEMPORARY_BUILDS`
"""

    DOCUMENT.write_text(
        doc,
        encoding="utf-8",
    )

    lines = []

    for path in (
        FREEZE,
        DESIGN,
        DOCUMENT,
    ):
        lines.append(
            f"{sha256_file(path)}  {path}"
        )

    CHECKSUM.write_text(
        "\n".join(lines)
        + "\n",
        encoding="utf-8",
    )

    print(
        "PASS | future reconciliation amendment 001 candidate written"
    )


def validate_candidate() -> None:
    position = repository_position()

    dependencies = (
        validate_dependencies()
    )

    for path in (
        DESIGN,
        DOCUMENT,
        CHECKSUM,
    ):
        if not path.is_file():
            raise RuntimeError(
                "Amendment artifact missing: "
                + str(path)
            )

    observed = json.loads(
        DESIGN.read_text(
            encoding="utf-8"
        )
    )

    expected = expected_design(
        dependencies
    )

    if observed != expected:
        raise RuntimeError(
            "Amendment design differs from expected object"
        )

    lines = [
        line
        for line in CHECKSUM.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    if len(lines) != 3:
        raise RuntimeError(
            "Amendment checksum manifest must have 3 entries"
        )

    expected_targets = {
        str(FREEZE),
        str(DESIGN),
        str(DOCUMENT),
    }

    observed_targets = set()

    for line in lines:
        digest, path_text = line.split(
            None,
            1,
        )

        path_text = (
            path_text.strip()
        )

        observed_targets.add(
            path_text
        )

        if (
            sha256_file(
                Path(path_text)
            )
            != digest
        ):
            raise RuntimeError(
                "Amendment checksum mismatch: "
                + path_text
            )

    if observed_targets != expected_targets:
        raise RuntimeError(
            "Amendment checksum target set differs"
        )

    print(
        "PASS | repository position =",
        position,
    )
    print(
        "PASS | direct OpenAlex not-found count = 10"
    )
    print(
        "PASS | Wave-B population remains 40"
    )
    print(
        "PASS | future reconciliation amendment 001 validates"
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "usage: "
            + str(FREEZE)
            + " --write|--validate"
        )

    if sys.argv[1] == "--write":
        write_candidate()

    elif sys.argv[1] == "--validate":
        validate_candidate()

    else:
        raise SystemExit(
            "unknown argument"
        )


if __name__ == "__main__":
    main()
