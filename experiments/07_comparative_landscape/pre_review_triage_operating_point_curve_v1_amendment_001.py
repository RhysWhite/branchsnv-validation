from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


BASE_PATH = (
    Path(__file__).resolve().parent
    / "pre_review_triage_operating_point_curve_v1.py"
)

EXPECTED_BASE_SHA256 = (
    "bc0b44961ba6e1c5c8e022979d97d7df961ab68c79bc6c2815be6d72cac8db65"
)


class AmendmentError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def load_base():

    if not BASE_PATH.is_file():
        raise AmendmentError(
            "Frozen base curve implementation missing"
        )

    if sha256(
        BASE_PATH
    ) != EXPECTED_BASE_SHA256:
        raise AmendmentError(
            "Frozen base curve implementation hash changed"
        )

    spec = importlib.util.spec_from_file_location(
        "pre_review_triage_operating_point_curve_v1_frozen_base",
        BASE_PATH,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise AmendmentError(
            "Could not load frozen base curve implementation"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        spec.name
    ] = module

    spec.loader.exec_module(
        module
    )

    return module


BASE = load_base()


def format_number(
    value,
) -> str:

    if value is None:
        return ""

    if isinstance(
        value,
        str,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        return str(
            value
        )

    return format(
        float(
            value
        ),
        ".17g",
    )


# Amendment 001 changes only the serialization callback used by the
# already-frozen base implementation. The mathematical curve logic,
# ranking, exact Fraction grid and selection boundaries remain the base
# implementation.
BASE.format_number = format_number


def development_plan() -> dict:
    return BASE.development_plan()


def generate(
    output_dir: Path,
) -> dict:
    return BASE.generate(
        output_dir
    )


def main() -> int:

    parser = argparse.ArgumentParser()

    action = parser.add_mutually_exclusive_group(
        required=True
    )

    action.add_argument(
        "--plan",
        action="store_true",
    )

    action.add_argument(
        "--generate",
        action="store_true",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
    )

    args = parser.parse_args()

    if args.plan:

        if args.output_dir is not None:
            raise AmendmentError(
                "--output-dir is invalid with --plan"
            )

        print(
            json.dumps(
                development_plan(),
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    if args.output_dir is None:
        raise AmendmentError(
            "--output-dir is required with --generate"
        )

    summary = generate(
        args.output_dir
    )

    print(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
