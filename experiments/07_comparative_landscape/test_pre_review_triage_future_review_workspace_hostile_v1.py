from __future__ import annotations

import tempfile
import unittest

from dataclasses import replace
from pathlib import Path

import pre_review_triage_future_review_workspace_v1 as w


class FutureReviewWorkspaceHostileTests(
    unittest.TestCase
):

    @classmethod
    def setUpClass(cls):
        cls.raw = w.load_real_inputs()
        cls.bundle = w.build_workspace(
            cls.raw
        )

    def replace_lane_row(
        self,
        raw,
        lane,
        index,
        **changes,
    ):
        lanes = {
            key: list(value)
            for key, value
            in raw.lanes.items()
        }

        row = dict(
            lanes[lane][index]
        )

        row.update(
            changes
        )

        lanes[lane][index] = row

        return replace(
            raw,
            lanes=lanes,
        )

    def test_duplicate_future_identity_fails(self):
        sid = self.raw.lanes[
            "priority"
        ][0][
            "screening_entity_id"
        ]

        mutated = self.replace_lane_row(
            self.raw,
            "residual",
            0,
            screening_entity_id=sid,
        )

        with self.assertRaises(
            w.WorkspaceError
        ):
            w.validate_raw_inputs(
                mutated
            )

    def test_queue_position_gap_fails(self):
        mutated = self.replace_lane_row(
            self.raw,
            "priority",
            0,
            queue_position="2",
        )

        with self.assertRaises(
            w.WorkspaceError
        ):
            w.validate_raw_inputs(
                mutated
            )

    def test_missing_input_identity_fails(self):
        values = dict(
            self.raw.input_by_id
        )

        values.pop(
            next(iter(values))
        )

        mutated = replace(
            self.raw,
            input_by_id=values,
        )

        with self.assertRaises(
            w.WorkspaceError
        ):
            w.validate_raw_inputs(
                mutated
            )

    def test_missing_resolution_identity_fails(self):
        values = dict(
            self.raw.resolution_by_id
        )

        values.pop(
            next(iter(values))
        )

        mutated = replace(
            self.raw,
            resolution_by_id=values,
        )

        with self.assertRaises(
            w.WorkspaceError
        ):
            w.validate_raw_inputs(
                mutated
            )

    def test_manual_identity_in_normalized_text_fails(self):
        manual_sid = (
            self.raw.lanes[
                "manual"
            ][0][
                "screening_entity_id"
            ]
        )

        values = dict(
            self.raw.text_by_id
        )

        values[
            manual_sid
        ] = {
            field: ""
            for field
            in w.TEXT_FIELDS
        }

        values[
            manual_sid
        ][
            "screening_entity_id"
        ] = manual_sid

        mutated = replace(
            self.raw,
            text_by_id=values,
        )

        with self.assertRaises(
            w.WorkspaceError
        ):
            w.validate_raw_inputs(
                mutated
            )

    def test_baseline_state_drift_fails(self):
        sid = (
            self.raw.lanes[
                "priority"
            ][1000][
                "screening_entity_id"
            ]
        )

        values = dict(
            self.raw.baseline_by_id
        )

        row = dict(
            values[sid]
        )

        row[
            "screening_state"
        ] = "complete"

        values[sid] = row

        mutated = replace(
            self.raw,
            baseline_by_id=values,
        )

        with self.assertRaises(
            w.WorkspaceError
        ):
            w.validate_raw_inputs(
                mutated
            )

    def test_active_membership_loss_fails(self):
        values = dict(
            self.raw.membership_by_id
        )

        sid = next(
            sid
            for sid in values
            if sid in {
                row[
                    "screening_entity_id"
                ]
                for row
                in self.raw.lanes[
                    "residual"
                ]
            }
        )

        values.pop(
            sid
        )

        mutated = replace(
            self.raw,
            membership_by_id=values,
        )

        with self.assertRaises(
            w.WorkspaceError
        ):
            w.validate_raw_inputs(
                mutated
            )

    def test_carry_forward_decision_drift_fails(self):
        values = dict(
            self.raw.carry_by_id
        )

        future_ids = {
            row[
                "screening_entity_id"
            ]
            for lane
            in w.LANE_ORDER
            for row
            in self.raw.lanes[lane]
        }

        sid = next(
            sid
            for sid in values
            if sid in future_ids
        )

        row = dict(
            values[sid]
        )

        row[
            "record_decision"
        ] = "exclude"

        values[sid] = row

        mutated = replace(
            self.raw,
            carry_by_id=values,
        )

        with self.assertRaises(
            w.WorkspaceError
        ):
            w.validate_raw_inputs(
                mutated
            )

    def test_carry_forward_reassessment_fails(self):
        values = dict(
            self.raw.carry_by_id
        )

        future_ids = {
            row[
                "screening_entity_id"
            ]
            for lane
            in w.LANE_ORDER
            for row
            in self.raw.lanes[lane]
        }

        sid = next(
            sid
            for sid in values
            if sid in future_ids
        )

        row = dict(
            values[sid]
        )

        row[
            "scientific_reassessment_performed"
        ] = "true"

        values[sid] = row

        mutated = replace(
            self.raw,
            carry_by_id=values,
        )

        with self.assertRaises(
            w.WorkspaceError
        ):
            w.validate_raw_inputs(
                mutated
            )

    def test_existing_future_event_fails(self):
        sid = (
            self.raw.lanes[
                "priority"
            ][1000][
                "screening_entity_id"
            ]
        )

        mutated = replace(
            self.raw,
            events=[
                {
                    "screening_entity_id":
                        sid
                }
            ],
        )

        with self.assertRaises(
            w.WorkspaceError
        ):
            w.validate_raw_inputs(
                mutated
            )

    def test_existing_output_root_fails(self):
        with tempfile.TemporaryDirectory() as td:

            root = (
                Path(td)
                / "workspace"
            )

            root.mkdir()

            with self.assertRaises(
                FileExistsError
            ):
                w.write_workspace(
                    root,
                    self.bundle,
                )

    def test_nonblank_review_field_detected(self):
        with tempfile.TemporaryDirectory() as td:

            root = (
                Path(td)
                / "workspace"
            )

            w.write_workspace(
                root,
                self.bundle,
            )

            packet = (
                root
                / w.PACKETS_DIR_NAME
                / "priority_001.tsv"
            )

            text = packet.read_text(
                encoding="utf-8"
            )

            lines = text.splitlines()

            fields = lines[0].split(
                "\t"
            )

            decision_index = fields.index(
                "proposed_record_decision"
            )

            values = lines[1].split(
                "\t"
            )

            values[
                decision_index
            ] = "exclude"

            lines[1] = "\t".join(
                values
            )

            packet.write_text(
                "\n".join(lines)
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(
                w.WorkspaceError
            ):
                w.validate_materialized_workspace(
                    root
                )

    def test_checksum_tamper_detected(self):
        with tempfile.TemporaryDirectory() as td:

            root = (
                Path(td)
                / "workspace"
            )

            w.write_workspace(
                root,
                self.bundle,
            )

            target = (
                root
                / w.WORK_MEMBERSHIP_NAME
            )

            target.write_bytes(
                target.read_bytes()
                + b"\n"
            )

            with self.assertRaises(
                w.WorkspaceError
            ):
                w.validate_materialized_workspace(
                    root
                )

    def test_source_has_no_network_or_model_execution(self):
        source = Path(
            w.__file__
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
            ".fit(",
        ):
            self.assertNotIn(
                forbidden,
                source,
            )


if __name__ == "__main__":
    unittest.main()
