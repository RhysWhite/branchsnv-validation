#!/usr/bin/env python3
"""Deterministic benchmark adapters and output normalizers.

These functions do not invoke comparator software.
"""
from __future__ import annotations

import csv
from hashlib import sha256
import io
from pathlib import Path
import re
from typing import Iterable

DNA = set("ACGT")


def read_fasta(path: Path) -> dict[str, str]:
    records: dict[str, list[str]] = {}
    current = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            current = line[1:].split()[0]
            if current in records:
                raise ValueError(f"duplicate FASTA id: {current}")
            records[current] = []
        elif current is None:
            raise ValueError("FASTA sequence before header")
        else:
            records[current].append(line)
    return {k: "".join(v).upper() for k, v in records.items()}


def fasta_text(records: dict[str, str], width: int = 80) -> str:
    parts = []
    for name in sorted(records):
        seq = records[name]
        parts.append(f">{name}")
        parts.extend(seq[i:i+width] for i in range(0, len(seq), width))
    return "\n".join(parts) + "\n"


def variable_positions(root_sequence: str, sequences: dict[str, str]) -> list[int]:
    lengths = {len(root_sequence), *(len(x) for x in sequences.values())}
    if len(lengths) != 1:
        raise ValueError("sequence lengths differ")
    out = []
    for i, root_base in enumerate(root_sequence, start=1):
        states = {seq[i - 1] for seq in sequences.values() if seq[i - 1] in DNA}
        if any(s != root_base for s in states):
            out.append(i)
    return out


def pastml_table_text(
    observed_sequences: dict[str, str],
    positions: Iterable[int],
) -> str:
    positions = list(positions)
    out = io.StringIO(newline="")
    fields = ["id"] + [f"site_{p}" for p in positions]
    w = csv.DictWriter(out, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    for tip in sorted(observed_sequences):
        seq = observed_sequences[tip]
        row = {"id": tip}
        for p in positions:
            base = seq[p - 1]
            row[f"site_{p}"] = "" if base not in DNA else base
        w.writerow(row)
    return out.getvalue()


def snppar_mfasta_text(
    observed_sequences: dict[str, str],
    positions: Iterable[int],
) -> str:
    positions = list(positions)
    projected = {}
    for tip, seq in observed_sequences.items():
        projected[tip] = "".join(
            seq[p - 1] if seq[p - 1] in DNA else "-"
            for p in positions
        )
    return fasta_text(projected)


def positions_text(positions: Iterable[int]) -> str:
    return "".join(f"{p}\n" for p in positions)


def minimal_genbank_text(
    root_sequence: str,
    variable_positions: Iterable[int],
    locus: str = "BENCHREF",
) -> str:
    seq = root_sequence.lower()
    variable = {int(p) for p in variable_positions}

    if len(seq) < 3:
        raise ValueError("reference sequence must contain at least three bases")

    if any(p < 1 or p > len(seq) for p in variable):
        raise ValueError("variable position lies outside reference sequence")

    cds_start = next(
        (
            start
            for start in range(1, len(seq) - 1)
            if variable.isdisjoint((start, start + 1, start + 2))
        ),
        None,
    )

    if cds_start is None:
        raise ValueError(
            "reference sequence contains no three-base interval free of variable sites"
        )

    cds_end = cds_start + 2

    lines = [
        f"LOCUS       {locus:<16}{len(seq):>11} bp    DNA     linear   BCT 01-JAN-2000",
        "DEFINITION  Synthetic benchmark reference.",
        f"ACCESSION   {locus}",
        f"VERSION     {locus}.1",
        "FEATURES             Location/Qualifiers",
        f"     source          1..{len(seq)}",
        "                     /organism=\"synthetic construct\"",
        f"     CDS             {cds_start}..{cds_end}",
        "                     /locus_tag=\"SYNTH_CDS_001\"",
        "ORIGIN",
    ]

    for i in range(0, len(seq), 60):
        chunk = seq[i:i+60]
        groups = " ".join(chunk[j:j+10] for j in range(0, len(chunk), 10))
        lines.append(f"{i+1:>9} {groups}")

    lines.append("//")
    return "\n".join(lines) + "\n"


def paml_phylip_text(observed_sequences: dict[str, str]) -> str:
    names = sorted(observed_sequences)
    length = len(observed_sequences[names[0]])
    if any(len(observed_sequences[x]) != length for x in names):
        raise ValueError("PAML sequence lengths differ")
    # PAML accepts sequential format with names separated by whitespace.
    lines = [f"{len(names)} {length}"]
    for name in names:
        seq = observed_sequences[name].replace("N", "?")
        lines.append(f"{name}  {seq}")
    return "\n".join(lines) + "\n"


def paml_tree_text(tree_newick: str, n_taxa: int) -> str:
    if n_taxa < 2:
        raise ValueError("PAML tree requires at least two taxa")
    tree = tree_newick.strip()
    if not tree or not tree.startswith("("):
        raise ValueError("PAML tree must be non-empty Newick beginning with (")
    if not tree.endswith(";") or tree.count(";") != 1:
        raise ValueError("PAML tree must contain exactly one semicolon-terminated Newick record")
    return f"{n_taxa} 1\n{tree}\n"


def paml_baseml_ctl_text(seqfile: str, treefile: str, outfile: str) -> str:
    # JC69, fixed input branch lengths, constant site rate, ancestral reconstruction.
    return f"""seqfile = {seqfile}
treefile = {treefile}
outfile = {outfile}
noisy = 0
verbose = 1
runmode = 0
model = 0
Mgene = 0
clock = 0
fix_kappa = 1
kappa = 1
fix_alpha = 1
alpha = 0
Malpha = 0
ncatG = 4
nparK = 0
nhomo = 0
getSE = 0
RateAncestor = 1
Small_Diff = 1e-8
cleandata = 0
fix_blength = 2
method = 0
"""


def arpip_config_text(
    alignment_path: str,
    tree_path: str,
    out_dir: str,
    seed: int,
) -> str:
    # lambda/mu are taken from the official nucleotide example and are not truth-tuned.
    return f"""analysis_name=BRANCHSNV_BENCH
alphabet=DNA
input.sequence.file={alignment_path}
input.sequence.sites_to_use=all
init.tree=user
input.tree.file={tree_path}
model=PIP(model=JC69,lambda=10,mu=0.01)
opt.seed={seed}
opt.likelihood=0
opt.pip_param_estimate=0
opt.tree.with_ans_node_names=1
rate_distribution=Constant
output.msa.file={out_dir}/msa.fasta
output.tree.file={out_dir}/tree.nwk
output.ancestral.file={out_dir}/anc.fasta
output.node_rel.file={out_dir}/node_rel.txt
output.mlindelpoints.file={out_dir}/mlindelpoints.txt
"""


def poutine_dummy_phenotype_text(tips: Iterable[str]) -> str:
    # POUTINE's scored endpoint here is genotype homoplasy count, not association.
    # A deterministic balanced dummy phenotype prevents phenotype choice from
    # becoming an analysis degree of freedom.
    lines = []
    for i, tip in enumerate(sorted(tips)):
        lines.append(f"{tip}\t{i % 2}")
    return "\n".join(lines) + "\n"


def poutine_variant_fasta_text(
    observed_sequences: dict[str, str],
    positions: Iterable[int],
) -> str:
    positions = list(positions)
    projected = {}
    for tip, seq in observed_sequences.items():
        projected[tip] = "".join(seq[p - 1] for p in positions)
    return fasta_text(projected)


# ---------- lightweight tree parser for output normalization ----------

class _Node:
    def __init__(self, label: str = ""):
        self.label = label
        self.children: list["_Node"] = []


def _strip_newick_comments(text: str) -> str:
    return re.sub(r"\[[^\]]*\]", "", text)


def extract_newick(text: str) -> str:
    text = text.strip()
    if text.lower().startswith("#nexus"):
        matches = re.findall(r"(?im)^\s*tree\s+[^=]+=\s*(.+?;)\s*$", text)
        if not matches:
            raise ValueError("no tree statement in NEXUS")
        text = matches[-1]
        text = re.sub(r"^\s*\[&R\]\s*", "", text)
    start = text.find("(")
    end = text.rfind(";")
    if start < 0 or end < start:
        raise ValueError("cannot locate Newick tree")
    return _strip_newick_comments(text[start:end+1])


def parse_newick(text: str) -> _Node:
    s = extract_newick(text)
    i = 0
    auto = [0]

    def skip_ws():
        nonlocal i
        while i < len(s) and s[i].isspace():
            i += 1

    def read_label() -> str:
        nonlocal i
        skip_ws()
        start = i
        while i < len(s) and s[i] not in ",():;":
            i += 1
        return s[start:i].strip()

    def skip_length():
        nonlocal i
        skip_ws()
        if i < len(s) and s[i] == ":":
            i += 1
            while i < len(s) and s[i] not in ",();":
                i += 1

    def parse_node() -> _Node:
        nonlocal i
        skip_ws()
        if s[i] == "(":
            i += 1
            node = _Node()
            node.children.append(parse_node())
            skip_ws()
            while i < len(s) and s[i] == ",":
                i += 1
                node.children.append(parse_node())
                skip_ws()
            if i >= len(s) or s[i] != ")":
                raise ValueError("unbalanced Newick")
            i += 1
            label = read_label()
            if not label:
                auto[0] += 1
                label = f"__AUTO_INTERNAL_{auto[0]:04d}"
            node.label = label
            skip_length()
            return node
        label = read_label()
        if not label:
            raise ValueError("empty tip label")
        node = _Node(label)
        skip_length()
        return node

    root = parse_node()
    skip_ws()
    if i >= len(s) or s[i] != ";":
        raise ValueError("trailing Newick content")
    return root


def node_descendant_tips(newick_text: str) -> dict[str, tuple[str, ...]]:
    root = parse_newick(newick_text)
    out: dict[str, tuple[str, ...]] = {}

    def visit(node: _Node) -> tuple[str, ...]:
        if not node.children:
            tips = (node.label,)
        else:
            tips = tuple(sorted(x for c in node.children for x in visit(c)))
        if node.label in out:
            raise ValueError(f"duplicate node label: {node.label}")
        out[node.label] = tips
        return tips

    visit(root)
    return out


def canonical_edge_ids_by_node(newick_text: str) -> dict[str, str]:
    root = parse_newick(newick_text)
    desc = node_descendant_tips(newick_text)
    mapping = {}

    def walk(node: _Node, is_root: bool = False):
        if not is_root:
            material = "\n".join(desc[node.label]).encode("utf-8")
            mapping[node.label] = sha256(material).hexdigest()
        for child in node.children:
            walk(child, False)

    walk(root, True)
    return mapping


def parent_by_node(newick_text: str) -> dict[str, str]:
    root = parse_newick(newick_text)
    out = {}

    def walk(node: _Node):
        for child in node.children:
            out[child.label] = node.label
            walk(child)

    walk(root)
    return out


def events_from_node_sequences(
    newick_text: str,
    node_sequences: dict[str, str],
    *,
    method: str,
    scenario_id: str,
) -> list[dict[str, str]]:
    parents = parent_by_node(newick_text)
    edge_map = canonical_edge_ids_by_node(newick_text)
    events = []
    for child, parent in parents.items():
        if child not in node_sequences or parent not in node_sequences:
            raise ValueError(f"missing reconstructed sequence for edge {parent}->{child}")
        anc, der = node_sequences[parent], node_sequences[child]
        if len(anc) != len(der):
            raise ValueError("ancestral sequence lengths differ")
        for idx, (a, d) in enumerate(zip(anc, der), start=1):
            if a in DNA and d in DNA and a != d:
                events.append({
                    "scenario_id": scenario_id,
                    "method": method,
                    "edge_id": edge_map[child],
                    "position": str(idx),
                    "ancestral_state": a,
                    "derived_state": d,
                })
    return events


def parse_homoplasyfinder_report(text: str) -> list[dict[str, str]]:
    lines = [x for x in text.splitlines() if x.strip()]
    if not lines:
        return []
    dialect = "\t" if "\t" in lines[0] else ","
    rd = csv.DictReader(io.StringIO("\n".join(lines)), delimiter=dialect)
    fields = {x.lower().replace("_", "").replace(" ", ""): x for x in (rd.fieldnames or [])}
    pos_field = fields.get("position") or fields.get("site") or fields.get("alignmentposition")
    ci_field = fields.get("consistencyindex") or fields.get("consistency")
    count_field = fields.get("minimumnumberchangesontree")
    if not pos_field:
        raise ValueError("HomoplasyFinder report lacks position field")
    out = []
    for row in rd:
        if ci_field:
            try:
                if float(row[ci_field]) >= 1.0:
                    continue
            except (TypeError, ValueError):
                pass

        count = ""
        if count_field:
            raw_count = (row.get(count_field) or "").strip()
            if raw_count:
                try:
                    numeric_count = float(raw_count)
                except ValueError as exc:
                    raise ValueError(
                        "HomoplasyFinder minimum-change count is not numeric"
                    ) from exc
                if not numeric_count.is_integer():
                    raise ValueError(
                        "HomoplasyFinder minimum-change count is not an integer"
                    )
                count = str(int(numeric_count))

        out.append({
            "position": str(int(float(row[pos_field]))),
            "reported_recurrence_count_if_available": count,
        })
    return out


def parse_poutine_result(text: str) -> list[dict[str, str]]:
    lines = [x for x in text.splitlines() if x.strip() and not x.startswith("#")]
    if not lines:
        return []
    rd = csv.DictReader(io.StringIO("\n".join(lines)), delimiter="\t")
    needed = {"physical_pos", "a1_count", "a2_count"}
    if not needed.issubset(set(rd.fieldnames or [])):
        raise ValueError("POUTINE result lacks required columns")
    out = []
    for row in rd:
        count = int(float(row["a1_count"])) + int(float(row["a2_count"]))
        if count >= 2:
            out.append({
                "position": str(int(float(row["physical_pos"]))),
                "reported_recurrence_count_if_available": str(count),
            })
    return out


def parse_snppar_mutation_events(
    text: str,
    output_tree_newick: str,
    *,
    scenario_id: str,
) -> list[dict[str, str]]:
    rd = csv.DictReader(io.StringIO(text), delimiter="\t")
    required = {"Position", "Ancestor_Node", "Derived_Node", "Ancestor_Call", "Derived_Call"}
    if not required.issubset(set(rd.fieldnames or [])):
        raise ValueError("SNPPar mutation table lacks required columns")
    edge_map = canonical_edge_ids_by_node(output_tree_newick)
    out = []
    for row in rd:
        child = row["Derived_Node"]
        if child not in edge_map:
            raise ValueError(f"SNPPar derived node not found in tree: {child}")
        a, d = row["Ancestor_Call"].upper(), row["Derived_Call"].upper()
        if a in DNA and d in DNA and a != d:
            out.append({
                "scenario_id": scenario_id,
                "method": "SNPPar",
                "edge_id": edge_map[child],
                "position": str(int(float(row["Position"]))),
                "ancestral_state": a,
                "derived_state": d,
            })
    return out


def parse_paml_rst_sequences(text: str) -> dict[str, str]:
    # PAML rst contains a "List of extant and reconstructed sequences" block.
    marker = "List of extant and reconstructed sequences"
    if marker not in text:
        raise ValueError("PAML rst lacks reconstructed-sequence block")
    block = text.split(marker, 1)[1]
    stop_markers = [
        "Prob of best state at each node, listed by site",
        "Posterior probabilities",
        "Overall accuracy",
    ]
    for marker2 in stop_markers:
        if marker2 in block:
            block = block.split(marker2, 1)[0]

    out = {}
    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"(?:(node\s*#\s*\d+)|([A-Za-z0-9_.:-]+))\s+([ACGTUN?\s]+)$", line, re.I)
        if not m:
            continue
        label = m.group(1) or m.group(2)
        label = re.sub(r"\s+", "", label)
        if label.lower().startswith("node#"):
            label = "node#" + label.split("#", 1)[1]
        seq = re.sub(r"\s+", "", m.group(3)).replace("U", "T").replace("?", "N").upper()
        if seq and set(seq) <= set("ACGTN"):
            out[label] = seq
    if not out:
        raise ValueError("no PAML sequences parsed")
    return out


def paml_node_sequences_for_tree(
    rst_text: str,
    benchmark_newick: str,
) -> dict[str, str]:
    sequences = parse_paml_rst_sequences(rst_text)

    branch_re = re.compile(
        r"^Branch\s+\d+:\s+(\d+)\.\.(\d+)(?:\s+\(([^)]+)\))?\s*$",
        re.M,
    )
    branches = branch_re.findall(rst_text)
    if not branches:
        raise ValueError("PAML rst lacks explicit branch graph")

    children: dict[str, list[str]] = {}
    parent_of: dict[str, str] = {}
    tip_name: dict[str, str] = {}
    nodes: set[str] = set()

    for parent, child, annotated_tip in branches:
        nodes.update((parent, child))
        if child in parent_of and parent_of[child] != parent:
            raise ValueError("PAML branch graph gives a node multiple parents")
        parent_of[child] = parent
        children.setdefault(parent, []).append(child)

        if annotated_tip:
            annotated_tip = annotated_tip.strip()
            if child in tip_name and tip_name[child] != annotated_tip:
                raise ValueError("PAML tip annotation conflicts")
            tip_name[child] = annotated_tip

    roots = sorted(nodes - set(parent_of))
    if len(roots) != 1:
        raise ValueError("PAML branch graph does not have exactly one root")
    root = roots[0]

    visiting: set[str] = set()
    visited: set[str] = set()
    paml_desc: dict[str, tuple[str, ...]] = {}

    def descend(node: str) -> tuple[str, ...]:
        if node in visiting:
            raise ValueError("PAML branch graph contains a cycle")
        if node in visited:
            return paml_desc[node]

        visiting.add(node)
        kids = children.get(node, [])
        if kids:
            if node in tip_name:
                raise ValueError("PAML internal node has a tip annotation")
            tips = tuple(sorted(x for child in kids for x in descend(child)))
        else:
            if node not in tip_name:
                raise ValueError("PAML terminal node lacks a tip annotation")
            tips = (tip_name[node],)

        visiting.remove(node)
        visited.add(node)
        paml_desc[node] = tips
        return tips

    descend(root)
    if visited != nodes:
        raise ValueError("PAML branch graph is disconnected")

    benchmark_desc = node_descendant_tips(benchmark_newick)
    by_desc: dict[tuple[str, ...], str] = {}
    for label, tips in benchmark_desc.items():
        if tips in by_desc:
            raise ValueError("benchmark tree has ambiguous descendant-tip sets")
        by_desc[tips] = label

    if paml_desc[root] not in by_desc:
        raise ValueError("PAML and benchmark trees contain different tip sets")

    mapped: dict[str, str] = {}
    for node, tips in paml_desc.items():
        if tips not in by_desc:
            raise ValueError("PAML node has no matching benchmark node")
        mapped[node] = by_desc[tips]

    if len(set(mapped.values())) != len(mapped):
        raise ValueError("PAML node mapping is not one-to-one")
    if set(mapped.values()) != set(benchmark_desc):
        raise ValueError("PAML node mapping does not cover the benchmark tree")

    out: dict[str, str] = {}
    for node, benchmark_label in mapped.items():
        source_label = tip_name[node] if node in tip_name else f"node#{node}"
        if source_label not in sequences:
            raise ValueError(f"PAML reconstructed sequence missing for node {node}")
        out[benchmark_label] = sequences[source_label]

    return out


def fastml_node_sequences_for_tree(
    joint_fasta_text: str,
    fastml_newick: str,
    benchmark_newick: str,
) -> dict[str, str]:
    sequences: dict[str, str] = {}
    current: str | None = None
    parts: list[str] = []

    def store() -> None:
        if current is None:
            return
        seq = "".join(parts).upper()
        if not seq or not set(seq) <= set("ACGTN"):
            raise ValueError(f"invalid FastML reconstructed sequence for node {current}")
        sequences[current] = seq

    for raw in joint_fasta_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            store()
            label = line[1:].split()[0]
            if not label:
                raise ValueError("empty FastML FASTA identifier")
            if label in sequences:
                raise ValueError(f"duplicate FastML FASTA identifier: {label}")
            current = label
            parts = []
        else:
            if current is None:
                raise ValueError("FastML FASTA sequence before header")
            parts.append(line)
    store()

    if not sequences:
        raise ValueError("no FastML reconstructed sequences parsed")

    fastml_desc = node_descendant_tips(fastml_newick)
    benchmark_desc = node_descendant_tips(benchmark_newick)

    def by_desc(
        desc: dict[str, tuple[str, ...]],
        tree_name: str,
    ) -> dict[tuple[str, ...], str]:
        out: dict[tuple[str, ...], str] = {}
        for label, tips in desc.items():
            if tips in out:
                raise ValueError(
                    f"{tree_name} tree has ambiguous descendant-tip sets"
                )
            out[tips] = label
        return out

    fastml_by_desc = by_desc(fastml_desc, "FastML")
    benchmark_by_desc = by_desc(benchmark_desc, "benchmark")

    fastml_tips = max(fastml_by_desc, key=len)
    benchmark_tips = max(benchmark_by_desc, key=len)
    if fastml_tips != benchmark_tips:
        raise ValueError("FastML and benchmark trees contain different tip sets")

    mapped: dict[str, str] = {}
    for tips, fastml_label in fastml_by_desc.items():
        if tips not in benchmark_by_desc:
            raise ValueError("FastML node has no matching benchmark node")
        mapped[fastml_label] = benchmark_by_desc[tips]

    if len(set(mapped.values())) != len(mapped):
        raise ValueError("FastML node mapping is not one-to-one")
    if set(mapped.values()) != set(benchmark_desc):
        raise ValueError("FastML node mapping does not cover the benchmark tree")

    out: dict[str, str] = {}
    for fastml_label, benchmark_label in mapped.items():
        if fastml_label not in sequences:
            raise ValueError(
                f"missing reconstructed sequence for FastML node {fastml_label}"
            )
        out[benchmark_label] = sequences[fastml_label]

    return out


def arpip_node_sequences_for_tree(
    ancestral_fasta_text: str,
    arpip_newick: str,
    benchmark_newick: str,
    observed_tip_sequences: dict[str, str],
) -> dict[str, str]:
    reconstructed: dict[str, str] = {}
    current: str | None = None
    parts: list[str] = []

    def store() -> None:
        if current is None:
            return
        seq = "".join(parts).upper()
        if not seq or not set(seq) <= set("ACGTN"):
            raise ValueError(
                f"invalid ARPIP reconstructed sequence for node {current}"
            )
        if current in reconstructed:
            raise ValueError(
                f"duplicate ARPIP FASTA identifier: {current}"
            )
        reconstructed[current] = seq

    for raw in ancestral_fasta_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            store()
            current = line[1:].split()[0]
            if not current:
                raise ValueError("empty ARPIP FASTA identifier")
            parts = []
        else:
            if current is None:
                raise ValueError("ARPIP FASTA sequence before header")
            parts.append(line)
    store()

    if not reconstructed:
        raise ValueError("no ARPIP reconstructed sequences parsed")

    arpip_desc = node_descendant_tips(arpip_newick)
    benchmark_desc = node_descendant_tips(benchmark_newick)

    def by_desc(
        desc: dict[str, tuple[str, ...]],
        tree_name: str,
    ) -> dict[tuple[str, ...], str]:
        out: dict[tuple[str, ...], str] = {}
        for label, tips in desc.items():
            if tips in out:
                raise ValueError(
                    f"{tree_name} tree has ambiguous descendant-tip sets"
                )
            out[tips] = label
        return out

    arpip_by_desc = by_desc(arpip_desc, "ARPIP")
    benchmark_by_desc = by_desc(benchmark_desc, "benchmark")

    arpip_tips = max(arpip_by_desc, key=len)
    benchmark_tips = max(benchmark_by_desc, key=len)
    if arpip_tips != benchmark_tips:
        raise ValueError("ARPIP and benchmark trees contain different tip sets")

    if set(observed_tip_sequences) != set(arpip_tips):
        raise ValueError("observed tip sequences do not match ARPIP tree tips")

    sequences = dict(reconstructed)
    for tip in arpip_tips:
        if tip in sequences:
            raise ValueError(
                f"ARPIP ancestral FASTA unexpectedly contains tip {tip}"
            )
        seq = observed_tip_sequences[tip].upper()
        if not seq or not set(seq) <= set("ACGTN"):
            raise ValueError(f"invalid observed sequence for tip {tip}")
        sequences[tip] = seq

    mapped: dict[str, str] = {}
    for tips, arpip_label in arpip_by_desc.items():
        if tips not in benchmark_by_desc:
            raise ValueError("ARPIP node has no matching benchmark node")
        mapped[arpip_label] = benchmark_by_desc[tips]

    if len(set(mapped.values())) != len(mapped):
        raise ValueError("ARPIP node mapping is not one-to-one")
    if set(mapped.values()) != set(benchmark_desc):
        raise ValueError("ARPIP node mapping does not cover the benchmark tree")

    out: dict[str, str] = {}
    for arpip_label, benchmark_label in mapped.items():
        if arpip_label not in sequences:
            raise ValueError(
                f"missing reconstructed sequence for ARPIP node {arpip_label}"
            )
        out[benchmark_label] = sequences[arpip_label]

    return out


def parse_tabular_node_states(
    text: str,
    site_columns: Iterable[int],
) -> dict[str, str]:
    """Parse generic tabular node-state output (used by PastML wrapper contract).

    First column is node id; columns are named site_<1-based-position>.
    PastML may represent uncertainty using multiple rows for the same node.
    A node-site combination is retained only when exactly one distinct A/C/G/T
    state is reported; absent or multi-state calls are encoded as N.
    """
    site_columns = list(site_columns)
    rd = csv.DictReader(io.StringIO(text), delimiter="\t")
    if not rd.fieldnames:
        raise ValueError("empty state table")
    node_field = rd.fieldnames[0]
    needed = [f"site_{p}" for p in site_columns]
    if not set(needed).issubset(rd.fieldnames):
        raise ValueError("state table missing site columns")

    states_by_node: dict[str, dict[str, set[str]]] = {}

    for row in rd:
        node = (row.get(node_field) or "").strip()
        if not node:
            raise ValueError("state table row lacks node id")

        per_site = states_by_node.setdefault(
            node,
            {column: set() for column in needed},
        )

        for column in needed:
            state = (row.get(column) or "").strip().upper()
            if state in DNA:
                per_site[column].add(state)

    out = {}
    for node, per_site in states_by_node.items():
        out[node] = "".join(
            sorted(per_site[column])[0]
            if len(per_site[column]) == 1
            else "N"
            for column in needed
        )

    return out
