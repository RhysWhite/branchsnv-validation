from __future__ import annotations

import unittest
from unittest.mock import patch

import pre_review_triage_future_text_reconciliation_v1 as r


BODY_SHA = '30228dfcd8815a4e8dfbbefc810d9033a579b2733cb7091c6314e514178943a1'
PROVIDER_ID = 'https://openalex.org/W2119850564'
REQUEST_IDENTITY = '0ce8b2384745cddbd10549afeb55642d781f067fd7d5c612b75006a1dd0bf1e2'
ENTITY = 'publication_component:citation:publication:doi:10.5897/ajb11.773'


def exact_manifest_row() -> dict[str, str]:
    return {
        "provider": "openalex",
        "request_sequence":
            '9180',
        "retrieval_record_index":
            '9191',
        "screening_entity_id":
            ENTITY,
        "identifier_namespace":
            'openalex',
        "identifier":
            'W2119850564',
        "frozen_route":
            'exact_work_id',
        "request_identity_sha256":
            REQUEST_IDENTITY,
    }


def gap_result() -> dict:
    return {
        "source_body_sha256":
            BODY_SHA,
        "parser_status":
            'ok',
        "error":
            "",
        "abstract_status":
            "openalex_position_gap",
        "provider_record_id":
            PROVIDER_ID,
        "provider_identity_status":
            "transport_validated",
    }


def evidence() -> dict:
    return {
        "terminal_body_sha256":
            BODY_SHA,
        "provider_record_id":
            PROVIDER_ID,
        "provider_identity_status":
            "matched",
    }


class Amendment002NormalizerTests(
    unittest.TestCase
):

    def test_exact_frozen_position_gap_is_admitted(
        self,
    ):
        with patch.object(
            r.normalizer,
            "normalize_openalex",
            return_value=gap_result(),
        ):
            observed = r._normalize_live_success(
                manifest_row=
                    exact_manifest_row(),
                evidence=
                    evidence(),
                body=
                    b"frozen-body",
            )

        self.assertEqual(
            observed[
                "abstract_status"
            ],
            "openalex_position_gap",
        )

        self.assertEqual(
            observed[
                "provider_identity_status"
            ],
            "matched",
        )

    def test_second_position_gap_fails_closed(
        self,
    ):
        row = exact_manifest_row()

        row[
            "request_sequence"
        ] = "9181"

        row[
            "retrieval_record_index"
        ] = "9192"

        with patch.object(
            r.normalizer,
            "normalize_openalex",
            return_value=gap_result(),
        ):
            with self.assertRaisesRegex(
                r.ReconciliationError,
                "outside Amendment 002 exception",
            ):
                r._normalize_live_success(
                    manifest_row=
                        row,
                    evidence=
                        evidence(),
                    body=
                        b"other-body",
                )

    def test_exact_gap_requires_matched_adapter_identity(
        self,
    ):
        bad_evidence = evidence()

        bad_evidence[
            "provider_identity_status"
        ] = "unmatched"

        with patch.object(
            r.normalizer,
            "normalize_openalex",
            return_value=gap_result(),
        ):
            with self.assertRaisesRegex(
                r.ReconciliationError,
                "outside Amendment 002 exception",
            ):
                r._normalize_live_success(
                    manifest_row=
                        exact_manifest_row(),
                    evidence=
                        bad_evidence,
                    body=
                        b"frozen-body",
                )

    def test_generic_gap_still_fails_closed(
        self,
    ):
        with self.assertRaisesRegex(
            r.ReconciliationError,
            "Unexpected abstract status",
        ):
            r._normalizer_result_checks(
                result=
                    gap_result(),
                expected_body_sha=
                    BODY_SHA,
            )


if __name__ == "__main__":
    unittest.main()
