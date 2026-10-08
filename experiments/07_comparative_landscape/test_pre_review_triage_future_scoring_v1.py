from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import pre_review_triage_future_scoring_v1 as s


class FutureScoringTests(
    unittest.TestCase
):

    def test_document_construction_exact(
        self,
    ):
        row = {
            "title_text": "Title",
            "abstract_text": "Abstract",
        }

        self.assertEqual(
            s.make_document(
                row
            ),
            "Title\n\nAbstract",
        )

    def test_vectorizer_contract_exact(
        self,
    ):
        params = (
            s.make_vectorizer()
            .get_params()
        )

        expected = {
            "analyzer": "word",
            "lowercase": True,
            "strip_accents": "unicode",
            "ngram_range": (1, 2),
            "min_df": 2,
            "max_df": 1.0,
            "max_features": None,
            "norm": "l2",
            "use_idf": True,
            "smooth_idf": True,
            "sublinear_tf": True,
            "stop_words": None,
            "token_pattern": r"(?u)\b\w\w+\b",
            "dtype": np.float64,
        }

        for key, value in (
            expected.items()
        ):
            self.assertEqual(
                params[
                    key
                ],
                value,
            )

    def test_model_contract_exact(
        self,
    ):
        params = (
            s.make_model()
            .get_params()
        )

        expected = {
            "penalty": "l2",
            "loss": "squared_hinge",
            "dual": True,
            "C": 1.0,
            "class_weight": "balanced",
            "tol": 1e-4,
            "max_iter": 10000,
            "random_state": 0,
        }

        for key, value in (
            expected.items()
        ):
            self.assertEqual(
                params[
                    key
                ],
                value,
            )

    def test_training_join_and_order(
        self,
    ):
        text = [
            {
                "retrieval_record_index": "2",
                "screening_entity_id": "b",
                "abstract_status": "usable_abstract_pubmed",
                "title_text": "B",
                "abstract_text": "beta",
            },
            {
                "retrieval_record_index": "1",
                "screening_entity_id": "a",
                "abstract_status": "usable_abstract_openalex",
                "title_text": "A",
                "abstract_text": "alpha",
            },
        ]

        scores = [
            {
                "screening_entity_id": "a",
                "selected_candidate_id":
                    s.SELECTED_CANDIDATE,
                "label_numeric": "1",
            },
            {
                "screening_entity_id": "b",
                "selected_candidate_id":
                    s.SELECTED_CANDIDATE,
                "label_numeric": "0",
            },
        ]

        rows = s.assemble_training(
            text,
            scores,
            expected_rows=2,
            expected_positive=1,
        )

        self.assertEqual(
            [
                row[
                    "screening_entity_id"
                ]
                for row in rows
            ],
            [
                "a",
                "b",
            ],
        )

        self.assertEqual(
            [
                row[
                    "label_numeric"
                ]
                for row in rows
            ],
            [
                1,
                0,
            ],
        )

    def test_future_coverage_exact(
        self,
    ):
        text = [
            {
                "retrieval_record_index": "2",
                "screening_entity_id": "b",
                "abstract_status": "usable_abstract_pubmed",
                "title_text": "B",
                "abstract_text": "beta",
            },
        ]

        resolution = [
            {
                "retrieval_record_index": "1",
                "screening_entity_id": "a",
                "abstract_status": "abstract_absent",
                "normalized_text_present": "0",
            },
            {
                "retrieval_record_index": "2",
                "screening_entity_id": "b",
                "abstract_status": "usable_abstract_pubmed",
                "normalized_text_present": "1",
            },
        ]

        future, coverage = (
            s.assemble_future(
                text,
                resolution,
                expected_scored=1,
                expected_total=2,
            )
        )

        self.assertEqual(
            future[
                0
            ][
                "screening_entity_id"
            ],
            "b",
        )

        self.assertEqual(
            [
                row[
                    "coverage_status"
                ]
                for row in coverage
            ],
            [
                "no_normalized_text",
                "scored",
            ],
        )

    def test_fit_returns_continuous_scores_only(
        self,
    ):
        training = [
            {
                "title_text": "negative common",
                "abstract_text": "alpha common",
                "label_numeric": 0,
            },
            {
                "title_text": "negative common",
                "abstract_text": "alpha common",
                "label_numeric": 0,
            },
            {
                "title_text": "positive common",
                "abstract_text": "beta common",
                "label_numeric": 1,
            },
            {
                "title_text": "positive common",
                "abstract_text": "beta common",
                "label_numeric": 1,
            },
        ]

        future = [
            {
                "title_text": "positive common",
                "abstract_text": "beta common",
            },
            {
                "title_text": "negative common",
                "abstract_text": "alpha common",
            },
        ]

        scores, metadata = (
            s.fit_and_score(
                training,
                future,
            )
        )

        self.assertEqual(
            len(
                scores
            ),
            2,
        )

        self.assertTrue(
            all(
                np.isfinite(
                    value
                )
                for value in scores
            )
        )

        self.assertEqual(
            metadata[
                "candidate_id"
            ],
            s.SELECTED_CANDIDATE,
        )

        self.assertFalse(
            metadata[
                "threshold_selected"
            ]
        )

        self.assertFalse(
            metadata[
                "hard_predictions_generated"
            ]
        )

    def test_fit_is_deterministic_on_identical_inputs(
        self,
    ):
        training = [
            {
                "title_text": "negative common",
                "abstract_text": "alpha common",
                "label_numeric": 0,
            },
            {
                "title_text": "negative common",
                "abstract_text": "alpha common",
                "label_numeric": 0,
            },
            {
                "title_text": "positive common",
                "abstract_text": "beta common",
                "label_numeric": 1,
            },
            {
                "title_text": "positive common",
                "abstract_text": "beta common",
                "label_numeric": 1,
            },
        ]

        future = [
            {
                "title_text": "positive common",
                "abstract_text": "beta common",
            },
            {
                "title_text": "negative common",
                "abstract_text": "alpha common",
            },
        ]

        first, _ = (
            s.fit_and_score(
                training,
                future,
            )
        )

        second, _ = (
            s.fit_and_score(
                training,
                future,
            )
        )

        self.assertEqual(
            [
                s.format_score(
                    value
                )
                for value in first
            ],
            [
                s.format_score(
                    value
                )
                for value in second
            ],
        )

    def test_runtime_environment_exact(
        self,
    ):
        s.verify_runtime_environment()

    def test_authorization_payload_exact(
        self,
    ):
        with tempfile.TemporaryDirectory() as d:

            output_root = (
                Path(
                    d
                )
                / "out"
            )

            value = {
                "schema_version": 1,
                "status": "AUTHORIZED_ONE_USE",
                "authorization_id":
                    "PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_EXECUTION_001",
                "future_scoring_authorized": True,
                "final_deployment_fit_authorized": True,
                "one_use": True,
                "consumed_before_execution": False,
                "blind_validation_content_use_authorized": False,
                "threshold_selection_authorized": False,
                "hard_prediction_authorized": False,
                "probability_calibration_authorized": False,
                "selected_candidate_id":
                    s.SELECTED_CANDIDATE,
                "design_checksum_manifest_sha256":
                    s.EXPECTED_DESIGN_SUMS_SHA256,
                "design_amendment_001_checksum_manifest_sha256":
                    s.EXPECTED_AMENDMENT_SUMS_SHA256,
                "reconciliation_completion_sha256":
                    s.EXPECTED_RECONCILIATION_COMPLETION_SHA256,
                "implementation_freeze_sha256":
                    "abc",
                "expected_development_rows":
                    4190,
                "expected_development_positive_rows":
                    168,
                "expected_future_scored_rows":
                    11905,
                "expected_future_coverage_rows":
                    12162,
                "output_root":
                    str(
                        output_root
                    ),
                "confirmation":
                    s.EXECUTION_CONFIRMATION,
            }

            s.validate_authorization_payload(
                value,
                implementation_freeze_sha256=
                    "abc",
                output_root=
                    output_root,
            )

    def test_unauthorized_execution_creates_nothing(
        self,
    ):
        with tempfile.TemporaryDirectory() as d:

            root = Path(
                d
            )

            auth = (
                root
                / "authorization.json"
            )

            output = (
                root
                / "future-output"
            )

            with (
                patch.object(
                    s,
                    "AUTHORIZATION",
                    auth,
                ),
                patch.object(
                    s,
                    "OUTPUT_ROOT",
                    output,
                ),
            ):
                with self.assertRaises(
                    s.FutureScoringError
                ):
                    s.execute_authorized(
                        authorization_path=
                            auth,
                        confirmation=
                            s.EXECUTION_CONFIRMATION,
                    )

            self.assertFalse(
                output.exists()
            )


if __name__ == "__main__":
    unittest.main()
