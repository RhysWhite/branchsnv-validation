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
import pre_review_triage_future_text_wave_b_guard_v1 as guard
import pre_review_triage_future_text_wave_b_runner_core_v1 as core
import pre_review_triage_future_text_wave_b_transport_evidence_adapter_v1 as adapter


CONFIRMATION_LITERAL = (
    "EXECUTE-AUTHORIZED-WAVE-B"
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
      "pre_review_triage_future_text_retrieval_v1/"
      "live_wave_b/authorization.json"
).resolve()

ROOT = (
    REPO_ROOT
    / "experiments/07_comparative_landscape"
)

FROZEN_DEPENDENCIES = {
    "wave_b_execution_design": (
        ROOT
        / "pre_review_triage_future_text_wave_b_execution_v1_design.json",
        "bb6fe772ccb8d12515d5469a2b790240ffa9da632e87f45187d1e3db73393230",
    ),
    "wave_b_manifest": (
        REPO_ROOT
        / "results/07_comparative_landscape/"
          "pre_review_triage_future_text_retrieval_v1/"
          "live_wave_b_request_manifest.tsv",
        "e6b79c2fff3f31a8155dd7c37188d0ea2c4bd786c7e7de9950570288a2c62d11",
    ),
    "wave_b_derivation": (
        REPO_ROOT
        / "results/07_comparative_landscape/"
          "pre_review_triage_future_text_retrieval_v1/"
          "live_wave_b_derivation.tsv",
        "7fc3bd6fee6c5a3539587223ef6459df1ecce41ad670de3929836eef7a6c4474",
    ),
    "wave_b_guard": (
        ROOT
        / "pre_review_triage_future_text_wave_b_guard_v1.py",
        "60dad0cf516e829e4a33c52d693436662dd40dbae02dc7b67ae830dabc9f8610",
    ),
    "wave_b_adapter": (
        ROOT
        / "pre_review_triage_future_text_wave_b_transport_evidence_adapter_v1.py",
        "fff2203b57de35b11fbce2678466196dfcc192599978eedf3e12cf18996271d6",
    ),
    "wave_b_runner": (
        ROOT
        / "pre_review_triage_future_text_wave_b_runner_core_v1.py",
        "bf94d9d84d74783fbe05b4414738b332d0ed9bfe8fad8798c09b3775c03df101",
    ),
    "exact_transport": (
        ROOT
        / "retrieve_metadata_resolution_queue.py",
        "9c8c11edbbec86e5cbf857f25c1bf576a0638ba5cdcf69d1fa2a8b8bfc1a994f",
    ),
    "transport_policy": (
        ROOT
        / "t000002_authoritative_source_network_transport.py",
        "cc68579ff66af7633b7dd79520f748cfbe09cf8f95eaaf5cc927b833c4a7d962",
    ),
    "normalizer": (
        ROOT
        / "triage_pre_review_text_normalizer_v1.py",
        "cbe66fc9ab406fa5ee3745e099c16250c404a949c0f301e40a7397c285dc459d",
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
                "Another Wave B execution process already holds "
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

    return None



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
            "Explicit Wave B live-execution confirmation is absent or incorrect"
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
            "Authorization path is not the frozen canonical Wave B path"
        )

    if not resolved_authorization.is_file():

        raise LiveEntrypointError(
            "Canonical Wave B authorization file is missing"
        )

    if authorization_is_tracked(
        resolved_authorization
    ):

        raise LiveEntrypointError(
            "Wave B authorization must remain untracked at execution time"
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


def execute_authorized_wave_b(
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
                "Wave B exited without completed guard state"
            )

        return state

def parse_args(
    argv=None,
) -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Execute the separately human-authorized "
            "Wave B exact pre-review text retrieval."
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

    state = execute_authorized_wave_b(
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
