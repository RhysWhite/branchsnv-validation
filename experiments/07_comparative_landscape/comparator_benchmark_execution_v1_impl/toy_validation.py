#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import os
import tempfile

import generator
import adapters
import metrics


def require(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    print("===== TOY-ONLY IMPLEMENTATION VALIDATION =====")

    # Canonical generation must be fail-closed before later authorization.
    prior_auth = os.environ.pop(generator.CANONICAL_AUTH_ENV, None)
    try:
        try:
            generator.generate_dataset(
                "S001", 32, "unique_only", "complete",
                length_bp=10000, canonical=True,
            )
        except PermissionError:
            print("PASS | canonical generation fail-closed")
        else:
            raise AssertionError("canonical generation unexpectedly authorized")
    finally:
        if prior_auth is not None:
            os.environ[generator.CANONICAL_AUTH_ENV] = prior_auth

    toy1 = generator.generate_dataset(
        "TOY_MIXED",
        8,
        "mixed_recurrence",
        "complete",
        length_bp=400,
        canonical=False,
    )
    toy2 = generator.generate_dataset(
        "TOY_MIXED",
        8,
        "mixed_recurrence",
        "complete",
        length_bp=400,
        canonical=False,
    )
    require(toy1["tree_newick"] == toy2["tree_newick"], "toy tree nondeterministic")
    require(toy1["events"] == toy2["events"], "toy events nondeterministic")
    require(toy1["truth_sequences"] == toy2["truth_sequences"], "toy sequences nondeterministic")
    require(len(toy1["variable_positions"]) == 40, "toy variable-site count differs")
    require(len(toy1["edge_ids"]) == 14, "8-tip bifurcating tree must have 14 rooted edges")
    require(all(len(x) == 64 for x in toy1["edge_ids"].values()), "edge ids not SHA256")
    print("PASS | deterministic independent toy generator")
    print("PASS | canonical descendant-tip edge identifiers")

    missing = generator.generate_dataset(
        "TOY_MISSING",
        8,
        "parallel",
        "missing_5pct",
        length_bp=400,
        canonical=False,
    )
    expected_missing = 8 * 40 * 5 // 100
    require(len(missing["missing_mask"]) == expected_missing, "missing mask is not exactly 5%")
    print("PASS | exact 5% variable-site missingness")

    # Every event has a nonidentity nucleotide transition.
    for e in toy1["events"]:
        require(e["ancestral_state"] in "ACGT", "bad ancestral state")
        require(e["derived_state"] in "ACGT", "bad derived state")
        require(e["ancestral_state"] != e["derived_state"], "identity event")
    print("PASS | event ledger nucleotide-state invariants")

    # Adapter contracts.
    positions = toy1["variable_positions"]
    pml = adapters.pastml_table_text(toy1["observed_sequences"], positions)
    require(pml.splitlines()[0].startswith("id\tsite_"), "PastML table header")
    snpfa = adapters.snppar_mfasta_text(missing["observed_sequences"], positions)
    require("-" in snpfa, "SNPPar missing calls must be '-'")
    gbk = adapters.minimal_genbank_text(
        toy1["root_sequence"],
        positions,
    )
    require(gbk.endswith("//\n"), "GenBank terminator absent")

    cds_lines = [
        line
        for line in gbk.splitlines()
        if line.startswith("     CDS")
    ]
    require(len(cds_lines) == 1, "synthetic GenBank must contain one CDS")

    cds_location = cds_lines[0].split()[-1]
    cds_start, cds_end = [
        int(x)
        for x in cds_location.split("..")
    ]

    require(
        cds_end - cds_start + 1 == 3,
        "synthetic CDS must span exactly three bases",
    )

    variable_set = set(positions)

    require(
        variable_set.isdisjoint(
            range(cds_start, cds_end + 1)
        ),
        "synthetic CDS overlaps a variable site",
    )

    eligible_starts = [
        start
        for start in range(
            1,
            len(toy1["root_sequence"]) - 1,
        )
        if variable_set.isdisjoint(
            (start, start + 1, start + 2)
        )
    ]

    require(
        bool(eligible_starts),
        "no variable-site-free triplet exists",
    )

    require(
        cds_start == eligible_starts[0],
        "synthetic CDS placement is not deterministic",
    )

    require(
        '/locus_tag="SYNTH_CDS_001"' in gbk,
        "synthetic CDS locus tag absent",
    )

    origin = gbk.split("ORIGIN\n", 1)[1].split("//", 1)[0]
    rendered_sequence = "".join(
        c
        for c in origin.lower()
        if c in "acgt"
    ).upper()

    require(
        rendered_sequence == toy1["root_sequence"],
        "synthetic GenBank changed the reference sequence",
    )

    print("PASS | synthetic SNPPar GenBank fixture contract")
    paml_tree = adapters.paml_tree_text("((A:0.1,B:0.1):0.1,(C:0.1,D:0.1):0.1);", 4)
    require(paml_tree == "4 1\n((A:0.1,B:0.1):0.1,(C:0.1,D:0.1):0.1);\n", "PAML tree serializer differs")
    ctl = adapters.paml_baseml_ctl_text("seq.phy", "tree.nwk", "mlb")
    require("RateAncestor = 1" in ctl and "fix_blength = 2" in ctl, "PAML contract differs")
    arp = adapters.arpip_config_text("a.fa", "t.nwk", "out", 7)
    require("alphabet=DNA" in arp and "model=PIP(model=JC69,lambda=10,mu=0.01)" in arp, "ARPIP contract differs")
    print("PASS | static input-adapter contracts")

    # Newick mapping must reproduce generator edge IDs.
    parsed_edges = adapters.canonical_edge_ids_by_node(toy1["tree_newick"])
    require(parsed_edges == toy1["edge_ids"], "output-tree edge mapping differs")
    print("PASS | output-tree canonical edge mapping")

    # Perfect branch-event scoring.
    truth = [
        {
            "edge_id": e["edge_id"],
            "position": e["position"],
            "ancestral_state": e["ancestral_state"],
            "derived_state": e["derived_state"],
        }
        for e in toy1["events"]
    ]
    b = metrics.score_branch_events(truth, truth)
    require(b["precision"] == 1 and b["recall"] == 1 and b["f1"] == 1, "perfect branch score differs")

    h = metrics.score_homoplasy_sites(toy1["recurrent_positions"], toy1["recurrent_positions"])
    require(h["site_precision"] == 1 and h["site_recall"] == 1 and h["site_f1"] == 1, "perfect homoplasy score differs")

    empty = metrics.score_homoplasy_sites([], [])
    require(empty["site_f1"] == 1, "empty-perfect homoplasy convention differs")
    print("PASS | truth-blind metric engine")

    # Synthetic output parser fixtures; no comparator is executed.
    hf = (
        "Position\tConsistencyIndex\tCountsACGT\tMinimumNumberChangesOnTree\n"
        "10\t0.5\t6:0:2:0\t2\n"
        "20\t1.0\t8:0:0:0\t1\n"
    )
    parsed_hf = adapters.parse_homoplasyfinder_report(hf)
    require(
        parsed_hf == [
            {
                "position": "10",
                "reported_recurrence_count_if_available": "2",
            }
        ],
        "HomoplasyFinder parser real-schema fixture differs",
    )

    hf_without_count = "Position\tConsistencyIndex\n10\t0.5\n"
    parsed_hf_without_count = adapters.parse_homoplasyfinder_report(
        hf_without_count
    )
    require(
        parsed_hf_without_count == [
            {
                "position": "10",
                "reported_recurrence_count_if_available": "",
            }
        ],
        "HomoplasyFinder parser missing-count behaviour differs",
    )

    hf_empty_count = (
        "Position\tConsistencyIndex\tMinimumNumberChangesOnTree\n"
        "10\t0.5\t\n"
    )
    parsed_hf_empty_count = adapters.parse_homoplasyfinder_report(
        hf_empty_count
    )
    require(
        parsed_hf_empty_count == [
            {
                "position": "10",
                "reported_recurrence_count_if_available": "",
            }
        ],
        "HomoplasyFinder parser empty-count behaviour differs",
    )

    try:
        adapters.parse_homoplasyfinder_report(
            "Position\tConsistencyIndex\tMinimumNumberChangesOnTree\n"
            "10\t0.5\tnot-a-number\n"
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "HomoplasyFinder parser accepted non-numeric change count"
        )

    try:
        adapters.parse_homoplasyfinder_report(
            "Position\tConsistencyIndex\tMinimumNumberChangesOnTree\n"
            "10\t0.5\t2.5\n"
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "HomoplasyFinder parser accepted non-integer change count"
        )

    po = (
        "segsite_ID\tphysical_pos\tallele1\tallele2\ta1_count\ta2_count\n"
        "1\t10\tA\tT\t1\t1\n"
        "2\t20\tA\tG\t1\t0\n"
    )
    parsed_po = adapters.parse_poutine_result(po)
    require(parsed_po == [{"position":"10","reported_recurrence_count_if_available":"2"}], "POUTINE parser fixture differs")

    # Synthetic SNPPar event table + toy tree.
    tips = sorted(toy1["truth_sequences"])
    # Find one terminal edge to construct a valid fixture.
    child = tips[0]
    parent = toy1["parent"][child]
    table = (
        "Position\tAncestor_Node\tDerived_Node\tAncestor_Call\tDerived_Call\n"
        f"1\t{parent}\t{child}\tA\tT\n"
    )
    parsed_sp = adapters.parse_snppar_mutation_events(
        table,
        toy1["tree_newick"],
        scenario_id="TOY",
    )
    require(len(parsed_sp) == 1 and parsed_sp[0]["edge_id"] == toy1["edge_ids"][child], "SNPPar parser fixture differs")
    print("PASS | synthetic tool-output parser fixtures")

    print("PASS | no third-party comparator installed or executed")
    print("TOY_IMPLEMENTATION_VALIDATION=PASS")


if __name__ == "__main__":
    main()
