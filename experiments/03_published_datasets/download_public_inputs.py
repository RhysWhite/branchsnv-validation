#!/usr/bin/env python3
"""Download and checksum the public SNPPar inputs used by Experiment 03."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import urllib.request
import sys
from pathlib import Path


def load_manifest(run_script: Path) -> dict[str, dict[str, str]]:
    spec = importlib.util.spec_from_file_location("experiment03", run_script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load manifest from {run_script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.PUBLIC_INPUTS


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(Path(__file__).with_name("run.py"))

    for name, item in manifest.items():
        target = output_dir / name
        if target.exists() and not args.force:
            observed = sha256_file(target)
            if observed == item["sha256"]:
                print(f"verified {name}")
                continue
            raise RuntimeError(
                f"Existing file has the wrong checksum: {target}. Use --force to replace it."
            )
        temporary = target.with_suffix(target.suffix + ".download")
        try:
            with urllib.request.urlopen(item["url"]) as response, temporary.open("wb") as handle:
                while chunk := response.read(1024 * 1024):
                    handle.write(chunk)
            observed = sha256_file(temporary)
            if observed != item["sha256"]:
                raise RuntimeError(
                    f"Checksum mismatch for {name}: expected {item['sha256']}, observed {observed}"
                )
            temporary.replace(target)
            print(f"downloaded {name}")
        finally:
            temporary.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
