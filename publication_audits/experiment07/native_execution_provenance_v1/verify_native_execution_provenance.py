#!/usr/bin/env python3
"""Fail-closed verification of the archived Experiment 07 extension source inventory.

Scope: 900 immutable receipt/hash references, version files, and SNPPar S001
saved-output normalization receipt. Does NOT claim to replay native execution,
rehash 900 original receipt/prediction files, or verify unavailable failed receipt.
"""
from __future__ import annotations
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
METHODS = ('ARPIP','HomoplasyFinder','PAML','POUTINE','PastML','SNPPar')
SCENARIOS = {f'S{i:03d}' for i in range(1,151)}
RUNNERS = {
 '63a5e45a4082a5709e385e57f3af389769bc4520b5e2a4310bb20fb86e964a33': ('runner_early_A.py',11),
 '8e9bbcc9821d7e1ed01966db4c3914d4833b1424664eec7e6d4407b4902b9207': ('runner_early_B.py',1),
 'a1ec5c6899fcad9800fc2fdc07debf50ab0efe4a5d6120194039e362d0e94d29': ('runner_final.py',888),
}
ADAPTERS = {
 '206f891421e9f6b43164f118e20c0fd5ad2a2b7006f16806ee9937e30ee20b9a': ('adapter_early.py',7),
 '155e3e6f10ea558ef155236ae60a884439112c2b06da6c81dd78d43762b5193d': ('adapter_final.py',893),
}
SCORER_SHA = '38de8bd815738a83c0baf4f78fad36ce7b9e6719313108bdbb91c52cbee42cb0'
FAILURE_RECORD_SHA = 'c42a2b1b2269706b8683e77847779cd9ecf4c22245d2aeadb00f0df5bea58a5d'
HEADERS = ['method','scenario_id','runner_sha256','adapter_sha256','execution_receipt_sha256',
           'prediction_sha256','native_exit_code','normalization_recovered',
           'normalization_runner_sha256','normalization_recovery_receipt_sha256']
HEX64 = re.compile(r'^[0-9a-f]{64}$')

def require(value, message):
    if not value:
        raise AssertionError(message)

def digest(path):
    require(path.is_file() and not path.is_symlink(), f'missing/unsafe file: {path}')
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    # Manifest is strict: unexpected files in the sealed subtree are not accepted.
    lines = (HERE/'SHA256SUMS').read_text(encoding='utf-8').splitlines()
    expected = {}
    for line in lines:
        require('  ' in line, f'malformed sha256sum line: {line!r}')
        h, rel = line.split('  ',1)
        require(bool(HEX64.fullmatch(h)), f'invalid digest {h!r}')
        p = Path(rel)
        require(not p.is_absolute() and '..' not in p.parts and len(p.parts)>0, f'unsafe path {rel!r}')
        require(rel not in expected, f'duplicate manifest path: {rel}')
        expected[rel] = h
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*')
              if p.is_file() and p.name != 'SHA256SUMS' and p.name != Path(__file__).name
              and '__pycache__' not in p.parts and not p.name.endswith('.pyc')}
    require(set(expected)==actual, f'manifest coverage mismatch: extra={actual-set(expected)}, missing={set(expected)-actual}')
    for rel, h in expected.items():
        require(digest(HERE/rel)==h, f'checksum changed: {rel}')

    for h,(filename,total) in RUNNERS.items():
        require(digest(HERE/'source_versions'/filename)==h,f'runner source {filename} mismatch')
    for h,(filename,total) in ADAPTERS.items():
        require(digest(HERE/'source_versions'/filename)==h,f'adapter source {filename} mismatch')
    require(digest(REPO/'experiments/07_comparative_landscape/accuracy_benchmark_v1/exp07_score_archived.py') == SCORER_SHA,
            'native collection scorer does not match committed independent scorer')

    with (HERE/'execution_source_matrix.tsv').open('r',encoding='utf-8',newline='') as fh:
        reader=csv.DictReader(fh,delimiter='\t')
        require(reader.fieldnames==HEADERS, 'matrix columns/order changed')
        rows=list(reader)
    require(len(rows)==900, f'expected 900 rows, got {len(rows)}')
    seen=set()
    methods=defaultdict(set)
    runners=Counter()
    adapters=Counter()
    recoveries=[]
    for row in rows:
        method=row['method'];sid=row['scenario_id']
        pair=(method,sid)
        require(method in METHODS and sid in SCENARIOS, f'unexpected pair {pair}')
        require(pair not in seen, f'duplicate pair {pair}')
        seen.add(pair)
        methods[method].add(sid)
        runner=row['runner_sha256'];adapter=row['adapter_sha256']
        require(runner in RUNNERS and adapter in ADAPTERS, f'unknown source digest {pair}')
        require(row['native_exit_code']=='0',f'nonzero native exit {pair}')
        for key in ('execution_receipt_sha256','prediction_sha256'):
            require(bool(HEX64.fullmatch(row[key])), f'invalid unembedded receipt/prediction hash {pair} {key}')
        runners[runner]+=1;adapters[adapter]+=1
        flag=row['normalization_recovered']
        require(flag in ('true','false'), f'bad recovery flag {pair}')
        if flag=='true':
            require(pair==('SNPPar','S001'),'unexpected recovery')
            require(row['normalization_runner_sha256'] in RUNNERS and bool(HEX64.fullmatch(row['normalization_recovery_receipt_sha256'])),
                    'invalid normalization provenance')
            recoveries.append(row)
        else:
            require(row['normalization_runner_sha256']==row['normalization_recovery_receipt_sha256']=='',
                    f'nonrecovery carries recovery metadata {pair}')
    require(set(methods)==set(METHODS) and all(methods[m]==SCENARIOS for m in METHODS),
            'missing scenario or method')
    require(runners==Counter({h:n for h,(_,n) in RUNNERS.items()}),f'runner counts mismatch {runners}')
    require(adapters==Counter({h:n for h,(_,n) in ADAPTERS.items()}),f'adapter counts mismatch {adapters}')
    require(len(recoveries)==1,'expected single documented SNPPar normalization recovery')
    row=recoveries[0]
    require(row['runner_sha256']=='8e9bbcc9821d7e1ed01966db4c3914d4833b1424664eec7e6d4407b4902b9207',
            'historical SNPPar runner mismatch')
    require(row['adapter_sha256']=='155e3e6f10ea558ef155236ae60a884439112c2b06da6c81dd78d43762b5193d',
            'historical SNPPar adapter mismatch')
    rp=HERE/'recovery_receipts/SNPPar_S001_receipt.json'
    rec=json.loads(rp.read_text(encoding='utf-8'))
    require(digest(rp)==row['normalization_recovery_receipt_sha256'], 'recovery receipt not matched to matrix')
    require(rec['kind']=='truth_blind_saved_native_output_normalization_recovery', 'recovery type changed')
    require(rec['native_rerun'] is False and rec['simulator_truth_read'] is False, 'native rerun/truth read not excluded in receipt')
    require(rec['original_source_runner_sha256']==row['runner_sha256'], 'original runner differs')
    require(rec['normalization_runner_sha256']==row['normalization_runner_sha256']==
            'a1ec5c6899fcad9800fc2fdc07debf50ab0efe4a5d6120194039e362d0e94d29',
            'final normalization runner mismatch')
    require(rec['normalized_predictions_sha256']==row['prediction_sha256'],'recovery prediction hash differs')
    require(rec['original_failed_record_sha256']==FAILURE_RECORD_SHA,'unresolved original failure record ID changed')
    stdout_path=HERE/'recovery_receipts/SNPPar_S001_native_stdout.txt'
    require(digest(stdout_path)==rec['native_stdout_sha256'], 'original native stdout mismatch')
    stdout=stdout_path.read_text(encoding='utf-8',errors='replace')
    markers=('Found 0 mutation events that are homoplasic',
             'Writing all calls at homoplasic event positions',
             'homoplasic_events_all_calls.tsv',
             'No output available... writing of file aborted!',
             'Mapping mutation events to NEXUS tree:',
             'Also mapping mutation events to Newick NHX tree:')
    require(all(marker in stdout for marker in markers), 'SNPPar native completion evidence incomplete')
    require('...Terminé' not in stdout, 'historical missing-completion-marker explanation no longer supported')
    print('EXP07_NATIVE_SOURCE_PROVENANCE=PASS')
    print('MAPPED_EXECUTIONS=900; SIX_METHODS=150_EACH; SOURCE_VERSIONS=5')
    print('RUNNER_COUNTS=11,1,888; ADAPTER_COUNTS=7,893')
    print('SNPPar_S001_SAVED_NATIVE_OUTPUT_RECOVERY=PASS')
    print('SCORE_SOURCE_MATCH=PASS; MANIFEST_SHA256=PASS')
    print('BOUNDARY=Archived per-run receipt/prediction bytes, original failed record, native inputs and environments are NOT present')

if __name__=='__main__':
    main()
