#!/usr/bin/env python3
"""Check the Experiment 06/07 manuscript evidence without third-party dependencies."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,tarfile
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent
S=ROOT/'results/07_comparative_landscape/accuracy_benchmark_v1'
EXPECTED_SHA='cf9ef552a8849343a288f65a8dc07c2e6a359ec2e8b538f08ab6febe129075af'
BRANCH={'ARPIP','BRANCHSNV','FastML','PAML','PastML','SNPPar','TreeTime'}
REC={'HomoplasyFinder','POUTINE','SNPPar','TreeTime'}

def require(cond,msg):
    if not cond:raise AssertionError(msg)

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def read_tsv(p):
    with p.open(newline='',encoding='utf-8') as h:return list(csv.DictReader(h,delimiter='\t'))

def counts(row):return tuple(int(row[k]) for k in ('TP','FP','FN'))

def metrics(row):
    tp,fp,fn=counts(row)
    prec=tp/(tp+fp) if tp+fp else None
    rec=tp/(tp+fn) if tp+fn else None
    f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None
    return prec,rec,f1

def check_metric(row):
    a=metrics(row)
    for k,v in zip(('precision','recall','F1'),a):
        require(v is not None,f'undefined {k} pooled: {row}')
        require(math.isclose(float(row[k]),v,abs_tol=1e-12),f'{k} error: {row}')

def check_sha_manifest(path,base):
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith('#'):continue
        expected,rel=line.split(maxsplit=1)
        rel=rel.removeprefix('*')
        dest=(base/rel).resolve()
        require(dest.is_relative_to(base.resolve()),f'unsafe manifest path: {rel}')
        require(dest.is_file(),f'missing: {rel}')
        require(digest(dest)==expected,f'checksum mismatch: {dest}')

def verify():
    check_sha_manifest(ROOT/'publication_evidence.sha256',ROOT)
    assert digest(S/'BRANCHSNV_Experiment07_FINAL_RESULTS.tar.gz')==EXPECTED_SHA
    # Both extracted results and the frozen external archive have their own SHA256 manifest.
    check_sha_manifest(S/'SHA256SUMS',S)
    with tarfile.open(S/'BRANCHSNV_Experiment07_FINAL_RESULTS.tar.gz','r:gz') as a:
        names={m.name for m in a.getmembers() if m.isfile()}
        for name in ['SHA256SUMS','combined_branch_event_accuracy.tsv',
                     'combined_recurrent_site_accuracy.tsv','per_scenario_scores.tsv',
                     'provenance.json','aggregate_scores.tsv',
                     'frozen_primary_3_method_comparative_aggregate_scores.tsv']:
            rel='independent_scoring_extension_v1/'+name
            require(rel in names,f'archive member absent: {rel}')
            require(a.extractfile(rel).read()==(S/name).read_bytes(),f'archive/extract mismatch: {name}')
    prov=json.loads((S/'provenance.json').read_text())
    scorer=ROOT/'experiments/07_comparative_landscape/accuracy_benchmark_v1/exp07_score_archived.py'
    require(digest(scorer)==prov['source_score_script_sha256'],'original independent scorer hash mismatch')
    require(int(prov['new_comparator_executions'])==900,'new run-count mismatch')
    require(prov['truth_read_stage']=='after_all_900_predictions_finalized','truth-stage invalid')

    b=read_tsv(S/'combined_branch_event_accuracy.tsv')
    r=read_tsv(S/'combined_recurrent_site_accuracy.tsv')
    require({x['method'] for x in b}==BRANCH and len(b)==7,'branch methods incomplete')
    require({x['method'] for x in r}==REC and len(r)==4,'recurrent methods incomplete')
    for row in b+r:
        require(int(row['scenarios'])==150,'incomplete scenario total')
        check_metric(row)
        require(int(row['TP'])+int(row['FN']) in (9600,2700),'unexpected truth total')
    require(all(int(x['TP'])+int(x['FN'])==9600 for x in b),'branch truth mismatch')
    require(all(int(x['TP'])+int(x['FN'])==2700 for x in r),'recurrence truth mismatch')

    p=read_tsv(S/'per_scenario_scores.tsv')
    required={
        ('ARPIP','exact_latent_branch_event'),('PAML','exact_latent_branch_event'),
        ('PastML','exact_latent_branch_event'),('SNPPar','exact_latent_branch_event'),
        ('HomoplasyFinder','recurrent_site_full'),('POUTINE','recurrent_site_full'),
        ('POUTINE','recurrent_site_observed_biallelic_only'),
        ('SNPPar','recurrent_site_full'),('TreeTime','recurrent_site_full')}
    keys=Counter((x['method'],x['endpoint']) for x in p)
    require(set(keys)==required and set(keys.values())=={150},'new per-scenario coverage mismatch')
    require(len(p)==1350 and len({(x['method'],x['endpoint'],x['scenario_id']) for x in p})==1350,
            'duplicate/missing per-scenario rows')
    for key in required:
        rows=[x for x in p if (x['method'],x['endpoint'])==key]
        require({x['scenario_id'] for x in rows}=={f'S{i:03d}' for i in range(1,151)},'scenario ID mismatch')
        for x in rows:require(all(int(x[k])>=0 for k in ('TP','FP','FN')),'negative counts')
        totals=[sum(int(x[k]) for x in rows) for k in ('TP','FP','FN')]
        matched=next((x for x in b+r if (x['method'],x['endpoint'])==key),None)
        if matched:require(tuple(totals)==counts(matched),f'pooled vs source mismatch: {key}')
    frozen=read_tsv(S/'frozen_primary_3_method_comparative_aggregate_scores.tsv')
    for m in ('BRANCHSNV','FastML','TreeTime'):
        z=[x for x in frozen if x['scope']=='overall' and x['method']==m]
        require(len(z)==1,f'frozen overall absent: {m}')
        result=next(x for x in b if x['method']==m)
        require(counts(z[0])==counts(result),f'frozen vs combined mismatch: {m}')

    # Experiment 06 exactly checks supplied user-facing manuscript claim.
    d=ROOT/'results/06_empirical_cross_classification'
    summary=json.loads((d/'summary.json').read_text())['analysis']['totals']
    wanted={'taxa':912,'variable_sites':31457,'eligible_non_root_adjacent_branches':1804,
            'branch_site_comparisons':16073690,'informative':31644,'outside_intersection':827}
    for k,v in wanted.items():require(summary[k]==v,f'Experiment 06 manuscript number {k} invalid')
    ds=read_tsv(d/'dataset_summary.tsv')
    require(len(ds)==5,'Experiment 06 dataset count')
    for k,col in [('taxa','taxa'),('variable_sites','variable_sites'),
                   ('eligible_non_root_adjacent_branches','eligible_non_root_adjacent_branches'),
                   ('branch_site_comparisons','branch_site_comparisons')]:
        require(sum(int(x[col]) for x in ds)==wanted[k],f'Experiment 06 tables vs summary: {k}')
    qc=json.loads((d/'summary.json').read_text())['production_qc']
    require(qc['exact_records']==1617 and qc['discrepancies']==0,'production QC mismatch')

    # Require a visible scientific warning and no false 100% F1 in truth-negative unique-only regime.
    src=(ROOT/'manuscript/comparator_accuracy/plot_final_figures.py').read_text()
    require('F1 undefined' in src and 'unique_only' in src and "'reversal'" in src,'regime caveat missing in figure generator')
    print('PUBLICATION_EVIDENCE=PASS')
    print('EXPERIMENT06: 5 phylogenies; 912 genomes; 31,457 variable sites; 1,804 edges; 16,073,690 branch-sites')
    print('EXPERIMENT07: 7 branch-event methods × 150 scenarios; 4 recurrent-site methods × 150 scenarios')
    print('NEW_EXECUTIONS=900 ORIGINAL_EXTERNAL_EXECUTIONS=300 BRANCHSNV_SCENARIOS=150')
    print('HASHED_SCORE_SCRIPT=PASS FIGURE_SOURCE_MANIFEST=PASS')
    print('BOUNDARY=published scoring and plotting audit, NOT fresh native re-execution')

if __name__=='__main__':verify()
