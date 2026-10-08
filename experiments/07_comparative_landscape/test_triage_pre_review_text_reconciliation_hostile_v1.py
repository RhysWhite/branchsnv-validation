from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

import triage_pre_review_text_reconciliation_v1 as reconciliation


class ReconciliationHostileUnitTests(
    unittest.TestCase
):

    def test_duplicate_checksum_path_fails_closed(
        self,
    ):

        digest = (
            "a"
            * 64
        )

        with tempfile.TemporaryDirectory() as td:

            path = (
                Path(td)
                / "checksums.sha256"
            )

            path.write_text(
                f"{digest}  x\n"
                f"{digest}  x\n",
                encoding="utf-8",
            )

            with self.assertRaises(
                reconciliation.ReconciliationError
            ):
                reconciliation.parse_checksum_manifest(
                    path
                )

    def test_invalid_checksum_digest_fails_closed(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            path = (
                Path(td)
                / "checksums.sha256"
            )

            path.write_text(
                "not-a-sha  x\n",
                encoding="utf-8",
            )

            with self.assertRaises(
                reconciliation.ReconciliationError
            ):
                reconciliation.parse_checksum_manifest(
                    path
                )

    def test_unexpected_provider_fails_closed(
        self,
    ):

        with self.assertRaises(
            reconciliation.ReconciliationError
        ):
            reconciliation.canonical_provider_id(
                "crossref",
                "123",
            )

    def test_existing_output_is_never_overwritten(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            (
                root
                / "reconciled_resolution.tsv"
            ).write_text(
                "existing\n",
                encoding="utf-8",
            )

            with self.assertRaises(
                reconciliation.ReconciliationError
            ):
                reconciliation.validate_output_destination(
                    root,
                    canonical_confirmation=None,
                )

    def test_wrong_canonical_confirmation_fails(
        self,
    ):

        with self.assertRaises(
            reconciliation.ReconciliationError
        ):
            reconciliation.validate_output_destination(
                reconciliation.RROOT,
                canonical_confirmation="WRONG",
            )


class ReconciliationHostileNormalizerTests(
    unittest.TestCase
):

    def base_result(
        self,
    ):

        return {
            "source_body_sha256":
                "a" * 64,

            "parser_status":
                "ok",

            "abstract_status":
                "usable_abstract_openalex",

            "provider_record_id":
                "https://openalex.org/W1",

            "provider_identity_status":
                "transport_validated",

            "error":
                "",
        }

    def test_normalizer_body_sha_mismatch_fails_closed(
        self,
    ):

        value = self.base_result()

        with self.assertRaises(
            reconciliation.ReconciliationError
        ):
            reconciliation._normalizer_result_checks(
                result=value,
                expected_body_sha="b" * 64,
            )

    def test_normalizer_parser_failure_fails_closed(
        self,
    ):

        value = self.base_result()

        value[
            "parser_status"
        ] = "error"

        with self.assertRaises(
            reconciliation.ReconciliationError
        ):
            reconciliation._normalizer_result_checks(
                result=value,
                expected_body_sha="a" * 64,
            )

    def test_normalizer_reported_error_fails_closed(
        self,
    ):

        value = self.base_result()

        value[
            "error"
        ] = "synthetic_error"

        with self.assertRaises(
            reconciliation.ReconciliationError
        ):
            reconciliation._normalizer_result_checks(
                result=value,
                expected_body_sha="a" * 64,
            )

    def test_unexpected_abstract_status_fails_closed(
        self,
    ):

        value = self.base_result()

        value[
            "abstract_status"
        ] = "unexpected_state"

        with self.assertRaises(
            reconciliation.ReconciliationError
        ):
            reconciliation._normalizer_result_checks(
                result=value,
                expected_body_sha="a" * 64,
            )

    def test_empty_provider_record_id_fails_closed(
        self,
    ):

        value = self.base_result()

        value[
            "provider_record_id"
        ] = ""

        with self.assertRaises(
            reconciliation.ReconciliationError
        ):
            reconciliation._normalizer_result_checks(
                result=value,
                expected_body_sha="a" * 64,
            )

    def test_empty_provider_identity_status_fails_closed(
        self,
    ):

        value = self.base_result()

        value[
            "provider_identity_status"
        ] = ""

        with self.assertRaises(
            reconciliation.ReconciliationError
        ):
            reconciliation._normalizer_result_checks(
                result=value,
                expected_body_sha="a" * 64,
            )

    def test_abstract_absent_cannot_enter_text_table(
        self,
    ):

        contract = (
            reconciliation.assert_frozen_contract()
        )

        normalized = {
            "provider_record_id":
                "https://openalex.org/W1",

            "source_body_sha256":
                "a" * 64,

            "provider_identity_status":
                "transport_validated",

            "parser_status":
                "ok",

            "abstract_status":
                "abstract_absent",

            "title_text":
                "not inspected",

            "abstract_text":
                "",

            "abstract_section_metadata_json":
                "[]",
        }

        with self.assertRaises(
            reconciliation.ReconciliationError
        ):
            reconciliation._text_row(
                retrieval_record_index="1",
                screening_entity_id="entity:1",
                provider_used="openalex",
                provider_lookup_type="exact_work_id",
                normalized=normalized,
                columns=(
                    reconciliation.normalized_text_columns(
                        contract
                    )
                ),
            )


class ReconciliationHistoricalArchiveHostileTests(
    unittest.TestCase
):

    def copy_selected_fixture(
        self,
        destination: Path,
    ):

        contract = (
            reconciliation.assert_frozen_contract()
        )

        amendment = contract[
            "amendment"
        ]

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            reconciliation.HISTORICAL_CHECKSUM_PATH,
            destination
            / "checksums.sha256",
        )

        for item in amendment[
            "historical_cache_dependency"
        ][
            "selected_lookups"
        ]:

            logical = item[
                "logical_lookup_id"
            ]

            token = logical.split(
                ":",
                1,
            )[1]

            source = (
                reconciliation.HROOT
                / "raw"
                / (
                    "lookup_"
                    + token
                )
            )

            target = (
                destination
                / "raw"
                / (
                    "lookup_"
                    + token
                )
            )

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copytree(
                source,
                target,
            )

        return contract

    def test_selected_historical_body_tamper_fails_closed(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            fixture = (
                Path(td)
                / "historical"
            )

            contract = (
                self.copy_selected_fixture(
                    fixture
                )
            )

            checksum_path = (
                fixture
                / "checksums.sha256"
            )

            with (
                mock.patch.object(
                    reconciliation,
                    "HROOT",
                    fixture,
                ),
                mock.patch.object(
                    reconciliation,
                    "HISTORICAL_CHECKSUM_PATH",
                    checksum_path,
                ),
            ):

                mapping = (
                    reconciliation.validate_historical_selected_dependency(
                        contract
                    )
                )

                self.assertEqual(
                    len(
                        mapping
                    ),
                    8666,
                )

                first = (
                    contract[
                        "amendment"
                    ][
                        "historical_cache_dependency"
                    ][
                        "selected_lookups"
                    ][0]
                )

                token = (
                    first[
                        "logical_lookup_id"
                    ].split(
                        ":",
                        1,
                    )[1]
                )

                body = (
                    fixture
                    / "raw"
                    / (
                        "lookup_"
                        + token
                    )
                    / "attempt_01"
                    / "hop_00_body.bin"
                )

                body.write_bytes(
                    body.read_bytes()
                    + b"tamper"
                )

                with self.assertRaises(
                    reconciliation.ReconciliationError
                ):
                    reconciliation.validate_historical_selected_dependency(
                        contract
                    )

    def test_selected_historical_file_removal_fails_closed(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            fixture = (
                Path(td)
                / "historical"
            )

            contract = (
                self.copy_selected_fixture(
                    fixture
                )
            )

            checksum_path = (
                fixture
                / "checksums.sha256"
            )

            first = (
                contract[
                    "amendment"
                ][
                    "historical_cache_dependency"
                ][
                    "selected_lookups"
                ][0]
            )

            token = (
                first[
                    "logical_lookup_id"
                ].split(
                    ":",
                    1,
                )[1]
            )

            terminal = (
                fixture
                / "raw"
                / (
                    "lookup_"
                    + token
                )
                / "terminal.json"
            )

            terminal.unlink()

            with (
                mock.patch.object(
                    reconciliation,
                    "HROOT",
                    fixture,
                ),
                mock.patch.object(
                    reconciliation,
                    "HISTORICAL_CHECKSUM_PATH",
                    checksum_path,
                ),
            ):

                with self.assertRaises(
                    reconciliation.ReconciliationError
                ):
                    reconciliation.validate_historical_selected_dependency(
                        contract
                    )


class ReconciliationOutputHostileTests(
    unittest.TestCase
):

    def test_every_existing_output_name_blocks_write(
        self,
    ):

        for filename in (
            reconciliation.OUTPUT_FILENAMES
        ):

            with self.subTest(
                filename=filename
            ):

                with tempfile.TemporaryDirectory() as td:

                    root = Path(td)

                    (
                        root
                        / filename
                    ).write_text(
                        "existing\n",
                        encoding="utf-8",
                    )

                    with self.assertRaises(
                        reconciliation.ReconciliationError
                    ):
                        reconciliation.validate_output_destination(
                            root,
                            canonical_confirmation=None,
                        )

    def test_resolution_row_rejects_wrong_schema(
        self,
    ):

        normalized = {
            "provider_record_id":
                "W1",

            "source_body_sha256":
                "a" * 64,

            "provider_identity_status":
                "transport_validated",

            "parser_status":
                "ok",

            "abstract_status":
                "abstract_absent",
        }

        with self.assertRaises(
            reconciliation.ReconciliationError
        ):
            reconciliation._resolution_row(
                retrieval_record_index="1",
                screening_entity_id="entity:1",
                resolution_lane="offline_cache",
                provider_used="openalex",
                provider_lookup_type="exact_work_id",
                normalized=normalized,
                wave_a_request_sequence="",
                wave_a_request_identity_sha256="",
                wave_b_request_sequence="",
                wave_b_request_identity_sha256="",
                fallback_reason="",
                normalized_text_present=False,
                columns=[
                    "wrong",
                ],
            )



if __name__ == "__main__":
    unittest.main()
