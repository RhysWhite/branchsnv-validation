#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
MERGER_PATH = HERE / "merge_search_universe.py"

OUTPUT_FILES = [
    "candidate_records.tsv",
    "deduplicated_records.tsv",
    "metadata_conflicts.tsv",
    "search_counts.tsv",
    "merge_manifest.json",
    "checksums.sha256",
]


def load_merger():
    spec = importlib.util.spec_from_file_location(
        "branchsnv_merge_search_universe",
        MERGER_PATH,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load merger: {MERGER_PATH}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    merger = load_merger()

    with tempfile.TemporaryDirectory(
        prefix="branchsnv_merge_test_"
    ) as tmp:
        root = Path(tmp)
        forward = root / "forward"
        reverse = root / "reverse"

        merger.build_and_write(
            forward,
            input_order=("formal", "high_recall"),
        )

        merger.build_and_write(
            reverse,
            input_order=("high_recall", "formal"),
        )

        for name in OUTPUT_FILES:
            a = forward / name
            b = reverse / name

            if a.read_bytes() != b.read_bytes():
                raise RuntimeError(
                    f"Order-independence failure: {name}\n"
                    f"forward SHA256={sha256(a)}\n"
                    f"reverse SHA256={sha256(b)}"
                )

        manifest = json.loads(
            (forward / "merge_manifest.json").read_text(
                encoding="utf-8"
            )
        )

        assert manifest["candidate_record_rows"] == 116_556
        assert manifest["deduplicated_record_rows"] == 79_917
        assert manifest["search_count_rows"] == 69
        assert manifest["status"] == "COMPLETE"
        assert manifest["screening_performed"] is False
        assert (
            manifest["eligibility_decisions_made"]
            is False
        )
        assert (
            manifest["capability_classification_performed"]
            is False
        )

        print(
            "PASS | forward/reverse candidate outputs "
            "byte-identical"
        )
        print(
            "PASS | forward/reverse deduplicated outputs "
            "byte-identical"
        )
        print(
            "PASS | forward/reverse conflict outputs "
            "byte-identical"
        )
        print(
            "PASS | forward/reverse search-count outputs "
            "byte-identical"
        )
        print(
            "PASS | forward/reverse manifests and checksums "
            "byte-identical"
        )
        print(
            "PASS | candidate rows    = "
            f"{manifest['candidate_record_rows']:,}"
        )
        print(
            "PASS | deduplicated rows = "
            f"{manifest['deduplicated_record_rows']:,}"
        )
        print(
            "PASS | search-count rows = "
            f"{manifest['search_count_rows']:,}"
        )
        print(
            "INFO | metadata conflict keys = "
            f"{manifest['metadata_conflict_keys']:,}"
        )
        print(
            "INFO | metadata conflict rows = "
            f"{manifest['metadata_conflict_rows']:,}"
        )

    print()
    print(
        "PASS | all merged-universe order-independence "
        "regression tests"
    )


if __name__ == "__main__":
    main()
