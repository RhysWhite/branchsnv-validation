from __future__ import annotations

from pathlib import Path
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
    "3e7f1707630054652a68bae1208a5be4202b8c56"
)

ORIGINAL_DESIGN = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_design.json"
)

AMENDMENT_001_DESIGN = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_001_design.json"
)

WAVE_A_MANIFEST = (
    RROOT
    / "live_wave_a_request_manifest_amendment_001.tsv"
)

WAVE_A_RAW = (
    RROOT
    / "live_wave_a"
    / "raw"
)

FREEZE = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_002_freeze.py"
)

DESIGN = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_002_design.json"
)

DOCUMENT = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_TEXT_RECONCILIATION_V1_AMENDMENT_002.md"
)

CHECKSUM = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_amendment_002.sha256"
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

EXPECTED_SEQUENCE = 9180
EXPECTED_INDEX = 9191
EXPECTED_PROVIDER = "openalex"
EXPECTED_IDENTIFIER = "W2119850564"
EXPECTED_NAMESPACE = "openalex"
EXPECTED_ROUTE = "exact_work_id"
EXPECTED_TRANSPORT_ROUTE = "work_by_openalex_id"
EXPECTED_ENTITY = (
    "publication_component:citation:publication:"
    "doi:10.5897/ajb11.773"
)
EXPECTED_PROVIDER_RECORD_ID = (
    "https://openalex.org/W2119850564"
)
EXPECTED_BODY_SHA = (
    "30228dfcd8815a4e8dfbbefc810d9033"
    "a579b2733cb7091c6314e514178943a1"
)
EXPECTED_MISSING_POSITIONS = [
    86,
    110,
    215,
    217,
    250,
    251,
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


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
            "its direct amendment-002 freeze child"
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
            "Committed amendment-002 path set differs"
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

    for path in (
        ORIGINAL_DESIGN,
        AMENDMENT_001_DESIGN,
        WAVE_A_MANIFEST,
    ):
        if not path.is_file():
            raise RuntimeError(
                "Required dependency missing: "
                + str(path)
            )

    for path in PLANNED_OUTPUTS:
        if path.exists():
            raise RuntimeError(
                "Canonical reconciliation output already exists: "
                + str(path)
            )

    rows = read_tsv(
        WAVE_A_MANIFEST
    )

    matching = [
        row
        for row in rows
        if int(
            row[
                "request_sequence"
            ]
        )
        == EXPECTED_SEQUENCE
    ]

    if len(matching) != 1:
        raise RuntimeError(
            "Expected exactly one Wave-A sequence 9180"
        )

    row = matching[0]

    expected_fields = {
        "retrieval_record_index":
            str(EXPECTED_INDEX),
        "screening_entity_id":
            EXPECTED_ENTITY,
        "provider":
            EXPECTED_PROVIDER,
        "frozen_route":
            EXPECTED_ROUTE,
        "transport_route":
            EXPECTED_TRANSPORT_ROUTE,
        "identifier_namespace":
            EXPECTED_NAMESPACE,
        "identifier":
            EXPECTED_IDENTIFIER,
    }

    for key, expected in expected_fields.items():
        if row.get(key) != expected:
            raise RuntimeError(
                f"Manifest mismatch: {key}"
            )

    terminals = []

    for path in WAVE_A_RAW.rglob(
        "terminal.json"
    ):
        terminal = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if (
            terminal.get(
                "logical_lookup_id"
            )
            == (
                "triage_text_wave_a:"
                f"{EXPECTED_SEQUENCE}:"
                + row[
                    "request_identity_sha256"
                ][:16]
            )
        ):
            terminals.append(
                (path, terminal)
            )

    if len(terminals) != 1:
        raise RuntimeError(
            "Expected exactly one matching terminal archive"
        )

    terminal_path, terminal = (
        terminals[0]
    )

    if terminal.get(
        "terminal_status"
    ) != "success":
        raise RuntimeError(
            "Position-gap terminal is not transport success"
        )

    if terminal.get(
        "provider"
    ) != "openalex":
        raise RuntimeError(
            "Position-gap provider changed"
        )

    if terminal.get(
        "provider_identifier"
    ) != EXPECTED_PROVIDER_RECORD_ID:
        raise RuntimeError(
            "Position-gap provider identifier changed"
        )

    if terminal.get(
        "terminal_body_sha256"
    ) != EXPECTED_BODY_SHA:
        raise RuntimeError(
            "Position-gap body SHA changed"
        )

    body_candidates = sorted(
        terminal_path.parent.rglob(
            "*body*"
        )
    )

    body_path = None

    for path in body_candidates:
        if (
            path.is_file()
            and sha256_file(
                path
            )
            == EXPECTED_BODY_SHA
        ):
            body_path = path
            break

    if body_path is None:
        raise RuntimeError(
            "Verified body file not found"
        )

    raw = json.loads(
        body_path.read_bytes().decode(
            "utf-8"
        )
    )

    if (
        "https://openalex.org/"
        + str(
            raw.get("id", "")
        ).split("/")[-1]
        != EXPECTED_PROVIDER_RECORD_ID
    ):
        raise RuntimeError(
            "OpenAlex body identity changed"
        )

    inv = raw.get(
        "abstract_inverted_index"
    )

    if not isinstance(
        inv,
        dict,
    ):
        raise RuntimeError(
            "Expected inverted index missing"
        )

    positions = []

    for values in inv.values():
        if isinstance(
            values,
            list,
        ):
            for value in values:
                if isinstance(
                    value,
                    int,
                ):
                    positions.append(
                        value
                    )

    observed = set(
        positions
    )

    if not observed:
        raise RuntimeError(
            "No OpenAlex abstract positions found"
        )

    missing = [
        value
        for value in range(
            min(observed),
            max(observed) + 1,
        )
        if value not in observed
    ]

    if missing != EXPECTED_MISSING_POSITIONS:
        raise RuntimeError(
            "OpenAlex missing-position set changed: "
            + repr(missing)
        )

    if len(positions) != 256:
        raise RuntimeError(
            "Position occurrence count changed"
        )

    if len(observed) != 256:
        raise RuntimeError(
            "Unique-position count changed"
        )

    return {
        "original_design_sha256":
            sha256_file(
                ORIGINAL_DESIGN
            ),
        "amendment_001_design_sha256":
            sha256_file(
                AMENDMENT_001_DESIGN
            ),
        "wave_a_manifest_sha256":
            sha256_file(
                WAVE_A_MANIFEST
            ),
        "request_identity_sha256":
            row[
                "request_identity_sha256"
            ],
        "terminal_path":
            str(
                terminal_path
            ),
        "terminal_json_sha256":
            sha256_file(
                terminal_path
            ),
    }


def expected_design(
    dep: dict,
) -> dict:
    return {
        "schema_version":
            1,
        "amendment_name":
            "pre_review_triage_future_text_"
            "reconciliation_v1_amendment_002",
        "status":
            "FROZEN_PRE_IMPLEMENTATION",
        "amends_commit":
            EXPECTED_PARENT,
        "scope":
            (
                "Authorize deterministic provenance-only "
                "resolution of the single frozen successful "
                "OpenAlex record whose abstract inverted "
                "index contains verified position gaps."
            ),
        "dependency_hashes": {
            "original_reconciliation_design_sha256":
                dep[
                    "original_design_sha256"
                ],
            "amendment_001_design_sha256":
                dep[
                    "amendment_001_design_sha256"
                ],
            "wave_a_amended_manifest_sha256":
                dep[
                    "wave_a_manifest_sha256"
                ],
        },
        "openalex_position_gap_exception": {
            "count":
                1,
            "request_sequence":
                EXPECTED_SEQUENCE,
            "retrieval_record_index":
                EXPECTED_INDEX,
            "screening_entity_id":
                EXPECTED_ENTITY,
            "provider":
                EXPECTED_PROVIDER,
            "identifier_namespace":
                EXPECTED_NAMESPACE,
            "identifier":
                EXPECTED_IDENTIFIER,
            "frozen_route":
                EXPECTED_ROUTE,
            "transport_route":
                EXPECTED_TRANSPORT_ROUTE,
            "request_identity_sha256":
                dep[
                    "request_identity_sha256"
                ],
            "provider_record_id":
                EXPECTED_PROVIDER_RECORD_ID,
            "terminal_body_sha256":
                EXPECTED_BODY_SHA,
            "terminal_path":
                dep[
                    "terminal_path"
                ],
            "terminal_json_sha256":
                dep[
                    "terminal_json_sha256"
                ],
            "parser_status":
                "ok",
            "abstract_status":
                "openalex_position_gap",
            "position_min":
                0,
            "position_max":
                261,
            "position_occurrence_count":
                256,
            "unique_position_count":
                256,
            "duplicate_position_count":
                0,
            "missing_position_count":
                6,
            "missing_positions":
                EXPECTED_MISSING_POSITIONS,
        },
        "resolution_semantics": {
            "included_in_reconciled_resolution":
                True,
            "included_in_reconciled_normalized_text":
                False,
            "resolution_lane":
                "wave_a_primary",
            "provider_used":
                "openalex",
            "provider_lookup_type":
                "exact_work_id",
            "provider_record_id":
                EXPECTED_PROVIDER_RECORD_ID,
            "source_body_sha256":
                EXPECTED_BODY_SHA,
            "provider_identity_status":
                "matched",
            "parser_status":
                "ok",
            "abstract_status":
                "openalex_position_gap",
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
        "safety_semantics": {
            "abstract_reconstruction_permitted":
                False,
            "missing_token_inference_permitted":
                False,
            "position_repair_permitted":
                False,
            "network_reretrieval_permitted":
                False,
            "wave_b_fallback_permitted":
                False,
            "scientific_exclusion_permitted":
                False,
            "exception_is_exact_record_only":
                True,
        },
        "validation_amendments": {
            "openalex_position_gap_count":
                1,
            "provider_not_found_count":
                10,
            "parser_failure_count":
                0,
            "final_population_equation":
                (
                    "usable_abstract_total + "
                    "abstract_absent_total + "
                    "provider_not_found_total + "
                    "openalex_position_gap_total = 12162"
                ),
        },
        "next_gate":
            (
                "IMPLEMENT_AND_HOSTILE_TEST_FUTURE_TEXT_"
                "RECONCILIATION_V1_AGAINST_DESIGN_PLUS_"
                "AMENDMENTS_001_002_WITH_TWO_INDEPENDENT_"
                "TEMPORARY_BUILDS"
            ),
    }


def write_candidate() -> None:
    if repository_position() != "PRE_COMMIT_PARENT":
        raise RuntimeError(
            "Amendment 002 candidate may only be written "
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

    dep = validate_dependency()

    design = expected_design(
        dep
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

    doc = f"""# Pre-review triage future text reconciliation v1 — Amendment 002

## Status

`FROZEN_PRE_IMPLEMENTATION`

This amendment supplements the future reconciliation design and Amendment 001.

## Reason for amendment

Exhaustive validation of all 3,608 Future Wave-A OpenAlex requests identified
exactly one transport-successful, identity-verified OpenAlex record whose
abstract inverted index cannot be reconstructed contiguously by the frozen
normalizer.

The affected record is:

- request sequence: `{EXPECTED_SEQUENCE}`
- retrieval record index: `{EXPECTED_INDEX}`
- OpenAlex work: `{EXPECTED_IDENTIFIER}`
- screening entity: `{EXPECTED_ENTITY}`
- body SHA256: `{EXPECTED_BODY_SHA}`

The frozen inverted index contains 256 unique positions between 0 and 261, with
no duplicate positions, but positions 86, 110, 215, 217, 250 and 251 are
absent.

## Resolution semantics

The record remains present in `reconciled_resolution.tsv` with:

- `resolution_lane = wave_a_primary`
- `provider_used = openalex`
- `provider_lookup_type = exact_work_id`
- `provider_record_id = {EXPECTED_PROVIDER_RECORD_ID}`
- `provider_identity_status = matched`
- `parser_status = ok`
- `abstract_status = openalex_position_gap`
- no Wave-B fallback
- `normalized_text_present = 0`

It must not enter `reconciled_normalized_text.tsv`.

## Safety boundary

No attempt may be made to infer, synthesize, reorder or repair missing abstract
tokens.

No network reretrieval is authorized.

This state is retrieval provenance only and is not scientific exclusion
evidence.

The exception applies only to this exact frozen request identity and body SHA.

## Population accounting

The final 12,162-record reconciliation population must be accounted for as:

usable abstracts + abstract-absent + provider-not-found +
OpenAlex-position-gap = 12,162.

Exactly one `openalex_position_gap` record is permitted.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_FUTURE_TEXT_RECONCILIATION_V1_AGAINST_DESIGN_PLUS_AMENDMENTS_001_002_WITH_TWO_INDEPENDENT_TEMPORARY_BUILDS`
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
        "PASS | future reconciliation amendment 002 candidate written"
    )


def validate_candidate() -> None:
    position = repository_position()

    dep = validate_dependency()

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
        dep
    )

    if observed != expected:
        raise RuntimeError(
            "Amendment 002 design differs from expected object"
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

    targets = {
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

    if observed_targets != targets:
        raise RuntimeError(
            "Amendment checksum target set differs"
        )

    print(
        "PASS | repository position =",
        position,
    )
    print(
        "PASS | exactly one OpenAlex position-gap exception"
    )
    print(
        "PASS | missing positions =",
        EXPECTED_MISSING_POSITIONS,
    )
    print(
        "PASS | future reconciliation amendment 002 validates"
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
