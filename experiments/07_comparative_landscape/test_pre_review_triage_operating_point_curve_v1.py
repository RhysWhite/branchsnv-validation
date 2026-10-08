from __future__ import annotations

from fractions import Fraction
import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(
    "experiments/07_comparative_landscape/"
    "pre_review_triage_operating_point_curve_v1.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "pre_review_triage_operating_point_curve_v1",
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


class CurveNoFitTests(
    unittest.TestCase
):

    @classmethod
    def setUpClass(cls):
        cls.m = load_module()
        cls.records = cls.m.read_scores()

    def test_exact_input_population(self):
        self.assertEqual(
            len(
                self.records
            ),
            4190,
        )

        self.assertEqual(
            sum(
                record.label_numeric
                for record in self.records
            ),
            168,
        )

    def test_selected_family_exact(self):
        self.assertEqual(
            {
                self.m.SELECTED_FAMILY
            },
            {
                "linear_svc_balanced_l2_v1"
            },
        )

    def test_prefix_curve_exact_row_count(self):
        rows, indexed = (
            self.m.build_prefix_rows(
                self.records
            )
        )

        self.assertEqual(
            len(
                rows
            ),
            4199,
        )

        self.assertEqual(
            set(
                indexed
            ),
            set(
                self.m.BATCHES
            ),
        )

    def test_each_prefix_curve_has_endpoints(self):
        _, indexed = (
            self.m.build_prefix_rows(
                self.records
            )
        )

        for batch in self.m.BATCHES:
            rows = indexed[
                batch
            ]

            self.assertEqual(
                rows[0][
                    "reviewed_count"
                ],
                0,
            )

            self.assertEqual(
                rows[0][
                    "recall"
                ],
                0.0,
            )

            self.assertIsNone(
                rows[0][
                    "precision"
                ]
            )

            self.assertEqual(
                rows[-1][
                    "recall"
                ],
                1.0,
            )

    def test_exact_fraction_grid_endpoints(self):
        grid = (
            self.m.exact_fraction_grid()
        )

        self.assertEqual(
            grid[0],
            Fraction(
                0,
                1,
            ),
        )

        self.assertEqual(
            grid[-1],
            Fraction(
                1,
                1,
            ),
        )

        self.assertEqual(
            grid,
            sorted(
                set(
                    grid
                )
            ),
        )

    def test_exact_ceil_rule(self):
        self.assertEqual(
            self.m.ceil_fraction_times_n(
                Fraction(
                    1,
                    3,
                ),
                10,
            ),
            4,
        )

        self.assertEqual(
            self.m.ceil_fraction_times_n(
                Fraction(
                    0,
                    1,
                ),
                10,
            ),
            0,
        )

        self.assertEqual(
            self.m.ceil_fraction_times_n(
                Fraction(
                    1,
                    1,
                ),
                10,
            ),
            10,
        )

    def test_cross_batch_curve_endpoints(self):
        _, indexed = (
            self.m.build_prefix_rows(
                self.records
            )
        )

        rows = (
            self.m.build_cross_batch_rows(
                indexed
            )
        )

        self.assertEqual(
            rows[0][
                "reviewed_record_count"
            ],
            0,
        )

        self.assertEqual(
            rows[0][
                "pooled_development_recall"
            ],
            0.0,
        )

        self.assertEqual(
            rows[-1][
                "reviewed_record_count"
            ],
            4190,
        )

        self.assertEqual(
            rows[-1][
                "minimum_batch_recall"
            ],
            1.0,
        )

        self.assertEqual(
            rows[-1][
                "pooled_development_recall"
            ],
            1.0,
        )

    def test_plan_has_no_selection_or_fit(self):
        plan = (
            self.m.development_plan()
        )

        self.assertEqual(
            plan[
                "status"
            ],
            "OPERATING_POINT_CURVE_PLAN_ONLY",
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
