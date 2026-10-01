from __future__ import annotations

import unittest

import pre_review_triage_future_text_reconciliation_v1 as r


class Request10083RecoveryTests(
    unittest.TestCase
):

    @classmethod
    def setUpClass(
        cls,
    ):
        manifest = (
            r.wave_a_guard.read_manifest()
        )

        rows = [
            row
            for row in manifest
            if int(
                row[
                    "request_sequence"
                ]
            )
            == 10083
        ]

        if len(
            rows
        ) != 1:
            raise AssertionError(
                "Request 10083 manifest cardinality changed"
            )

        cls.row = rows[0]

    def test_exact_frozen_recovery_reproduces(
        self,
    ):
        evidence, body, evidence_sha = (
            r._verify_wave_a_request_10083_recovery(
                manifest_row=
                    self.row,
            )
        )

        self.assertEqual(
            evidence[
                "adapter_status"
            ],
            "verified_success",
        )

        self.assertEqual(
            evidence[
                "provider_record_id"
            ],
            "37878119",
        )

        self.assertEqual(
            evidence[
                "terminal_body_sha256"
            ],
            (
                "7cffd5a4977e2b74058b3476e4d1d9bc"
                "5a85151d303f59acb8125c4f94e20e15"
            ),
        )

        self.assertEqual(
            evidence_sha,
            (
                "487fc11994dceb62b169180f291e0d18"
                "a93cb23b5ecb2937871f3fdccf27d496"
            ),
        )

        normalized = (
            r._normalize_live_success(
                manifest_row=
                    self.row,
                evidence=
                    evidence,
                body=
                    body,
            )
        )

        self.assertEqual(
            normalized[
                "abstract_status"
            ],
            "usable_abstract_pubmed",
        )

        self.assertEqual(
            normalized[
                "provider_identity_status"
            ],
            "matched",
        )

        self.assertEqual(
            normalized[
                "provider_record_id"
            ],
            "37878119",
        )

    def test_selected_pmid_requires_exact_recovery_evidence(
        self,
    ):
        evidence, body, _ = (
            r._verify_wave_a_request_10083_recovery(
                manifest_row=
                    self.row,
            )
        )

        evidence = dict(
            evidence
        )

        evidence[
            "evidence_type"
        ] = "NOT_THE_FROZEN_RECOVERY"

        with self.assertRaisesRegex(
            r.ReconciliationError,
            "Unexpected abstract status",
        ):
            r._normalize_live_success(
                manifest_row=
                    self.row,
                evidence=
                    evidence,
                body=
                    body,
            )

    def test_manifest_identity_drift_fails_closed(
        self,
    ):
        row = dict(
            self.row
        )

        row[
            "request_identity_sha256"
        ] = "0" * 64

        with self.assertRaisesRegex(
            r.ReconciliationError,
            "manifest identity mismatch",
        ):
            r._verify_wave_a_request_10083_recovery(
                manifest_row=
                    row,
            )


if __name__ == "__main__":
    unittest.main()
