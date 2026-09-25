#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import json
import shutil
import sys
import tempfile


HERE = Path(__file__).resolve().parent

MODULE_PATH = (
    HERE
    / "pre_decision_execution_production_writer.py"
)

spec = importlib.util.spec_from_file_location(
    "pre_decision_execution_production_writer_tests",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

mod = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = mod

spec.loader.exec_module(
    mod
)


def expect_error(
    label,
    fn,
):
    try:
        fn()

    except mod.ProductionWriterError:
        print(
            "PASS |",
            label,
        )

        return

    raise AssertionError(
        "Expected ProductionWriterError: "
        + label
    )


payloads_1, summary_1 = (
    mod.build_package_bytes(
        queue_path=
            mod.DEFAULT_QUEUE,

        resolution_path=
            mod.DEFAULT_RESOLUTION,

        contract_path=
            mod.DEFAULT_CONTRACT,

        design_path=
            mod.DEFAULT_DESIGN,
    )
)

payloads_2, summary_2 = (
    mod.build_package_bytes(
        queue_path=
            mod.DEFAULT_QUEUE,

        resolution_path=
            mod.DEFAULT_RESOLUTION,

        contract_path=
            mod.DEFAULT_CONTRACT,

        design_path=
            mod.DEFAULT_DESIGN,
    )
)


assert payloads_1 == payloads_2
assert summary_1 == summary_2

assert set(
    payloads_1
) == mod.GENESIS_ARTIFACT_NAMES

assert summary_1[
    "artifact_count"
] == 8

assert summary_1[
    "batch_membership_rows"
] == 94622

assert summary_1[
    "batch_count"
] == 190

assert summary_1[
    "carry_forward_rows"
] == 7

assert summary_1[
    "out_of_baseline_anchor_rows"
] == 1

assert summary_1[
    "event_ledger_rows"
] == 0

assert summary_1[
    "scientific_screening_decisions"
] == 0

assert summary_1[
    "batch_manifest_sha256"
] == mod.EXPECTED_BATCH_MANIFEST_SHA256

assert summary_1[
    "active_ordered_entity_ids_sha256"
] == mod.EXPECTED_ACTIVE_IDS_SHA256

assert summary_1[
    "event_ledger_genesis_sha256"
] == mod.EXPECTED_LEDGER_GENESIS_SHA256

print(
    "PASS | deterministic eight-artifact package built in memory"
)

print(
    "PASS | 94,622 membership rows / 190 batches"
)

print(
    "PASS | zero-event genesis exact"
)


with tempfile.TemporaryDirectory(
    prefix="branchsnv-exp07-writer-tests-"
) as tmp:
    parent = Path(tmp)

    output = (
        parent
        / "execution-package"
    )

    result = (
        mod.write_package_atomic(
            output_root=
                output,

            queue_path=
                mod.DEFAULT_QUEUE,

            resolution_path=
                mod.DEFAULT_RESOLUTION,

            contract_path=
                mod.DEFAULT_CONTRACT,

            design_path=
                mod.DEFAULT_DESIGN,
        )
    )

    assert output.is_dir()

    assert result[
        "status"
    ] == "PRE_DECISION_EXECUTION_PACKAGE_VALID"

    assert result[
        "atomic_publication_performed"
    ] is True

    assert result[
        "event_ledger_rows"
    ] == 0

    print(
        "PASS | atomic temporary package publication validated"
    )


    validated = (
        mod.validate_package_directory(
            root=output,

            queue_path=
                mod.DEFAULT_QUEUE,

            resolution_path=
                mod.DEFAULT_RESOLUTION,

            contract_path=
                mod.DEFAULT_CONTRACT,

            design_path=
                mod.DEFAULT_DESIGN,
        )
    )

    assert validated[
        "scientific_screening_decisions"
    ] == 0

    print(
        "PASS | independent package validation accepted exact package"
    )


    expect_error(
        "writer refuses overwrite of existing destination",
        lambda:
            mod.write_package_atomic(
                output_root=
                    output,

                queue_path=
                    mod.DEFAULT_QUEUE,

                resolution_path=
                    mod.DEFAULT_RESOLUTION,

                contract_path=
                    mod.DEFAULT_CONTRACT,

                design_path=
                    mod.DEFAULT_DESIGN,
            ),
    )


    # Tampered membership.
    tampered_membership = (
        parent
        / "tampered-membership"
    )

    shutil.copytree(
        output,
        tampered_membership,
    )

    with (
        tampered_membership
        / "batch_membership.tsv"
    ).open(
        "ab"
    ) as handle:
        handle.write(
            b"#tamper\n"
        )

    expect_error(
        "tampered membership fails closed",
        lambda:
            mod.validate_package_directory(
                root=
                    tampered_membership,

                queue_path=
                    mod.DEFAULT_QUEUE,

                resolution_path=
                    mod.DEFAULT_RESOLUTION,

                contract_path=
                    mod.DEFAULT_CONTRACT,

                design_path=
                    mod.DEFAULT_DESIGN,
            ),
    )


    # Unexpected ninth artifact.
    extra = (
        parent
        / "extra-artifact"
    )

    shutil.copytree(
        output,
        extra,
    )

    (
        extra
        / "unexpected.txt"
    ).write_text(
        "unexpected\n",
        encoding="utf-8",
    )

    expect_error(
        "unexpected ninth artifact fails closed",
        lambda:
            mod.validate_package_directory(
                root=extra,

                queue_path=
                    mod.DEFAULT_QUEUE,

                resolution_path=
                    mod.DEFAULT_RESOLUTION,

                contract_path=
                    mod.DEFAULT_CONTRACT,

                design_path=
                    mod.DEFAULT_DESIGN,
            ),
    )


    # Event ledger must remain exact zero-event genesis.
    event_tamper = (
        parent
        / "event-tamper"
    )

    shutil.copytree(
        output,
        event_tamper,
    )

    with (
        event_tamper
        / "event_ledger.tsv"
    ).open(
        "ab"
    ) as handle:
        handle.write(
            b"INVALID_EVENT\n"
        )

    expect_error(
        "non-genesis event ledger fails closed",
        lambda:
            mod.validate_package_directory(
                root=
                    event_tamper,

                queue_path=
                    mod.DEFAULT_QUEUE,

                resolution_path=
                    mod.DEFAULT_RESOLUTION,

                contract_path=
                    mod.DEFAULT_CONTRACT,

                design_path=
                    mod.DEFAULT_DESIGN,
            ),
    )


    # Immutable checksum corruption.
    checksum_tamper = (
        parent
        / "checksum-tamper"
    )

    shutil.copytree(
        output,
        checksum_tamper,
    )

    (
        checksum_tamper
        / "immutable_checksums.sha256"
    ).write_text(
        "0" * 64
        + "  batch_manifest.tsv\n",
        encoding="utf-8",
    )

    expect_error(
        "corrupt immutable checksum ledger fails closed",
        lambda:
            mod.validate_package_directory(
                root=
                    checksum_tamper,

                queue_path=
                    mod.DEFAULT_QUEUE,

                resolution_path=
                    mod.DEFAULT_RESOLUTION,

                contract_path=
                    mod.DEFAULT_CONTRACT,

                design_path=
                    mod.DEFAULT_DESIGN,
            ),
    )


expect_error(
    "writer cannot target frozen scientific-screening root",
    lambda:
        mod.validate_output_destination(
            mod.SCREENING_ROOT
        ),
)

expect_error(
    "writer cannot target child of frozen scientific-screening root",
    lambda:
        mod.validate_output_destination(
            mod.SCREENING_ROOT
            / "bad-child"
        ),
)

expect_error(
    "writer cannot target tracked experiment source tree",
    lambda:
        mod.validate_output_destination(
            HERE
            / "bad-output"
        ),
)


print(
    "PASS | hostile production-writer tests complete"
)
