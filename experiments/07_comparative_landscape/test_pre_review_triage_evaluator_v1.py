from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parent
    / "pre_review_triage_evaluator_v1.py"
)


def load_module():

    spec = importlib.util.spec_from_file_location(
        "pre_review_triage_evaluator_v1",
        MODULE_PATH,
    )

    assert spec
    assert spec.loader

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


class EvaluatorNoFitTests(
    unittest.TestCase
):

    @classmethod
    def setUpClass(cls):
        cls.m = load_module()

    def test_candidate_order_exact(self):

        self.assertEqual(
            self.m.CANDIDATE_ORDER,
            (
                "logistic_regression_balanced_l2_v1",
                "linear_svc_balanced_l2_v1",
                "complement_nb_v1",
            ),
        )

    def test_development_records_exact(self):

        records = (
            self.m.load_development_records()
        )

        self.assertEqual(
            len(records),
            4190,
        )

        positives = sum(
            r.label_numeric == 1
            for r in records
        )

        negatives = sum(
            r.label_numeric == 0
            for r in records
        )

        self.assertEqual(
            positives,
            168,
        )

        self.assertEqual(
            negatives,
            4022,
        )

    def test_outer_split_geometry(self):

        records = (
            self.m.load_development_records()
        )

        observed = []

        for (
            held_out,
            training_batches,
            train,
            test,
        ) in self.m.outer_splits(
            records
        ):

            self.assertEqual(
                len(
                    training_batches
                ),
                8,
            )

            self.assertNotIn(
                held_out,
                training_batches,
            )

            self.assertTrue(
                train
            )

            self.assertTrue(
                test
            )

            self.assertEqual(
                {
                    r.batch_id
                    for r in test
                },
                {
                    held_out
                },
            )

            observed.append(
                held_out
            )

        self.assertEqual(
            tuple(
                observed
            ),
            self.m.BATCH_IDS,
        )

    def test_every_outer_fold_has_eight_inner_folds(self):

        records = (
            self.m.load_development_records()
        )

        for (
            _held_out,
            training_batches,
            train,
            _test,
        ) in self.m.outer_splits(
            records
        ):

            inner = list(
                self.m.inner_splits(
                    train,
                    training_batches,
                )
            )

            self.assertEqual(
                len(
                    inner
                ),
                8,
            )

    def test_tie_break_candidate_order_last(self):

        values = [
            self.m.CandidateAggregate(
                candidate_id=candidate_id,
                macro_mean_ap=0.5,
                minimum_ap=0.2,
                median_ap=0.4,
            )
            for candidate_id in (
                reversed(
                    self.m.CANDIDATE_ORDER
                )
            )
        ]

        selected = (
            self.m.select_candidate(
                values
            )
        )

        self.assertEqual(
            selected.candidate_id,
            "logistic_regression_balanced_l2_v1",
        )

    def test_minimum_breaks_mean_tie(self):

        values = [
            self.m.CandidateAggregate(
                candidate_id=
                    "logistic_regression_balanced_l2_v1",
                macro_mean_ap=0.5,
                minimum_ap=0.2,
                median_ap=0.3,
            ),
            self.m.CandidateAggregate(
                candidate_id=
                    "linear_svc_balanced_l2_v1",
                macro_mean_ap=0.5,
                minimum_ap=0.25,
                median_ap=0.2,
            ),
            self.m.CandidateAggregate(
                candidate_id=
                    "complement_nb_v1",
                macro_mean_ap=0.4,
                minimum_ap=0.3,
                median_ap=0.3,
            ),
        ]

        selected = (
            self.m.select_candidate(
                values
            )
        )

        self.assertEqual(
            selected.candidate_id,
            "linear_svc_balanced_l2_v1",
        )

    def test_median_breaks_mean_minimum_tie(self):

        values = [
            self.m.CandidateAggregate(
                candidate_id=
                    "logistic_regression_balanced_l2_v1",
                macro_mean_ap=0.5,
                minimum_ap=0.2,
                median_ap=0.3,
            ),
            self.m.CandidateAggregate(
                candidate_id=
                    "linear_svc_balanced_l2_v1",
                macro_mean_ap=0.5,
                minimum_ap=0.2,
                median_ap=0.35,
            ),
            self.m.CandidateAggregate(
                candidate_id=
                    "complement_nb_v1",
                macro_mean_ap=0.4,
                minimum_ap=0.3,
                median_ap=0.3,
            ),
        ]

        selected = (
            self.m.select_candidate(
                values
            )
        )

        self.assertEqual(
            selected.candidate_id,
            "linear_svc_balanced_l2_v1",
        )

    def test_vectorizer_constructor_exact(self):

        vectorizer = (
            self.m.build_vectorizer()
        )

        params = (
            vectorizer.get_params(
                deep=False
            )
        )

        expected = {
            "analyzer":
                "word",
            "lowercase":
                True,
            "strip_accents":
                "unicode",
            "ngram_range":
                (1, 2),
            "min_df":
                2,
            "max_df":
                1.0,
            "max_features":
                None,
            "norm":
                "l2",
            "use_idf":
                True,
            "smooth_idf":
                True,
            "sublinear_tf":
                True,
            "stop_words":
                None,
            "token_pattern":
                r"(?u)\b\w\w+\b",
        }

        for field, expected_value in expected.items():

            self.assertEqual(
                params[
                    field
                ],
                expected_value,
                field,
            )

        self.assertEqual(
            params[
                "dtype"
            ].__name__,
            "float64",
        )

    def test_candidate_model_constructors_exact(self):

        logistic = self.m.build_model(
            "logistic_regression_balanced_l2_v1"
        ).get_params(
            deep=False
        )

        self.assertEqual(
            logistic[
                "penalty"
            ],
            "l2",
        )
        self.assertEqual(
            logistic[
                "C"
            ],
            1.0,
        )
        self.assertEqual(
            logistic[
                "solver"
            ],
            "liblinear",
        )
        self.assertEqual(
            logistic[
                "class_weight"
            ],
            "balanced",
        )
        self.assertEqual(
            logistic[
                "max_iter"
            ],
            5000,
        )
        self.assertEqual(
            logistic[
                "random_state"
            ],
            0,
        )

        svc = self.m.build_model(
            "linear_svc_balanced_l2_v1"
        ).get_params(
            deep=False
        )

        self.assertEqual(
            svc[
                "penalty"
            ],
            "l2",
        )
        self.assertEqual(
            svc[
                "loss"
            ],
            "squared_hinge",
        )
        self.assertIs(
            svc[
                "dual"
            ],
            True,
        )
        self.assertEqual(
            svc[
                "C"
            ],
            1.0,
        )
        self.assertEqual(
            svc[
                "class_weight"
            ],
            "balanced",
        )
        self.assertEqual(
            svc[
                "tol"
            ],
            1e-4,
        )
        self.assertEqual(
            svc[
                "max_iter"
            ],
            10000,
        )
        self.assertEqual(
            svc[
                "random_state"
            ],
            0,
        )

        cnb = self.m.build_model(
            "complement_nb_v1"
        ).get_params(
            deep=False
        )

        self.assertEqual(
            cnb[
                "alpha"
            ],
            1.0,
        )
        self.assertIs(
            cnb[
                "norm"
            ],
            False,
        )

    def test_plan_reports_no_fit(self):

        plan = (
            self.m.development_plan()
        )

        self.assertEqual(
            plan[
                "status"
            ],
            "IMPLEMENTATION_PLAN_ONLY_NO_FIT",
        )

        for field in (
            "model_fit_performed",
            "vectorizer_fit_performed",
            "threshold_selected",
            "future_scoring_performed",
            "blind_validation_content_used",
            "scientific_screening_decisions_made",
            "production_mutated",
        ):
            self.assertFalse(
                plan[
                    field
                ]
            )


if __name__ == "__main__":
    unittest.main()
