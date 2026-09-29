from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(
    "experiments/07_comparative_landscape"
)

RESULT_ROOT = Path(
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1"
)

DESIGN = (
    ROOT
    / "triage_pre_review_text_wave_b_execution_v1_design.json"
)

MANIFEST = (
    RESULT_ROOT
    / "live_wave_b_request_manifest.tsv"
)

NORMALIZER = (
    ROOT
    / "triage_pre_review_text_normalizer_v1.py"
)


EXPECTED_DESIGN_SHA256 = (
    "4a607178762e9e884f430b8fe1c47d078"
    "408b5a51e4e47701f2f4302ab5ca2ca"
)

EXPECTED_MANIFEST_SHA256 = (
    "f099f86cce2321ab07d639aeef5570145"
    "85faf49e2306a09f3fe40119535f0a6"
)

EXPECTED_NORMALIZER_SHA256 = (
    "cbe66fc9ab406fa5ee3745e099c16250"
    "c404a949c0f301e40a7397c285dc459d"
)

EXPECTED_DESIGN_PARENT_COMMIT = (
    "885bc43b845790ec85a29a9063b844217b36b67d"
)

EXPECTED_WAVE_ID = (
    "TRIAGE_TEXT_LIVE_WAVE_B"
)

EXPECTED_OUTPUT_ROOT = (
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1/"
    "live_wave_b"
)

EXPECTED_MAXIMUM_REQUEST_COUNT = 25

AUTHORIZATION_TYPE = (
    "TRIAGE_TEXT_LIVE_WAVE_B_AUTHORIZATION"
)

AUTHORIZATION_STATEMENT = (
    "AUTHORIZE_TRIAGE_TEXT_LIVE_WAVE_B"
)

CLAIM_FILENAME = (
    "authorization_claim.json"
)

STATE_FILENAME = (
    "execution_state.json"
)

COMPLETION_RECEIPT_FILENAME = (
    "completion_receipt.json"
)

CHECKPOINT_DIRECTORY = (
    "checkpoints"
)


class AuthorizationGuardError(
    RuntimeError
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


def canonical_compact_bytes(
    value: Any,
) -> bytes:

    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
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


def git_head() -> str:

    return subprocess.check_output(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        text=True,
    ).strip()


def tracked_tree_clean() -> bool:

    value = subprocess.check_output(
        [
            "git",
            "status",
            "--porcelain",
            "--untracked-files=no",
        ],
        text=True,
    )

    return not value.strip()


def read_json(
    path: Path,
) -> dict:

    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        value,
        dict,
    ):
        raise AuthorizationGuardError(
            "JSON object required: "
            + str(
                path
            )
        )

    return value


def read_manifest() -> list[dict[str, str]]:

    if (
        sha256_file(
            MANIFEST
        )
        != EXPECTED_MANIFEST_SHA256
    ):
        raise AuthorizationGuardError(
            "Frozen Wave B manifest hash mismatch"
        )

    with MANIFEST.open(
        encoding="utf-8",
        newline="",
    ) as handle:

        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        expected_fields = [
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

        if (
            reader.fieldnames
            != expected_fields
        ):
            raise AuthorizationGuardError(
                "Frozen Wave B manifest schema mismatch"
            )

        rows = list(
            reader
        )

    if (
        len(
            rows
        )
        != EXPECTED_MAXIMUM_REQUEST_COUNT
    ):
        raise AuthorizationGuardError(
            "Frozen Wave B request count mismatch"
        )

    expected_sequences = list(
        range(
            1,
            EXPECTED_MAXIMUM_REQUEST_COUNT
            + 1,
        )
    )

    actual_sequences = [
        int(
            row[
                "request_sequence"
            ]
        )
        for row in rows
    ]

    if (
        actual_sequences
        != expected_sequences
    ):
        raise AuthorizationGuardError(
            "Frozen Wave B request sequence mismatch"
        )

    physical = set()

    identities = set()

    for row in rows:

        validate_manifest_row(
            row
        )

        physical_key = (
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

        if physical_key in physical:

            raise AuthorizationGuardError(
                "Duplicate physical exact request"
            )

        physical.add(
            physical_key
        )

        identity = row[
            "request_identity_sha256"
        ]

        if identity in identities:

            raise AuthorizationGuardError(
                "Duplicate request identity"
            )

        identities.add(
            identity
        )

    return rows


def expected_request_identity(
    row: dict[str, str],
) -> str:

    value = {
        "wave_id":
            row[
                "wave_id"
            ],

        "request_sequence":
            int(
                row[
                    "request_sequence"
                ]
            ),

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
                "frozen_route"
            ],

        "transport_route":
            row[
                "transport_route"
            ],

        "identifier_namespace":
            row[
                "identifier_namespace"
            ],

        "identifier":
            row[
                "identifier"
            ],
    }

    return sha256_bytes(
        canonical_compact_bytes(
            value
        )
    )



def validate_manifest_row(
    row: dict[str, str],
) -> None:

    if (
        row[
            "wave_id"
        ]
        != EXPECTED_WAVE_ID
    ):
        raise AuthorizationGuardError(
            "Request has wrong Wave B identity"
        )

    allowed = {
        (
            "openalex",
            "exact_work_id",
            "work_by_openalex_id",
            "openalex",
        ),
        (
            "openalex",
            "exact_doi",
            "work_by_doi",
            "doi",
        ),
    }

    actual = (
        row[
            "provider"
        ],
        row[
            "frozen_route"
        ],
        row[
            "transport_route"
        ],
        row[
            "identifier_namespace"
        ],
    )

    if actual not in allowed:
        raise AuthorizationGuardError(
            "Request route outside frozen Wave B contract"
        )

    if not row[
        "identifier"
    ].strip():
        raise AuthorizationGuardError(
            "Request identifier is empty"
        )

    if (
        row[
            "request_identity_sha256"
        ]
        != expected_request_identity(
            row
        )
    ):
        raise AuthorizationGuardError(
            "Request identity hash mismatch"
        )




def load_frozen_design() -> dict:

    if (
        sha256_file(
            DESIGN
        )
        != EXPECTED_DESIGN_SHA256
    ):
        raise AuthorizationGuardError(
            "Frozen Wave B execution design hash mismatch"
        )

    design = read_json(
        DESIGN
    )

    exact = {
        "schema_version":
            1,

        "design_id":
            "TRIAGE_PRE_REVIEW_TEXT_WAVE_B_EXECUTION_V1",

        "status":
            "FROZEN_PRE_IMPLEMENTATION",

        "wave_id":
            EXPECTED_WAVE_ID,

        "design_parent_commit":
            EXPECTED_DESIGN_PARENT_COMMIT,
    }

    for key, expected in exact.items():

        if (
            design.get(
                key
            )
            != expected
        ):
            raise AuthorizationGuardError(
                "Wave B execution design invariant changed: "
                + key
            )

    request_contract = design.get(
        "request_contract",
        {},
    )

    if (
        request_contract.get(
            "manifest_path"
        )
        != str(
            MANIFEST
        )
    ):
        raise AuthorizationGuardError(
            "Wave B manifest path changed"
        )

    if (
        request_contract.get(
            "manifest_sha256"
        )
        != EXPECTED_MANIFEST_SHA256
    ):
        raise AuthorizationGuardError(
            "Wave B manifest SHA changed"
        )

    if (
        request_contract.get(
            "maximum_request_count"
        )
        != EXPECTED_MAXIMUM_REQUEST_COUNT
    ):
        raise AuthorizationGuardError(
            "Wave B maximum request count changed"
        )

    if (
        request_contract.get(
            "provider"
        )
        != "openalex"
    ):
        raise AuthorizationGuardError(
            "Wave B provider contract changed"
        )

    expected_routes = [
        {
            "frozen_route":
                "exact_work_id",
            "transport_route":
                "work_by_openalex_id",
            "identifier_namespace":
                "openalex",
        },
        {
            "frozen_route":
                "exact_doi",
            "transport_route":
                "work_by_doi",
            "identifier_namespace":
                "doi",
        },
    ]

    if (
        request_contract.get(
            "allowed_exact_routes"
        )
        != expected_routes
    ):
        raise AuthorizationGuardError(
            "Wave B exact-route contract changed"
        )

    for key in (
        "pubmed_permitted",
        "search_or_list_endpoints_permitted",
        "crossref_permitted",
        "ad_hoc_probe_permitted",
    ):

        if (
            request_contract.get(
                key
            )
            is not False
        ):
            raise AuthorizationGuardError(
                "Wave B forbidden-request boundary changed: "
                + key
            )

    execution = design.get(
        "execution_contract",
        {},
    )

    expected_execution = {
        "ordering":
            "strict ascending request_sequence",

        "concurrency":
            1,

        "maximum_requests_per_second_per_provider":
            2,

        "cold_start_seconds_before_first_openalex_request":
            0.5,

        "halt_on_first_unresolved_fault":
            True,

        "automatic_reissue_after_ambiguous_network_intent":
            False,

        "same_execution_id_resume_only":
            True,

        "logical_lookup_id_format":
            (
                "triage_text_wave_b:"
                "{request_sequence:04d}:"
                "{request_identity_sha256_prefix16}"
            ),

        "output_root":
            EXPECTED_OUTPUT_ROOT,
    }

    for key, expected in (
        expected_execution.items()
    ):

        if (
            execution.get(
                key
            )
            != expected
        ):
            raise AuthorizationGuardError(
                "Wave B execution invariant changed: "
                + key
            )

    authorization = design.get(
        "authorization_contract",
        {},
    )

    required_true = (
        "explicit_human_authorization_required",
        "must_be_untracked_at_execution_time",
        "one_use",
        "execution_id_bound_at_first_start",
    )

    for key in required_true:

        if (
            authorization.get(
                key
            )
            is not True
        ):
            raise AuthorizationGuardError(
                "Wave B authorization invariant changed: "
                + key
            )

    required_false = (
        "second_execution_id_with_same_authorization_permitted",
        "completed_authorization_replay_permitted",
        "authorization_created_by_this_freeze",
    )

    for key in required_false:

        if (
            authorization.get(
                key
            )
            is not False
        ):
            raise AuthorizationGuardError(
                "Wave B authorization invariant changed: "
                + key
            )

    if (
        authorization.get(
            "authorization_type"
        )
        != AUTHORIZATION_TYPE
    ):
        raise AuthorizationGuardError(
            "Wave B authorization type changed"
        )

    if (
        authorization.get(
            "authorization_statement"
        )
        != AUTHORIZATION_STATEMENT
    ):
        raise AuthorizationGuardError(
            "Wave B authorization statement changed"
        )

    if (
        authorization.get(
            "canonical_path"
        )
        != (
            EXPECTED_OUTPUT_ROOT
            + "/authorization.json"
        )
    ):
        raise AuthorizationGuardError(
            "Wave B authorization path changed"
        )

    safety = design.get(
        "safety_boundary",
        {},
    )

    for key in (
        "network_authorized",
        "authorization_created",
        "network_execution_permitted",
        "production_mutation_permitted",
        "blind_validation_content_used",
        "scientific_decision_fields_permitted_in_transport_evidence",
    ):

        if (
            safety.get(
                key
            )
            is not False
        ):
            raise AuthorizationGuardError(
                "Wave B safety boundary changed: "
                + key
            )

    return design




def verify_transport_source_files(
    design: dict,
) -> None:

    dependencies = design.get(
        "frozen_dependencies",
        {},
    )

    if (
        not isinstance(
            dependencies,
            dict,
        )
        or not dependencies
    ):
        raise AuthorizationGuardError(
            "Wave B frozen dependency map missing"
        )

    for raw_path, expected_sha in (
        dependencies.items()
    ):

        path = Path(
            raw_path
        )

        if not path.is_file():
            raise AuthorizationGuardError(
                "Frozen dependency missing: "
                + raw_path
            )

        if (
            sha256_file(
                path
            )
            != expected_sha
        ):
            raise AuthorizationGuardError(
                "Frozen dependency hash mismatch: "
                + raw_path
            )



def authorization_sha256(
    authorization: dict,
) -> str:

    return sha256_bytes(
        canonical_json_bytes(
            authorization
        )
    )



def validate_authorization(
    authorization_path: Path,
) -> dict:

    if not authorization_path.exists():
        raise AuthorizationGuardError(
            "Live authorization missing"
        )

    if not tracked_tree_clean():
        raise AuthorizationGuardError(
            "Tracked repository state is not clean"
        )

    design = load_frozen_design()

    verify_transport_source_files(
        design
    )

    read_manifest()

    if (
        sha256_file(
            NORMALIZER
        )
        != EXPECTED_NORMALIZER_SHA256
    ):
        raise AuthorizationGuardError(
            "Pinned normalizer hash mismatch"
        )

    authorization = read_json(
        authorization_path
    )

    exact_scalars = {
        "schema_version":
            1,

        "authorization_type":
            AUTHORIZATION_TYPE,

        "status":
            "AUTHORIZED",

        "wave_id":
            EXPECTED_WAVE_ID,

        "authorization_statement":
            AUTHORIZATION_STATEMENT,

        "design_sha256":
            EXPECTED_DESIGN_SHA256,

        "wave_b_request_manifest_sha256":
            EXPECTED_MANIFEST_SHA256,

        "design_parent_commit":
            EXPECTED_DESIGN_PARENT_COMMIT,

        "normalizer_sha256":
            EXPECTED_NORMALIZER_SHA256,

        "maximum_request_count":
            EXPECTED_MAXIMUM_REQUEST_COUNT,

        "execution_output_root":
            EXPECTED_OUTPUT_ROOT,

        "one_use":
            True,

        "authorized_by":
            "human",
    }

    for key, expected in (
        exact_scalars.items()
    ):

        if (
            authorization.get(
                key
            )
            != expected
        ):
            raise AuthorizationGuardError(
                "Authorization field mismatch: "
                + key
            )

    authorization_id = authorization.get(
        "authorization_id"
    )

    if (
        not isinstance(
            authorization_id,
            str,
        )
        or not authorization_id.strip()
    ):
        raise AuthorizationGuardError(
            "Authorization ID missing"
        )

    created = authorization.get(
        "authorization_created_at_utc"
    )

    if (
        not isinstance(
            created,
            str,
        )
        or not created.strip()
    ):
        raise AuthorizationGuardError(
            "Authorization creation timestamp missing"
        )

    authorized_execution_commit = (
        authorization.get(
            "authorized_execution_commit"
        )
    )

    if (
        authorized_execution_commit
        != git_head()
    ):
        raise AuthorizationGuardError(
            "Authorization does not bind current execution commit"
        )

    frozen = design[
        "frozen_dependencies"
    ]

    transport_paths = [
        str(
            ROOT
            / "retrieve_metadata_resolution_queue.py"
        ),
        str(
            ROOT
            / "t000002_authoritative_source_network_transport.py"
        ),
    ]

    expected_transport_sources = {
        path:
            frozen[
                path
            ]
        for path in transport_paths
    }

    if (
        authorization.get(
            "transport_source_hashes"
        )
        != expected_transport_sources
    ):
        raise AuthorizationGuardError(
            "Authorization transport-source hashes mismatch"
        )

    return authorization



def checksum_path(
    path: Path,
) -> Path:

    return Path(
        str(
            path
        )
        + ".sha256"
    )


def write_json_with_checksum(
    path: Path,
    value: dict,
    *,
    exclusive: bool = False,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw = canonical_json_bytes(
        value
    )

    digest = sha256_bytes(
        raw
    )

    if exclusive:

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

    else:

        temporary = Path(
            str(
                path
            )
            + ".tmp"
        )

        temporary.write_bytes(
            raw
        )

        os.replace(
            temporary,
            path,
        )

    digest_path = checksum_path(
        path
    )

    digest_value = (
        digest
        + "  "
        + path.name
        + "\n"
    ).encode(
        "utf-8"
    )

    if exclusive:

        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
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
                    digest_value
                )

        except Exception:

            try:
                digest_path.unlink()
            except FileNotFoundError:
                pass

            raise

    else:

        temporary = Path(
            str(
                digest_path
            )
            + ".tmp"
        )

        temporary.write_bytes(
            digest_value
        )

        os.replace(
            temporary,
            digest_path,
        )


def read_json_with_checksum(
    path: Path,
) -> dict:

    digest_path = checksum_path(
        path
    )

    if (
        not path.exists()
        or not digest_path.exists()
    ):
        raise AuthorizationGuardError(
            "Checkpoint object/checksum pair incomplete: "
            + str(
                path
            )
        )

    raw = path.read_bytes()

    expected_line = (
        digest_path.read_text(
            encoding="utf-8"
        ).strip()
    )

    pieces = expected_line.split()

    if len(
        pieces
    ) != 2:

        raise AuthorizationGuardError(
            "Malformed checkpoint checksum file"
        )

    expected_digest = pieces[0]

    expected_name = pieces[1]

    if (
        expected_name
        != path.name
    ):
        raise AuthorizationGuardError(
            "Checkpoint checksum filename mismatch"
        )

    actual = sha256_bytes(
        raw
    )

    if (
        actual
        != expected_digest
    ):
        raise AuthorizationGuardError(
            "Checkpoint checksum mismatch"
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
        raise AuthorizationGuardError(
            "Checkpoint must be JSON object"
        )

    return value


def claim_path_for_authorization(
    authorization_path: Path,
) -> Path:

    return (
        authorization_path.parent
        / CLAIM_FILENAME
    )


def execution_state_path(
    execution_root: Path,
) -> Path:

    return (
        execution_root
        / STATE_FILENAME
    )


def completion_receipt_path(
    execution_root: Path,
) -> Path:

    return (
        execution_root
        / COMPLETION_RECEIPT_FILENAME
    )


def request_checkpoint_path(
    execution_root: Path,
    sequence: int,
) -> Path:

    return (
        execution_root
        / CHECKPOINT_DIRECTORY
        / f"{sequence:04d}.json"
    )


def claim_execution(
    *,
    authorization_path: Path,
    execution_id: str,
) -> dict:

    if (
        not isinstance(
            execution_id,
            str,
        )
        or not execution_id.strip()
    ):
        raise AuthorizationGuardError(
            "Execution ID missing"
        )

    authorization = (
        validate_authorization(
            authorization_path
        )
    )

    auth_sha = (
        authorization_sha256(
            authorization
        )
    )

    execution_root = Path(
        authorization[
            "execution_output_root"
        ]
    )

    claim_path = (
        claim_path_for_authorization(
            authorization_path
        )
    )

    state_path = (
        execution_state_path(
            execution_root
        )
    )


    if claim_path.exists():

        claim = (
            read_json_with_checksum(
                claim_path
            )
        )

        if (
            claim.get(
                "authorization_sha256"
            )
            != auth_sha
        ):
            raise AuthorizationGuardError(
                "Existing claim binds different authorization bytes"
            )

        if (
            claim.get(
                "execution_id"
            )
            != execution_id
        ):
            raise AuthorizationGuardError(
                "Authorization already claimed by another execution ID"
            )

        if (
            claim.get(
                "status"
            )
            == "COMPLETED"
        ):

            if not state_path.exists():

                raise AuthorizationGuardError(
                    "Completed claim lacks execution state"
                )

            state = (
                read_json_with_checksum(
                    state_path
                )
            )

            validate_state(
                state=state,
                authorization=authorization,
                authorization_sha=auth_sha,
                execution_id=execution_id,
            )

            if (
                state[
                    "status"
                ]
                != "COMPLETED"
            ):
                raise AuthorizationGuardError(
                    "Completed claim has active state"
                )

            validate_completion_receipt(
                authorization=authorization,
                authorization_sha=auth_sha,
                execution_id=execution_id,
                execution_root=execution_root,
                state=state,
            )

            raise AuthorizationGuardError(
                "Completed authorization cannot be replayed"
            )

        if (
            claim.get(
                "status"
            )
            != "ACTIVE"
        ):
            raise AuthorizationGuardError(
                "Authorization claim has invalid status"
            )

        if not state_path.exists():

            raise AuthorizationGuardError(
                "Claim exists but execution state is missing"
            )

        state = (
            read_json_with_checksum(
                state_path
            )
        )

        validate_state(
            state=state,
            authorization=authorization,
            authorization_sha=auth_sha,
            execution_id=execution_id,
        )

        state = recover_state_from_checkpoints(
            state=state,
            authorization=authorization,
            authorization_sha=auth_sha,
            execution_id=execution_id,
            execution_root=execution_root,
        )

        if (
            state[
                "status"
            ]
            == "COMPLETED"
        ):

            finalize_completed_execution(
                authorization_path=authorization_path,
                authorization=authorization,
                authorization_sha=auth_sha,
                execution_id=execution_id,
                execution_root=execution_root,
                state=state,
            )

            raise AuthorizationGuardError(
                "Completed authorization cannot be replayed"
            )

        return {
            "authorization":
                authorization,
            "authorization_sha256":
                auth_sha,
            "claim":
                claim,
            "state":
                state,
            "execution_root":
                execution_root,
            "resumed":
                True,
        }


    if (
        state_path.exists()
        or checksum_path(
            state_path
        ).exists()
    ):

        raise AuthorizationGuardError(
            "Execution state exists without authorization claim"
        )


    claim = {
        "schema_version":
            1,

        "authorization_id":
            authorization[
                "authorization_id"
            ],

        "authorization_sha256":
            auth_sha,

        "execution_id":
            execution_id,

        "wave_id":
            EXPECTED_WAVE_ID,

        "execution_output_root":
            str(
                execution_root
            ),

        "authorized_execution_commit":
            authorization[
                "authorized_execution_commit"
            ],

        "status":
            "ACTIVE",
    }


    write_json_with_checksum(
        claim_path,
        claim,
        exclusive=True,
    )


    initial_chain = sha256_bytes(
        canonical_compact_bytes({
            "authorization_sha256":
                auth_sha,

            "execution_id":
                execution_id,

            "wave_b_request_manifest_sha256":
                EXPECTED_MANIFEST_SHA256,

            "state":
                "GENESIS",
        })
    )


    state = {
        "schema_version":
            1,

        "authorization_id":
            authorization[
                "authorization_id"
            ],

        "authorization_sha256":
            auth_sha,

        "execution_id":
            execution_id,

        "wave_id":
            EXPECTED_WAVE_ID,

        "wave_b_request_manifest_sha256":
            EXPECTED_MANIFEST_SHA256,

        "status":
            "ACTIVE",

        "completed_request_count":
            0,

        "next_request_sequence":
            1,

        "checkpoint_chain_sha256":
            initial_chain,
    }


    try:

        write_json_with_checksum(
            state_path,
            state,
            exclusive=True,
        )

    except Exception:

        # A claim without state deliberately fails closed.
        # Never silently erase the one-use claim here.
        raise


    return {
        "authorization":
            authorization,
        "authorization_sha256":
            auth_sha,
        "claim":
            claim,
        "state":
            state,
        "execution_root":
            execution_root,
        "resumed":
            False,
    }


def validate_state(
    *,
    state: dict,
    authorization: dict,
    authorization_sha: str,
    execution_id: str,
) -> None:

    exact = {
        "schema_version":
            1,

        "authorization_id":
            authorization[
                "authorization_id"
            ],

        "authorization_sha256":
            authorization_sha,

        "execution_id":
            execution_id,

        "wave_id":
            EXPECTED_WAVE_ID,

        "wave_b_request_manifest_sha256":
            EXPECTED_MANIFEST_SHA256,
    }

    for key, expected in exact.items():

        if (
            state.get(
                key
            )
            != expected
        ):
            raise AuthorizationGuardError(
                "Execution-state field mismatch: "
                + key
            )

    status = state.get(
        "status"
    )

    if status not in {
        "ACTIVE",
        "COMPLETED",
    }:
        raise AuthorizationGuardError(
            "Execution-state status invalid"
        )

    completed = state.get(
        "completed_request_count"
    )

    next_sequence = state.get(
        "next_request_sequence"
    )

    if (
        not isinstance(
            completed,
            int,
        )
        or completed < 0
        or completed
        > EXPECTED_MAXIMUM_REQUEST_COUNT
    ):
        raise AuthorizationGuardError(
            "Execution-state completed count invalid"
        )

    if (
        not isinstance(
            next_sequence,
            int,
        )
    ):
        raise AuthorizationGuardError(
            "Execution-state next sequence invalid"
        )

    if status == "ACTIVE":

        if (
            completed
            >= EXPECTED_MAXIMUM_REQUEST_COUNT
        ):
            raise AuthorizationGuardError(
                "Active state cannot already be complete"
            )

        if (
            next_sequence
            != completed + 1
        ):
            raise AuthorizationGuardError(
                "Active state sequence/count mismatch"
            )

    else:

        if (
            completed
            != EXPECTED_MAXIMUM_REQUEST_COUNT
        ):
            raise AuthorizationGuardError(
                "Completed state count mismatch"
            )

        if (
            next_sequence
            != EXPECTED_MAXIMUM_REQUEST_COUNT
            + 1
        ):
            raise AuthorizationGuardError(
                "Completed state next sequence mismatch"
            )

    chain = state.get(
        "checkpoint_chain_sha256"
    )

    if (
        not isinstance(
            chain,
            str,
        )
        or len(
            chain
        )
        != 64
    ):
        raise AuthorizationGuardError(
            "Execution-state checkpoint chain invalid"
        )


def recover_state_from_checkpoints(
    *,
    state: dict,
    authorization: dict,
    authorization_sha: str,
    execution_id: str,
    execution_root: Path,
) -> dict:

    validate_state(
        state=state,
        authorization=authorization,
        authorization_sha=authorization_sha,
        execution_id=execution_id,
    )

    while (
        state[
            "status"
        ]
        == "ACTIVE"
    ):

        sequence = state[
            "next_request_sequence"
        ]

        checkpoint_path = (
            request_checkpoint_path(
                execution_root,
                sequence,
            )
        )

        digest_path = checksum_path(
            checkpoint_path
        )

        if (
            not checkpoint_path.exists()
            and not digest_path.exists()
        ):

            checkpoint_root = (
                execution_root
                / CHECKPOINT_DIRECTORY
            )

            if checkpoint_root.exists():

                future = []

                for candidate in (
                    checkpoint_root.glob(
                        "*.json"
                    )
                ):

                    try:
                        candidate_sequence = int(
                            candidate.stem
                        )
                    except ValueError:
                        raise AuthorizationGuardError(
                            "Malformed checkpoint filename: "
                            + candidate.name
                        )

                    if (
                        candidate_sequence
                        > sequence
                    ):
                        future.append(
                            candidate_sequence
                        )

                if future:

                    raise AuthorizationGuardError(
                        "Future checkpoint exists beyond "
                        "current recovery boundary"
                    )

            return state

        checkpoint = (
            read_json_with_checksum(
                checkpoint_path
            )
        )

        expected_row = (
            manifest_row_for_sequence(
                sequence
            )
        )

        expected = {
            "schema_version":
                1,

            "authorization_id":
                authorization[
                    "authorization_id"
                ],

            "authorization_sha256":
                authorization_sha,

            "execution_id":
                execution_id,

            "wave_id":
                EXPECTED_WAVE_ID,

            "request_sequence":
                sequence,

            "request_identity_sha256":
                expected_row[
                    "request_identity_sha256"
                ],

            "previous_checkpoint_chain_sha256":
                state[
                    "checkpoint_chain_sha256"
                ],
        }

        for key, expected_value in (
            expected.items()
        ):

            if (
                checkpoint.get(
                    key
                )
                != expected_value
            ):
                raise AuthorizationGuardError(
                    "Recovery checkpoint mismatch: "
                    + key
                )

        terminal_receipt = (
            checkpoint.get(
                "terminal_receipt"
            )
        )

        validate_terminal_receipt(
            expected_row=expected_row,
            terminal_receipt=terminal_receipt,
        )

        checkpoint_sha = sha256_file(
            checkpoint_path
        )

        new_chain = sha256_bytes(
            (
                state[
                    "checkpoint_chain_sha256"
                ]
                + ":"
                + checkpoint_sha
            ).encode(
                "utf-8"
            )
        )

        completed = (
            state[
                "completed_request_count"
            ]
            + 1
        )

        if (
            completed
            > EXPECTED_MAXIMUM_REQUEST_COUNT
        ):
            raise AuthorizationGuardError(
                "Recovered checkpoint exceeds "
                "request ceiling"
            )

        status = (
            "COMPLETED"
            if completed
            == EXPECTED_MAXIMUM_REQUEST_COUNT
            else "ACTIVE"
        )

        state = {
            **state,

            "status":
                status,

            "completed_request_count":
                completed,

            "next_request_sequence":
                completed + 1,

            "checkpoint_chain_sha256":
                new_chain,
        }

        write_json_with_checksum(
            execution_state_path(
                execution_root
            ),
            state,
        )

        validate_state(
            state=state,
            authorization=authorization,
            authorization_sha=authorization_sha,
            execution_id=execution_id,
        )

    return state


def expected_completion_receipt(
    *,
    authorization: dict,
    authorization_sha: str,
    execution_id: str,
    execution_root: Path,
    state: dict,
) -> dict:

    if (
        state.get(
            "status"
        )
        != "COMPLETED"
    ):
        raise AuthorizationGuardError(
            "Cannot construct completion receipt "
            "for active execution"
        )

    state_path = (
        execution_state_path(
            execution_root
        )
    )

    return {
        "schema_version":
            1,

        "status":
            "COMPLETED",

        "authorization_id":
            authorization[
                "authorization_id"
            ],

        "authorization_sha256":
            authorization_sha,

        "execution_id":
            execution_id,

        "wave_id":
            EXPECTED_WAVE_ID,

        "wave_b_request_manifest_sha256":
            EXPECTED_MANIFEST_SHA256,

        "completed_request_count":
            EXPECTED_MAXIMUM_REQUEST_COUNT,

        "final_checkpoint_chain_sha256":
            state[
                "checkpoint_chain_sha256"
            ],

        "final_execution_state_sha256":
            sha256_file(
                state_path
            ),
    }


def validate_completion_receipt(
    *,
    authorization: dict,
    authorization_sha: str,
    execution_id: str,
    execution_root: Path,
    state: dict,
) -> dict:

    receipt_path = (
        completion_receipt_path(
            execution_root
        )
    )

    receipt = (
        read_json_with_checksum(
            receipt_path
        )
    )

    expected = (
        expected_completion_receipt(
            authorization=authorization,
            authorization_sha=authorization_sha,
            execution_id=execution_id,
            execution_root=execution_root,
            state=state,
        )
    )

    if receipt != expected:

        raise AuthorizationGuardError(
            "Completion receipt does not match "
            "completed execution state"
        )

    return receipt


def finalize_completed_execution(
    *,
    authorization_path: Path,
    authorization: dict,
    authorization_sha: str,
    execution_id: str,
    execution_root: Path,
    state: dict,
) -> dict:

    validate_state(
        state=state,
        authorization=authorization,
        authorization_sha=authorization_sha,
        execution_id=execution_id,
    )

    if (
        state[
            "status"
        ]
        != "COMPLETED"
    ):
        raise AuthorizationGuardError(
            "Cannot finalize active execution"
        )

    receipt_path = (
        completion_receipt_path(
            execution_root
        )
    )

    digest_path = checksum_path(
        receipt_path
    )

    expected_receipt = (
        expected_completion_receipt(
            authorization=authorization,
            authorization_sha=authorization_sha,
            execution_id=execution_id,
            execution_root=execution_root,
            state=state,
        )
    )

    if (
        receipt_path.exists()
        or digest_path.exists()
    ):

        receipt = (
            validate_completion_receipt(
                authorization=authorization,
                authorization_sha=authorization_sha,
                execution_id=execution_id,
                execution_root=execution_root,
                state=state,
            )
        )

    else:

        write_json_with_checksum(
            receipt_path,
            expected_receipt,
            exclusive=True,
        )

        receipt = (
            validate_completion_receipt(
                authorization=authorization,
                authorization_sha=authorization_sha,
                execution_id=execution_id,
                execution_root=execution_root,
                state=state,
            )
        )

    # Completion receipt is durable before the one-use
    # authorization claim is marked completed.
    claim_path = (
        claim_path_for_authorization(
            authorization_path
        )
    )

    claim = read_json_with_checksum(
        claim_path
    )

    if (
        claim.get(
            "authorization_sha256"
        )
        != authorization_sha
    ):
        raise AuthorizationGuardError(
            "Completion claim authorization mismatch"
        )

    if (
        claim.get(
            "execution_id"
        )
        != execution_id
    ):
        raise AuthorizationGuardError(
            "Completion claim execution mismatch"
        )

    if (
        claim.get(
            "status"
        )
        not in {
            "ACTIVE",
            "COMPLETED",
        }
    ):
        raise AuthorizationGuardError(
            "Completion claim status invalid"
        )

    claim[
        "status"
    ] = "COMPLETED"

    claim[
        "final_checkpoint_chain_sha256"
    ] = state[
        "checkpoint_chain_sha256"
    ]

    claim[
        "completed_request_count"
    ] = state[
        "completed_request_count"
    ]

    claim[
        "completion_receipt_sha256"
    ] = sha256_file(
        receipt_path
    )

    write_json_with_checksum(
        claim_path,
        claim,
    )

    return receipt


def manifest_row_for_sequence(
    sequence: int,
) -> dict[str, str]:

    rows = read_manifest()

    if (
        sequence < 1
        or sequence > len(
            rows
        )
    ):
        raise AuthorizationGuardError(
            "Request sequence outside frozen manifest"
        )

    row = rows[
        sequence - 1
    ]

    if (
        int(
            row[
                "request_sequence"
            ]
        )
        != sequence
    ):
        raise AuthorizationGuardError(
            "Frozen request sequence mismatch"
        )

    return row


def validate_exact_request(
    *,
    expected_row: dict[str, str],
    proposed_request: dict[str, str],
) -> None:

    fields = [
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

    for field in fields:

        if (
            str(
                proposed_request.get(
                    field,
                    ""
                )
            )
            != str(
                expected_row[
                    field
                ]
            )
        ):
            raise AuthorizationGuardError(
                "Proposed request differs from "
                "frozen manifest field: "
                + field
            )


def contains_forbidden_secret_field(
    value: Any,
) -> bool:

    forbidden_key_fragments = {
        "api_key",
        "apikey",
        "authorization",
        "ncbi_email",
        "email_address",
        "bearer",
        "secret",
        "token",
        "password",
    }

    if isinstance(
        value,
        dict,
    ):

        for key, child in value.items():

            lowered = str(
                key
            ).lower()

            if any(
                fragment in lowered
                for fragment
                in forbidden_key_fragments
            ):
                return True

            if contains_forbidden_secret_field(
                child
            ):
                return True

    elif isinstance(
        value,
        list,
    ):

        return any(
            contains_forbidden_secret_field(
                item
            )
            for item in value
        )

    return False


def validate_terminal_receipt(
    *,
    expected_row: dict[str, str],
    terminal_receipt: dict,
) -> None:

    if not isinstance(
        terminal_receipt,
        dict,
    ):
        raise AuthorizationGuardError(
            "Terminal receipt must be object"
        )

    if contains_forbidden_secret_field(
        terminal_receipt
    ):
        raise AuthorizationGuardError(
            "Terminal receipt contains credential-bearing field"
        )

    exact = {
        "wave_id":
            EXPECTED_WAVE_ID,

        "request_sequence":
            int(
                expected_row[
                    "request_sequence"
                ]
            ),

        "request_identity_sha256":
            expected_row[
                "request_identity_sha256"
            ],

        "provider":
            expected_row[
                "provider"
            ],

        "transport_route":
            expected_row[
                "transport_route"
            ],
    }

    for key, expected in exact.items():

        if (
            terminal_receipt.get(
                key
            )
            != expected
        ):
            raise AuthorizationGuardError(
                "Terminal receipt mismatch: "
                + key
            )

    terminal_status = (
        terminal_receipt.get(
            "terminal_status"
        )
    )

    if (
        not isinstance(
            terminal_status,
            str,
        )
        or not terminal_status.strip()
    ):
        raise AuthorizationGuardError(
            "Terminal receipt lacks terminal status"
        )

    archive_sha = (
        terminal_receipt.get(
            "archived_terminal_sha256"
        )
    )

    if (
        not isinstance(
            archive_sha,
            str,
        )
        or len(
            archive_sha
        )
        != 64
        or any(
            character
            not in "0123456789abcdef"
            for character
            in archive_sha
        )
    ):
        raise AuthorizationGuardError(
            "Terminal receipt archive SHA invalid"
        )


def checkpoint_terminal(
    *,
    context: dict,
    proposed_request: dict[str, str],
    terminal_receipt: dict,
) -> dict:

    authorization = context[
        "authorization"
    ]

    auth_sha = context[
        "authorization_sha256"
    ]

    execution_id = context[
        "state"
    ][
        "execution_id"
    ]

    execution_root = context[
        "execution_root"
    ]

    state_path = (
        execution_state_path(
            execution_root
        )
    )

    state = read_json_with_checksum(
        state_path
    )

    validate_state(
        state=state,
        authorization=authorization,
        authorization_sha=auth_sha,
        execution_id=execution_id,
    )

    if (
        state[
            "status"
        ]
        != "ACTIVE"
    ):
        raise AuthorizationGuardError(
            "Cannot checkpoint completed execution"
        )

    sequence = state[
        "next_request_sequence"
    ]

    if (
        sequence
        > authorization[
            "maximum_request_count"
        ]
    ):
        raise AuthorizationGuardError(
            "Authorization request ceiling exceeded"
        )

    expected_row = (
        manifest_row_for_sequence(
            sequence
        )
    )

    validate_exact_request(
        expected_row=expected_row,
        proposed_request=proposed_request,
    )

    validate_terminal_receipt(
        expected_row=expected_row,
        terminal_receipt=terminal_receipt,
    )


    checkpoint = {
        "schema_version":
            1,

        "authorization_id":
            authorization[
                "authorization_id"
            ],

        "authorization_sha256":
            auth_sha,

        "execution_id":
            execution_id,

        "wave_id":
            EXPECTED_WAVE_ID,

        "request_sequence":
            sequence,

        "request_identity_sha256":
            expected_row[
                "request_identity_sha256"
            ],

        "terminal_receipt":
            terminal_receipt,

        "previous_checkpoint_chain_sha256":
            state[
                "checkpoint_chain_sha256"
            ],
    }


    checkpoint_path = (
        request_checkpoint_path(
            execution_root,
            sequence,
        )
    )

    if (
        checkpoint_path.exists()
        or checksum_path(
            checkpoint_path
        ).exists()
    ):
        raise AuthorizationGuardError(
            "Request checkpoint already exists"
        )


    checkpoint_sha = sha256_bytes(
        canonical_json_bytes(
            checkpoint
        )
    )

    new_chain = sha256_bytes(
        (
            state[
                "checkpoint_chain_sha256"
            ]
            + ":"
            + checkpoint_sha
        ).encode(
            "utf-8"
        )
    )


    write_json_with_checksum(
        checkpoint_path,
        checkpoint,
        exclusive=True,
    )


    completed = (
        state[
            "completed_request_count"
        ]
        + 1
    )

    if (
        completed
        > EXPECTED_MAXIMUM_REQUEST_COUNT
    ):
        raise AuthorizationGuardError(
            "Checkpoint would exceed request ceiling"
        )


    status = (
        "COMPLETED"
        if completed
        == EXPECTED_MAXIMUM_REQUEST_COUNT
        else "ACTIVE"
    )


    next_state = {
        **state,

        "status":
            status,

        "completed_request_count":
            completed,

        "next_request_sequence":
            completed + 1,

        "checkpoint_chain_sha256":
            new_chain,
    }


    write_json_with_checksum(
        state_path,
        next_state,
    )


    if status == "COMPLETED":

        if (
            "authorization_path"
            not in context
        ):
            raise AuthorizationGuardError(
                "Authorization path absent at completion"
            )

        finalize_completed_execution(
            authorization_path=Path(
                context[
                    "authorization_path"
                ]
            ),
            authorization=authorization,
            authorization_sha=auth_sha,
            execution_id=execution_id,
            execution_root=execution_root,
            state=next_state,
        )



    context[
        "state"
    ] = next_state

    return next_state


def open_execution(
    *,
    authorization_path: Path,
    execution_id: str,
) -> dict:

    context = claim_execution(
        authorization_path=authorization_path,
        execution_id=execution_id,
    )

    context[
        "authorization_path"
    ] = str(
        authorization_path
    )

    return context
