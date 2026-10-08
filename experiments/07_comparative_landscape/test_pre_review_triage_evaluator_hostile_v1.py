from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import tempfile
import unittest

import numpy as np
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parent
    / "pre_review_triage_evaluator_v1.py"
)


def load_module():

    spec = importlib.util.spec_from_file_location(
        "pre_review_triage_evaluator_v1_hostile",
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


class EvaluatorHostileNoFitTests(
    unittest.TestCase
):

    @classmethod
    def setUpClass(cls):
        cls.m = load_module()

    def test_execution_authorization_absent(self):

        self.assertFalse(
            self.m.execution_authorization_path().exists()
        )

        with self.assertRaises(
            self.m.ExecutionNotAuthorized
        ):
            self.m.require_execution_authorization()

    def test_execution_guard_precedes_any_fit(self):

        with tempfile.TemporaryDirectory() as tmp:

            output = (
                Path(tmp)
                / "evaluation"
            )

            with mock.patch.object(
                self.m,
                "fit_and_score_partition",
                side_effect=AssertionError(
                    "fit path reached"
                ),
            ):

                with self.assertRaises(
                    self.m.ExecutionNotAuthorized
                ):
                    self.m.run_development_evaluation(
                        output
                    )

            self.assertFalse(
                output.exists()
            )

    def test_unknown_candidate_rejected_before_constructor(self):

        with self.assertRaises(
            self.m.EvaluatorError
        ):
            self.m.build_model(
                "not-a-frozen-candidate"
            )

    def test_missing_candidate_aggregate_rejected(self):

        values = [
            self.m.CandidateAggregate(
                candidate_id=
                    "logistic_regression_balanced_l2_v1",
                macro_mean_ap=0.5,
                minimum_ap=0.3,
                median_ap=0.4,
            ),
            self.m.CandidateAggregate(
                candidate_id=
                    "linear_svc_balanced_l2_v1",
                macro_mean_ap=0.5,
                minimum_ap=0.3,
                median_ap=0.4,
            ),
        ]

        with self.assertRaises(
            self.m.EvaluatorError
        ):
            self.m.select_candidate(
                values
            )

    def test_duplicate_candidate_aggregate_rejected(self):

        values = [
            self.m.CandidateAggregate(
                candidate_id=
                    "logistic_regression_balanced_l2_v1",
                macro_mean_ap=0.5,
                minimum_ap=0.3,
                median_ap=0.4,
            ),
            self.m.CandidateAggregate(
                candidate_id=
                    "logistic_regression_balanced_l2_v1",
                macro_mean_ap=0.5,
                minimum_ap=0.3,
                median_ap=0.4,
            ),
            self.m.CandidateAggregate(
                candidate_id=
                    "complement_nb_v1",
                macro_mean_ap=0.5,
                minimum_ap=0.3,
                median_ap=0.4,
            ),
        ]

        with self.assertRaises(
            self.m.EvaluatorError
        ):
            self.m.select_candidate(
                values
            )

    def test_train_test_identity_leakage_rejected(self):

        record = self.m.DevelopmentRecord(
            screening_entity_id="X",
            batch_id="B000001",
            label_text=self.m.POSITIVE_LABEL,
            label_numeric=1,
            document="x",
        )

        with self.assertRaisesRegex(
            self.m.EvaluatorError,
            "identity leakage",
        ):
            self.m.validate_split(
                [
                    record,
                    self.m.DevelopmentRecord(
                        screening_entity_id="Y",
                        batch_id="B000002",
                        label_text=self.m.NEGATIVE_LABEL,
                        label_numeric=0,
                        document="y",
                    ),
                ],
                [
                    record,
                    self.m.DevelopmentRecord(
                        screening_entity_id="Z",
                        batch_id="B000003",
                        label_text=self.m.NEGATIVE_LABEL,
                        label_numeric=0,
                        document="z",
                    ),
                ],
            )

    def test_one_class_test_partition_rejected(self):

        train = [
            self.m.DevelopmentRecord(
                screening_entity_id="A",
                batch_id="B000001",
                label_text=self.m.POSITIVE_LABEL,
                label_numeric=1,
                document="a",
            ),
            self.m.DevelopmentRecord(
                screening_entity_id="B",
                batch_id="B000001",
                label_text=self.m.NEGATIVE_LABEL,
                label_numeric=0,
                document="b",
            ),
        ]

        test = [
            self.m.DevelopmentRecord(
                screening_entity_id="C",
                batch_id="B000002",
                label_text=self.m.NEGATIVE_LABEL,
                label_numeric=0,
                document="c",
            ),
        ]

        with self.assertRaisesRegex(
            self.m.EvaluatorError,
            "Test partition does not contain both classes",
        ):
            self.m.validate_split(
                train,
                test,
            )

    def test_direct_fit_function_cannot_bypass_authorization(self):

        train = [
            self.m.DevelopmentRecord(
                screening_entity_id="A",
                batch_id="B000001",
                label_text=self.m.POSITIVE_LABEL,
                label_numeric=1,
                document="positive training text",
            ),
            self.m.DevelopmentRecord(
                screening_entity_id="B",
                batch_id="B000001",
                label_text=self.m.NEGATIVE_LABEL,
                label_numeric=0,
                document="negative training text",
            ),
        ]

        test = [
            self.m.DevelopmentRecord(
                screening_entity_id="C",
                batch_id="B000002",
                label_text=self.m.POSITIVE_LABEL,
                label_numeric=1,
                document="positive test text",
            ),
            self.m.DevelopmentRecord(
                screening_entity_id="D",
                batch_id="B000002",
                label_text=self.m.NEGATIVE_LABEL,
                label_numeric=0,
                document="negative test text",
            ),
        ]

        with mock.patch.object(
            self.m,
            "build_vectorizer",
            side_effect=AssertionError(
                "vectorizer construction reached"
            ),
        ):

            with self.assertRaises(
                self.m.ExecutionNotAuthorized
            ):
                self.m.fit_and_score_partition(
                    "logistic_regression_balanced_l2_v1",
                    train,
                    test,
                )

    def test_probability_score_orientation_uses_positive_class_identity(self):

        class FakeProbabilityModel:

            classes_ = np.array(
                [
                    1,
                    0,
                ]
            )

            def predict_proba(
                self,
                matrix,
            ):
                return np.array(
                    [
                        [
                            0.8,
                            0.2,
                        ],
                        [
                            0.3,
                            0.7,
                        ],
                    ]
                )

        observed = self.m.positive_scores(
            FakeProbabilityModel(),
            "logistic_regression_balanced_l2_v1",
            np.zeros(
                (
                    2,
                    1,
                )
            ),
        )

        np.testing.assert_allclose(
            observed,
            np.array(
                [
                    0.8,
                    0.3,
                ]
            ),
        )

        observed_cnb = self.m.positive_scores(
            FakeProbabilityModel(),
            "complement_nb_v1",
            np.zeros(
                (
                    2,
                    1,
                )
            ),
        )

        np.testing.assert_allclose(
            observed_cnb,
            np.array(
                [
                    0.8,
                    0.3,
                ]
            ),
        )

    def test_linear_svc_score_orientation_requires_zero_one_class_order(self):

        class GoodSVC:

            classes_ = np.array(
                [
                    0,
                    1,
                ]
            )

            def decision_function(
                self,
                matrix,
            ):
                return np.array(
                    [
                        -0.5,
                        0.75,
                    ]
                )

        observed = self.m.positive_scores(
            GoodSVC(),
            "linear_svc_balanced_l2_v1",
            np.zeros(
                (
                    2,
                    1,
                )
            ),
        )

        np.testing.assert_allclose(
            observed,
            np.array(
                [
                    -0.5,
                    0.75,
                ]
            ),
        )

        class BadSVC:

            classes_ = np.array(
                [
                    1,
                    0,
                ]
            )

            def decision_function(
                self,
                matrix,
            ):
                return np.array(
                    [
                        0.5,
                        -0.75,
                    ]
                )

        with self.assertRaisesRegex(
            self.m.EvaluatorError,
            "Unexpected LinearSVC class order",
        ):
            self.m.positive_scores(
                BadSVC(),
                "linear_svc_balanced_l2_v1",
                np.zeros(
                    (
                        2,
                        1,
                    )
                ),
            )

    def test_output_directory_existing_rejected_after_authorization_mock(self):

        with tempfile.TemporaryDirectory() as tmp:

            output = Path(tmp)

            with mock.patch.object(
                self.m,
                "require_execution_authorization",
                return_value={
                    "authorization_status":
                        "AUTHORIZED_DEVELOPMENT_EVALUATION",
                },
            ), mock.patch.object(
                self.m,
                "require_dedicated_runtime",
                return_value=None,
            ), mock.patch.object(
                self.m,
                "verify_environment_contract",
                return_value=None,
            ), mock.patch.object(
                self.m,
                "candidate_design",
                return_value={},
            ):

                with self.assertRaisesRegex(
                    self.m.EvaluatorError,
                    "already exists",
                ):
                    self.m.run_development_evaluation(
                        output
                    )


if __name__ == "__main__":
    unittest.main()
