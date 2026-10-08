#!/usr/bin/env python3
"""Offline regression and negative tests; synthetic miniature Git history only."""
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name("verify_historical_implementation_freeze.py")
spec = importlib.util.spec_from_file_location("pr3_provenance", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def command(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], stderr=subprocess.PIPE, text=True
    ).strip()


class FrozenProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="exp07_freeze_test_")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        command(self.repo, "init", "-q")
        command(self.repo, "config", "user.email", "test@example.invalid")
        command(self.repo, "config", "user.name", "Synthetic test")
        self.root = self.repo / module.IMPL
        self.root.mkdir(parents=True)
        original_expected = {}
        for name in module.REVIEWED_POST_FREEZE_COMMITS:
            data = f"frozen synthetic test artifact: {name}\n".encode()
            (self.root / name).write_bytes(data)
            original_expected[name] = hashlib.sha256(data).hexdigest()
        self.validator_path = self.repo / module.VALIDATOR
        self.validator_path.write_text(f"IMPLEMENTATION_FILES = {original_expected!r}\n")
        command(self.repo, "add", ".")
        command(self.repo, "commit", "-qm", "freeze original synthetic artifacts")
        self.original = command(self.repo, "rev-parse", "HEAD")
        self.counts = dict.fromkeys(module.REVIEWED_POST_FREEZE_COMMITS, 0)
        (self.root / "IMPLEMENTATION.md").write_text("one synthetic authorized change\n")
        command(self.repo, "add", ".")
        command(self.repo, "commit", "-qm", "synthetic later amendment")
        self.anchor = command(self.repo, "rev-parse", "HEAD")
        self.counts["IMPLEMENTATION.md"] = 1

    def run_verify(self):
        return module.verify(self.repo, self.original, self.anchor, self.counts)

    def test_valid_history(self):
        result = self.run_verify()
        self.assertEqual(result["original_artifacts_verified"], 8)
        self.assertFalse(result["canonical_execution_authorized"])
        self.assertFalse(result["original_validator_replayed"])

    def test_unreviewed_post_anchor_change_fails(self):
        (self.root / "adapters.py").write_text("unexpected post-anchor change\n")
        command(self.repo, "add", ".")
        command(self.repo, "commit", "-qm", "unexpected post-anchor implementation change")
        with self.assertRaisesRegex(module.ProvenanceError, "Unreviewed post-anchor"):
            self.run_verify()

    def test_original_validator_mutation_fails(self):
        self.validator_path.write_text("IMPLEMENTATION_FILES = {}\n")
        command(self.repo, "add", ".")
        command(self.repo, "commit", "-qm", "unexpected change to original validator")
        with self.assertRaisesRegex(module.ProvenanceError, "Original freeze validator source changed"):
            self.run_verify()

    def test_unreviewed_change_count_fails(self):
        self.counts["IMPLEMENTATION.md"] = 2
        with self.assertRaisesRegex(module.ProvenanceError, "change-count differs"):
            self.run_verify()

    def test_unrelated_documentation_commit_is_safe(self):
        (self.repo / "README.md").write_text("unrelated additive docs\n")
        command(self.repo, "add", ".")
        command(self.repo, "commit", "-qm", "documentation only")
        self.assertEqual(self.run_verify()["original_artifacts_verified"], 8)

    def test_wrong_initial_freeze_fails(self):
        self.counts["generator.py"] = 1
        with self.assertRaisesRegex(module.ProvenanceError, "change-count differs"):
            self.run_verify()


if __name__ == "__main__":
    unittest.main(verbosity=2)
