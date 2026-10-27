#!/usr/bin/env python3
"""Explicitly versioned, truth-blind Experiment 07 remaining-six execution.

Outputs are a *new exploratory extension*, not a modification of frozen v1.
This wrapper reuses historical command/normalization functions without invoking
historical runner-v3's incompatible amendment-identity authorization gate.
Only the six methods previously absent from the canonical execution inventory
are eligible. This new wrapper is separately identifiable and hash-manifested.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import frozen_runner as runner
import comparator_benchmark_execution_v1_impl.adapters as adapters

METHODS = ('ARPIP','HomoplasyFinder','PAML','PastML','POUTINE','SNPPar')
STUDY_ID='EXP07_150_SCENARIO_REMAINING6_EXPLORATORY_EXTENSION_20261026'
ORIGINAL_HEAD='14cc805c068edbf4e0923b7531a96cc1c35556f2'
DEFAULT_ASSETS=Path.home()/'branchsnv-exp07-smoke-assets'
DEFAULT_REPO=Path.home()/'github/branchsnv-exp07-smoke'
DEFAULT_OUT=DEFAULT_ASSETS/'validation/exp07_eight_tool_extension_20261026'


def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as fh:
  for b in iter(lambda:fh.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def dump(path,value):
 path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')

def manifest(path):
 items=[json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
 assert len({(x['method'],x['scenario_id']) for x in items})==len(items)
 for x in items:
  assert x['method'] in METHODS
  assert x['scenario_id'] in {f'S{i:03d}' for i in range(1,151)}
  assert x['status']=='CANDIDATE_NOT_AUTHORIZED'
 return items

def git_checks(repo):
 actual=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
 dirty=subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip()
 assert actual==ORIGINAL_HEAD,(actual,ORIGINAL_HEAD)
 assert not dirty,'Frozen repository has local changes'

def make_observation_stage(job, assets, root):
 """Derive every auxiliary input solely from the comparator-facing alignment.

Projection deliberately uses *observed* variation, never the sealed
simulator variable_positions. That is an explicit new input-adapter choice.
"""
 sid=job['scenario_id']
 base=assets/'canonical_datasets/experiment07_v1'/sid/'comparator_inputs'
 fasta=base/'observed_tips.fasta'; tree=base/'rooted_tree.nwk'
 assert fasta.is_file() and tree.is_file()
 assert sha(fasta)==job['alignment_sha256'],f'{sid}: alignment checksum differs'
 assert sha(tree)==job['rooted_tree_sha256'],f'{sid}: tree checksum differs'
 seqs=adapters.read_fasta(fasta)
 assert len(seqs)==job['tip_count']
 lengths={len(x) for x in seqs.values()}
 assert len(lengths)==1 and next(iter(lengths))==10000
 assert all(set(seq) <=set('ACGTN') for seq in seqs.values())
 n=next(iter(lengths))
 # Includes only polymorphism observable from A/C/G/T at the tips.
 pos=[]; cons=[]
 for i in range(n):
  observed=[seq[i] for seq in seqs.values() if seq[i] in 'ACGT']
  alleles=set(observed)
  if len(alleles)>1: pos.append(i+1)
  cons.append(sorted(alleles)[0] if alleles else 'A')
 stage=root/'comparator_inputs'
 stage.mkdir()
 (stage/'alignment.fasta').write_bytes(fasta.read_bytes())
 (stage/'tree.nwk').write_bytes(tree.read_bytes())
 (stage/'variable_positions.txt').write_text(adapters.positions_text(pos))
 (stage/'reference.gb').write_text(adapters.minimal_genbank_text(''.join(cons),pos))
 return runner.scenario_inputs_from_directory(sid,stage),{'observed_projected_positions':len(pos),'reference':'lexicographically first observed ACGT allele per position; A for entirely missing','variable_site_policy':'at least two observed unmasked ACGT states','fasta_sha256':sha(fasta),'tree_sha256':sha(tree)}

def read_runtime():
 return runner.load_runtime_config(ROOT/'runtime_paths.json')

def run_one(job,repo,assets,out,print_mode=False):
 sid=job['scenario_id']; method=job['method']
 root=out/'runs'/method/sid
 if root.exists():
  p=root/'execution_result.json'
  if p.is_file() and json.loads(p.read_text()).get('status')=='EXECUTION_PASS':
   print('EXISTING_PASS',method,sid)
   return
  raise RuntimeError(f'Output already exists (failure/incomplete not overwritten): {root}')
 root.parent.mkdir(parents=True,exist_ok=True)
 root.mkdir()
 record={'study_id':STUDY_ID,'method':method,'scenario_id':sid,'status':'INITIALIZING','start_utc':datetime.now(timezone.utc).isoformat(),'truth_read':False,'source_runner_sha256':sha(ROOT/'frozen_runner.py'),'source_adapters_sha256':sha(ROOT/'comparator_benchmark_execution_v1_impl/adapters.py'),'original_repo_head':ORIGINAL_HEAD,'job':job}
 try:
  runtime=read_runtime()
  if method not in runtime: raise RuntimeError('Missing method runtime configuration')
  inputs,projection=make_observation_stage(job,assets,root)
  record['observation_projection']=projection
  if not projection['observed_projected_positions'] and method in {'PastML','POUTINE','SNPPar'}:
   raise RuntimeError('No observable variable sites; method requires projected sites; not treated as a zero prediction')
  # ARPIP/Bio++ interprets internal Newick labels as numeric supports.
  # Canonical N0001-style labels therefore must be hidden on this native
  # parser-facing copy. Keep the original rooted tree for normalization.
  plan_inputs = inputs
  if method == 'ARPIP':
   import re
   from dataclasses import replace
   benchmark_tree_text = inputs.tree_newick.read_text()
   arpip_tree_text, n_internal = re.subn(
    r'\)(N[0-9]{4})(?=[:),;])', ')', benchmark_tree_text)
   assert n_internal == job['tip_count'] - 1, (
    'Unexpected internal-node labels', sid, n_internal)
   assert re.findall(r':[^,();]+', benchmark_tree_text) == re.findall(r':[^,();]+', arpip_tree_text), (
    'Branch lengths changed', sid)
   orig_desc = {tuple(tips) for tips in
    adapters.node_descendant_tips(benchmark_tree_text).values()}
   projected_desc = {tuple(tips) for tips in
    adapters.node_descendant_tips(arpip_tree_text).values()}
   assert orig_desc == projected_desc, ('Topology changed', sid)
   arpip_tree_path = root / 'comparator_inputs/arpip_parser_tree.nwk'
   arpip_tree_path.write_text(arpip_tree_text)
   plan_inputs = replace(inputs, tree_newick=arpip_tree_path)
   record['arpip_parser_tree'] = {
    'policy': 'strip nonnumeric internal labels for ARPIP only',
    'original_sha256': sha(inputs.tree_newick),
    'parser_sha256': sha(arpip_tree_path),
    'internal_labels_removed': n_internal,
    'all_descendant_clades_unchanged': True,
    'branch_length_tokens_unchanged': True}
  from comparator_benchmark_execution_v1_impl.generator import scenario_seed
  plan=runner.build_command_plan(method=method,inputs=plan_inputs,runtime_config=runtime,plan_root=root/'execution',scenario_seed=scenario_seed(sid))
  # New, isolated native-output directory already exists by runner contract.
  # POUTINE requires an explicit opt-in to use that directory. Never point it
  # at the frozen outputs and never reuse an existing job directory.
  if method == 'POUTINE':
   from dataclasses import replace
   assert '--out-dir' in plan.argv and '--force-overwrite' not in plan.argv
   assert Path(plan.argv[plan.argv.index('--out-dir')+1]) == plan.native_dir
   assert sorted(x.name for x in plan.native_dir.iterdir()) == ['compiled']
   assert (plan.native_dir/'compiled').is_symlink()
   plan=replace(plan,argv=tuple(plan.argv)+('--force-overwrite',))
   record['poutine_native_dir_policy']='fresh isolated output directory with --force-overwrite; contains compiled runtime symlink only'
  # SNPPar's default intermediate filter removes monophyletic variants prior
  # to TreeTime. A unique-mutation scenario can then pass a zero-column MSA
  # to legacy TreeTime, which crashes rather than returning native events.
  # Use SNPPar's documented *simple* mode consistently in all 150 scenarios.
  # This retains non-singleton monophyletic sites in native ASR, while SNPPar
  # still handles singletons via its own documented native machinery.
  if method == 'SNPPar':
   from dataclasses import replace
   assert '-E' not in plan.argv
   plan=replace(plan,argv=tuple(plan.argv)+('-E','simple'))
   record['snppar_sorting']='simple; same policy for all 150 SNPPar scenarios'
  env=runner.build_subprocess_environment(plan=plan,runtime_config=runtime)
  record.update({'status':'EXECUTING','argv':list(plan.argv),'cwd':str(plan.cwd),'runtime_sha256':{k:sha(Path(v)) for k,v in runtime[method].items() if Path(v).is_file()}})
  dump(root/'execution_result.json',record)
  timeout=float(job['timeout_seconds'])
  outcome=runner.default_executor(plan,env,timeout)
  (root/'stdout.txt').write_text(outcome.stdout)
  (root/'stderr.txt').write_text(outcome.stderr)
  record.update({'exit_code':outcome.returncode,'timed_out':outcome.timed_out})
  if outcome.timed_out: raise RuntimeError('TIMEOUT')
  if outcome.returncode!=0: raise RuntimeError('NONZERO_EXIT')
  predictions=runner.normalize_native_outputs(plan=plan,inputs=inputs)
  assert predictions['method']==method and predictions['scenario_id']==sid
  dump(root/'predictions.json',predictions)
  record.update({'status':'EXECUTION_PASS','predictions_sha256':sha(root/'predictions.json'),'n_branch_events':len(predictions['branch_events']),'n_recurrent_sites':len(predictions['recurrent_sites'])})
  dump(root/'execution_result.json',record)
  print('EXECUTION_PASS',method,sid)
 except Exception as e:
  record.update({'status':'EXECUTION_FAIL','failure':f'{type(e).__name__}: {e}','traceback':traceback.format_exc()})
  dump(root/'execution_result.json',record)
  print('EXECUTION_FAIL',method,sid,type(e).__name__,str(e),file=sys.stderr)
  raise

def preflight(assets,repo,out):
 git_checks(repo)
 jobs=manifest(ROOT/'remaining_900_jobs.jsonl')
 assert len(jobs)==900
 assert {x['method'] for x in jobs}==set(METHODS)
 assert all(len([x for x in jobs if x['method']==m])==150 for m in METHODS)
 runtime=read_runtime()
 print('RUNTIME_METHODS=',','.join(sorted(runtime)))
 for x in jobs[::150]:
  base=assets/'canonical_datasets/experiment07_v1'/x['scenario_id']/'comparator_inputs'
  for k,filename in [('alignment_sha256','observed_tips.fasta'),('rooted_tree_sha256','rooted_tree.nwk')]:
   assert sha(base/filename)==x[k]
 existing=assets/'canonical_comparator_runs/experiment07_v1'
 for method in ('FastML','TreeTime'):
  assert all((existing/method/f'S{i:03d}'/'execution_result.json').is_file() for i in range(1,151))
 for method in METHODS:
  assert all(not (existing/method/f'S{i:03d}').exists() for i in range(1,151))
 print('READ_ONLY_PREFLIGHT=PASS')
 print('PROPOSED_EXTENSION_ROOT=',out)
 print('ORIGINAL_CANONICAL_EXECUTIONS_UNCHANGED=300')
 print('MISSING_JOBS=900')
 print('SIMULATOR_TRUTH_READ=NO')

def audit(out):
 jobs=manifest(ROOT/'remaining_900_jobs.jsonl')
 from collections import Counter
 counts=Counter()
 for job in jobs:
  p=out/'runs'/job['method']/job['scenario_id']/'execution_result.json'
  if not p.is_file():counts['ABSENT']+=1;continue
  v=json.loads(p.read_text())
  status=v.get('status','UNKNOWN')
  if status=='EXECUTION_PASS':
   pred=out/'runs'/job['method']/job['scenario_id']/'predictions.json'
   if not pred.is_file() or sha(pred)!=v['predictions_sha256']:status='DAMAGED_PREDICTIONS'
  counts[status]+=1
 print(json.dumps(dict(sorted(counts.items())),indent=2))
 print('ALL_900_PASS=',counts['EXECUTION_PASS']==900)


def main():
 a=argparse.ArgumentParser()
 a.add_argument('action',choices=('preflight','pilot','worker','audit'))
 a.add_argument('--index',type=int)
 a.add_argument('--assets',type=Path,default=DEFAULT_ASSETS)
 a.add_argument('--repo',type=Path,default=DEFAULT_REPO)
 a.add_argument('--out',type=Path,default=DEFAULT_OUT)
 args=a.parse_args()
 if args.action=='audit': audit(args.out);return
 if args.action=='preflight': preflight(args.assets,args.repo,args.out);return
 jobs=manifest(ROOT/('pilot_12_jobs.jsonl' if args.action=='pilot' else 'remaining_900_jobs.jsonl'))
 if args.index is None:raise SystemExit('--index required (1-indexed)')
 if not 1<=args.index<=len(jobs):raise SystemExit('Job index out of range')
 git_checks(args.repo)
 run_one(jobs[args.index-1],args.repo,args.assets,args.out)
if __name__=='__main__':main()
