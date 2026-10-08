from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Callable

import retrieve_metadata_resolution_queue as transport
import triage_pre_review_text_wave_a_guard_v1 as guard
import triage_pre_review_text_wave_a_runner_core_v1 as core
import triage_pre_review_text_wave_a_transport_evidence_adapter_v1 as adapter


CONFIRMATION_LITERAL = (
    "EXECUTE-AUTHORIZED-WAVE-A"
)

COLD_START_SECONDS = 0.5

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

CANONICAL_AUTHORIZATION_PATH = (
    REPO_ROOT
    / "results/07_comparative_landscape/"
      "triage_pre_review_text_retrieval_v1/"
      "live_wave_a/authorization.json"
).resolve()

ROOT = (
    REPO_ROOT
    / "experiments/07_comparative_landscape"
)

FROZEN_DEPENDENCIES = {
    "live_entrypoint_base_design": (
        ROOT
        / "triage_pre_review_text_wave_a_live_entrypoint_v1_design.json",
        "84078785db79d2016739e8d4dd003917edf8ba79a5092b96a9f72d4fcd724e77",
    ),

    "live_entrypoint_amendment_01": (
        ROOT
        / "triage_pre_review_text_wave_a_live_entrypoint_v1_amendment_01_design.json",
        "0e2540581f41b101e130922f96ecdcf0f28f5e1a505d1a0ea5c7becfa2423c19",
    ),

    "frozen_mock_runner": (
        ROOT
        / "triage_pre_review_text_wave_a_mock_runner_v1.py",
        "21c67dd6791aac29d995ab33828ec6ff444fd4e52d911a10fd20809d30ca5242",
    ),

    "transport_evidence_adapter": (
        ROOT
        / "triage_pre_review_text_wave_a_transport_evidence_adapter_v1.py",
        "30a311626b3e99e6520601585b87df3b600991094d7724cd358b52159d902bac",
    ),

    "authorization_guard": (
        ROOT
        / "triage_pre_review_text_wave_a_guard_v1.py",
        "40dadd678bfe282e196ef007dbb443e4672c578055f1608d737625bae9c5b7af",
    ),

    "exact_transport": (
        ROOT
        / "retrieve_metadata_resolution_queue.py",
        "9c8c11edbbec86e5cbf857f25c1bf576a0638ba5cdcf69d1fa2a8b8bfc1a994f",
    ),

    "live_retrieval_design": (
        ROOT
        / "triage_pre_review_text_live_retrieval_v1_design.json",
        "3dff9e1a41196343adc02951b7a88a2b1306e7df05838f3b2ab50ed53ce16172",
    ),
}


class LiveEntrypointError(
    RuntimeError
):
    pass


def sha256_file(
    path: Path,
) -> str:

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def validate_frozen_dependencies(
) -> None:

    for name, (
        path,
        expected_sha,
    ) in FROZEN_DEPENDENCIES.items():

        if not path.is_file():

            raise LiveEntrypointError(
                "Frozen dependency missing: "
                + name
            )

        actual = sha256_file(
            path
        )

        if actual != expected_sha:

            raise LiveEntrypointError(
                "Frozen dependency hash mismatch: "
                + name
            )


def authorization_is_tracked(
    path: Path,
) -> bool:

    resolved = path.resolve()

    try:

        relative = resolved.relative_to(
            REPO_ROOT
        )

    except ValueError as exc:

        raise LiveEntrypointError(
            "Authorization path is outside repository"
        ) from exc

    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--error-unmatch",
            "--",
            relative.as_posix(),
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


@contextmanager
def execution_process_lock(
    authorization_path: Path,
):

    handle = authorization_path.open(
        "rb"
    )

    locked = False

    try:

        try:

            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_EX
                | fcntl.LOCK_NB,
            )

            locked = True

        except BlockingIOError as exc:

            raise LiveEntrypointError(
                "Another Wave A execution process already holds "
                "the authorization lock"
            ) from exc

        yield

    finally:

        if locked:

            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_UN,
            )

        handle.close()


def validate_live_environment(
    environ: dict[str, str],
) -> None:

    if (
        environ.get(
            "NCBI_API_KEY",
            "",
        ).strip()
    ):

        raise LiveEntrypointError(
            "NCBI_API_KEY is forbidden by the frozen Wave A contract"
        )

    if not (
        environ.get(
            "NCBI_EMAIL",
            "",
        ).strip()
    ):

        raise LiveEntrypointError(
            "NCBI_EMAIL is required before Wave A live execution"
        )


def preclaim_validate(
    *,
    authorization_path: Path,
    execution_id: str,
    confirmation: str,
    environ: dict[str, str],
) -> dict:

    if (
        confirmation
        != CONFIRMATION_LITERAL
    ):

        raise LiveEntrypointError(
            "Explicit Wave A live-execution confirmation is absent or incorrect"
        )

    if (
        not isinstance(
            execution_id,
            str,
        )
        or not execution_id.strip()
    ):

        raise LiveEntrypointError(
            "Explicit non-empty execution ID is required"
        )

    resolved_authorization = (
        authorization_path.resolve()
    )

    if (
        resolved_authorization
        != CANONICAL_AUTHORIZATION_PATH
    ):

        raise LiveEntrypointError(
            "Authorization path is not the frozen canonical Wave A path"
        )

    if not resolved_authorization.is_file():

        raise LiveEntrypointError(
            "Canonical Wave A authorization file is missing"
        )

    if authorization_is_tracked(
        resolved_authorization
    ):

        raise LiveEntrypointError(
            "Wave A authorization must remain untracked at execution time"
        )

    validate_frozen_dependencies()

    # Non-mutating frozen guard validation occurs before any claim/state.
    authorization = (
        guard.validate_authorization(
            resolved_authorization
        )
    )

    validate_live_environment(
        environ
    )

    # Base adapter plus amendment must also remain valid before claim.
    adapter.load_contract()

    return authorization


def validate_runtime_invariants(
    *,
    context: dict,
    authorization_path: Path,
) -> dict:

    resolved_authorization = (
        authorization_path.resolve()
    )

    if (
        resolved_authorization
        != CANONICAL_AUTHORIZATION_PATH
    ):

        raise LiveEntrypointError(
            "Runtime authorization path is no longer canonical"
        )

    if not resolved_authorization.is_file():

        raise LiveEntrypointError(
            "Runtime authorization file is missing"
        )

    if authorization_is_tracked(
        resolved_authorization
    ):

        raise LiveEntrypointError(
            "Runtime authorization became tracked"
        )

    # Re-run the frozen non-mutating guard before every request.
    # This reasserts:
    #   * tracked tree is clean;
    #   * authorized_execution_commit == current HEAD;
    #   * frozen transport/manifest/normalizer dependencies still verify.
    authorization = (
        guard.validate_authorization(
            resolved_authorization
        )
    )

    current_authorization_sha = (
        guard.authorization_sha256(
            authorization
        )
    )

    if (
        current_authorization_sha
        != context[
            "authorization_sha256"
        ]
    ):

        raise LiveEntrypointError(
            "Runtime authorization bytes changed after claim"
        )

    return authorization


def make_live_paced_executor(
    *,
    executor: Callable,
    pacer,
) -> Callable:

    cold_started = set()

    def paced_executor(
        request,
    ):

        provider = request.provider

        if provider not in cold_started:

            pacer.sleeper(
                COLD_START_SECONDS
            )

            cold_started.add(
                provider
            )

        pacer.wait(
            provider
        )

        return executor(
            request
        )

    return paced_executor


def execute_authorized_wave_a(
    *,
    execution_id: str,
    confirmation: str,
    environ: dict[str, str] | None = None,
) -> dict:

    runtime_environ = dict(
        os.environ
        if environ is None
        else environ
    )

    authorization_path = (
        CANONICAL_AUTHORIZATION_PATH
    )

    # All frozen non-mutating preclaim checks happen first.
    preclaim_validate(
        authorization_path=
            authorization_path,
        execution_id=
            execution_id,
        confirmation=
            confirmation,
        environ=
            runtime_environ,
    )

    # Same-ID resume is deliberately permitted by the guard, so the
    # live wrapper must prevent two processes from executing that same
    # claim concurrently.
    with execution_process_lock(
        authorization_path
    ):

        # Close the race between the first preflight and lock
        # acquisition. No claim/state exists or changes until this
        # second validation has also succeeded.
        preclaim_validate(
            authorization_path=
                authorization_path,
            execution_id=
                execution_id,
            confirmation=
                confirmation,
            environ=
                runtime_environ,
        )

        # This is the first execution-state mutation.
        context = guard.open_execution(
            authorization_path=
                authorization_path,
            execution_id=
                execution_id,
        )

        pacer = transport.ProviderPacer(
            interval_seconds=0.5,
        )

        paced_executor = (
            make_live_paced_executor(
                executor=
                    transport.default_http_executor,
                pacer=pacer,
            )
        )

        state = context[
            "state"
        ]

        while (
            state[
                "status"
            ]
            == "ACTIVE"
        ):

            validate_runtime_invariants(
                context=context,
                authorization_path=
                    authorization_path,
            )

            state = core.run_one(
                context=context,
                executor=
                    paced_executor,
                retry_sleeper=
                    time.sleep,
                environ=
                    runtime_environ,
            )

        if (
            state[
                "status"
            ]
            != "COMPLETED"
        ):

            raise LiveEntrypointError(
                "Wave A exited without completed guard state"
            )

        return state

def parse_args(
    argv=None,
) -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Execute the separately human-authorized "
            "Wave A exact pre-review text retrieval."
        )
    )

    parser.add_argument(
        "--execution-id",
        required=True,
    )

    parser.add_argument(
        "--confirm",
        required=True,
    )

    return parser.parse_args(
        argv
    )


def main(
    argv=None,
) -> int:

    args = parse_args(
        argv
    )

    state = execute_authorized_wave_a(
        execution_id=
            args.execution_id,
        confirmation=
            args.confirm,
    )

    print(
        json.dumps(
            {
                "status":
                    state[
                        "status"
                    ],

                "completed_request_count":
                    state[
                        "completed_request_count"
                    ],

                "execution_id":
                    state[
                        "execution_id"
                    ],
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
