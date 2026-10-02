from __future__ import annotations

import csv
import json
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch

import pre_review_triage_future_review_queue_v1 as q


class FutureReviewQueueHostileTests(
    unittest.TestCase
):

    def scored(
        self,
        index,
        entity,
        score=0.1,
    ):
        return q.ScoredRecord(
            retrieval_record_index=index,
            screening_entity_id=entity,
            selected_candidate_id=q.SELECTED_CANDIDATE,
            continuous_score=float(score),
            continuous_score_text=str(score),
        )

    def coverage(
        self,
        index,
        entity,
        status="scored",
    ):
        return q.CoverageRecord(
            retrieval_record_index=index,
            screening_entity_id=entity,
            abstract_status=(
                "abstract_present"
                if status == "scored"
                else "abstract_absent"
            ),
            coverage_status=status,
        )

    def write_scored(
        self,
        path,
        rows,
    ):
        with path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as fh:

            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "retrieval_record_index",
                    "screening_entity_id",
                    "selected_candidate_id",
                    "continuous_score",
                ],
                delimiter="\t",
                lineterminator="\n",
            )

            writer.writeheader()
            writer.writerows(
                rows
            )

    def write_coverage(
        self,
        path,
        rows,
    ):
        with path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as fh:

            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "retrieval_record_index",
                    "screening_entity_id",
                    "abstract_status",
                    "coverage_status",
                ],
                delimiter="\t",
                lineterminator="\n",
            )

            writer.writeheader()
            writer.writerows(
                rows
            )

    def test_duplicate_scored_identity_fails(
        self,
    ):
        scored = [
            self.scored(1, "x"),
            self.scored(2, "x"),
        ]

        coverage = [
            self.coverage(1, "x"),
        ]

        with self.assertRaises(
            q.QueueError
        ):
            q.validate_cross_sets(
                scored,
                coverage,
            )

    def test_duplicate_coverage_identity_fails(
        self,
    ):
        scored = [
            self.scored(1, "x"),
        ]

        coverage = [
            self.coverage(1, "x"),
            self.coverage(2, "x"),
        ]

        with self.assertRaises(
            q.QueueError
        ):
            q.validate_cross_sets(
                scored,
                coverage,
            )

    def test_scored_coverage_mismatch_fails(
        self,
    ):
        scored = [
            self.scored(1, "x"),
        ]

        coverage = [
            self.coverage(2, "y"),
        ]

        with self.assertRaises(
            q.QueueError
        ):
            q.validate_cross_sets(
                scored,
                coverage,
            )

    def test_no_text_cannot_enter_scored_set(
        self,
    ):
        scored = [
            self.scored(1, "x"),
        ]

        coverage = [
            self.coverage(
                1,
                "x",
                "no_normalized_text",
            ),
        ]

        with self.assertRaises(
            q.QueueError
        ):
            q.validate_cross_sets(
                scored,
                coverage,
            )

    def test_candidate_family_drift_fails(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:

            path = (
                Path(td)
                / "scores.tsv"
            )

            self.write_scored(
                path,
                [
                    {
                        "retrieval_record_index": "1",
                        "screening_entity_id": "x",
                        "selected_candidate_id": "drift",
                        "continuous_score": "0.1",
                    }
                ],
            )

            with self.assertRaises(
                q.QueueError
            ):
                q.load_scored(
                    path
                )

    def test_nonfinite_score_fails(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:

            path = (
                Path(td)
                / "scores.tsv"
            )

            self.write_scored(
                path,
                [
                    {
                        "retrieval_record_index": "1",
                        "screening_entity_id": "x",
                        "selected_candidate_id":
                            q.SELECTED_CANDIDATE,
                        "continuous_score": "nan",
                    }
                ],
            )

            with self.assertRaises(
                q.QueueError
            ):
                q.load_scored(
                    path
                )

    def test_unknown_coverage_status_fails(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:

            path = (
                Path(td)
                / "coverage.tsv"
            )

            self.write_coverage(
                path,
                [
                    {
                        "retrieval_record_index": "1",
                        "screening_entity_id": "x",
                        "abstract_status": "x",
                        "coverage_status": "invented",
                    }
                ],
            )

            with self.assertRaises(
                q.QueueError
            ):
                q.load_coverage(
                    path
                )

    def test_real_dependency_closure_exact(
        self,
    ):
        q.verify_dependencies()

        scored, coverage = (
            q.load_real_inputs()
        )

        self.assertEqual(
            len(scored),
            11905,
        )

        self.assertEqual(
            len(coverage),
            12162,
        )

    def test_source_has_no_network_or_prediction_transport(
        self,
    ):
        source = Path(
            q.__file__
        ).read_text(
            encoding="utf-8"
        ).lower()

        for forbidden in (
            "requests.",
            "urllib.",
            "httpx.",
            "aiohttp.",
            ".predict(",
            ".predict_proba(",
        ):
            self.assertNotIn(
                forbidden,
                source,
            )

    def test_existing_output_root_blocks_generation(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:

            td = Path(td)

            auth = (
                td
                / "auth.json"
            )

            auth.write_text(
                json.dumps(
                    q.expected_authorization_payload(),
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            output = (
                td
                / "already_exists"
            )

            output.mkdir()

            with patch.object(
                q,
                "OUTPUT_ROOT",
                output,
            ):
                with self.assertRaises(
                    q.QueueError
                ):
                    q.execute_authorized(
                        auth,
                        q.GENERATION_CONFIRMATION,
                    )


if __name__ == "__main__":
    unittest.main()
