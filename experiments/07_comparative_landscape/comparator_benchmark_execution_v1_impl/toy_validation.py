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


def require_value_error(fn, expected, msg):
    try:
        fn()
    except ValueError as exc:
        require(expected in str(exc), msg)
    else:
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
    # Synthetic PAML rst: internal numbering is intentionally arbitrary.
    paml_tree = "((A:0.1,B:0.1):0.1,(C:0.1,D:0.1):0.1);"
    paml_rst = (
        "Branch 1:    20..30\n"
        "Branch 2:    30..1  (A)\n"
        "Branch 3:    30..2  (B)\n"
        "Branch 4:    20..40\n"
        "Branch 5:    40..3  (C)\n"
        "Branch 6:    40..4  (D)\n"
        "List of extant and reconstructed sequences\n"
        "     7     4\n"
        "A                 AAAA\n"
        "B                 AAAG\n"
        "C                 AAAA\n"
        "D                 AAAA\n"
        "node #20          AAAA\n"
        "node #30          AAAA\n"
        "node #40          AAAA\n"
        "Overall accuracy\n"
    )
    paml_seqs = adapters.paml_node_sequences_for_tree(paml_rst, paml_tree)
    paml_events = adapters.events_from_node_sequences(
        paml_tree,
        paml_seqs,
        method="PAML",
        scenario_id="TOY_PAML",
    )
    require(len(paml_seqs) == 7, "PAML node mapping fixture incomplete")
    require(len(paml_events) == 1, "PAML event fixture differs")
    require(
        paml_events[0]["edge_id"] == next(v for k, v in vars(adapters).items() if k.endswith("edge_ids_by_node"))(paml_tree)["B"]
        and paml_events[0]["position"] == "4"
        and paml_events[0]["ancestral_state"] == "A"
        and paml_events[0]["derived_state"] == "G",
        "PAML node mapping fixture differs",
    )

    paml_incomplete = paml_rst.replace(
        "Branch 6:    40..4  (D)\n",
        "",
    )
    require_value_error(
        lambda: adapters.paml_node_sequences_for_tree(paml_incomplete, paml_tree),
        "different tip sets",
        "incomplete PAML mapping did not fail closed",
    )

    paml_conflicting = paml_rst.replace(
        "List of extant and reconstructed sequences\n",
        "Branch 7:    99..2  (B)\nList of extant and reconstructed sequences\n",
    )
    require_value_error(
        lambda: adapters.paml_node_sequences_for_tree(paml_conflicting, paml_tree),
        "multiple parents",
        "conflicting PAML parentage did not fail closed",
    )

    paml_disconnected = paml_rst.replace(
        "Branch 1:    20..30\n",
        "Branch 1:    50..30\n",
    )
    require_value_error(
        lambda: adapters.paml_node_sequences_for_tree(paml_disconnected, paml_tree),
        "exactly one root",
        "disconnected PAML graph did not fail closed",
    )

    paml_nonbijective_tree = "(A:0.1,B:0.1);"
    paml_nonbijective_rst = (
        "Branch 1:    20..30\n"
        "Branch 2:    30..1  (A)\n"
        "Branch 3:    30..2  (B)\n"
        "List of extant and reconstructed sequences\n"
        "A AAAA\n"
        "B AAAG\n"
        "node #20 AAAA\n"
        "node #30 AAAA\n"
        "Overall accuracy\n"
    )
    require_value_error(
        lambda: adapters.paml_node_sequences_for_tree(
            paml_nonbijective_rst,
            paml_nonbijective_tree,
        ),
        "not one-to-one",
        "non-bijective PAML mapping did not fail closed",
    )

    paml_ambiguous_tree = "((A:0.1):0.1,B:0.1);"
    paml_ambiguous_rst = (
        "Branch 1:    20..1  (A)\n"
        "Branch 2:    20..2  (B)\n"
        "List of extant and reconstructed sequences\n"
        "A AAAA\n"
        "B AAAG\n"
        "node #20 AAAA\n"
        "Overall accuracy\n"
    )
    require_value_error(
        lambda: adapters.paml_node_sequences_for_tree(
            paml_ambiguous_rst,
            paml_ambiguous_tree,
        ),
        "ambiguous descendant-tip sets",
        "ambiguous benchmark node mapping did not fail closed",
    )


    # Synthetic FastML joint reconstruction with arbitrary internal labels.
    fastml_tree = "((A:0.1,B:0.1)XAB:0.1,(C:0.1,D:0.1)XCD:0.1)XROOT;"
    fastml_benchmark_tree = "((A:0.1,B:0.1):0.1,(C:0.1,D:0.1):0.1);"
    fastml_joint = (
        ">A\nAAAA\n"
        ">B\nAAAG\n"
        ">C\nAAAA\n"
        ">D\nAAAA\n"
        ">XAB\nAAAA\n"
        ">XCD\nAAAA\n"
        ">XROOT\nAAAA\n"
    )

    fastml_seqs = adapters.fastml_node_sequences_for_tree(
        fastml_joint,
        fastml_tree,
        fastml_benchmark_tree,
    )
    fastml_events = adapters.events_from_node_sequences(
        fastml_benchmark_tree,
        fastml_seqs,
        method="FastML",
        scenario_id="TOY_FASTML",
    )

    require(len(fastml_seqs) == 7, "FastML node mapping fixture incomplete")
    require(len(fastml_events) == 1, "FastML event fixture differs")
    require(
        fastml_events[0]["edge_id"]
        == next(
            v for k, v in vars(adapters).items()
            if k.endswith("edge_ids_by_node")
        )(fastml_benchmark_tree)["B"]
        and fastml_events[0]["position"] == "4"
        and fastml_events[0]["ancestral_state"] == "A"
        and fastml_events[0]["derived_state"] == "G",
        "FastML node mapping fixture differs",
    )

    require_value_error(
        lambda: adapters.fastml_node_sequences_for_tree(
            fastml_joint,
            fastml_tree.replace("D:0.1", "E:0.1"),
            fastml_benchmark_tree,
        ),
        "different tip sets",
        "different-tip FastML mapping did not fail closed",
    )

    require_value_error(
        lambda: adapters.fastml_node_sequences_for_tree(
            fastml_joint,
            fastml_tree,
            "((A:0.1):0.1,B:0.1);",
        ),
        "ambiguous descendant-tip sets",
        "ambiguous FastML mapping did not fail closed",
    )

    require_value_error(
        lambda: adapters.fastml_node_sequences_for_tree(
            fastml_joint.replace(">XCD\nAAAA\n", ""),
            fastml_tree,
            fastml_benchmark_tree,
        ),
        "missing reconstructed sequence",
        "missing-sequence FastML mapping did not fail closed",
    )

    print("PASS | synthetic tool-output parser fixtures")

    print("PASS | no third-party comparator installed or executed")
    print("TOY_IMPLEMENTATION_VALIDATION=PASS")


if __name__ == "__main__":
    main()
