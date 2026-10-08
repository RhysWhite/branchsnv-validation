from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(
    "experiments/07_comparative_landscape/"
    "pre_review_triage_operating_point_curve_v1_amendment_001.py"
)

BASE_PATH = Path(
    "experiments/07_comparative_landscape/"
    "pre_review_triage_operating_point_curve_v1.py"
)

EXPECTED_BASE_SHA = (
    "bc0b44961ba6e1c5c8e022979d97d7df961ab68c79bc6c2815be6d72cac8db65"
)


def sha(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def load_module():

    spec = importlib.util.spec_from_file_location(
        "pre_review_triage_operating_point_curve_v1_amendment_001_hostile_test",
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


class SerializationAmendmentHostileTests(
    unittest.TestCase
):

    @classmethod
    def setUpClass(cls):
        cls.before = sha(
            BASE_PATH
        )

        cls.m = load_module()

        cls.after = sha(
            BASE_PATH
        )

    def test_base_file_remains_byte_exact(self):
        self.assertEqual(
            self.before,
            EXPECTED_BASE_SHA,
        )

        self.assertEqual(
            self.after,
            EXPECTED_BASE_SHA,
        )

    def test_non_numeric_non_string_object_rejected(self):

        with self.assertRaises(
            (
                TypeError,
                ValueError,
            )
        ):
            self.m.format_number(
                object()
            )

    def test_amendment_does_not_select_any_operating_point(self):

        plan = (
            self.m.development_plan()
        )

        self.assertIs(
            plan[
                "raw_score_threshold_selected"
            ],
            False,
        )

        self.assertIs(
            plan[
                "review_fraction_selected"
            ],
            False,
        )

        self.assertIs(
            plan[
                "acceptable_recall_target_defined"
            ],
            False,
        )


if __name__ == "__main__":
    unittest.main()
