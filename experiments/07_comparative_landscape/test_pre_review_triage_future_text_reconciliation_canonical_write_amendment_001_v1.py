from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pre_review_triage_future_text_reconciliation_v1 as r


class CanonicalWriteAmendment001Tests(
    unittest.TestCase
):

    def test_missing_confirmation_fails_closed(
        self,
    ):
        with tempfile.TemporaryDirectory() as d:

            root = Path(
                d
            ).resolve()

            with patch.object(
                r,
                "RROOT",
                root,
            ):
                with self.assertRaisesRegex(
                    r.ReconciliationError,
                    "Canonical output requires exact confirmation",
                ):
                    r.validate_output_destination(
                        root,
                        canonical_confirmation=
                            None,
                    )

    def test_wrong_confirmation_fails_closed(
        self,
    ):
        with tempfile.TemporaryDirectory() as d:

            root = Path(
                d
            ).resolve()

            with patch.object(
                r,
                "RROOT",
                root,
            ):
                with self.assertRaisesRegex(
                    r.ReconciliationError,
                    "Canonical output requires exact confirmation",
                ):
                    r.validate_output_destination(
                        root,
                        canonical_confirmation=
                            "WRONG-CONFIRMATION",
                    )

    def test_exact_confirmation_permits_empty_canonical_root(
        self,
    ):
        with tempfile.TemporaryDirectory() as d:

            root = Path(
                d
            ).resolve()

            with patch.object(
                r,
                "RROOT",
                root,
            ):
                observed = (
                    r.validate_output_destination(
                        root,
                        canonical_confirmation=
                            r.CANONICAL_CONFIRMATION,
                    )
                )

            self.assertEqual(
                observed,
                root,
            )

    def test_exact_confirmation_does_not_allow_overwrite(
        self,
    ):
        with tempfile.TemporaryDirectory() as d:

            root = Path(
                d
            ).resolve()

            existing = (
                root
                / "reconciled_resolution.tsv"
            )

            existing.write_text(
                "existing\n",
                encoding="utf-8",
            )

            with patch.object(
                r,
                "RROOT",
                root,
            ):
                with self.assertRaisesRegex(
                    r.ReconciliationError,
                    "Refusing to overwrite reconciliation output",
                ):
                    r.validate_output_destination(
                        root,
                        canonical_confirmation=
                            r.CANONICAL_CONFIRMATION,
                    )


if __name__ == "__main__":
    unittest.main()
