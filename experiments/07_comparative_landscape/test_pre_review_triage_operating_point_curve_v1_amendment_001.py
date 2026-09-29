from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(
    "experiments/07_comparative_landscape/"
    "pre_review_triage_operating_point_curve_v1_amendment_001.py"
)


def load_module():

    spec = importlib.util.spec_from_file_location(
        "pre_review_triage_operating_point_curve_v1_amendment_001_test",
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


class SerializationAmendmentTests(
    unittest.TestCase
):

    @classmethod
    def setUpClass(cls):
        cls.m = load_module()

    def test_none_serializes_empty(self):
        self.assertEqual(
            self.m.format_number(
                None
            ),
            "",
        )

    def test_string_serializes_unchanged(self):
        self.assertEqual(
            self.m.format_number(
                "B000001"
            ),
            "B000001",
        )

    def test_integer_serialization_unchanged(self):
        self.assertEqual(
            self.m.format_number(
                4190
            ),
            "4190",
        )

    def test_float_serialization_unchanged(self):
        self.assertEqual(
            self.m.format_number(
                0.5
            ),
            ".5"
            if False
            else "0.5",
        )

    def test_base_uses_amended_serializer(self):
        self.assertIs(
            self.m.BASE.format_number,
            self.m.format_number,
        )

    def test_writer_serializes_string_and_numeric_fields(self):

        with tempfile.TemporaryDirectory() as tmp:

            path = (
                Path(
                    tmp
                )
                / "test.tsv"
            )

            self.m.BASE.write_tsv(
                path,
                [
                    "batch_id",
                    "reviewed_count",
                    "recall",
                    "precision",
                ],
                [
                    {
                        "batch_id":
                            "B000001",

                        "reviewed_count":
                            1,

                        "recall":
                            0.5,

                        "precision":
                            None,
                    }
                ],
            )

            lines = path.read_text(
                encoding="utf-8"
            ).splitlines()

            self.assertEqual(
                len(
                    lines
                ),
                2,
            )

            self.assertEqual(
                lines[
                    0
                ],
                "batch_id\treviewed_count\trecall\tprecision",
            )

            self.assertEqual(
                lines[
                    1
                ],
                "B000001\t1\t0.5\t",
            )

    def test_plan_identical_contract(self):

        plan = (
            self.m.development_plan()
        )

        self.assertEqual(
            plan[
                "status"
            ],
            "OPERATING_POINT_CURVE_PLAN_ONLY",
        )

        self.assertEqual(
            plan[
                "input_records"
            ],
            4190,
        )

        self.assertEqual(
            plan[
                "per_batch_prefix_rows"
            ],
            4199,
        )

        self.assertEqual(
            plan[
                "cross_batch_exact_fraction_grid_rows"
            ],
            4047,
        )

        for field in (
            "raw_score_threshold_selected",
            "review_fraction_selected",
            "acceptable_recall_target_defined",
            "model_fit_performed",
            "vectorizer_fit_performed",
            "calibration_fit_performed",
            "future_scoring_performed",
            "blind_validation_content_used",
            "scientific_screening_decisions_made",
            "production_mutated",
        ):
            self.assertIs(
                plan[
                    field
                ],
                False,
            )


if __name__ == "__main__":
    unittest.main()
