from __future__ import annotations

from fractions import Fraction
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(
    "experiments/07_comparative_landscape/"
    "pre_review_triage_operating_point_curve_v1.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "pre_review_triage_operating_point_curve_hostile_v1",
        MODULE_PATH,
    )

    assert spec and spec.loader

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        spec.name
    ] = module

    spec.loader.exec_module(
        module
    )

    return module


class CurveHostileNoFitTests(
    unittest.TestCase
):

    @classmethod
    def setUpClass(cls):
        cls.m = load_module()

    def test_rank_tie_break_is_entity_id_ascending(self):
        records = [
            self.m.ScoreRecord(
                screening_entity_id="C",
                batch_id="B000001",
                label_numeric=1,
                continuous_score=0.5,
            ),
            self.m.ScoreRecord(
                screening_entity_id="A",
                batch_id="B000001",
                label_numeric=0,
                continuous_score=0.5,
            ),
            self.m.ScoreRecord(
                screening_entity_id="B",
                batch_id="B000001",
                label_numeric=1,
                continuous_score=0.5,
            ),
        ]

        ranked = self.m.rank_batch(
            records
        )

        self.assertEqual(
            [
                record.screening_entity_id
                for record in ranked
            ],
            [
                "A",
                "B",
                "C",
            ],
        )

    def test_ranking_does_not_use_label(self):
        first = [
            self.m.ScoreRecord(
                screening_entity_id="A",
                batch_id="B000001",
                label_numeric=0,
                continuous_score=2.0,
            ),
            self.m.ScoreRecord(
                screening_entity_id="B",
                batch_id="B000001",
                label_numeric=1,
                continuous_score=1.0,
            ),
        ]

        second = [
            self.m.ScoreRecord(
                screening_entity_id="A",
                batch_id="B000001",
                label_numeric=1,
                continuous_score=2.0,
            ),
            self.m.ScoreRecord(
                screening_entity_id="B",
                batch_id="B000001",
                label_numeric=0,
                continuous_score=1.0,
            ),
        ]

        self.assertEqual(
            [
                record.screening_entity_id
                for record in self.m.rank_batch(
                    first
                )
            ],
            [
                record.screening_entity_id
                for record in self.m.rank_batch(
                    second
                )
            ],
        )

    def test_duplicate_entity_rejected_in_rank(self):
        records = [
            self.m.ScoreRecord(
                screening_entity_id="A",
                batch_id="B000001",
                label_numeric=0,
                continuous_score=1.0,
            ),
            self.m.ScoreRecord(
                screening_entity_id="A",
                batch_id="B000001",
                label_numeric=1,
                continuous_score=0.0,
            ),
        ]

        with self.assertRaisesRegex(
            self.m.CurveError,
            "Duplicate screening entity ID",
        ):
            self.m.rank_batch(
                records
            )

    def test_multiple_batches_rejected_in_rank(self):
        records = [
            self.m.ScoreRecord(
                screening_entity_id="A",
                batch_id="B000001",
                label_numeric=0,
                continuous_score=1.0,
            ),
            self.m.ScoreRecord(
                screening_entity_id="B",
                batch_id="B000002",
                label_numeric=1,
                continuous_score=0.0,
            ),
        ]

        with self.assertRaisesRegex(
            self.m.CurveError,
            "multiple batches",
        ):
            self.m.rank_batch(
                records
            )

    def test_fraction_outside_unit_interval_rejected(self):
        with self.assertRaises(
            self.m.CurveError
        ):
            self.m.ceil_fraction_times_n(
                Fraction(
                    -1,
                    10,
                ),
                100,
            )

        with self.assertRaises(
            self.m.CurveError
        ):
            self.m.ceil_fraction_times_n(
                Fraction(
                    11,
                    10,
                ),
                100,
            )

    def test_existing_output_directory_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(
                tmp
            )

            with self.assertRaisesRegex(
                self.m.CurveError,
                "differs from frozen curve output path",
            ):
                self.m.generate(
                    path
                )


if __name__ == "__main__":
    unittest.main()
