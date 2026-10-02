from __future__ import annotations

import json
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch

import pre_review_triage_future_review_queue_v1 as q


class FutureReviewQueueAmendment001Tests(
    unittest.TestCase
):

    def test_consumed_generation_001_authorization_rejected(
        self,
    ):
        historical = (
            q.repo_root()
            / "experiments/07_comparative_landscape/"
            "pre_review_triage_future_review_queue_v1_"
            "generation_authorization.json"
        )

        self.assertTrue(
            historical.is_file()
        )

        value = json.loads(
            historical.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            value["authorization_id"],
            (
                "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_"
                "GENERATION_001"
            ),
        )

        self.assertEqual(
            q.AUTHORIZATION_ID,
            (
                "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_"
                "GENERATION_002"
            ),
        )

        with self.assertRaises(
            q.QueueError
        ):
            q.validate_generation_authorization(
                historical,
                q.GENERATION_CONFIRMATION,
            )

    def test_staging_parent_payload_generation_succeeds(
        self,
    ):
        priority = [
            q.ScoredRecord(
                retrieval_record_index=1,
                screening_entity_id="priority",
                selected_candidate_id=q.SELECTED_CANDIDATE,
                continuous_score=0.9,
                continuous_score_text="0.9",
            )
        ]

        residual = [
            q.ScoredRecord(
                retrieval_record_index=2,
                screening_entity_id="residual",
                selected_candidate_id=q.SELECTED_CANDIDATE,
                continuous_score=0.1,
                continuous_score_text="0.1",
            )
        ]

        manual = [
            q.CoverageRecord(
                retrieval_record_index=3,
                screening_entity_id="manual",
                abstract_status="abstract_absent",
                coverage_status="no_normalized_text",
            )
        ]

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)

            output = (
                td
                / "results"
                / "queue"
            )

            auth = (
                td
                / "generation_002.json"
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

            with (
                patch.object(
                    q,
                    "OUTPUT_ROOT",
                    output,
                ),
                patch.object(
                    q,
                    "verify_dependencies",
                    return_value=None,
                ),
                patch.object(
                    q,
                    "load_real_inputs",
                    return_value=(
                        [],
                        [],
                    ),
                ),
                patch.object(
                    q,
                    "build_real_queues",
                    return_value=(
                        priority,
                        residual,
                        manual,
                    ),
                ),
            ):
                q.execute_authorized(
                    auth,
                    q.GENERATION_CONFIRMATION,
                )

            self.assertTrue(
                output.is_dir()
            )

            self.assertEqual(
                {
                    path.name
                    for path in output.iterdir()
                    if path.is_file()
                },
                {
                    q.PRIORITY_NAME,
                    q.RESIDUAL_NAME,
                    q.UNSCORED_NAME,
                    q.MANIFEST_NAME,
                },
            )

            staging = list(
                output.parent.glob(
                    ".pre_review_triage_"
                    "future_review_queue_v1.*"
                )
            )

            self.assertEqual(
                staging,
                [],
            )


if __name__ == "__main__":
    unittest.main()
