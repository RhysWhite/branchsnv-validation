#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import csv, hashlib, json, subprocess
EXPECTED_PARENT='3f1f6c6210561661d6deae8153261f2d62be0f1c'
RESULT_DIR=Path("results/07_comparative_landscape/comparative_landscape_v1")
CONTROL_DIR=Path("experiments/07_comparative_landscape")
DESIGN=CONTROL_DIR/"comparative_landscape_v1_results_design.json"
CLOSURE=CONTROL_DIR/"comparative_landscape_v1_results.sha256"
RESULT_CHECKSUMS=RESULT_DIR/"checksums.sha256"
EXPECTED_REVIEW_HASHES={'priority_001': ('df28e43ae4e4258522f730e8cbb32fe21a115555566c4f8e972d0548e757a643', 'db041138598249780ce68fbe6cb3834117be0cd170b6ba04c1602a0edb8289a7'), 'priority_002': ('97d3b262446a7c2cf4bdfba4fa2932810b29f3c15cf3ad52cd47d0e34cf2607e', '92860f43d07596c3d0ad76fd2dc0daca4b168895070f51bb83ce3e5e33670011'), 'priority_003': ('dcd294dd16e1e2b68108704f18b4fdd8003108becaf507acdc6fbce1337a91c6', 'dd46c87cdd4ab01e5e141bceff9c3f908930af4502d126e87d566cdb2eca068f'), 'priority_004': ('931ce59c2266b333faf28fad92a843c47e368269ae247fb4ef6941dac82125b4', 'eaddda380661af6ce810a1521b43b7834d407dd7e8242752e471efa797045aa3'), 'priority_005': ('fd74ad6194ab55eb6aef2faeac3881e29789640d923fab4dba2db94d27bf1832', '22e205294e2184e9545f2d220ff0ee61e4d52aeea9e10538723ed07c021f493a'), 'priority_006': ('dc880a8672feb6caeb9f5309fccf9d832d0fd06f7f5d8bf65567aebae7fdddcb', 'f09ae88d942f75b5aabd1eaa3dc258068d2b8f0284dbe9650dcb489c7d5276cb'), 'priority_007': ('9a8b3579ccc4fae0a6ace0f794d3160e4af7b80273a64a5fc0cb505c531d08ed', '7f9e9823e1a30bc5ad183fc31a616586e24bcb2aaf4855f8cf1815b112d03a5b'), 'priority_008': ('706bf13da15026888a4021b3e6db993163c3f7ad577408337ac16d6a8c604c06', '6839f9f55a007d4cd0ad8cddeda219df96180911985e65e209275e861d790202'), 'priority_009': ('ea8fbfcc2270f815c061b21864b0c30ad8058bd03c29a012693ad113029b612b', 'f527d08c9c798aec010b21a9f19caca5020ab204411b28f4f3d6b14103544b1d'), 'priority_010': ('b0e7f09e41584d76a48be28e6ce59d56d35dbe1d041718ba21ae72b4cd43b0c0', '49d79b111a496fe2caf3c1336de090c4246ddb9a4643bc7cfc587136f537bae8'), 'priority_011': ('ce1e36ba970ab62fa231da7ff3da5b87e8e78ef8a30ccc30ffe3ee5b3e8af1ca', 'd2b53ae5286622fe3a1de7bb1260a2677b52fb052094078c4de5da89149b284c'), 'residual_001': ('e03491feb95dcc71f7ec6da32a125e4ae5a3f45caa005368ab00dfe7b8fcacb8', 'f9b9f185a468a601dddc6d3d81ca974194d05e2d623a6986b3eab9463ee75c31'), 'residual_002': ('06b1502d4f22a9f5618b695e94648f27c782a3f6fb29192243cd80c534fd1ff4', '09bb4ba5e61468c8e2c4b485a1f83ead361c27d8877feb3b938c5d7f2be71858'), 'residual_003': ('8c49c084cffb597f79f9922eafe7306c6af9eb41474bede0596dc35ca37cbc01', 'fd5a04dc37d5f76ba6f718b77e6ed985a689e939fbb4b040be3564fdb5fc26e8'), 'residual_004': ('e89d935a9f5c239aff64c9099c5e7c515ac188574d54435d7e49b7f4b61cd25e', '5910d1c1601eb2c807a8ed15b92d35dce3723c55450d4ebe86519af4b1aebbba'), 'residual_005': ('6bdd932ed5762ed0546fb99b5f11d65d41a15edbe831ad8b0bbf729531a563a3', '85245c9ac67ce49b50f8c5031b4bf0ae92dc3107a376118a7c0283b7cd4208ef'), 'residual_006': ('9fd3fa1d47e9cf33b641a513fa2faedaf9d0df1292de3c868713748200551777', '89a4f4e9bf10acd2d00c0ccf01698a9ae456e17db7c3367eea01e618233a37a1'), 'residual_007': ('dc59ef9011e48376758ec36bb62db4c5bc05e2bded65ae95a5dd2d0e1ece2feb', '56e097e4ae2388aace8df2178377c188a7b15fe7b5b4d62ed61c657f9c070866'), 'residual_008': ('4e4ea33f00fb79b4e62f6d0310357e2526f46c3eab978cc2db5a742b03fe4c64', '91e0e613aa2a57b4ce1e20b25d8fa138d45bd1891ee39c959837c0560a2d97ad'), 'residual_009': ('f308f158a99d39ae696d42cf7fac4fdd754ed37a3dd8432d0fdd42c7ee4ba471', '4cd32e01446b9bd0ea434b2e3fcd819c11f556634faa9ca89534bf214386b114'), 'residual_010': ('1d89cc9c956cff9011822320acd9d3d5a58908807034b42580d83543d8304b49', '930d9001ed3f755a75fa9aabc21996d3829f1699b83cf613948586a2d3e8cff3'), 'residual_011': ('1cfef04a0e068dd3934b17d62cc3a3b3df941a2d1a4ce08b49f0b182d352633a', 'f9496f014d73b6d2fcc0136b7b9af90340b9ac1ff98b5602a3770b914155a79b'), 'residual_012': ('2b1299119526794d414605ca65c637c76bdc683e5c0ab6cab8f5b5511fd464f6', 'df07c406bb4faf4985f37f9b31f72230a5dc74c7d539ad222f684ad797450e35'), 'residual_013': ('d89586090261899559a46bc8bfd5eab7228d4b88670c0abf13dfdd713bb26202', 'f393a00a3298f3bfb32ca3b19c15de90035d85ff82f9cbd960eb53817657d849'), 'manual_001': ('0dbd3c04ac5ed20350e6e5a695d40fc06167940449d2f58e562742343fe00a01', 'dcb343a4028b9d2add38084ed9e26aa93310b852da2b50fed40edfc7696c2b25')}
DIRECT={"SubRecon","SNPPar","TreeTime"}
NEAR_ANCHORS={"PAML","PastML","FastML"}
ALL_ANCHORS=DIRECT|NEAR_ANCHORS
ALLOWED_ROLES={"clade_lineage_marker_discovery","branch_change_reconstruction","homoplasy_recurrent_state_analysis","marker_deployment_genotyping","general_phylogenetic_parsimony_infrastructure","upstream_variant_recombination_phylogeny_workflows"}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open("r",encoding="utf-8",newline="") as h: return list(csv.DictReader(h,delimiter="\t"))
def checks(p):
    out={}
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d,q=line.split("  ",1); out[q]=d
    return out
def verify_checks(p):
    for q,d in checks(p).items():
        x=Path(q)
        if not x.is_file(): raise SystemExit(f"FAIL | checksum target absent: {q}")
        if sha(x)!=d: raise SystemExit(f"FAIL | checksum mismatch: {q}")
def names(data): return {r["canonical_name"] for r in data}
head=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
anc=subprocess.run(["git","merge-base","--is-ancestor",EXPECTED_PARENT,head],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
if head!=EXPECTED_PARENT and not anc: raise SystemExit("FAIL | repository does not descend from freeze parent")
verify_checks(CLOSURE); verify_checks(RESULT_CHECKSUMS)
d=json.loads(DESIGN.read_text(encoding="utf-8"))
if d["freeze_id"]!="COMPARATIVE_LANDSCAPE_V1_RESULTS" or d["status"]!="FROZEN_COMPARATIVE_LANDSCAPE_V1_RESULTS": raise SystemExit("FAIL | freeze identity/status")
if d["next_gate"]!="FREEZE_COMPARATOR_BENCHMARK_FEASIBILITY_DESIGN_BEFORE_EXECUTION": raise SystemExit("FAIL | next gate")
if any(d["authority"].values()): raise SystemExit("FAIL | authority boundary")
recorded={k:(v["reviewed"],v["approval"]) for k,v in d["review_prerequisites"]["review_packet_and_approval_sha256"].items()}
if recorded!=EXPECTED_REVIEW_HASHES or d["review_prerequisites"]["active_review_packets"]!=25 or d["review_prerequisites"]["active_review_rows"]!=12156: raise SystemExit("FAIL | review prerequisite evidence")
reviews=rows(RESULT_DIR/"branchsnv_approved_review_decisions_v1.tsv")
if len(reviews)!=12156 or len({r["screening_entity_id"] for r in reviews})!=12156: raise SystemExit("FAIL | approved review decision ledger identity/count")
if {r["packet_id"] for r in reviews} != ({f"priority_{i:03d}" for i in range(1,12)} | {f"residual_{i:03d}" for i in range(1,14)} | {"manual_001"}): raise SystemExit("FAIL | approved review packet set")
if sum(r["proposed_record_decision"]=="retain_for_method_assessment" for r in reviews)!=5120 or sum(r["proposed_record_decision"]=="exclude" for r in reviews)!=7036: raise SystemExit("FAIL | approved review decision counts")
if any(r["evidence_escalation_status"] for r in reviews): raise SystemExit("FAIL | unexpected source escalation")
if any(r["approval_status"]!="SCIENTIFIC_REVIEW_PACKET_APPROVED_PRE_PRODUCTION" for r in reviews): raise SystemExit("FAIL | review approval status")
for r in reviews:
    if not r["evidence_source_locator"]: raise SystemExit("FAIL | approved decision missing evidence locator")
    if r["proposed_record_decision"]=="retain_for_method_assessment" and r["proposed_candidate_method_flag"]!="true": raise SystemExit("FAIL | retained candidate flag")
    if r["proposed_record_decision"]=="exclude" and r["proposed_candidate_method_flag"]!="false": raise SystemExit("FAIL | excluded candidate flag")
master=rows(RESULT_DIR/"branchsnv_all_lanes_method_identity_master_v1.tsv")
land=rows(RESULT_DIR/"branchsnv_comparative_landscape_v1.tsv")
dn=rows(RESULT_DIR/"branchsnv_direct_near_comparators_v1.tsv")
sup=rows(RESULT_DIR/"branchsnv_supporting_methods_v1.tsv")
non=rows(RESULT_DIR/"branchsnv_noncomparators_v1.tsv")
carry=rows(RESULT_DIR/"branchsnv_prior_anchor_carry_forwards_v1.tsv")
if (len(master),len(land),len(dn),len(sup),len(non),len(carry))!=(247,218,29,189,29,6): raise SystemExit("FAIL | result counts")
if names(carry)!=ALL_ANCHORS: raise SystemExit("FAIL | carry-forward identities")
if {r["canonical_name"]:r["final_comparator_class"] for r in carry} != {"SNPPar":"direct","SubRecon":"direct","TreeTime":"direct","PAML":"near_direct","PastML":"near_direct","FastML":"near_direct"}: raise SystemExit("FAIL | carry-forward classes")
if len(names(master))!=247: raise SystemExit("FAIL | duplicate master identity")
classes={c:sum(r["final_comparator_class"]==c for r in master) for c in ["direct","near_direct","supporting_relevant","not_comparator"]}
if classes!={"direct":3,"near_direct":26,"supporting_relevant":189,"not_comparator":29}: raise SystemExit(f"FAIL | class counts {classes}")
if {r["canonical_name"] for r in master if r["final_comparator_class"]=="direct"}!=DIRECT: raise SystemExit("FAIL | direct set")
if not ALL_ANCHORS<=names(master): raise SystemExit("FAIL | prior anchors absent")
for n in DIRECT:
    r=next(x for x in master if x["canonical_name"]==n)
    if "frozen_prior_anchor_carry_forward" not in r["catalogue_provenance"]: raise SystemExit(f"FAIL | direct anchor provenance {n}")
for n in NEAR_ANCHORS:
    r=next(x for x in master if x["canonical_name"]==n)
    if r["final_comparator_class"]!="near_direct" or "frozen_prior_anchor_carry_forward" not in r["catalogue_provenance"]: raise SystemExit(f"FAIL | near anchor {n}")
if "CODEML" in names(master) or "ProtASR2" in names(master): raise SystemExit("FAIL | unconsolidated identity")
paml=next(r for r in master if r["canonical_name"]=="PAML"); protasr=next(r for r in master if r["canonical_name"]=="ProtASR"); char=next(r for r in master if r["canonical_name"]=="chARNement")
if "CODEML" not in paml["aliases_or_versions"] or "ProtASR2" not in protasr["aliases_or_versions"] or char["final_comparator_class"]!="near_direct": raise SystemExit("FAIL | consolidation/correction")
if names(land)!={r["canonical_name"] for r in master if r["final_comparator_class"] in {"direct","near_direct","supporting_relevant"}}: raise SystemExit("FAIL | landscape projection")
if names(dn)!={r["canonical_name"] for r in master if r["final_comparator_class"] in {"direct","near_direct"}}: raise SystemExit("FAIL | direct-near projection")
if names(sup)!={r["canonical_name"] for r in master if r["final_comparator_class"]=="supporting_relevant"}: raise SystemExit("FAIL | support projection")
if names(non)!={r["canonical_name"] for r in master if r["final_comparator_class"]=="not_comparator"}: raise SystemExit("FAIL | noncomparator projection")
for r in master:
    roles={x for x in r["frozen_role_signals"].split(" | ") if x}
    if not roles<=ALLOWED_ROLES: raise SystemExit(f"FAIL | unknown role: {r['canonical_name']}")
m=json.loads((RESULT_DIR/"branchsnv_comparative_landscape_v1_manifest.json").read_text(encoding="utf-8"))
if m["status"]!="ALL_LANES_COMPARATIVE_LANDSCAPE_V1": raise SystemExit("FAIL | manifest status")
if (m["record_review"]["active_review_rows"],m["record_review"]["retained_records"],m["record_review"]["excluded_records"])!=(12156,5120,7036): raise SystemExit("FAIL | review totals")
if (m["identity_consolidation"]["master_distinct_identities"],m["identity_consolidation"]["included_landscape_identities"])!=(247,218): raise SystemExit("FAIL | identity totals")
if m["interpretation"]["no_new_direct_comparator_found_outside_frozen_prior_anchors"] is not True: raise SystemExit("FAIL | direct interpretation")
if any(m["boundaries"].values()): raise SystemExit("FAIL | result boundary")
print("PASS | comparative landscape v1 result freeze validates")
print("PASS | self-contained approved-decision ledger = 12,156 rows")
print("PASS | 247 distinct method/tool identities")
print("PASS | 218 comparative-landscape identities")
print("PASS | 3 direct / 26 near-direct / 189 supporting / 29 noncomparators")
print("PASS | direct set = SNPPar + SubRecon + TreeTime")
print("PASS | six frozen prior-anchor carry-forwards preserved")
print("PASS | CODEML->PAML and ProtASR2->ProtASR consolidations enforced")
print("PASS | archival validation does not require mutable local review workspace")
print("PASS | no benchmark execution or production-bridge authority granted")
print("PASS | next gate = FREEZE_COMPARATOR_BENCHMARK_FEASIBILITY_DESIGN_BEFORE_EXECUTION")
