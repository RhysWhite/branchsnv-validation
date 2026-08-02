#!/usr/bin/env python3
"""Compare BRANCHSNV with published bacterial branch-mutation results.

This experiment has two components:

1. Re-analyse the public SNPPar Elizabethkingia anophelis and Burkholderia
   dolosa example datasets using BRANCHSNV, map every non-root edge by its exact
   descendant-tip set, and compare every branch-level substitution reported by
   SNPPar with BRANCHSNV's all-optima equal-cost parsimony classification.
2. Compare the committed BRANCHSNV AK3 working-data outputs with Tables 2 and 3
   of White et al. (Microbial Genomics 2025;11:001452). The exact AK3 alignment
   and tree can optionally be supplied to repeat the checksum-gated raw-data
   analysis before the table comparison.

The production BRANCHSNV source is imported read-only and is never modified.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PUBLIC_INPUTS: dict[str, dict[str, str]] = {
    "elizabethkingia_snps.csv": {
        "sha256": "7b477073857943fd4a90ebc4a78d152c9aa9462b209f94cfd118de9797f74f24",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Elizabethkingia/CP014805v2_CP014805_alleles_1outgroup_69strains_var_regionFiltered_cons0.95_var.csv",
    },
    "elizabethkingia_tree.nwk": {
        "sha256": "fdd88a0765e0ae2ba08e20fb4b565e6ccef051f72332e839a6159be94f4137b1",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Elizabethkingia/final_raxml_tree_no_recomb.tree",
    },
    "elizabethkingia_snppar_all_mutation_events.tsv": {
        "sha256": "3b872573c5245b7d527b70dec623ebb5b60a90563b1f1b0b3cc2c008951e4110",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Elizabethkingia/snppar_output/all_mutation_events.tsv",
    },
    "elizabethkingia_snppar_node_labelled.nwk": {
        "sha256": "bbfa81a63899099abd76b4ee397024c7bb708b0a15f618e9182de38d9a4ead61",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Elizabethkingia/snppar_output/node_labelled_newick.tre",
    },
    "burkholderia_tree.nwk": {
        "sha256": "a2162d1043af2d7921ea82238e68020f90729aa2cea622c2ffbbd3c788fea24d",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Burkholderia/lieberman2011natgen_ss_root.newick",
    },
    "burkholderia_chr1_snps.csv": {
        "sha256": "8d305f9b344d72ea0e57f4ac81d81859038b06e64ac3ef66023dd98239eb6842",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Burkholderia/NIHMS335194-supplement-2-alleles_chr1.csv",
    },
    "burkholderia_chr1_snppar_all_mutation_events.tsv": {
        "sha256": "1240c4f7488cfc74bf63cac879906306345ab9c30e4c28589a306db6fffb5b10",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Burkholderia/snppar_output/chr1_all_mutation_events.tsv",
    },
    "burkholderia_chr1_snppar_node_labelled.nwk": {
        "sha256": "fe0182c8e96979512d96f99b6e77a9704015299684e97a38f6e73f516a7a6fc0",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Burkholderia/snppar_output/chr1_node_labelled_newick.tre",
    },
    "burkholderia_chr2_snps.csv": {
        "sha256": "b0b6bd69c2fd5f32bd501a49d418a9f02d14f287addc51664d318dfc511d52b1",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Burkholderia/NIHMS335194-supplement-2-alleles_chr2.csv",
    },
    "burkholderia_chr2_snppar_all_mutation_events.tsv": {
        "sha256": "14806bfa82fe96073c526a4bb3a4ac35c1063d669151f650f6e5bda8be239dae",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Burkholderia/snppar_output/chr2_all_mutation_events.tsv",
    },
    "burkholderia_chr2_snppar_node_labelled.nwk": {
        "sha256": "ab1d1d06d34bec81fd6f2f3c798faff5e3789e540b8c0632d005de604aa65112",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Burkholderia/snppar_output/chr2_node_labelled_newick.tre",
    },
    "burkholderia_chr3_snps.csv": {
        "sha256": "128ce91d252b5e70aa0bae919881b8240019a9ffa1ae8c1322c7eecce3ea6f8a",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Burkholderia/NIHMS335194-supplement-2-alleles_chr3.csv",
    },
    "burkholderia_chr3_snppar_all_mutation_events.tsv": {
        "sha256": "2f0574f363a17220c7f30020f69d705afe1d92832baf742e5815b5f6698020f0",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Burkholderia/snppar_output/chr3_all_mutation_events.tsv",
    },
    "burkholderia_chr3_snppar_node_labelled.nwk": {
        "sha256": "feabeef7ca5ddfd6457ffdc32a5f360b68579150e872aa526e2c06205003dd31",
        "url": "https://raw.githubusercontent.com/d-j-e/SNPPar_test/refs/heads/master/data/published_data/Burkholderia/snppar_output/chr3_node_labelled_newick.tre",
    },
}


@dataclass(frozen=True)
class PublicDataset:
    dataset_id: str
    organism: str
    chromosome: str
    snps_file: str
    tree_file: str
    events_file: str
    labelled_tree_file: str
    site_prefix: str
    rooting: str
    outgroup: tuple[str, ...] = ()


DATASETS = (
    PublicDataset(
        dataset_id="elizabethkingia",
        organism="Elizabethkingia anophelis",
        chromosome="CP014805",
        snps_file="elizabethkingia_snps.csv",
        tree_file="elizabethkingia_tree.nwk",
        events_file="elizabethkingia_snppar_all_mutation_events.tsv",
        labelled_tree_file="elizabethkingia_snppar_node_labelled.nwk",
        site_prefix="CP014805",
        rooting="outgroup",
        outgroup=("DRR015707",),
    ),
    PublicDataset(
        dataset_id="burkholderia_chr1",
        organism="Burkholderia dolosa",
        chromosome="chromosome 1",
        snps_file="burkholderia_chr1_snps.csv",
        tree_file="burkholderia_tree.nwk",
        events_file="burkholderia_chr1_snppar_all_mutation_events.tsv",
        labelled_tree_file="burkholderia_chr1_snppar_node_labelled.nwk",
        site_prefix="AU0158_chr1",
        rooting="existing",
    ),
    PublicDataset(
        dataset_id="burkholderia_chr2",
        organism="Burkholderia dolosa",
        chromosome="chromosome 2",
        snps_file="burkholderia_chr2_snps.csv",
        tree_file="burkholderia_tree.nwk",
        events_file="burkholderia_chr2_snppar_all_mutation_events.tsv",
        labelled_tree_file="burkholderia_chr2_snppar_node_labelled.nwk",
        site_prefix="AU0158_chr2",
        rooting="existing",
    ),
    PublicDataset(
        dataset_id="burkholderia_chr3",
        organism="Burkholderia dolosa",
        chromosome="chromosome 3",
        snps_file="burkholderia_chr3_snps.csv",
        tree_file="burkholderia_tree.nwk",
        events_file="burkholderia_chr3_snppar_all_mutation_events.tsv",
        labelled_tree_file="burkholderia_chr3_snppar_node_labelled.nwk",
        site_prefix="AU0158_chr3",
        rooting="existing",
    ),
)


AK3_MRSA_PUBLISHED = (
    (99286, "T>C"), (237606, "G>T"), (268432, "A>G"), (297655, "C>A"),
    (541577, "C>T"), (643271, "A>G"), (728512, "T>C"), (1032205, "C>A"),
    (1067855, "C>T"), (1167367, "A>C"), (1193138, "A>T"), (1217440, "A>G"),
    (1435784, "G>C"), (1680288, "T>G"), (1751961, "T>C"), (1800235, "A>T"),
    (1837199, "G>A"), (2122507, "C>T"), (2144733, "C>T"), (2266325, "G>A"),
    (2310728, "C>T"), (2537681, "C>T"), (2777570, "C>T"),
)
AK3_MRSA_PUBLISHED_INDEL = (1465812, "ATTGTTGTTTTGC>A", "deletion")
AK3_SAPI_PUBLISHED = (
    (408, "G>A"), (148318, "A>C"), (470837, "C>A"), (738146, "A>G"),
    (849992, "T>C"), (1248573, "T>C"), (1413986, "A>G"), (1542411, "C>T"),
    (1557108, "C>A"), (1682364, "C>T"), (2201553, "A>G"), (2556045, "T>G"),
    (2577011, "C>T"), (2722031, "G>A"),
)
AK3_SAPI_PUBLISHED_INDEL = (1051023, "G>GATTCAT", "insertion")
AK3_ALIGNMENT_NAME = "396_MRSA_AK3(1).nex"
AK3_TREE_NAME = "Cluster_1_396genomes_refsa230905_barcode06_ML_Flitered_BS.nwk"
AK3_ALIGNMENT_SHA256 = "40c49b026c52e04530ecbbee7044567ac3355eccf7adda42a7d96bf977df9014"
AK3_TREE_SHA256 = "18322b2808baf621d09dd5292027205e68a0f207d7be44f043bd044d0d314bd0"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_tsv(path: Path, fields: list[str], rows: Iterable[Iterable[Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(fields)
        writer.writerows(rows)


def quote_nexus(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def convert_csv_to_nexus(csv_path: Path, nexus_path: Path, site_prefix: str) -> tuple[int, int]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if not header or header[0].strip().lower() != "pos":
            raise ValueError(f"Unexpected SNP-table header in {csv_path}")
        taxa = [item.strip() for item in header[1:]]
        rows = list(reader)
    if len(taxa) != len(set(taxa)):
        raise ValueError(f"Duplicate taxon names in {csv_path}")
    with nexus_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("#NEXUS\nBEGIN DATA;\n")
        handle.write(f"DIMENSIONS NTAX={len(taxa)} NCHAR={len(rows)};\n")
        handle.write('FORMAT DATATYPE=DNA SYMBOLS="ACGT" MISSING=? GAP=- TRANSPOSE;\n')
        handle.write("TAXLABELS\n")
        for taxon in taxa:
            handle.write(f"  {quote_nexus(taxon)}\n")
        handle.write(";\nMATRIX\n")
        for row_number, row in enumerate(rows, start=1):
            if len(row) != len(taxa) + 1:
                raise ValueError(
                    f"Row {row_number} in {csv_path} has {len(row) - 1} states; "
                    f"expected {len(taxa)}"
                )
            position = row[0].strip()
            states = "".join(item.strip().upper() for item in row[1:])
            handle.write(f"  {site_prefix}_{position} {states}\n")
        handle.write(";\nEND;\n")
    return len(taxa), len(rows)


def read_events(path: Path) -> dict[str, set[tuple[int, str]]]:
    events: dict[str, set[tuple[int, str]]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"Position", "Derived_Node", "Ancestor_Call", "Derived_Call"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"Unexpected SNPPar event columns in {path}")
        for row in reader:
            event = (int(row["Position"]), f"{row['Ancestor_Call']}>{row['Derived_Call']}")
            bucket = events.setdefault(row["Derived_Node"], set())
            if event in bucket:
                raise ValueError(f"Duplicate SNPPar event in {path}: {row['Derived_Node']} {event}")
            bucket.add(event)
    return events


def read_result_events(path: Path) -> dict[int, str]:
    values: dict[int, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            position = int(row["position"])
            if position in values:
                raise ValueError(f"Duplicate result position in {path}: {position}")
            values[position] = row["change"]
    return values


def compare_ak3_table(
    dataset_id: str,
    published: tuple[tuple[int, str], ...],
    observed_path: Path,
) -> tuple[dict[str, Any], list[tuple[Any, ...]]]:
    observed = read_result_events(observed_path)
    published_map = dict(published)
    all_positions = sorted(set(observed) | set(published_map))
    rows: list[tuple[Any, ...]] = []
    exact = 0
    reversed_direction = 0
    published_only = 0
    observed_only = 0
    for position in all_positions:
        pub = published_map.get(position, "")
        obs = observed.get(position, "")
        if pub and obs:
            if pub == obs:
                status = "exact"
                exact += 1
            elif ">" in pub and obs == ">".join(reversed(pub.split(">"))):
                status = "reversed_direction"
                reversed_direction += 1
            else:
                status = "direction_or_state_difference"
        elif pub:
            status = "published_only"
            published_only += 1
        else:
            status = "working_output_only"
            observed_only += 1
        rows.append((dataset_id, position, pub, obs, status))
    summary = {
        "dataset_id": dataset_id,
        "published_snv_events": len(published_map),
        "working_output_snv_events": len(observed),
        "shared_positions": len(set(observed) & set(published_map)),
        "exact_position_and_direction": exact,
        "reversed_direction": reversed_direction,
        "published_only": published_only,
        "working_output_only": observed_only,
    }
    return summary, rows


def maybe_rerun_ak3(branchsnv_root: Path, ak3_input_dir: Path | None) -> dict[str, Any]:
    status: dict[str, Any] = {
        "performed": False,
        "alignment_sha256": AK3_ALIGNMENT_SHA256,
        "tree_sha256": AK3_TREE_SHA256,
    }
    if ak3_input_dir is None:
        status["reason"] = "Exact checksum-matched AK3 alignment and tree were not supplied."
        return status
    alignment = ak3_input_dir / AK3_ALIGNMENT_NAME
    tree = ak3_input_dir / AK3_TREE_NAME
    if not alignment.is_file() or not tree.is_file():
        raise FileNotFoundError(
            f"AK3 input directory must contain {AK3_ALIGNMENT_NAME!r} and {AK3_TREE_NAME!r}"
        )
    observed_alignment_hash = sha256_file(alignment)
    observed_tree_hash = sha256_file(tree)
    if observed_alignment_hash != AK3_ALIGNMENT_SHA256:
        raise ValueError(f"AK3 alignment checksum mismatch: {observed_alignment_hash}")
    if observed_tree_hash != AK3_TREE_SHA256:
        raise ValueError(f"AK3 tree checksum mismatch: {observed_tree_hash}")
    script = branchsnv_root / "validation" / "ak3" / "run_validation.sh"
    completed = subprocess.run(
        ["bash", str(script), str(alignment), str(tree)],
        cwd=branchsnv_root,
        check=False,
        capture_output=True,
        text=True,
    )
    status.update(
        {
            "performed": True,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "passed": completed.returncode == 0,
        }
    )
    if completed.returncode != 0:
        raise RuntimeError("AK3 checksum-gated validation failed; see run metadata")
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branchsnv-root", required=True, type=Path)
    parser.add_argument("--public-input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--ak3-input-dir",
        type=Path,
        help="Optional directory containing the exact checksum-matched AK3 alignment and tree.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started_utc = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()
    branchsnv_root = args.branchsnv_root.resolve()
    public_input_dir = args.public_input_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_root = branchsnv_root / "src"
    if not (source_root / "branchsnv" / "__init__.py").is_file():
        raise FileNotFoundError(f"Not a BRANCHSNV source checkout: {branchsnv_root}")
    sys.path.insert(0, str(source_root))

    import branchsnv  # type: ignore
    from branchsnv.analysis import analyse_branch  # type: ignore
    from branchsnv.newick import (  # type: ignore
        branch_records,
        descendant_tip_map,
        read_newick,
        reroot_on_outgroup,
    )
    from branchsnv.nexus import read_transposed_nexus  # type: ignore

    input_rows: list[tuple[Any, ...]] = []
    for name, spec in PUBLIC_INPUTS.items():
        path = public_input_dir / name
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing public input {path}. Run download_public_inputs.py first."
            )
        observed = sha256_file(path)
        if observed != spec["sha256"]:
            raise ValueError(f"Checksum mismatch for {path}: {observed}")
        input_rows.append((name, observed, spec["url"]))
    write_tsv(output_dir / "public_input_checksums.tsv", ["file", "sha256", "source_url"], input_rows)

    dataset_rows: list[tuple[Any, ...]] = []
    branch_rows: list[tuple[Any, ...]] = []
    event_rows: list[tuple[Any, ...]] = []
    ambiguous_rows: list[tuple[Any, ...]] = []
    dataset_summaries: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="branchsnv-exp3-") as temp_name:
        temp_dir = Path(temp_name)
        for spec in DATASETS:
            csv_path = public_input_dir / spec.snps_file
            nexus_path = temp_dir / f"{spec.dataset_id}.nex"
            ntax, nchar = convert_csv_to_nexus(csv_path, nexus_path, spec.site_prefix)
            alignment = read_transposed_nexus(nexus_path)
            tree = read_newick(public_input_dir / spec.tree_file)
            if spec.rooting == "outgroup":
                tree = reroot_on_outgroup(tree, set(spec.outgroup))
            labelled_tree = read_newick(public_input_dir / spec.labelled_tree_file)

            alignment_tips = set(alignment.taxa)
            tree_tips = {tip.name for tip in tree.tips()}
            labelled_tips = {tip.name for tip in labelled_tree.tips()}
            if alignment_tips != tree_tips or alignment_tips != labelled_tips:
                raise ValueError(f"Taxon mismatch in {spec.dataset_id}")

            labelled_descendants = descendant_tip_map(labelled_tree)
            label_by_descendants: dict[tuple[str, ...], str] = {}
            for node, tips in labelled_descendants.items():
                if node is labelled_tree.root:
                    continue
                if not node.name:
                    raise ValueError(f"Unlabelled non-root node in {spec.labelled_tree_file}")
                if tips in label_by_descendants:
                    raise ValueError(f"Duplicate descendant set in {spec.labelled_tree_file}")
                label_by_descendants[tips] = node.name

            records = branch_records(tree)
            if len(records) != len(label_by_descendants):
                raise ValueError(
                    f"Branch-count mismatch in {spec.dataset_id}: "
                    f"BRANCHSNV={len(records)}, SNPPar={len(label_by_descendants)}"
                )
            snppar_events = read_events(public_input_dir / spec.events_file)

            total_unambiguous = 0
            total_placement_ambiguous = 0
            total_change_state_ambiguous = 0
            total_snppar = sum(len(items) for items in snppar_events.values())
            total_common = 0
            total_branch_only = 0
            total_snppar_only = 0
            direction_differences = 0
            exact_branches = 0
            affected_branches = 0

            for branch in records:
                node_label = label_by_descendants.get(branch.descendant_tips)
                if node_label is None:
                    raise ValueError(
                        f"No SNPPar node maps to BRANCHSNV edge {branch.branch_id} "
                        f"in {spec.dataset_id}"
                    )
                analysis = analyse_branch(
                    alignment=alignment,
                    tree=tree,
                    branch=branch,
                    mode="parsimony",
                    include_ambiguous=True,
                )
                result_by_position = {item.position: item for item in analysis.results}
                branch_events = {
                    (item.position, item.change)
                    for item in analysis.results
                    if item.parsimony_status == "unambiguous_change"
                }
                published_events = snppar_events.get(node_label, set())
                common = branch_events & published_events
                branch_only = branch_events - published_events
                snppar_only = published_events - branch_events

                branch_by_position = {position: change for position, change in branch_events}
                snppar_by_position = {position: change for position, change in published_events}
                pair_differences = {
                    position
                    for position in branch_by_position.keys() & snppar_by_position.keys()
                    if branch_by_position[position] != snppar_by_position[position]
                }

                ambiguous_supported = 0
                for position, change in sorted(snppar_only):
                    result = result_by_position.get(position)
                    if result is None:
                        comparison = "snppar_only_not_reported_by_branchsnv"
                        possible_pairs = ""
                        status = "no_change_or_unreported"
                    else:
                        possible = set(result.possible_pairs.split("|"))
                        possible_pairs = result.possible_pairs
                        status = result.parsimony_status
                        if result.parsimony_status == "placement_ambiguous" and change in possible:
                            comparison = "snppar_event_is_one_branchsnv_optimum"
                            ambiguous_supported += 1
                        else:
                            comparison = "method_difference_unexplained"
                    row = (
                        spec.dataset_id,
                        spec.organism,
                        spec.chromosome,
                        node_label,
                        branch.branch_id,
                        branch.descendant_count,
                        position,
                        change,
                        status,
                        possible_pairs,
                        comparison,
                    )
                    event_rows.append(row)
                    ambiguous_rows.append(row)

                for position, change in sorted(common):
                    result = result_by_position[position]
                    event_rows.append(
                        (
                            spec.dataset_id,
                            spec.organism,
                            spec.chromosome,
                            node_label,
                            branch.branch_id,
                            branch.descendant_count,
                            position,
                            change,
                            result.parsimony_status,
                            result.possible_pairs,
                            "exact_unambiguous",
                        )
                    )
                for position, change in sorted(branch_only):
                    result = result_by_position[position]
                    event_rows.append(
                        (
                            spec.dataset_id,
                            spec.organism,
                            spec.chromosome,
                            node_label,
                            branch.branch_id,
                            branch.descendant_count,
                            position,
                            change,
                            result.parsimony_status,
                            result.possible_pairs,
                            "branchsnv_only_unambiguous",
                        )
                    )

                is_exact = not branch_only and not snppar_only and not pair_differences
                exact_branches += int(is_exact)
                affected_branches += int(not is_exact)
                total_unambiguous += analysis.unambiguous_change_sites
                total_placement_ambiguous += analysis.placement_ambiguous_sites
                total_change_state_ambiguous += analysis.change_state_ambiguous_sites
                total_common += len(common)
                total_branch_only += len(branch_only)
                total_snppar_only += len(snppar_only)
                direction_differences += len(pair_differences)

                branch_rows.append(
                    (
                        spec.dataset_id,
                        node_label,
                        branch.branch_id,
                        branch.descendant_count,
                        analysis.unambiguous_change_sites,
                        analysis.placement_ambiguous_sites,
                        analysis.change_state_ambiguous_sites,
                        len(published_events),
                        len(common),
                        len(branch_only),
                        len(snppar_only),
                        len(pair_differences),
                        ambiguous_supported,
                        "exact" if is_exact else "method_difference",
                    )
                )

            if total_common != total_unambiguous:
                raise AssertionError(
                    f"Not every BRANCHSNV unambiguous event matched SNPPar in {spec.dataset_id}"
                )
            if total_branch_only or direction_differences:
                raise AssertionError(
                    f"Unexpected unambiguous disagreement in {spec.dataset_id}: "
                    f"BRANCHSNV-only={total_branch_only}, direction={direction_differences}"
                )
            supported_for_all_snppar_only = sum(
                row[-1] == "snppar_event_is_one_branchsnv_optimum"
                for row in ambiguous_rows
                if row[0] == spec.dataset_id
            )
            if supported_for_all_snppar_only != total_snppar_only:
                raise AssertionError(
                    f"Not every SNPPar-only event was placement-ambiguous in {spec.dataset_id}"
                )

            dataset_summary = {
                "dataset_id": spec.dataset_id,
                "organism": spec.organism,
                "chromosome": spec.chromosome,
                "taxa": ntax,
                "variable_sites": nchar,
                "non_root_edges": len(records),
                "exact_edge_comparisons": exact_branches,
                "method_difference_edge_comparisons": affected_branches,
                "branchsnv_unambiguous_events": total_unambiguous,
                "snppar_events": total_snppar,
                "exact_unambiguous_matches": total_common,
                "branchsnv_only_unambiguous": total_branch_only,
                "snppar_only_events": total_snppar_only,
                "snppar_only_supported_as_branchsnv_placement_ambiguous": supported_for_all_snppar_only,
                "direction_differences": direction_differences,
                "branchsnv_placement_ambiguous_edge_sites": total_placement_ambiguous,
                "branchsnv_change_state_ambiguous_edge_sites": total_change_state_ambiguous,
                "converted_nexus_sha256": sha256_file(nexus_path),
            }
            dataset_summaries.append(dataset_summary)
            dataset_rows.append(
                tuple(dataset_summary[field] for field in (
                    "dataset_id", "organism", "chromosome", "taxa", "variable_sites",
                    "non_root_edges", "exact_edge_comparisons",
                    "method_difference_edge_comparisons", "branchsnv_unambiguous_events",
                    "snppar_events", "exact_unambiguous_matches",
                    "branchsnv_only_unambiguous", "snppar_only_events",
                    "snppar_only_supported_as_branchsnv_placement_ambiguous",
                    "direction_differences", "branchsnv_placement_ambiguous_edge_sites",
                    "branchsnv_change_state_ambiguous_edge_sites", "converted_nexus_sha256",
                ))
            )

    dataset_fields = [
        "dataset_id", "organism", "chromosome", "taxa", "variable_sites",
        "non_root_edges", "exact_edge_comparisons", "method_difference_edge_comparisons",
        "branchsnv_unambiguous_events", "snppar_events", "exact_unambiguous_matches",
        "branchsnv_only_unambiguous", "snppar_only_events",
        "snppar_only_supported_as_branchsnv_placement_ambiguous", "direction_differences",
        "branchsnv_placement_ambiguous_edge_sites", "branchsnv_change_state_ambiguous_edge_sites",
        "converted_nexus_sha256",
    ]
    write_tsv(output_dir / "dataset_summary.tsv", dataset_fields, dataset_rows)
    write_tsv(
        output_dir / "branch_summary.tsv",
        [
            "dataset_id", "snppar_derived_node", "branchsnv_branch_id", "descendant_count",
            "branchsnv_unambiguous_events", "branchsnv_placement_ambiguous_sites",
            "branchsnv_change_state_ambiguous_sites", "snppar_events", "exact_matches",
            "branchsnv_only_unambiguous", "snppar_only_events", "direction_differences",
            "snppar_only_supported_as_branchsnv_placement_ambiguous", "comparison",
        ],
        branch_rows,
    )
    event_fields = [
        "dataset_id", "organism", "chromosome", "snppar_derived_node",
        "branchsnv_branch_id", "descendant_count", "position", "snppar_or_branchsnv_change",
        "branchsnv_status", "branchsnv_possible_pairs", "comparison",
    ]
    write_tsv(output_dir / "event_comparison.tsv", event_fields, event_rows)
    write_tsv(output_dir / "placement_ambiguous_snppar_events.tsv", event_fields, ambiguous_rows)

    ak3_expected = branchsnv_root / "validation" / "ak3" / "expected"
    mrsa_path = ak3_expected / "mrsa_360_results.tsv"
    sapi_path = ak3_expected / "sapi_385_results.tsv"
    if not mrsa_path.is_file() or not sapi_path.is_file():
        raise FileNotFoundError("BRANCHSNV checkout lacks committed AK3 expected outputs")
    ak3_mrsa, mrsa_rows = compare_ak3_table("ak3_mrsa_360", AK3_MRSA_PUBLISHED, mrsa_path)
    ak3_sapi, sapi_rows = compare_ak3_table("ak3_sapi_385", AK3_SAPI_PUBLISHED, sapi_path)
    write_tsv(
        output_dir / "ak3_table_comparison.tsv",
        ["dataset_id", "position", "published_change", "working_output_change", "comparison"],
        mrsa_rows + sapi_rows,
    )
    ak3_rerun = maybe_rerun_ak3(branchsnv_root, args.ak3_input_dir.resolve() if args.ak3_input_dir else None)

    public_totals = {
        "datasets": len(dataset_summaries),
        "organisms": len({item["organism"] for item in dataset_summaries}),
        "branch_matrix_comparisons": sum(item["non_root_edges"] for item in dataset_summaries),
        "exact_edge_comparisons": sum(item["exact_edge_comparisons"] for item in dataset_summaries),
        "method_difference_edge_comparisons": sum(
            item["method_difference_edge_comparisons"] for item in dataset_summaries
        ),
        "branchsnv_unambiguous_events": sum(
            item["branchsnv_unambiguous_events"] for item in dataset_summaries
        ),
        "snppar_events": sum(item["snppar_events"] for item in dataset_summaries),
        "exact_unambiguous_matches": sum(
            item["exact_unambiguous_matches"] for item in dataset_summaries
        ),
        "branchsnv_only_unambiguous": sum(
            item["branchsnv_only_unambiguous"] for item in dataset_summaries
        ),
        "snppar_only_events": sum(item["snppar_only_events"] for item in dataset_summaries),
        "snppar_only_supported_as_branchsnv_placement_ambiguous": sum(
            item["snppar_only_supported_as_branchsnv_placement_ambiguous"]
            for item in dataset_summaries
        ),
        "direction_differences": sum(item["direction_differences"] for item in dataset_summaries),
    }
    public_pass = (
        public_totals["exact_unambiguous_matches"]
        == public_totals["branchsnv_unambiguous_events"]
        and public_totals["branchsnv_only_unambiguous"] == 0
        and public_totals["direction_differences"] == 0
        and public_totals["snppar_only_events"]
        == public_totals["snppar_only_supported_as_branchsnv_placement_ambiguous"]
    )
    ak3_mrsa_pass = (
        ak3_mrsa["exact_position_and_direction"] == len(AK3_MRSA_PUBLISHED)
        and ak3_mrsa["working_output_only"] == 0
        and ak3_mrsa["published_only"] == 0
    )

    elapsed = time.perf_counter() - start
    summary = {
        "schema_version": 1,
        "experiment": "03_published_datasets",
        "description": (
            "All-edge comparison with published SNPPar bacterial datasets and comparison of "
            "committed AK3 working-data outputs with published branch tables."
        ),
        "branchsnv_version": branchsnv.__version__,
        "branchsnv_analysis_sha256": sha256_file(source_root / "branchsnv" / "analysis.py"),
        "branchsnv_parsimony_sha256": sha256_file(source_root / "branchsnv" / "parsimony.py"),
        "validation_script_sha256": sha256_file(Path(__file__).resolve()),
        "public_comparison": {
            "passed": public_pass,
            "datasets": dataset_summaries,
            "totals": public_totals,
        },
        "ak3_comparison": {
            "publication": "White et al. Microbial Genomics 2025;11:001452; DOI 10.1099/mgen.0.001452",
            "mrsa_360": ak3_mrsa,
            "mrsa_published_indel_outside_scope": {
                "position": AK3_MRSA_PUBLISHED_INDEL[0],
                "change": AK3_MRSA_PUBLISHED_INDEL[1],
                "type": AK3_MRSA_PUBLISHED_INDEL[2],
            },
            "sapi_385": ak3_sapi,
            "sapi_published_indel_outside_scope": {
                "position": AK3_SAPI_PUBLISHED_INDEL[0],
                "change": AK3_SAPI_PUBLISHED_INDEL[1],
                "type": AK3_SAPI_PUBLISHED_INDEL[2],
            },
            "primary_mrsa_reproduction_passed": ak3_mrsa_pass,
            "sapi_version_difference_unresolved": True,
            "raw_input_rerun": ak3_rerun,
        },
        "overall_pass": public_pass and ak3_mrsa_pass,
        "publication_archive_blocker": (
            None if ak3_rerun.get("performed") else
            "The exact checksum-matched AK3 alignment and tree still require public archiving."
        ),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    metadata = {
        "experiment": "03_published_datasets",
        "started_utc": started_utc,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 6),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "branchsnv_root": str(branchsnv_root),
        "public_input_dir": str(public_input_dir),
        "output_dir": str(output_dir),
        "exit_status": "PASS" if summary["overall_pass"] else "FAIL",
    }
    (output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )

    print(f"BRANCHSNV version: {branchsnv.__version__}")
    print(f"Public branch-matrix comparisons: {public_totals['branch_matrix_comparisons']:,}")
    print(f"BRANCHSNV unambiguous events: {public_totals['branchsnv_unambiguous_events']:,}")
    print(f"Exact SNPPar matches: {public_totals['exact_unambiguous_matches']:,}")
    print(f"SNPPar-only, placement-ambiguous events: {public_totals['snppar_only_events']:,}")
    print(
        f"AK3 MRSA published SNVs: {ak3_mrsa['exact_position_and_direction']}/"
        f"{ak3_mrsa['published_snv_events']} exact"
    )
    print("PASS" if summary["overall_pass"] else "FAIL")
    return 0 if summary["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
