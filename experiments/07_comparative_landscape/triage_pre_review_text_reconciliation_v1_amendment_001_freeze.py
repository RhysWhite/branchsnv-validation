from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import json
import subprocess
import sys


ROOT = Path(
    "experiments/07_comparative_landscape"
)

RROOT = Path(
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1"
)

HROOT = Path(
    "results/07_comparative_landscape/"
    "metadata_resolution_retrieval"
)

EXPECTED_PARENT = (
    "1aa32f02387e4c5638b18b951bd5bc7a231c0b5f"
)

EXPECTED_HISTORICAL_CHECKSUM_SHA = (
    "f51080de3383cae1981e19c57687e4c8"
    "ea0e7f9832316a3936728a23995e8b86"
)

ORIGINAL_DESIGN = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1_design.json"
)

ORIGINAL_DOC = (
    ROOT
    / "TRIAGE_PRE_REVIEW_TEXT_RECONCILIATION_V1.md"
)

HISTORICAL_CHECKSUMS = (
    HROOT
    / "checksums.sha256"
)

FREEZE = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1_amendment_001_freeze.py"
)

DESIGN = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1_amendment_001_design.json"
)

DOCUMENT = (
    ROOT
    / "TRIAGE_PRE_REVIEW_TEXT_RECONCILIATION_V1_AMENDMENT_001.md"
)

CHECKSUM = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1_amendment_001.sha256"
)


AMENDMENT_PATHS = {
    str(FREEZE),
    str(DESIGN),
    str(DOCUMENT),
    str(CHECKSUM),
}


PLANNED_OUTPUTS = [
    RROOT
    / "reconciled_resolution.tsv",

    RROOT
    / "reconciled_normalized_text.tsv",

    RROOT
    / "reconciliation_summary.json",

    RROOT
    / "reconciliation_outputs.sha256",
]


OFFLINE_LOOKUPS = [
    {
        "retrieval_record_index": 321,
        "logical_lookup_id":
            "lookup:6545dbb87a2570148bd1077c372b9655a3a1af5230aa24ecfe68788babac641c",
        "source_body_sha256":
            "afd40665d46e08066c8ecafdcdfb976bb4a230b9413c2c5430f4abdca8c14ba8",
        "abstract_status":
            "abstract_absent",
    },
    {
        "retrieval_record_index": 1004,
        "logical_lookup_id":
            "lookup:4a6aba3275ab89eba9e726d3b70a7e80e85e3a969c49d979e4fcd2d75635c143",
        "source_body_sha256":
            "bd5c3ad8726fe545705e3bce9d0aa5801ce2bbf398f80e2637b111d4110f17e9",
        "abstract_status":
            "abstract_absent",
    },
    {
        "retrieval_record_index": 1005,
        "logical_lookup_id":
            "lookup:33181558a23ef6da7bb492335f76d0686f08f1762511625e85fbfd4b65ae453e",
        "source_body_sha256":
            "a7037168721208862368681513a2d55f79e0ed2f3a5f29fea81440d1b4609b5f",
        "abstract_status":
            "abstract_absent",
    },
    {
        "retrieval_record_index": 1006,
        "logical_lookup_id":
            "lookup:d32229000e6c7db51843210877aed9c16ea957a3b2d65877bc98264afdc3a45a",
        "source_body_sha256":
            "d751a3db9df5ef810ff26969f19953fb39de1c12bc6cded6337c4439e9040218",
        "abstract_status":
            "abstract_absent",
    },
    {
        "retrieval_record_index": 1034,
        "logical_lookup_id":
            "lookup:6a4e30ab0d2b24c6efb791d351c828cc240f91d1413b73005000e0d5ee57b9cf",
        "source_body_sha256":
            "34f68eb411a935d721d85e5558ea3f5dd75d9c805347139379b3ee2bed50f5b6",
        "abstract_status":
            "abstract_absent",
    },
    {
        "retrieval_record_index": 1068,
        "logical_lookup_id":
            "lookup:a10060aac1e98a4e6c3450837628a9cfb4360c838d3cd613d0ff4544b7c18959",
        "source_body_sha256":
            "abb46b56e0d90fe023707de5dac6d7ddba983939892991c33025ca8675386558",
        "abstract_status":
            "abstract_absent",
    },
    {
        "retrieval_record_index": 2595,
        "logical_lookup_id":
            "lookup:eb42dd088c7cd2365ec8c6d948b92e3c5d1dc8f60d601aac88c210017851bc72",
        "source_body_sha256":
            "0d2ad7e6623670cd7f9f62c53b66aa96a3c42bac8d2911f31a6fb0a84053ce09",
        "abstract_status":
            "usable_abstract_openalex",
    },
    {
        "retrieval_record_index": 4164,
        "logical_lookup_id":
            "lookup:e616bacbe37c450647221da56be8bd171b133e6e85f512f14371f1ffb40fc9a0",
        "source_body_sha256":
            "479553f7093c5fb9af94a0459fe765d63caa201b5ef0f9297bdb1e89a04e60c5",
        "abstract_status":
            "usable_abstract_openalex",
    },
    {
        "retrieval_record_index": 4248,
        "logical_lookup_id":
            "lookup:b40bd4ad49ded8971296d1f2e2a5e9de7028d93acf42d3fb495fb193f57ecf08",
        "source_body_sha256":
            "1e8f482b73d147e6daa929c463d7d3bd042745fa2f9f1a14b885c7b448624f6b",
        "abstract_status":
            "usable_abstract_openalex",
    },
]


ABSENT_DERIVED_PROVENANCE = {
    321: {
        "provider_record_id":
            "https://openalex.org/W4205666856",
        "provider_identity_status":
            "transport_validated",
    },
    1004: {
        "provider_record_id":
            "https://openalex.org/W1972189965",
        "provider_identity_status":
            "transport_validated",
    },
    1005: {
        "provider_record_id":
            "https://openalex.org/W2046435207",
        "provider_identity_status":
            "transport_validated",
    },
    1006: {
        "provider_record_id":
            "https://openalex.org/W4210633230",
        "provider_identity_status":
            "transport_validated",
    },
    1034: {
        "provider_record_id":
            "https://openalex.org/W1534406401",
        "provider_identity_status":
            "transport_validated",
    },
    1068: {
        "provider_record_id":
            "https://openalex.org/W2594042085",
        "provider_identity_status":
            "transport_validated",
    },
}


def sha256_file(
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


def read_tsv(
    path: Path,
) -> list[dict[str, str]]:

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


def validate_dependency() -> dict:

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
            "Original frozen design missing"
        )

    if not ORIGINAL_DOC.is_file():
        raise RuntimeError(
            "Original frozen design document missing"
        )

    if not HISTORICAL_CHECKSUMS.is_file():
        raise RuntimeError(
            "Historical checksum manifest missing"
        )

    historical_checksum_sha = (
        sha256_file(
            HISTORICAL_CHECKSUMS
        )
    )

    if (
        historical_checksum_sha
        != EXPECTED_HISTORICAL_CHECKSUM_SHA
    ):
        raise RuntimeError(
            "Historical checksum manifest SHA changed"
        )

    checksum_lines = [
        line
        for line in HISTORICAL_CHECKSUMS.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    if len(
        checksum_lines
    ) != 8666:
        raise RuntimeError(
            "Historical checksum entry count changed"
        )

    checksum_map = {}

    for line in checksum_lines:

        digest, path_text = line.split(
            None,
            1,
        )

        checksum_map[
            path_text.strip()
        ] = digest

    resolution_rows = {
        int(
            row[
                "retrieval_record_index"
            ]
        ):
            row
        for row in read_tsv(
            RROOT
            / "offline_cache_resolution.tsv"
        )
    }

    if len(
        resolution_rows
    ) != 4499:
        raise RuntimeError(
            "offline_cache_resolution row count changed"
        )

    for item in OFFLINE_LOOKUPS:

        idx = item[
            "retrieval_record_index"
        ]

        row = resolution_rows[
            idx
        ]

        if (
            row[
                "chosen_logical_lookup_id"
            ]
            != item[
                "logical_lookup_id"
            ]
        ):
            raise RuntimeError(
                f"Logical lookup changed at index {idx}"
            )

        if (
            row[
                "chosen_source_body_sha256"
            ]
            != item[
                "source_body_sha256"
            ]
        ):
            raise RuntimeError(
                f"Body SHA changed at index {idx}"
            )

        if (
            row[
                "abstract_status"
            ]
            != item[
                "abstract_status"
            ]
        ):
            raise RuntimeError(
                f"Abstract status changed at index {idx}"
            )

        token = item[
            "logical_lookup_id"
        ].split(
            ":",
            1,
        )[1]

        prefix = (
            "raw/lookup_"
            + token
            + "/"
        )

        required = [
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
        ]

        for relative in required:

            if relative not in checksum_map:
                raise RuntimeError(
                    "Historical file is not checksum-covered: "
                    + relative
                )

            path = (
                HROOT
                / relative
            )

            if not path.is_file():
                raise RuntimeError(
                    "Historical file missing: "
                    + relative
                )

            if (
                sha256_file(
                    path
                )
                != checksum_map[
                    relative
                ]
            ):
                raise RuntimeError(
                    "Historical file checksum mismatch: "
                    + relative
                )

        body = (
            HROOT
            / (
                prefix
                + "attempt_01/hop_00_body.bin"
            )
        )

        if (
            sha256_file(
                body
            )
            != item[
                "source_body_sha256"
            ]
        ):
            raise RuntimeError(
                f"Selected body mismatch at index {idx}"
            )

    for path in PLANNED_OUTPUTS:

        if path.exists():
            raise RuntimeError(
                "Final reconciliation output already exists: "
                + str(path)
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

        "historical_checksum_manifest_sha256":
            historical_checksum_sha,
    }


def expected_design(
    dependency_hashes: dict,
) -> dict:

    return {
        "schema_version":
            1,

        "amendment_name":
            "triage_pre_review_text_reconciliation_v1_amendment_001",

        "status":
            "FROZEN_PRE_IMPLEMENTATION",

        "amends_design_commit":
            EXPECTED_PARENT,

        "scope":
            (
                "Pin the historical metadata-resolution cache "
                "archive required to reconstruct the nine frozen "
                "offline-cache reconciliation rows."
            ),

        "dependency_hashes":
            dependency_hashes,

        "historical_cache_dependency": {
            "root":
                str(HROOT),

            "checksum_manifest":
                str(
                    HISTORICAL_CHECKSUMS
                ),

            "checksum_manifest_sha256":
                EXPECTED_HISTORICAL_CHECKSUM_SHA,

            "checksum_manifest_entry_count":
                8666,

            "selected_lookup_count":
                9,

            "selected_lookups":
                OFFLINE_LOOKUPS,
        },

        "offline_cache_semantics": {
            "usable_cached_row_count":
                3,

            "abstract_absent_cached_row_count":
                6,

            "usable_rows": {
                "normalized_text_source":
                    "offline_cached_normalized_text.tsv",

                "historical_raw_body_must_also_verify":
                    True,

                "frozen_normalizer_status_must_reproduce":
                    "usable_abstract_openalex",
            },

            "abstract_absent_rows": {
                "included_in_reconciled_normalized_text":
                    False,

                "included_in_reconciled_resolution":
                    True,

                "provider_record_id_source":
                    (
                        "frozen normalize_openalex output over "
                        "checksum-verified historical body"
                    ),

                "provider_identity_status_source":
                    (
                        "frozen normalize_openalex output over "
                        "checksum-verified historical body"
                    ),

                "parser_status_required":
                    "ok",

                "abstract_status_required":
                    "abstract_absent",

                "derived_provenance":
                    {
                        str(key):
                            value
                        for key, value in sorted(
                            ABSENT_DERIVED_PROVENANCE.items()
                        )
                    },
            },

            "blank_provider_record_id_convention_permitted":
                False,

            "blank_provider_identity_status_convention_permitted":
                False,

            "fabricated_provider_identity_permitted":
                False,
        },

        "verification_requirements": [
            (
                "verify the historical checksum-manifest SHA "
                "before reading selected archive bodies"
            ),
            (
                "verify all required files for each of the nine "
                "lookups against the historical checksum manifest"
            ),
            (
                "verify selected body SHA against "
                "offline_cache_resolution.tsv"
            ),
            (
                "verify terminal archive through frozen transport "
                "verification before normalization"
            ),
            (
                "apply only the frozen "
                "triage_pre_review_text_normalizer_v1"
            ),
            (
                "fail closed if any of the six absent rows does "
                "not reproduce its pinned provider provenance"
            ),
            (
                "do not alter the three existing usable cached "
                "normalized-text rows"
            ),
            (
                "do not convert abstract absence into scientific "
                "exclusion evidence"
            ),
        ],

        "unchanged_original_contract": {
            "total_records":
                4499,

            "usable_abstract_total":
                4190,

            "abstract_absent_total":
                309,

            "network_permitted":
                False,

            "production_ledger_write_permitted":
                False,

            "raw_archive_modification_permitted":
                False,

            "blind_validation_content_used":
                False,

            "scientific_decisions_permitted":
                False,

            "model_fit_permitted":
                False,
        },

        "next_gate":
            (
                "IMPLEMENT_AND_HOSTILE_TEST_OFFLINE_"
                "TRIAGE_PRE_REVIEW_TEXT_RECONCILIATION_V1_"
                "AGAINST_DESIGN_PLUS_AMENDMENT_001"
            ),
    }


def write_candidate() -> None:

    if (
        repository_position()
        != "PRE_COMMIT_PARENT"
    ):
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

    dependency_hashes = (
        validate_dependency()
    )

    design = expected_design(
        dependency_hashes
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

    doc = f"""# Triage pre-review text reconciliation v1 — Amendment 001

## Status

`FROZEN_PRE_IMPLEMENTATION`

This amendment supplements, but does not modify, the reconciliation
design frozen at commit `{EXPECTED_PARENT}`.

## Reason for amendment

Post-freeze implementation prechecking established that the nine
records resolved from the historical cache depend on raw bodies under:

`{HROOT}`

The original reconciliation freeze pinned the derived offline cache
tables but did not explicitly pin this historical raw archive as an
implementation dependency.

This amendment closes that dependency gap before implementation.

## Frozen historical dependency

Checksum manifest:

`{HISTORICAL_CHECKSUMS}`

SHA256:

`{EXPECTED_HISTORICAL_CHECKSUM_SHA}`

Entries: 8,666.

Exactly nine offline-cache lookup identities are admitted. Each
selected lookup, source-body SHA256 and expected abstract status is
enumerated in the machine-readable amendment design.

## Three usable cached OpenAlex rows

The existing frozen `offline_cached_normalized_text.tsv` remains the
normalized-text source for these three records.

Their historical raw bodies must nevertheless verify against the
historical checksum archive and must reproduce
`usable_abstract_openalex` under the frozen normalizer.

The existing cached normalized rows are not rewritten or reinterpreted.

## Six cached abstract-absent rows

These records remain present in the 4,499-row resolution output and
remain absent from the 4,190-row normalized-text output.

Their `provider_record_id` and `provider_identity_status` are derived
only by applying the frozen OpenAlex normalizer to the exact
checksum-verified historical body.

No blank-field convention and no fabricated provider identity is
permitted.

All six must reproduce:

- `parser_status = ok`
- `abstract_status = abstract_absent`
- the provider provenance pinned in the amendment JSON.

Abstract absence remains retrieval state only. It is not scientific
evidence for exclusion.

## Unchanged boundaries

This amendment does not change:

- 4,499 total reconciliation records;
- 4,190 usable abstracts;
- 309 abstract-absent records;
- the Wave A or Wave B archives;
- scientific eligibility rules;
- model fitting or thresholds;
- the blind validation boundary;
- the production ledger.

No network access is authorized.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_OFFLINE_TRIAGE_PRE_REVIEW_TEXT_RECONCILIATION_V1_AGAINST_DESIGN_PLUS_AMENDMENT_001`
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
        "PASS | reconciliation amendment 001 candidate written"
    )


def validate_candidate() -> None:

    position = repository_position()

    dependency_hashes = (
        validate_dependency()
    )

    if not DESIGN.is_file():
        raise RuntimeError(
            "Amendment design JSON missing"
        )

    if not DOCUMENT.is_file():
        raise RuntimeError(
            "Amendment document missing"
        )

    if not CHECKSUM.is_file():
        raise RuntimeError(
            "Amendment checksum manifest missing"
        )

    observed = json.loads(
        DESIGN.read_text(
            encoding="utf-8"
        )
    )

    expected = expected_design(
        dependency_hashes
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

        path_text = path_text.strip()

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

    if (
        observed_targets
        != expected_targets
    ):
        raise RuntimeError(
            "Amendment checksum target set differs"
        )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | reconciliation amendment 001 validates"
    )


def main() -> None:

    if len(
        sys.argv
    ) != 2:
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
