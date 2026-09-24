#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import tempfile

from datetime import datetime, timezone
from pathlib import Path

import retrieve_metadata_resolution_queue as transport
import metadata_resolution_transport_archive as archive


FIXED_NOW = datetime(
    2026,
    9,
    24,
    0,
    0,
    tzinfo=timezone.utc,
)


def now_fn():
    return FIXED_NOW


def fake_pacer():
    return transport.ProviderPacer(
        interval_seconds=0.0,
        sleeper=lambda _: None,
    )


def oa_row(
    lookup_id="lookup:oa",
    identifier="W1",
):
    return {
        "logical_lookup_id":
            lookup_id,

        "provider":
            "openalex",

        "route":
            "work_by_openalex_id",

        "identifier_namespace":
            "openalex",

        "identifier":
            identifier,
    }


def oc_row(
    lookup_id="lookup:oc",
    identifier="br/1",
):
    return {
        "logical_lookup_id":
            lookup_id,

        "provider":
            "opencitations_meta",

        "route":
            "metadata_by_omid",

        "identifier_namespace":
            "omid",

        "identifier":
            identifier,
    }


# ------------------------------------------------------------
# Full frozen queue is still exactly 1,731 logical lookups.
# ------------------------------------------------------------

frozen = transport.read_queue()

assert len(frozen) == 1731

assert archive.queue_is_frozen_full_set(
    frozen
)

print(
    "PASS | archive layer recognizes exact frozen 1,731-lookup queue"
)


# ------------------------------------------------------------
# Small synthetic execution writes terminal raw evidence.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    rows = [
        oa_row(),
        oc_row(),
    ]

    calls = []

    def executor(request):
        calls.append(
            (
                request.provider,
                request.url,
            )
        )

        if (
            request.provider
            == "openalex"
        ):
            return transport.HTTPResponse(
                status=200,
                url=request.url,
                headers=(),
                body=json.dumps({
                    "id":
                        "https://openalex.org/W1",
                    "ids": {},
                }).encode(),
            )

        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=b"[]",
        )

    results = archive.execute_queue(
        rows,
        archive_root=root,
        executor=executor,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    assert [
        result[
            "terminal_status"
        ]
        for result in results
    ] == [
        "success",
        "not_found",
    ]

    assert len(calls) == 2

    manifest = (
        archive.write_archive_state(
            rows,
            root,
            now_fn=now_fn,
        )
    )

    # A small synthetic archive may have complete
    # coverage of its local rows, but cannot be called
    # COMPLETE because it is not the frozen 1,731 set.
    assert manifest[
        "status"
    ] == "INCOMPLETE"

    assert manifest[
        "archive_is_exact_frozen_queue"
    ] is False

    archive.validate_archive(
        rows,
        root,
        require_complete=False,
    )

    assert (
        root / "manifest.json"
    ).is_file()

    assert (
        root / "lookup_status.tsv"
    ).is_file()

    assert (
        root / "attempts.tsv"
    ).is_file()

    assert (
        root / "redirects.tsv"
    ).is_file()

    assert (
        root / "checksums.sha256"
    ).is_file()

print(
    "PASS | synthetic archive writes all required production ledgers"
)


# ------------------------------------------------------------
# Every executor call is paced, including redirect hops.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    providers = []

    class RecordingPacer:
        def wait(
            self,
            provider,
        ):
            providers.append(
                provider
            )

    count = [0]

    def redirect_then_ok(request):
        count[0] += 1

        if count[0] == 1:
            return transport.HTTPResponse(
                status=301,
                url=request.url,
                headers=(
                    (
                        "Location",
                        "https://api.openalex.org/works/W2",
                    ),
                ),
                body=b"redirect",
            )

        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W2",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [
            oa_row(),
        ],
        archive_root=root,
        executor=redirect_then_ok,
        pacer=RecordingPacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    assert providers == [
        "openalex",
        "openalex",
    ]

print(
    "PASS | pacing wraps every redirect HTTP exchange"
)


# ------------------------------------------------------------
# Pacing also wraps retry exchanges.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    providers = []

    class RecordingPacer:
        def wait(
            self,
            provider,
        ):
            providers.append(
                provider
            )

    calls = [0]

    def retry_then_ok(request):
        calls[0] += 1

        if calls[0] == 1:
            return transport.HTTPResponse(
                status=503,
                url=request.url,
                headers=(),
                body=b"",
            )

        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [
            oa_row(),
        ],
        archive_root=root,
        executor=retry_then_ok,
        pacer=RecordingPacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    assert providers == [
        "openalex",
        "openalex",
    ]

print(
    "PASS | pacing wraps every retry HTTP exchange"
)


# ------------------------------------------------------------
# Interrupted attempt is preserved and resume begins at next.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    lookup_root = archive.lookup_root(
        root,
        row[
            "logical_lookup_id"
        ],
    )

    attempt_1 = (
        lookup_root
        / "attempt_01"
    )

    attempt_1.mkdir(
        parents=True,
        exist_ok=True,
    )

    request_bytes = (
        transport.canonical_json_bytes({
            "timestamp_utc":
                "2026-09-24T00:00:00+00:00",

            "logical_lookup_id":
                row[
                    "logical_lookup_id"
                ],

            "provider":
                row["provider"],

            "route":
                row["route"],

            "identifier_namespace":
                row[
                    "identifier_namespace"
                ],

            "identifier":
                row["identifier"],

            "attempt_number":
                1,

            "method":
                "GET",

            "url":
                "https://api.openalex.org/works/W1",

            "headers":
                [],
        })
    )

    (
        attempt_1
        / "request.json"
    ).write_bytes(
        request_bytes
    )

    before = hashlib.sha256(
        request_bytes
    ).hexdigest()

    state = archive.infer_lookup_state(
        root,
        row,
    )

    assert state[
        "state"
    ] == "pending"

    assert state[
        "start_attempt_number"
    ] == 2

    assert state[
        "prior_attempts"
    ] == [
        {
            "attempt_number":
                1,

            "outcome":
                "interrupted_transport_attempt",
        }
    ]

    def ok(request):
        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    results = archive.execute_queue(
        [row],
        archive_root=root,
        executor=ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    assert results[0][
        "attempt_count"
    ] == 2

    after = hashlib.sha256(
        (
            attempt_1
            / "request.json"
        ).read_bytes()
    ).hexdigest()

    assert before == after

    assert (
        lookup_root
        / "attempt_02"
        / "attempt.json"
    ).exists()

print(
    "PASS | interrupted prior attempt is preserved during resume"
)


# ------------------------------------------------------------
# Existing accepted terminal lookup is not re-requested.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    calls = [0]

    def ok(request):
        calls[0] += 1

        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    assert calls[0] == 1

    second = archive.execute_queue(
        [row],
        archive_root=root,
        executor=ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    assert calls[0] == 1

    assert second[0][
        "resume_action"
    ] == "reused_terminal"

print(
    "PASS | valid terminal lookup is reused without another request"
)


# ------------------------------------------------------------
# Archived terminal identity mismatch fails closed.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    def ok(request):
        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    changed = dict(row)
    changed["identifier"] = "W999"

    try:
        archive.verify_terminal_for_row(
            root,
            changed,
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Mismatched archived lookup identity accepted"
        )

print(
    "PASS | resume requires exact provider/route/identifier identity"
)


# ------------------------------------------------------------
# Retry exhaustion persists as failure and blocks COMPLETE.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    def unavailable(request):
        return transport.HTTPResponse(
            status=503,
            url=request.url,
            headers=(),
            body=b"",
        )

    results = archive.execute_queue(
        [row],
        archive_root=root,
        executor=unavailable,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    assert results[0][
        "terminal_status"
    ] == "retry_exhausted"

    assert archive.failure_path(
        root,
        row[
            "logical_lookup_id"
        ],
    ).exists()

    manifest = archive.write_archive_state(
        [row],
        root,
        now_fn=now_fn,
    )

    assert manifest[
        "status"
    ] == "INCOMPLETE"

    status = archive.collect_lookup_status(
        [row],
        root,
    )

    assert status[0][
        "status"
    ] == "retry_exhausted"

print(
    "PASS | retry exhaustion persists and blocks COMPLETE"
)


# ------------------------------------------------------------
# Redirect ledger records redirect evidence.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    count = [0]

    def redirected(request):
        count[0] += 1

        if count[0] == 1:
            return transport.HTTPResponse(
                status=301,
                url=request.url,
                headers=(
                    (
                        "Location",
                        "https://api.openalex.org/works/W2",
                    ),
                ),
                body=b"r",
            )

        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W2",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=redirected,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    redirects = archive.collect_redirect_rows(
        [row],
        root,
    )

    assert len(redirects) == 1

    assert redirects[0][
        "status"
    ] == 301

    assert redirects[0][
        "location"
    ] == (
        "https://api.openalex.org/works/W2"
    )

print(
    "PASS | redirects.tsv source data preserves redirect target"
)


# ------------------------------------------------------------
# Checksums detect ledger/raw tampering.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    def ok(request):
        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    archive.write_archive_state(
        [row],
        root,
        now_fn=now_fn,
    )

    archive.validate_checksums(
        root
    )

    (
        root
        / "lookup_status.tsv"
    ).write_text(
        "tampered\\n",
        encoding="utf-8",
    )

    try:
        archive.validate_checksums(
            root
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Tampered ledger passed checksum validation"
        )

print(
    "PASS | archive checksum manifest detects tampering"
)


# ------------------------------------------------------------
# Credentials absent from full generated archive.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    secret = (
        "NEVER-WRITE-THIS-SECRET"
    )

    def ok(request):
        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={
            "OPENALEX_API_KEY":
                secret,
        },
        now_fn=now_fn,
    )

    archive.write_archive_state(
        [row],
        root,
        now_fn=now_fn,
    )

    assert not archive.scan_for_secret(
        root,
        secret,
    )

print(
    "PASS | credential absent from raw evidence and production ledgers"
)


# ------------------------------------------------------------
# Full frozen completion gate requires all 1,731 accepted.
# ------------------------------------------------------------

synthetic_terminals = [
    {
        "logical_lookup_id":
            row[
                "logical_lookup_id"
            ],

        "terminal_status":
            "success",
    }
    for row in frozen
]

completion = transport.validate_completion(
    frozen,
    synthetic_terminals,
)

assert completion[
    "status"
] == "COMPLETE"

assert completion[
    "logical_lookup_count"
] == 1731

synthetic_terminals[-1][
    "terminal_status"
] = "retry_exhausted"

completion = transport.validate_completion(
    frozen,
    synthetic_terminals,
)

assert completion[
    "status"
] == "INCOMPLETE"

print(
    "PASS | full frozen 1,731-lookup completion gate exercised"
)


# ------------------------------------------------------------
# No synthetic subarchive can claim production COMPLETE.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    manifest = archive.write_archive_state(
        [
            oa_row(),
        ],
        root,
        now_fn=now_fn,
    )

    assert manifest[
        "status"
    ] == "INCOMPLETE"

    assert manifest[
        "archive_is_exact_frozen_queue"
    ] is False

print(
    "PASS | partial/synthetic queue cannot claim production COMPLETE"
)


# ------------------------------------------------------------
# Live execution remains hard-disabled.
# ------------------------------------------------------------

assert (
    transport.LIVE_EXECUTION_ENABLED
    is False
)

print(
    "PASS | archive orchestration does not enable live execution"
)


# ------------------------------------------------------------
# No production retrieval directory exists.
# ------------------------------------------------------------

production = (
    Path(__file__).resolve().parent.parent.parent
    / "results"
    / "07_comparative_landscape"
    / "metadata_resolution_retrieval"
)

assert not production.exists()

print(
    "PASS | archive tests created no production retrieval directory"
)

print()
print(
    "PASS | all metadata-resolution archive/resume synthetic tests"
)


# ------------------------------------------------------------
# A corrupted earlier redirect-hop body must be detected
# BEFORE a new checksums.sha256 can bless it.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    count = [0]

    def redirected(request):
        count[0] += 1

        if count[0] == 1:
            return transport.HTTPResponse(
                status=301,
                url=request.url,
                headers=(
                    (
                        "Location",
                        "https://api.openalex.org/works/W2",
                    ),
                ),
                body=b"ORIGINAL-REDIRECT-BODY",
            )

        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W2",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=redirected,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    lookup_root = archive.lookup_root(
        root,
        row[
            "logical_lookup_id"
        ],
    )

    redirect_body = (
        lookup_root
        / "attempt_01"
        / "hop_00_body.bin"
    )

    redirect_body.write_bytes(
        b"CORRUPTED"
    )

    try:
        archive.write_archive_state(
            [row],
            root,
            now_fn=now_fn,
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Corrupted redirect-hop evidence "
            "was re-checksummed as valid"
        )

print(
    "PASS | corrupted earlier redirect hop cannot be re-blessed"
)


# ------------------------------------------------------------
# Corrupted earlier retry body also fails before checksumming.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    count = [0]

    def retry_then_ok(request):
        count[0] += 1

        if count[0] == 1:
            return transport.HTTPResponse(
                status=503,
                url=request.url,
                headers=(),
                body=b"ORIGINAL-503",
            )

        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=retry_then_ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    lookup_root = archive.lookup_root(
        root,
        row[
            "logical_lookup_id"
        ],
    )

    (
        lookup_root
        / "attempt_01"
        / "hop_00_body.bin"
    ).write_bytes(
        b"CORRUPTED-503"
    )

    try:
        archive.write_archive_state(
            [row],
            root,
            now_fn=now_fn,
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Corrupted retry evidence "
            "was re-checksummed as valid"
        )

print(
    "PASS | corrupted earlier retry evidence cannot be re-blessed"
)


# ------------------------------------------------------------
# request.json identity tampering fails closed.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    def ok(request):
        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    request_path = (
        archive.lookup_root(
            root,
            row[
                "logical_lookup_id"
            ],
        )
        / "attempt_01"
        / "request.json"
    )

    value = json.loads(
        request_path.read_text(
            encoding="utf-8"
        )
    )

    value[
        "identifier"
    ] = "W999"

    request_path.write_bytes(
        transport.canonical_json_bytes(
            value
        )
    )

    try:
        archive.write_archive_state(
            [row],
            root,
            now_fn=now_fn,
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Tampered request identity accepted"
        )

print(
    "PASS | archived request identity tampering fails closed"
)


# ------------------------------------------------------------
# Crash after successful attempt.json but before terminal.json
# is finalised WITHOUT another HTTP request.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    def ok(request):
        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    lookup_root = archive.lookup_root(
        root,
        row[
            "logical_lookup_id"
        ],
    )

    terminal = (
        lookup_root
        / "terminal.json"
    )

    terminal.unlink()

    state = archive.infer_lookup_state(
        root,
        row,
    )

    assert state[
        "state"
    ] == "accepted_unfinalized"

    calls = [0]

    def must_not_call(request):
        calls[0] += 1
        raise AssertionError(
            "Network should not be called "
            "to finalise existing accepted evidence"
        )

    result = archive.execute_queue(
        [row],
        archive_root=root,
        executor=must_not_call,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    assert calls[0] == 0

    assert result[0][
        "resume_action"
    ] == "finalized_existing_terminal"

    assert terminal.exists()

    archive.verify_terminal_for_row(
        root,
        row,
    )

print(
    "PASS | accepted attempt survives terminal-write crash without re-request"
)


# ------------------------------------------------------------
# failure.json attempt-count tampering fails closed.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    def unavailable(request):
        return transport.HTTPResponse(
            status=503,
            url=request.url,
            headers=(),
            body=b"",
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=unavailable,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    failure = archive.failure_path(
        root,
        row[
            "logical_lookup_id"
        ],
    )

    value = json.loads(
        failure.read_text(
            encoding="utf-8"
        )
    )

    value[
        "attempt_count"
    ] = 4

    failure.write_bytes(
        transport.canonical_json_bytes(
            value
        )
    )

    try:
        archive.validate_lookup_raw_evidence(
            root,
            row,
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Tampered failure attempt count accepted"
        )

print(
    "PASS | failure-ledger/attempt inconsistency fails closed"
)


# ------------------------------------------------------------
# Final validation requires exact checksum-file coverage.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    def ok(request):
        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    archive.write_archive_state(
        [row],
        root,
        now_fn=now_fn,
    )

    (
        root
        / "UNLISTED_FILE"
    ).write_bytes(
        b"x"
    )

    try:
        archive.validate_checksums(
            root,
            require_exact_coverage=True,
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Unchecksummed archive file accepted"
        )

print(
    "PASS | final checksum validation requires exact file coverage"
)


# ------------------------------------------------------------
# Live runner gate occurs BEFORE output-directory creation.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = (
        Path(tmp)
        / "must-not-exist"
    )

    assert not root.exists()

    try:
        archive.run_frozen_queue_live(
            archive_root=root,
            environ={
                "BRANCHSNV_ALLOW_METADATA_NETWORK":
                    "YES",
            },
        )

    except transport.LiveExecutionBlocked:
        pass

    else:
        raise AssertionError(
            "Live runner unexpectedly passed hard gate"
        )

    assert not root.exists()

print(
    "PASS | live runner hard gate precedes production-directory creation"
)


# ------------------------------------------------------------
# write_archive_state must not emit a manifest while accepted
# evidence lacks terminal.json.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    def ok(request):
        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    lookup_root = archive.lookup_root(
        root,
        row[
            "logical_lookup_id"
        ],
    )

    (
        lookup_root
        / "terminal.json"
    ).unlink()

    state = archive.infer_lookup_state(
        root,
        row,
    )

    assert state[
        "state"
    ] == "accepted_unfinalized"

    try:
        archive.write_archive_state(
            [row],
            root,
            now_fn=now_fn,
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Archive writer summarized "
            "accepted-unfinalized evidence"
        )

    assert not (
        root
        / "manifest.json"
    ).exists()

print(
    "PASS | archive writer cannot emit manifest before accepted evidence is finalised"
)


# ------------------------------------------------------------
# write_archive_state must not summarize a failure merely
# inferred from attempts unless failure.json has been
# materialised.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    lookup_root = archive.lookup_root(
        root,
        row[
            "logical_lookup_id"
        ],
    )

    attempt = (
        lookup_root
        / "attempt_01"
    )

    attempt.mkdir(
        parents=True,
        exist_ok=True,
    )

    request = transport.build_request(
        row,
        environ={},
    )

    (
        attempt
        / "request.json"
    ).write_bytes(
        transport.canonical_json_bytes({
            "timestamp_utc":
                "2026-09-24T00:00:00+00:00",

            "logical_lookup_id":
                row[
                    "logical_lookup_id"
                ],

            "provider":
                row["provider"],

            "route":
                row["route"],

            "identifier_namespace":
                row[
                    "identifier_namespace"
                ],

            "identifier":
                row["identifier"],

            "attempt_number":
                1,

            "method":
                "GET",

            "url":
                transport.sanitized_url(
                    request.url
                ),

            "headers":
                list(
                    transport.redact_headers(
                        request.headers
                    )
                ),
        })
    )

    (
        attempt
        / "hop_00_body.bin"
    ).write_bytes(
        b""
    )

    (
        attempt
        / "hop_00_response.json"
    ).write_bytes(
        transport.canonical_json_bytes({
            "hop_number":
                0,

            "request_url":
                transport.sanitized_url(
                    request.url
                ),

            "request_headers":
                list(
                    transport.redact_headers(
                        request.headers
                    )
                ),

            "response_status":
                401,

            "response_url":
                transport.sanitized_url(
                    request.url
                ),

            "response_headers":
                [],

            "body_file":
                "hop_00_body.bin",

            "body_sha256":
                transport.sha256_bytes(
                    b""
                ),

            "body_length":
                0,
        })
    )

    (
        attempt
        / "attempt.json"
    ).write_bytes(
        transport.canonical_json_bytes({
            "attempt_number":
                1,

            "outcome":
                "authentication_failure",

            "http_status":
                401,
        })
    )

    state = archive.infer_lookup_state(
        root,
        row,
    )

    assert state[
        "state"
    ] == "failure"

    assert not archive.failure_path(
        root,
        row[
            "logical_lookup_id"
        ],
    ).exists()

    try:
        archive.write_archive_state(
            [row],
            root,
            now_fn=now_fn,
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Archive writer summarized "
            "failure without failure.json"
        )

print(
    "PASS | archive writer requires materialised failure record"
)


# ------------------------------------------------------------
# A forged attempts.tsv must fail even if checksums.sha256 is
# regenerated afterwards.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    calls = [0]

    def retry_then_ok(request):
        calls[0] += 1

        if calls[0] == 1:
            return transport.HTTPResponse(
                status=503,
                url=request.url,
                headers=(),
                body=b"retry",
            )

        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=retry_then_ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    archive.write_archive_state(
        [row],
        root,
        now_fn=now_fn,
    )

    attempts_path = (
        root
        / "attempts.tsv"
    )

    value = attempts_path.read_text(
        encoding="utf-8"
    )

    assert "retryable_http_status" in value

    attempts_path.write_text(
        value.replace(
            "retryable_http_status",
            "FORGED_OUTCOME",
            1,
        ),
        encoding="utf-8",
    )

    # Simulate a subsequently regenerated checksum snapshot.
    archive.write_checksums(
        root
    )

    archive.validate_checksums(
        root,
        require_exact_coverage=True,
    )

    try:
        archive.validate_archive(
            [row],
            root,
            require_complete=False,
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Semantically forged attempts.tsv "
            "passed after checksum regeneration"
        )

print(
    "PASS | re-checksummed attempts.tsv forgery fails semantic validation"
)


# ------------------------------------------------------------
# A forged redirects.tsv must likewise fail after checksum
# regeneration.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    calls = [0]

    def redirected(request):
        calls[0] += 1

        if calls[0] == 1:
            return transport.HTTPResponse(
                status=301,
                url=request.url,
                headers=(
                    (
                        "Location",
                        "https://api.openalex.org/works/W2",
                    ),
                ),
                body=b"redirect",
            )

        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W2",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=redirected,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    archive.write_archive_state(
        [row],
        root,
        now_fn=now_fn,
    )

    redirects_path = (
        root
        / "redirects.tsv"
    )

    value = redirects_path.read_text(
        encoding="utf-8"
    )

    assert (
        "https://api.openalex.org/works/W2"
        in value
    )

    redirects_path.write_text(
        value.replace(
            "https://api.openalex.org/works/W2",
            "https://api.openalex.org/works/W999",
            1,
        ),
        encoding="utf-8",
    )

    archive.write_checksums(
        root
    )

    archive.validate_checksums(
        root,
        require_exact_coverage=True,
    )

    try:
        archive.validate_archive(
            [row],
            root,
            require_complete=False,
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Semantically forged redirects.tsv "
            "passed after checksum regeneration"
        )

print(
    "PASS | re-checksummed redirects.tsv forgery fails semantic validation"
)


# ------------------------------------------------------------
# lookup_status.tsv must also reproduce exactly from raw state,
# rather than merely containing plausible values.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = oa_row()

    def ok(request):
        return transport.HTTPResponse(
            status=200,
            url=request.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    archive.execute_queue(
        [row],
        archive_root=root,
        executor=ok,
        pacer=fake_pacer(),
        retry_sleeper=lambda _: None,
        environ={},
        now_fn=now_fn,
    )

    archive.write_archive_state(
        [row],
        root,
        now_fn=now_fn,
    )

    status_path = (
        root
        / "lookup_status.tsv"
    )

    value = status_path.read_text(
        encoding="utf-8"
    )

    status_path.write_text(
        value.replace(
            "\t1\n",
            "\t999\n",
            1,
        ),
        encoding="utf-8",
    )

    archive.write_checksums(
        root
    )

    try:
        archive.validate_archive(
            [row],
            root,
            require_complete=False,
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Semantically forged lookup_status.tsv "
            "passed after checksum regeneration"
        )

print(
    "PASS | all production TSV ledgers must reproduce from raw evidence"
)
