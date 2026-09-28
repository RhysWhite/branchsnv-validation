from __future__ import annotations

"""Transport-injected Wave A execution core.

This module contains no live-network authority and no default
executor.  Its orchestration semantics are derived from the
checksum-pinned mock runner, which remains unchanged.
"""

from pathlib import Path
from typing import Callable

import retrieve_metadata_resolution_queue as transport
import triage_pre_review_text_wave_a_guard_v1 as guard
import triage_pre_review_text_wave_a_transport_evidence_adapter_v1 as adapter




class RunnerError(
    RuntimeError
):
    pass


class RunnerHalt(
    RunnerError
):
    pass


def preflight_environment(
    *,
    manifest_row: dict[str, str],
    environ: dict[str, str],
) -> None:

    if (
        manifest_row[
            "provider"
        ]
        == "pubmed"
    ):

        if (
            environ.get(
                "NCBI_API_KEY",
                "",
            ).strip()
        ):

            raise RunnerHalt(
                "NCBI API key is not permitted by frozen Wave A contract"
            )

        if not (
            environ.get(
                "NCBI_EMAIL",
                "",
            ).strip()
        ):

            raise RunnerHalt(
                "NCBI_EMAIL is required before PubMed execution"
            )


def raw_lookup_has_evidence(
    lookup_root: Path,
) -> bool:

    if not lookup_root.exists():

        return False

    return any(
        True
        for _ in lookup_root.rglob("*")
    )


def refreshed_state(
    context: dict,
) -> dict:

    state_path = (
        guard.execution_state_path(
            context[
                "execution_root"
            ]
        )
    )

    state = (
        guard.read_json_with_checksum(
            state_path
        )
    )

    guard.validate_state(
        state=state,
        authorization=
            context[
                "authorization"
            ],
        authorization_sha=
            context[
                "authorization_sha256"
            ],
        execution_id=
            state[
                "execution_id"
            ],
    )

    context[
        "state"
    ] = state

    return state


def checkpoint_from_durable_evidence(
    *,
    context: dict,
    manifest_row: dict[str, str],
    evidence: dict,
) -> dict:

    if (
        evidence.get(
            "checkpoint_eligible"
        )
        is not True
    ):

        raise RunnerHalt(
            "Adapter evidence is not checkpoint-eligible"
        )

    sequence = int(
        manifest_row[
            "request_sequence"
        ]
    )

    evidence_path = (
        adapter.evidence_path(
            context[
                "execution_root"
            ],
            sequence,
        )
    )

    durable = (
        adapter.read_evidence_path(
            evidence_path
        )
    )

    if durable != evidence:

        raise RunnerHalt(
            "Durable adapter evidence differs before checkpoint"
        )

    terminal_sha = (
        evidence.get(
            "transport_terminal_json_sha256"
        )
    )

    if (
        not isinstance(
            terminal_sha,
            str,
        )
        or not re_hex64(
            terminal_sha
        )
    ):

        raise RunnerHalt(
            "Checkpoint-eligible evidence lacks terminal SHA"
        )

    bundle_sha = (
        evidence.get(
            "raw_archive_bundle_sha256"
        )
    )

    if (
        not isinstance(
            bundle_sha,
            str,
        )
        or not re_hex64(
            bundle_sha
        )
    ):

        raise RunnerHalt(
            "Checkpoint-eligible evidence lacks raw archive bundle SHA"
        )

    receipt = {
        "wave_id":
            manifest_row[
                "wave_id"
            ],

        "request_sequence":
            sequence,

        "request_identity_sha256":
            manifest_row[
                "request_identity_sha256"
            ],

        "provider":
            manifest_row[
                "provider"
            ],

        "transport_route":
            manifest_row[
                "transport_route"
            ],

        "terminal_status":
            evidence[
                "adapter_status"
            ],

        "archived_terminal_sha256":
            terminal_sha,

        "adapter_evidence_sha256":
            adapter.sha256_file(
                evidence_path
            ),
    }

    return guard.checkpoint_terminal(
        context=context,
        proposed_request=manifest_row,
        terminal_receipt=receipt,
    )


def re_hex64(
    value: str,
) -> bool:

    if len(
        value
    ) != 64:

        return False

    return all(
        character
        in "0123456789abcdef"
        for character
        in value
    )


def reconstruct_and_checkpoint(
    *,
    context: dict,
    manifest_row: dict[str, str],
) -> dict:

    try:

        evidence = (
            adapter.verified_evidence(
                manifest_row=
                    manifest_row,
                archive_root=
                    context[
                        "execution_root"
                    ],
                transport_module=
                    transport,
            )
        )

    except adapter.ProviderIdentityMismatch as exc:

        fault = (
            adapter.fault_evidence(
                manifest_row=
                    manifest_row,
                archive_root=
                    context[
                        "execution_root"
                    ],
                transport_terminal_status=
                    "success",
                adapter_status=
                    "provider_identity_mismatch",
            )
        )

        adapter.write_evidence(
            execution_root=
                context[
                    "execution_root"
                ],
            evidence=fault,
        )

        raise RunnerHalt(
            "Provider identity mismatch; execution halted"
        ) from exc

    except adapter.TransportEvidenceFault as exc:

        fault = (
            adapter.fault_evidence(
                manifest_row=
                    manifest_row,
                archive_root=
                    context[
                        "execution_root"
                    ],
                transport_terminal_status=
                    "unknown",
                adapter_status=
                    "archive_verification_failure",
            )
        )

        adapter.write_evidence(
            execution_root=
                context[
                    "execution_root"
                ],
            evidence=fault,
        )

        raise RunnerHalt(
            "Transport archive verification failed; execution halted"
        ) from exc

    adapter.write_evidence(
        execution_root=
            context[
                "execution_root"
            ],
        evidence=evidence,
    )

    return checkpoint_from_durable_evidence(
        context=context,
        manifest_row=manifest_row,
        evidence=evidence,
    )


def run_one(
    *,
    context: dict,
    executor: Callable,
    retry_sleeper: Callable[[float], None],
    environ: dict[str, str],
) -> dict:

    adapter.load_contract()

    state = refreshed_state(
        context
    )

    if (
        state[
            "status"
        ]
        != "ACTIVE"
    ):

        raise RunnerHalt(
            "Wave A execution is not active"
        )

    sequence = state[
        "next_request_sequence"
    ]

    manifest_row = (
        guard.manifest_row_for_sequence(
            sequence
        )
    )

    evidence_path = (
        adapter.evidence_path(
            context[
                "execution_root"
            ],
            sequence,
        )
    )

    evidence_checksum = (
        adapter.checksum_path(
            evidence_path
        )
    )

    if (
        evidence_path.exists()
        or evidence_checksum.exists()
    ):

        evidence = (
            adapter.read_evidence_path(
                evidence_path
            )
        )

        if (
            evidence.get(
                "request_identity_sha256"
            )
            != manifest_row[
                "request_identity_sha256"
            ]
        ):

            raise RunnerHalt(
                "Existing adapter evidence belongs to another request"
            )

        if (
            evidence.get(
                "checkpoint_eligible"
            )
            is not True
        ):

            raise RunnerHalt(
                "Existing fault evidence requires explicit recovery design"
            )

        reconstructed = (
            adapter.verified_evidence(
                manifest_row=
                    manifest_row,
                archive_root=
                    context[
                        "execution_root"
                    ],
                transport_module=
                    transport,
            )
        )

        if reconstructed != evidence:

            raise RunnerHalt(
                "Durable evidence no longer reproduces from complete raw archive"
            )

        return checkpoint_from_durable_evidence(
            context=context,
            manifest_row=manifest_row,
            evidence=evidence,
        )

    transport_row = (
        adapter.manifest_to_transport_row(
            manifest_row
        )
    )

    lookup_root = (
        adapter.transport_lookup_root(
            context[
                "execution_root"
            ],
            transport_row,
        )
    )

    if raw_lookup_has_evidence(
        lookup_root
    ):

        terminal_path = (
            lookup_root
            / "terminal.json"
        )

        if not terminal_path.is_file():

            fault = (
                adapter.fault_evidence(
                    manifest_row=
                        manifest_row,
                    archive_root=
                        context[
                            "execution_root"
                        ],
                    transport_terminal_status=
                        "unknown",
                    adapter_status=
                        "missing_terminal_archive",
                )
            )

            adapter.write_evidence(
                execution_root=
                    context[
                        "execution_root"
                    ],
                evidence=fault,
            )

            raise RunnerHalt(
                "Partial raw transport archive exists; automatic request replay forbidden"
            )

        return reconstruct_and_checkpoint(
            context=context,
            manifest_row=manifest_row,
        )

    preflight_environment(
        manifest_row=manifest_row,
        environ=environ,
    )

    result = (
        transport.transport_lookup(
            transport_row,
            archive_root=
                context[
                    "execution_root"
                ],
            executor=
                executor,
            sleeper=
                retry_sleeper,
            environ=
                environ,
        )
    )

    status = result.get(
        "terminal_status"
    )

    if status not in {
        "success",
        "not_found",
    }:

        allowed_faults = {
            "authentication_failure",
            "redirect_failure",
            "response_integrity_failure",
            "retry_exhausted",
        }

        adapter_status = (
            str(
                status
            )
            if status in allowed_faults
            else "unknown_transport_status"
        )

        fault = (
            adapter.fault_evidence(
                manifest_row=
                    manifest_row,
                archive_root=
                    context[
                        "execution_root"
                    ],
                transport_terminal_status=
                    str(
                        status
                    ),
                adapter_status=
                    adapter_status,
            )
        )

        adapter.write_evidence(
            execution_root=
                context[
                    "execution_root"
                ],
            evidence=fault,
        )

        raise RunnerHalt(
            "Transport returned non-checkpointing terminal status: "
            + str(
                status
            )
        )

    return reconstruct_and_checkpoint(
        context=context,
        manifest_row=manifest_row,
    )
