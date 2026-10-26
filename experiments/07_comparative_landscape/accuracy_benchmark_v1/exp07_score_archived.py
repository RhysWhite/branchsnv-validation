#!/usr/bin/env python3
"""Independent post-freeze scorer for the 150-scenario eight-external-tool extension.

Only this stage reads sealed_truth. All 900 remaining method predictions must
have completed and be checksummed before any truth file is opened. Scores
are labelled 'conditional on supplied truth-derived branch lengths'.
"""
from pathlib import Path
import argparse,csv,hashlib,json,sys
from collections import defaultdict
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from comparator_benchmark_execution_v1_impl import metrics

ASSETS=Path.home()/'branchsnv-exp07-smoke-assets'
RUNS=ASSETS/'validation/exp07_eight_tool_extension_20261026'
METHODS=('ARPIP','HomoplasyFinder','PAML','PastML','POUTINE','SNPPar')
BRANCH={'ARPIP','PAML','PastML','SNPPar'}
RECURRENT={'HomoplasyFinder','POUTINE','SNPPar'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def aggregate(rows):
 tp=sum(int(r['TP']) for r in rows)
 fp=sum(int(r['FP']) for r in rows)
 fn=sum(int(r['FN']) for r in rows)
 p=tp/(tp+fp) if tp+fp else (1. if tp+fn==0 else 0.)
 r=tp/(tp+fn) if tp+fn else 1.
 f=2*p*r/(p+r) if p+r else 0.
 return dict(TP=tp,FP=fp,FN=fn,precision=p,recall=r,F1=f,scenarios=len(rows))

def load_frozen_primary(stage):
 # Source is the original independent scoring output, never retallied here.
 a=stage/'comparative_aggregate_scores.tsv'
 if not a.exists(): raise RuntimeError('Missing independent BRANCHSNV/FastML/TreeTime comparative aggregates: '+str(a))
 with a.open(newline='') as fh: rows=list(csv.DictReader(fh,delimiter='\t'))
 if not rows:raise RuntimeError('Frozen aggregate file empty')
 print('FROZEN_PRIMARY_COLUMNS=',','.join(rows[0]))
 # Archive the full original scored aggregate verbatim; avoid schema assumptions.
 return a,rows

def main():
 a=argparse.ArgumentParser();a.add_argument('--assets',type=Path,default=ASSETS);a.add_argument('--runs',type=Path,default=RUNS);a.add_argument('--out',type=Path,default=None);args=a.parse_args()
 jobs=[json.loads(x) for x in (ROOT/'remaining_900_jobs.jsonl').read_text().splitlines() if x]
 if len(jobs)!=900:raise RuntimeError('Wrong job count')
 # TRUE SEPARATION: verify ALL predictions first; sealed_truth is not yet accessed.
 verified=[]
 for job in jobs:
  method,sid=job['method'],job['scenario_id'];base=args.runs/'runs'/method/sid
  r=base/'execution_result.json'; p=base/'predictions.json'
  if not r.is_file() or not p.is_file():raise RuntimeError('Absent finalized prediction: '+method+'/'+sid)
  rec=json.loads(r.read_text())
  if rec.get('status')!='EXECUTION_PASS':raise RuntimeError('Failed execution: '+method+'/'+sid)
  if rec.get('predictions_sha256')!=sha(p):raise RuntimeError('Prediction checksum mismatch: '+method+'/'+sid)
  pred=json.loads(p.read_text())
  if pred['method']!=method or pred['scenario_id']!=sid:raise RuntimeError('Prediction identity differs')
  verified.append((job, pred))
 assert len(verified)==900
 # Independently normalize the original 150 TreeTime native outputs to
 # recurrent-site predictions BEFORE opening any simulated truth ledger.
 from comparator_benchmark_execution_v1_impl import adapters
 tt_predictions={}
 for i in range(1,151):
  sid=f'S{i:03d}'
  original=args.assets/'canonical_comparator_runs/experiment07_v1/TreeTime'/sid/'output'
  ancestral=original/'ancestral_sequences.fasta'
  annotated=original/'annotated_tree.nexus'
  benchmark=args.assets/'canonical_datasets/experiment07_v1'/sid/'comparator_inputs/rooted_tree.nwk'
  if not ancestral.is_file() or not annotated.is_file():
   raise RuntimeError('Original TreeTime native ASR output missing for '+sid)
  native_sequences=adapters.read_fasta(ancestral)
  mapped=adapters.map_node_sequences_by_descendant_tips(annotated.read_text(),benchmark.read_text(),native_sequences)
  events=adapters.events_from_node_sequences(benchmark.read_text(),mapped,method='TreeTime',scenario_id=sid)
  recurrent=adapters.treetime_recurrent_sites_from_branch_events(events)
  tt_predictions[sid]=sorted(int(x['position']) for x in recurrent)
 primary=args.assets/'validation/experiment07_branchsnv_independent_accuracy_scoring_v1'
 if not (primary/'SHA256SUMS').is_file():raise RuntimeError('Original BRANCHSNV independent scoring stage absent')
 import subprocess
 subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=primary,check=True,stdout=subprocess.DEVNULL)
 pri,pr_rows=load_frozen_primary(primary)
 output=args.out or args.runs/'independent_scoring_extension_v1'
 if output.exists():raise RuntimeError('Scored output already exists; never overwrite: '+str(output))
 output.mkdir(parents=True)
 data=[];grouped=defaultdict(list)
 # Truth is first opened here: after 900/900 prediction identity verification.
 for job,pred in verified:
  sid,method=job['scenario_id'],job['method']
  truth_path=args.assets/'canonical_datasets/experiment07_v1'/sid/'sealed_truth/truth.json'
  truth=json.loads(truth_path.read_text())
  if truth['scenario_id']!=sid:raise RuntimeError('Truth identity mismatch')
  if method in BRANCH:
   result=metrics.score_branch_events(truth['events'],pred['branch_events'])
   row=dict(method=method,scenario_id=sid,endpoint='exact_latent_branch_event',regime=job['event_regime'],tip_count=job['tip_count'],observation_condition=job['observation_condition'],TP=result['true_positive_count'],FP=result['false_positive_count'],FN=result['false_negative_count'])
   data.append(row);grouped[(method,'exact_latent_branch_event','all')].append(row);grouped[(method,'exact_latent_branch_event',job['event_regime'])].append(row)
  if method in RECURRENT:
   call=[int(x['position']) for x in pred['recurrent_sites']]
   result=metrics.score_homoplasy_sites(truth['recurrent_positions'],call)
   row=dict(method=method,scenario_id=sid,endpoint='recurrent_site_full',regime=job['event_regime'],tip_count=job['tip_count'],observation_condition=job['observation_condition'],TP=result['true_positive_site_count'],FP=result['false_positive_site_count'],FN=result['false_negative_site_count'])
   data.append(row);grouped[(method,'recurrent_site_full','all')].append(row);grouped[(method,'recurrent_site_full',job['event_regime'])].append(row)
 # Score TreeTime's recurrence endpoint separately, using normalized native
 # ancestral outputs from its original 150 successful executions.
 for i in range(1,151):
  sid=f'S{i:03d}'
  tr=json.loads((args.assets/'canonical_datasets/experiment07_v1'/sid/'sealed_truth/truth.json').read_text())
  job=next(j for j in jobs if j['scenario_id']==sid)
  result=metrics.score_homoplasy_sites(tr['recurrent_positions'],tt_predictions[sid])
  row=dict(method='TreeTime',scenario_id=sid,endpoint='recurrent_site_full',regime=job['event_regime'],tip_count=job['tip_count'],observation_condition=job['observation_condition'],TP=result['true_positive_site_count'],FP=result['false_positive_site_count'],FN=result['false_negative_site_count'])
  data.append(row);grouped[('TreeTime','recurrent_site_full','all')].append(row);grouped[('TreeTime','recurrent_site_full',job['event_regime'])].append(row)
 # Add an explicitly labelled POUTINE eligibility analysis rather than silently
 # comparing its biallelic-only predictions to full-site methods.
 # Eligibility is based on observed unmasked tip alleles, not truth.
 for job,pred in verified:
  if job['method']!='POUTINE':continue
  sid=job['scenario_id']
  from comparator_benchmark_execution_v1_impl.adapters import read_fasta
  seqs=read_fasta(args.assets/'canonical_datasets/experiment07_v1'/sid/'comparator_inputs/observed_tips.fasta')
  n=len(next(iter(seqs.values())))
  eligible={i+1 for i in range(n) if len({seq[i] for seq in seqs.values() if seq[i] in 'ACGT'})==2}
  tr=json.loads((args.assets/'canonical_datasets/experiment07_v1'/sid/'sealed_truth/truth.json').read_text())
  observed_pred={int(x['position']) for x in pred['recurrent_sites']}
  result=metrics.score_homoplasy_sites(eligible.intersection(tr['recurrent_positions']),eligible.intersection(observed_pred))
  row=dict(method='POUTINE',scenario_id=sid,endpoint='recurrent_site_observed_biallelic_only',regime=job['event_regime'],tip_count=job['tip_count'],observation_condition=job['observation_condition'],TP=result['true_positive_site_count'],FP=result['false_positive_site_count'],FN=result['false_negative_site_count'])
  data.append(row);grouped[('POUTINE','recurrent_site_observed_biallelic_only','all')].append(row);grouped[('POUTINE','recurrent_site_observed_biallelic_only',job['event_regime'])].append(row)
 with (output/'per_scenario_scores.tsv').open('w',newline='') as fh:
  w=csv.DictWriter(fh,fieldnames=list(data[0]),delimiter='\t');w.writeheader();w.writerows(data)
 agg=[]
 for (m,e,g),records in sorted(grouped.items()):agg.append(dict(method=m,endpoint=e,regime=g,**aggregate(records)))
 with (output/'aggregate_scores.tsv').open('w',newline='') as fh:
  w=csv.DictWriter(fh,fieldnames=list(agg[0]),delimiter='\t');w.writeheader();w.writerows(agg)
 (output/'frozen_primary_3_method_comparative_aggregate_scores.tsv').write_bytes(pri.read_bytes())
 # Join on the one comparable numerical endpoint, using original frozen
 # BRANCHSNV/FastML/TreeTime totals WITHOUT recomputing or editing them.
 primary_overall=[r for r in pr_rows if r.get('scope')=='overall' and r.get('method') in {'BRANCHSNV','FastML','TreeTime'}]
 if len(primary_overall)!=3 or {r['method'] for r in primary_overall}!={'BRANCHSNV','FastML','TreeTime'}:
  raise RuntimeError('Original three-method aggregate lacks exactly three overall rows')
 combined=[]
 for r in primary_overall:
  combined.append(dict(method=r['method'],endpoint='exact_latent_branch_event',scenarios=r['scenarios'],TP=r['TP'],FP=r['FP'],FN=r['FN'],precision=r['pooled_precision'],recall=r['pooled_recall'],F1=r['pooled_F1'],evidence='original_frozen_independent_scoring'))
 for r in agg:
  if r['endpoint']=='exact_latent_branch_event' and r['regime']=='all':
   combined.append({k:r[k] for k in ('method','endpoint','scenarios','TP','FP','FN','precision','recall','F1')}|{'evidence':'new_exploratory_extension_scoring'})
 if len(combined)!=7 or len({r['method'] for r in combined})!=7:
  raise RuntimeError('Expected BRANCHSNV and six branch-event external workflows')
 with (output/'combined_branch_event_accuracy.tsv').open('w',newline='') as fh:
  w=csv.DictWriter(fh,fieldnames=list(combined[0]),delimiter='\t');w.writeheader();w.writerows(sorted(combined,key=lambda r:r['method']))
 # Recurrence is a separate endpoint and is now fully represented by
 # HomoplasyFinder, POUTINE, SNPPar and TreeTime.
 recurrent_overall=[r for r in agg if r['endpoint']=='recurrent_site_full' and r['regime']=='all']
 if {r['method'] for r in recurrent_overall}!={'HomoplasyFinder','POUTINE','SNPPar','TreeTime'}:
  raise RuntimeError('Four-method recurrence endpoint is incomplete')
 with (output/'combined_recurrent_site_accuracy.tsv').open('w',newline='') as fh:
  w=csv.DictWriter(fh,fieldnames=list(recurrent_overall[0]),delimiter='\t');w.writeheader();w.writerows(sorted(recurrent_overall,key=lambda r:r['method']))

 evidence={'study_id':'EXP07_150_SCENARIO_REMAINING6_EXPLORATORY_EXTENSION_20261026','new_comparator_executions':900,'new_scored_predictions':len(data),'original_3_method_results_imported_from':str(pri),'original_3_method_aggregate_sha256':sha(pri),'interpretation':'latent-history recovery conditional on event-derived branch lengths; not independent branch-length validation','truth_read_stage':'after_all_900_predictions_finalized','source_score_script_sha256':sha(Path(__file__))}
 (output/'provenance.json').write_text(json.dumps(evidence,indent=2)+'\n')
 with (output/'SHA256SUMS').open('w') as fh:
  for f in sorted(output.iterdir()):
   if f.name!='SHA256SUMS':fh.write(sha(f)+'  '+f.name+'\n')
 print('NEW_SCORING_COMPLETE=900/900')
 print('FROZEN_ORIGINAL_SCORES_IMPORTED=YES')
 print('OUTPUT=',output)
if __name__=='__main__':main()
