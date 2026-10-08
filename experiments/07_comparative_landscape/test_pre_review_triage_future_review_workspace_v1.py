from __future__ import annotations

import json
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch

import pre_review_triage_future_review_workspace_v1 as w


class FutureReviewWorkspaceTests(
    unittest.TestCase
):

    @classmethod
    def setUpClass(cls):
        cls.raw = w.load_real_inputs()
        cls.bundle = w.build_workspace(
            cls.raw
        )

    def test_real_input_partition(self):
        self.assertEqual(
            len(
                self.bundle.membership_rows
            ),
            12156,
        )

        self.assertEqual(
            len(
                self.bundle.carry_rows
            ),
            6,
        )

    def test_review_lane_counts(self):
        counts = {}

        for lane in w.LANE_ORDER:
            counts[lane] = sum(
                1
                for row
                in self.bundle.membership_rows
                if row["workspace_lane"]
                == lane
            )

        self.assertEqual(
            counts,
            {
                "priority": 5477,
                "residual": 6422,
                "manual": 257,
            },
        )

    def test_carry_forwards_are_not_review_tasks(self):
        review_ids = {
            row["screening_entity_id"]
            for row
            in self.bundle.membership_rows
        }

        carry_ids = {
            row["screening_entity_id"]
            for row
            in self.bundle.carry_rows
        }

        self.assertFalse(
            review_ids
            & carry_ids
        )

        self.assertEqual(
            len(carry_ids),
            6,
        )

        for row in self.bundle.carry_rows:
            self.assertEqual(
                row["record_decision"],
                "retain_for_method_assessment",
            )
            self.assertEqual(
                row["scientific_reassessment_performed"],
                "false",
            )

    def test_packet_contract(self):
        self.assertEqual(
            len(self.bundle.packets),
            25,
        )

        self.assertEqual(
            [
                len(
                    self.bundle.packets[
                        f"priority_{i:03d}"
                    ]
                )
                for i in range(
                    1,
                    12,
                )
            ],
            [500] * 10 + [477],
        )

        self.assertEqual(
            [
                len(
                    self.bundle.packets[
                        f"residual_{i:03d}"
                    ]
                )
                for i in range(
                    1,
                    14,
                )
            ],
            [500] * 12 + [422],
        )

        self.assertEqual(
            len(
                self.bundle.packets[
                    "manual_001"
                ]
            ),
            257,
        )

    def test_lane_local_positions_are_contiguous(self):
        for lane in w.LANE_ORDER:

            rows = [
                row
                for row
                in self.bundle.membership_rows
                if row["workspace_lane"]
                == lane
            ]

            self.assertEqual(
                [
                    int(
                        row[
                            "review_work_position"
                        ]
                    )
                    for row in rows
                ],
                list(
                    range(
                        1,
                        len(rows)
                        + 1,
                    )
                ),
            )

    def test_model_fields_absent(self):
        for row in self.bundle.membership_rows:
            self.assertFalse(
                w.FORBIDDEN_OUTPUT_FIELDS
                & set(row)
            )

        for rows in self.bundle.packets.values():
            for row in rows:
                self.assertFalse(
                    w.FORBIDDEN_OUTPUT_FIELDS
                    & set(row)
                )

    def test_human_entry_fields_blank(self):
        for rows in self.bundle.packets.values():

            for row in rows:

                for field in w.HUMAN_ENTRY_FIELDS:
                    self.assertEqual(
                        row[field],
                        "",
                    )

    def test_manifest_boundary(self):
        manifest = self.bundle.manifest

        self.assertFalse(
            manifest[
                "global_cross_lane_order_defined"
            ]
        )

        self.assertFalse(
            manifest[
                "manual_vs_scored_priority_defined"
            ]
        )

        self.assertTrue(
            all(
                value is False
                for value
                in manifest[
                    "scientific_boundary"
                ].values()
            )
        )

        self.assertTrue(
            all(
                value is False
                for value
                in manifest[
                    "model_information"
                ].values()
            )
        )

    def test_materialized_temp_workspace_round_trip(self):
        with tempfile.TemporaryDirectory() as td:

            root = (
                Path(td)
                / "workspace"
            )

            w.write_workspace(
                root,
                self.bundle,
            )

            w.validate_materialized_workspace(
                root
            )

            self.assertEqual(
                {
                    path.name
                    for path
                    in (
                        root
                        / w.PACKETS_DIR_NAME
                    ).iterdir()
                },
                {
                    f"{pid}.tsv"
                    for pid
                    in w.expected_packet_ids()
                },
            )

            manifest = json.loads(
                (
                    root
                    / w.WORKSPACE_MANIFEST_NAME
                ).read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(
                manifest[
                    "universe"
                ][
                    "new_review_work_rows"
                ],
                12156,
            )

    def test_temp_workspace_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:

            td = Path(td)

            first = (
                td
                / "first"
            )

            second = (
                td
                / "second"
            )

            w.write_workspace(
                first,
                self.bundle,
            )

            w.write_workspace(
                second,
                self.bundle,
            )

            first_files = sorted(
                path.relative_to(first)
                for path
                in first.rglob("*")
                if path.is_file()
            )

            second_files = sorted(
                path.relative_to(second)
                for path
                in second.rglob("*")
                if path.is_file()
            )

            self.assertEqual(
                first_files,
                second_files,
            )

            for rel in first_files:
                self.assertEqual(
                    (
                        first
                        / rel
                    ).read_bytes(),
                    (
                        second
                        / rel
                    ).read_bytes(),
                )

    def test_authorization_payload_has_no_scientific_authority(self):
        value = (
            w.expected_authorization_payload()
        )

        self.assertEqual(
            value[
                "expected_review_work_rows"
            ],
            12156,
        )

        self.assertEqual(
            value[
                "expected_prior_carry_forward_rows"
            ],
            6,
        )

        self.assertFalse(
            value[
                "scientific_decision_authorized"
            ]
        )

        self.assertFalse(
            value[
                "production_ledger_mutation_authorized"
            ]
        )

    def test_unauthorized_execution_creates_nothing(self):
        with tempfile.TemporaryDirectory() as td:

            output = (
                Path(td)
                / "workspace"
            )

            missing = (
                Path(td)
                / "missing.json"
            )

            with patch.object(
                w,
                "OUTPUT_ROOT",
                output,
            ):
                with self.assertRaises(
                    w.WorkspaceError
                ):
                    w.execute_authorized(
                        missing,
                        w.GENERATION_CONFIRMATION,
                    )

            self.assertFalse(
                output.exists()
            )


if __name__ == "__main__":
    unittest.main()
