from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(
    "experiments/07_comparative_landscape"
)

RUNNER = (
    ROOT
    / "triage_pre_review_text_offline_runner_v1.py"
)


class OfflineRunnerStaticTests(
    unittest.TestCase,
):

    def test_no_network_imports(
        self,
    ):

        tree = ast.parse(
            RUNNER.read_text(
                encoding="utf-8"
            )
        )

        forbidden = {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "aiohttp",
            "http.client",
        }

        imports = set()

        for node in ast.walk(
            tree
        ):

            if isinstance(
                node,
                ast.Import,
            ):

                for alias in node.names:

                    imports.add(
                        alias.name
                    )

            elif isinstance(
                node,
                ast.ImportFrom,
            ):

                if node.module:

                    imports.add(
                        node.module
                    )


        self.assertFalse(
            imports
            & forbidden,
            imports
            & forbidden,
        )


    def test_no_subprocess_or_shell_execution(
        self,
    ):

        text = RUNNER.read_text(
            encoding="utf-8"
        )

        forbidden = [
            "subprocess",
            "os.system",
            "Popen(",
            "run(",
            "check_output",
        ]

        present = [
            item
            for item in forbidden
            if item in text
        ]

        self.assertEqual(
            present,
            [],
        )


    def test_blind_holdout_is_explicitly_forbidden(
        self,
    ):

        text = RUNNER.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            '"triage_validation_v1"',
            text,
        )

        self.assertIn(
            "FORBIDDEN_PATH_PARTS",
            text,
        )


    def test_manifest_hash_is_pinned(
        self,
    ):

        text = RUNNER.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "4e5ba0313e008a58e968a9368ea90b6f",
            text,
        )

        self.assertIn(
            "db70049b866003742ed1c967c31120ba",
            text,
        )


if __name__ == "__main__":
    unittest.main()
