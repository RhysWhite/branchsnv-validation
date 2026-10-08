from __future__ import annotations

from pathlib import Path
import inspect
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import pre_review_triage_future_scoring_v1 as s


class FutureScoringHostileTests(
    unittest.TestCase
):

    def test_duplicate_development_identity_fails(
        self,
    ):
        text = [
            {
                "retrieval_record_index": "1",
                "screening_entity_id": "a",
                "abstract_status": "usable_abstract_pubmed",
                "title_text": "A",
                "abstract_text": "alpha",
            },
            {
                "retrieval_record_index": "2",
                "screening_entity_id": "a",
                "abstract_status": "usable_abstract_pubmed",
                "title_text": "A2",
                "abstract_text": "alpha2",
            },
        ]

        with self.assertRaises(
            s.FutureScoringError
        ):
            s.assemble_training(
                text,
                [],
                expected_rows=2,
                expected_positive=0,
            )

    def test_development_identity_mismatch_fails(
        self,
    ):
        text = [
            {
                "retrieval_record_index": "1",
                "screening_entity_id": "a",
                "abstract_status": "usable_abstract_pubmed",
                "title_text": "A",
                "abstract_text": "alpha",
            },
        ]

        scores = [
            {
                "screening_entity_id": "b",
                "selected_candidate_id":
                    s.SELECTED_CANDIDATE,
                "label_numeric": "0",
            },
        ]

        with self.assertRaises(
            s.FutureScoringError
        ):
            s.assemble_training(
                text,
                scores,
                expected_rows=1,
                expected_positive=0,
            )

    def test_candidate_family_drift_fails(
        self,
    ):
        text = [
            {
                "retrieval_record_index": "1",
                "screening_entity_id": "a",
                "abstract_status": "usable_abstract_pubmed",
                "title_text": "A",
                "abstract_text": "alpha",
            },
        ]

        scores = [
            {
                "screening_entity_id": "a",
                "selected_candidate_id":
                    "different_model",
                "label_numeric": "0",
            },
        ]

        with self.assertRaises(
            s.FutureScoringError
        ):
            s.assemble_training(
                text,
                scores,
                expected_rows=1,
                expected_positive=0,
            )

    def test_future_presence_mismatch_fails(
        self,
    ):
        text = [
            {
                "retrieval_record_index": "1",
                "screening_entity_id": "a",
                "abstract_status": "usable_abstract_pubmed",
                "title_text": "A",
                "abstract_text": "alpha",
            },
        ]

        resolution = [
            {
                "retrieval_record_index": "1",
                "screening_entity_id": "a",
                "abstract_status": "usable_abstract_pubmed",
                "normalized_text_present": "0",
            },
        ]

        with self.assertRaises(
            s.FutureScoringError
        ):
            s.assemble_future(
                text,
                resolution,
                expected_scored=1,
                expected_total=1,
            )

    def test_no_text_row_never_enters_scoring_set(
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
                "abstract_status": "provider_not_found",
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
            {
                row[
                    "screening_entity_id"
                ]
                for row in future
            },
            {
                "b",
            },
        )

        self.assertEqual(
            coverage[
                0
            ][
                "coverage_status"
            ],
            "no_normalized_text",
        )

    def test_future_documents_are_transform_only(
        self,
    ):
        events = []

        class FakeMatrix:
            shape = (
                2,
                3,
            )

        class FakeVectorizer:
            def fit_transform(
                self,
                documents,
            ):
                events.append(
                    (
                        "fit_transform",
                        tuple(
                            documents
                        ),
                    )
                )
                return FakeMatrix()

            def transform(
                self,
                documents,
            ):
                events.append(
                    (
                        "transform",
                        tuple(
                            documents
                        ),
                    )
                )
                return FakeMatrix()

        class FakeModel:
            classes_ = np.asarray(
                [
                    0,
                    1,
                ]
            )

            def fit(
                self,
                matrix,
                labels,
            ):
                events.append(
                    (
                        "fit",
                        tuple(
                            int(x)
                            for x in labels
                        ),
                    )
                )
                return self

            def decision_function(
                self,
                matrix,
            ):
                events.append(
                    (
                        "decision_function",
                    )
                )
                return np.asarray(
                    [
                        0.1,
                        -0.2,
                    ]
                )

        training = [
            {
                "title_text": "train zero",
                "abstract_text": "development zero",
                "label_numeric": 0,
            },
            {
                "title_text": "train one",
                "abstract_text": "development one",
                "label_numeric": 1,
            },
        ]

        future = [
            {
                "title_text": "future a",
                "abstract_text": "future text a",
            },
            {
                "title_text": "future b",
                "abstract_text": "future text b",
            },
        ]

        s.fit_and_score(
            training,
            future,
            vectorizer_factory=
                FakeVectorizer,
            model_factory=
                FakeModel,
        )

        self.assertEqual(
            events[
                0
            ][
                0
            ],
            "fit_transform",
        )

        self.assertTrue(
            all(
                "future"
                not in document
                for document in (
                    events[
                        0
                    ][
                        1
                    ]
                )
            )
        )

        transform_event = [
            event
            for event in events
            if event[
                0
            ] == "transform"
        ]

        self.assertEqual(
            len(
                transform_event
            ),
            1,
        )

        self.assertTrue(
            all(
                "future"
                in document
                for document in (
                    transform_event[
                        0
                    ][
                        1
                    ]
                )
            )
        )

    def test_wrong_runtime_version_rejected(
        self,
    ):
        with patch.object(
            s,
            "EXPECTED_SKLEARN_VERSION",
            "0.invalid",
        ):
            with self.assertRaises(
                s.FutureScoringError
            ):
                s.verify_runtime_environment()

    def test_authorization_threshold_true_fails(
        self,
    ):
        with tempfile.TemporaryDirectory() as d:

            output = (
                Path(
                    d
                )
                / "out"
            )

            value = {
                "schema_version": 1,
                "status": "AUTHORIZED_ONE_USE",
            }

            with self.assertRaises(
                s.FutureScoringError
            ):
                s.validate_authorization_payload(
                    value,
                    implementation_freeze_sha256=
                        "abc",
                    output_root=
                        output,
                )

    def test_source_has_no_predict_call(
        self,
    ):
        source = inspect.getsource(
            s
        )

        self.assertNotIn(
            ".predict(",
            source,
        )

        self.assertNotIn(
            ".predict_proba(",
            source,
        )

    def test_source_has_no_blind_validation_source_path(
        self,
    ):
        source = inspect.getsource(
            s
        )

        forbidden = [
            "triage_validation_sampling_v1",
            "blind_validation.tsv",
            "validation_labels.tsv",
        ]

        for value in forbidden:
            self.assertNotIn(
                value,
                source,
            )

    def test_source_has_no_network_transport(
        self,
    ):
        source = inspect.getsource(
            s
        )

        forbidden = [
            "import requests",
            "from requests",
            "import urllib",
            "import socket",
            "http.client",
        ]

        for value in forbidden:
            self.assertNotIn(
                value,
                source,
            )


if __name__ == "__main__":
    unittest.main()
