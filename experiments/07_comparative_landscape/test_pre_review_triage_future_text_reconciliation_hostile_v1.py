from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import pre_review_triage_future_text_reconciliation_v1 as r


class FutureReconciliationHostileNormalizerTests(
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

            "error":
                "",

            "abstract_status":
                "usable_abstract_openalex",

            "provider_record_id":
                "W1",

            "provider_identity_status":
                "matched",

            "abstract_text":
                "text",
        }


    def test_body_sha_mismatch_fails_closed(
        self,
    ):

        result = (
            self.base_result()
        )

        with self.assertRaises(
            r.ReconciliationError
        ):
            r._normalizer_result_checks(
                result=
                    result,
                expected_body_sha=
                    "b" * 64,
            )


    def test_parser_failure_fails_closed(
        self,
    ):

        result = (
            self.base_result()
        )

        result[
            "parser_status"
        ] = "error"

        with self.assertRaises(
            r.ReconciliationError
        ):
            r._normalizer_result_checks(
                result=
                    result,
                expected_body_sha=
                    "a" * 64,
            )


    def test_reported_error_fails_closed(
        self,
    ):

        result = (
            self.base_result()
        )

        result[
            "error"
        ] = "bad"

        with self.assertRaises(
            r.ReconciliationError
        ):
            r._normalizer_result_checks(
                result=
                    result,
                expected_body_sha=
                    "a" * 64,
            )


    def test_unexpected_abstract_state_fails_closed(
        self,
    ):

        result = (
            self.base_result()
        )

        result[
            "abstract_status"
        ] = "title_only"

        with self.assertRaises(
            r.ReconciliationError
        ):
            r._normalizer_result_checks(
                result=
                    result,
                expected_body_sha=
                    "a" * 64,
            )


    def test_empty_provider_record_fails_closed(
        self,
    ):

        result = (
            self.base_result()
        )

        result[
            "provider_record_id"
        ] = ""

        with self.assertRaises(
            r.ReconciliationError
        ):
            r._normalizer_result_checks(
                result=
                    result,
                expected_body_sha=
                    "a" * 64,
            )


    def test_abstract_absent_cannot_enter_text_table(
        self,
    ):

        normalized = (
            self.base_result()
        )

        normalized[
            "abstract_status"
        ] = "abstract_absent"

        normalized[
            "abstract_text"
        ] = ""

        with self.assertRaises(
            r.ReconciliationError
        ):
            r._text_row(
                retrieval_record_index=
                    "1",
                screening_entity_id=
                    "x",
                provider_used=
                    "openalex",
                provider_lookup_type=
                    "exact_work_id",
                normalized=
                    normalized,
                columns=
                    r.normalized_text_columns(),
            )


class FutureReconciliationHostileOutputTests(
    unittest.TestCase
):

    def test_existing_output_never_overwritten(
        self,
    ):

        with tempfile.TemporaryDirectory() as d:

            root = Path(
                d
            )

            (
                root
                / "reconciled_resolution.tsv"
            ).write_text(
                "sentinel\n",
                encoding="utf-8",
            )

            with self.assertRaises(
                r.ReconciliationError
            ):
                r.validate_output_destination(
                    root
                )


    def test_resolution_wrong_schema_fails_closed(
        self,
    ):

        normalized = {
            "provider_record_id":
                "W1",

            "source_body_sha256":
                "a" * 64,

            "provider_identity_status":
                "matched",

            "parser_status":
                "ok",

            "abstract_status":
                "abstract_absent",
        }

        with self.assertRaises(
            r.ReconciliationError
        ):
            r._resolution_row(
                retrieval_record_index=
                    "1",
                screening_entity_id=
                    "x",
                resolution_lane=
                    "wave_a_primary",
                provider_used=
                    "openalex",
                provider_lookup_type=
                    "exact_work_id",
                normalized=
                    normalized,
                wave_a_request_sequence=
                    "1",
                wave_a_request_identity_sha256=
                    "a" * 64,
                wave_b_request_sequence=
                    "",
                wave_b_request_identity_sha256=
                    "",
                fallback_reason=
                    "",
                normalized_text_present=
                    False,
                columns=
                    [
                        "wrong",
                    ],
            )


    def test_duplicate_checksum_path_fails_closed(
        self,
    ):

        with tempfile.TemporaryDirectory() as d:

            path = (
                Path(
                    d
                )
                / "sums"
            )

            path.write_text(
                ("a" * 64)
                + "  x\n"
                + ("b" * 64)
                + "  x\n",
                encoding="utf-8",
            )

            with self.assertRaises(
                r.ReconciliationError
            ):
                r.parse_checksum_manifest(
                    path
                )


    def test_invalid_checksum_digest_fails_closed(
        self,
    ):

        with tempfile.TemporaryDirectory() as d:

            path = (
                Path(
                    d
                )
                / "sums"
            )

            path.write_text(
                "not-a-sha  x\n",
                encoding="utf-8",
            )

            with self.assertRaises(
                r.ReconciliationError
            ):
                r.parse_checksum_manifest(
                    path
                )


    def test_unexpected_provider_fails_closed(
        self,
    ):

        with self.assertRaises(
            r.ReconciliationError
        ):
            r.canonical_provider_id(
                "crossref",
                "x",
            )


if __name__ == "__main__":
    unittest.main()
