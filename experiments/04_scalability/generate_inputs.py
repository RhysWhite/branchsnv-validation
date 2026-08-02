#!/usr/bin/env python3
"""Generate deterministic synthetic BRANCHSNV scalability inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def balanced_newick(names: list[str]) -> str:
    if not names:
        raise ValueError("At least one name is required")
    if len(names) == 1:
        return names[0]
    midpoint = len(names) // 2
    return f"({balanced_newick(names[:midpoint])},{balanced_newick(names[midpoint:])})"


def dataset_tree(taxa: list[str], focal: list[str]) -> str:
    outgroup = taxa[0]
    focal_set = set(focal)
    remainder = [name for name in taxa[1:] if name not in focal_set]
    return f"({outgroup},({balanced_newick(focal)},{balanced_newick(remainder)}));\n"


def site_states(site_index: int, ntax: int, focal_indices: range) -> str:
    """Create a deterministic mixture of phylogenetically relevant site patterns."""
    states = bytearray(b"A" * ntax)
    outside_start = focal_indices.stop
    outside_count = ntax - outside_start
    pattern = site_index % 20

    if pattern < 8:
        # Variable outside the focal clade: usually irrelevant to the selected edge.
        idx = outside_start + ((site_index * 17) % outside_count)
        states[idx] = ord("C")
    elif pattern < 12:
        # Fixed-exclusive focal marker and unambiguous focal-edge substitution.
        for idx in focal_indices:
            states[idx] = ord("C")
    elif pattern < 14:
        # Focal-edge substitution with one recurrent outside occurrence: not exclusive.
        for idx in focal_indices:
            states[idx] = ord("G")
        idx = outside_start + ((site_index * 31) % outside_count)
        states[idx] = ord("G")
    elif pattern < 16:
        # Mixed focal state: not fixed within the focal clade.
        for idx in range(focal_indices.start, focal_indices.stop, 2):
            states[idx] = ord("T")
    elif pattern == 16:
        # Two independent outside changes.
        idx1 = outside_start + ((site_index * 13) % outside_count)
        idx2 = outside_start + ((site_index * 29 + 1) % outside_count)
        states[idx1] = ord("C")
        states[idx2] = ord("G")
    elif pattern == 17:
        # Ambiguous state within the focal clade.
        for idx in focal_indices:
            states[idx] = ord("C")
        states[focal_indices.start] = ord("N")
    elif pattern == 18:
        # Missing state outside the focal clade.
        for idx in focal_indices:
            states[idx] = ord("T")
        states[outside_start + ((site_index * 7) % outside_count)] = ord("?")
    else:
        # Gap plus a recurrent base, exercising missing-data handling.
        for idx in focal_indices:
            states[idx] = ord("G")
        states[focal_indices.start] = ord("-")
        states[outside_start + ((site_index * 11) % outside_count)] = ord("G")

    return states.decode("ascii")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def generate_dataset(output_root: Path, ntax: int, nchar: int) -> dict[str, object]:
    dataset_id = f"t{ntax}_s{nchar}"
    folder = output_root / dataset_id
    folder.mkdir(parents=True, exist_ok=True)
    taxa = [f"taxon_{idx:05d}" for idx in range(ntax)]
    focal_size = max(2, ntax // 4)
    focal = taxa[1 : 1 + focal_size]
    focal_indices = range(1, 1 + focal_size)

    tree_path = folder / "tree.nwk"
    tips_path = folder / "focal_tips.txt"
    alignment_path = folder / "alignment.nex"
    tree_path.write_text(dataset_tree(taxa, focal), encoding="utf-8")
    tips_path.write_text("\n".join(focal) + "\n", encoding="utf-8")

    with alignment_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("#NEXUS\n\nBEGIN DATA;\n")
        handle.write(f"  DIMENSIONS NTAX={ntax} NCHAR={nchar};\n")
        handle.write('  FORMAT DATATYPE=DNA TRANSPOSE GAP=- MISSING=? SYMBOLS="ACGT";\n')
        handle.write("  TAXLABELS\n")
        for name in taxa:
            handle.write(f"    {name}\n")
        handle.write("  ;\n  MATRIX\n")
        for site_index in range(nchar):
            states = site_states(site_index, ntax, focal_indices)
            handle.write(f"    ref_{site_index + 1} {states}\n")
        handle.write("  ;\nEND;\n")

    return {
        "dataset_id": dataset_id,
        "ntax": ntax,
        "nchar": nchar,
        "focal_descendants": focal_size,
        "alignment": str(alignment_path.relative_to(output_root.parent)),
        "tree": str(tree_path.relative_to(output_root.parent)),
        "focal_tips": str(tips_path.relative_to(output_root.parent)),
        "alignment_bytes": alignment_path.stat().st_size,
        "alignment_sha256": sha256(alignment_path),
        "tree_sha256": sha256(tree_path),
        "focal_tips_sha256": sha256(tips_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)

    configs = {(ntax, 10_000) for ntax in (50, 100, 250, 500, 1000, 2000)}
    configs.update({(250, nchar) for nchar in (1_000, 5_000, 10_000, 25_000, 50_000, 100_000)})
    records = [generate_dataset(args.output_root, *config) for config in sorted(configs)]
    manifest = {
        "generator": "experiments/04_scalability/generate_inputs.py",
        "design": {
            "taxon_scaling_nchar": 10_000,
            "taxon_counts": [50, 100, 250, 500, 1000, 2000],
            "site_scaling_ntax": 250,
            "site_counts": [1_000, 5_000, 10_000, 25_000, 50_000, 100_000],
            "focal_clade_fraction": "approximately one quarter of taxa",
            "patterns": "deterministic 20-site cycle covering focal, recurrent, mixed, ambiguous, missing, and gap-containing states",
        },
        "datasets": records,
    }
    (args.output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
