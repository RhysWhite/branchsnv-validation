#!/usr/bin/env python3
"""Independently check prespecified v0.2.0 headline counts from retained tables."""
from __future__ import annotations
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def read(rel):
    with (ROOT/rel).open(newline='',encoding='utf-8') as fh:
        return list(csv.DictReader(fh,delimiter='\t'))

def obj(rel): return json.loads((ROOT/rel).read_text())
def require(cond, why):
    if not cond: raise SystemExit('INDEPENDENT_COUNTS_FAIL: '+why)

s=obj('results/01_exact_oracle/summary.json')
statuses=read('results/01_exact_oracle/status_summary.tsv')
require(sum(int(x['comparisons']) for x in statuses)==128881, '01 status denominators')
require(s['total_comparisons']==128881 and s['total_mismatches']==0, '01 total/errors')
require(len(read('results/01_exact_oracle/mismatches.tsv'))==0, '01 mismatch rows')

faults=read('results/02_deliberate_faults/fault_summary.tsv')
require(len(faults)==10 and all(x['detected']=='true' for x in faults), '02 faults')
require(sum(int(x['challenges']) for x in faults)==280216, '02 challenges')

snps=read('results/03_published_datasets/event_comparison.tsv')
require(Counter(x['comparison'] for x in snps)=={
 'exact_unambiguous':877,'snppar_event_is_one_branchsnv_optimum':66},'03 event classes')
amb=read('results/03_published_datasets/placement_ambiguous_snppar_events.tsv')
require(len(amb)==66,'03 ambiguity events')

runs=read('results/04_scalability/raw_runs.tsv')
bench=read('results/04_scalability/benchmark_summary.tsv')
groups=Counter((x['dataset_id'],x['mode']) for x in runs)
require(len(runs)==39 and len(groups)==13 and set(groups.values())=={3},'04 repetitions')
require(len(bench)==13 and all(x['exit_status']=='0' for x in runs),'04 successes')
require(set(groups)=={(x['dataset_id'],x['mode']) for x in bench},'04 dataset/mode pairs')

focal=read('results/05_published_focal_branches/focal_branch_comparison.tsv')
require(len(focal)==46 and Counter(x['dataset'] for x in focal)=={
 'ak3':23,'st97':10,'oxa48':13},'05 focal denominators')
require(all(x['comparison']=='exact' and x['fixed_exclusive']=='1' and
 x['unambiguous_change']=='1' for x in focal),'05 exact calls')

emp=read('results/06_empirical_cross_classification/informative_events.tsv')
primary=[x for x in emp if x['root_adjacent']=='0']
rootadj=[x for x in emp if x['root_adjacent']=='1']
require(len(primary)==31644 and len(rootadj)==740,'06 primary/root counts')
classes=Counter((x['parsimony_status'],x['fixed_exclusive']) for x in primary)
require(classes=={('unambiguous_change','1'):30817,
 ('unambiguous_change','0'):675,('placement_ambiguous','0'):152},'06 class counts')
qc=read('results/06_empirical_cross_classification/production_qc.tsv')
require(len(qc)==8 and sum(int(x['informative_records']) for x in qc)==1617,
 '06 QC count')
require(sum(int(x['discrepant_records']) for x in qc)==0 and
 len(read('results/06_empirical_cross_classification/production_qc_discrepancies.tsv'))==0,
 '06 QC discrepancies')

orient=read('input_equivalence/equivalence_records.tsv')
variants={
 'transposed_tokens','transposed_compact','conventional_compact',
 'conventional_tokens','conventional_no_taxlabels','conventional_reordered'
}
modes={'fixed-exclusive','parsimony','both'}
groups=defaultdict(list)
for x in orient:
    groups[(int(x['case']),x['mode'])].append(x)
require(len(orient)==540 and len(groups)==90,'NEXUS number of runs')
require({case for case,mode in groups}==set(range(1,31)),'NEXUS case numbering')
require({mode for case,mode in groups}==modes,'NEXUS analysis modes')
for k,rows in groups.items():
    require(len(rows)==6 and {x['variant'] for x in rows}==variants,
        f'NEXUS variants {k}')
    require(len({(x['results_sha256'],x['members_sha256'],x['reported_sites']) for x in rows})==1,
        f'NEXUS content mismatch {k}')
require(obj('input_equivalence/audit_summary.json')['mismatches']==0,
 'NEXUS recorded mismatch field')
print('BRANCHSNV_V020_INDEPENDENT_RETAINED_COUNTS_PASS')
print('E01=128881/128881 E02=10/10 E03=877+66 E04=39/39 E05=46/46')
print('E06=31644+740_root_adjacent QC=1617/1617 NEXUS=540/540')
