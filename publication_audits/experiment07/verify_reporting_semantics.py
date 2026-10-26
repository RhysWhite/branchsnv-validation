#!/usr/bin/env python3
"""Verify immutable Experiment 07 aggregate scores and reader-facing undefined-metric handling.

No external dependencies. Never modify the sealed original results or scorer.
"""
from __future__ import annotations
import csv
import io
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RESULTS=ROOT/'results/07_comparative_landscape/accuracy_benchmark_v1'
HERE=Path(__file__).resolve().parent
COLUMNS=['method','endpoint','regime','scenarios','TP','FP','FN','precision_pct','recall_pct','F1_pct','status']

def require(ok,why):
    if not ok:raise AssertionError(why)

def read_rows(path):
    with path.open(encoding='utf-8',newline='') as fh:
        return list(csv.DictReader(fh,delimiter='\t'))

def display(numerator,denominator):
    return 'NA' if denominator==0 else f'{100*numerator/denominator:.4f}'

def expected_rows():
    original=read_rows(RESULTS/'aggregate_scores.tsv')
    scenarios=read_rows(RESULTS/'per_scenario_scores.tsv')
    require(len(original)==54,f'expected 54 aggregate rows, got {len(original)}')
    require(len(scenarios)==1350,f'expected 1,350 scenario rows, got {len(scenarios)}')
    groups=defaultdict(list)
    for row in scenarios:
        key=(row['method'],row['endpoint'])
        groups[key,'all'].append(row)
        groups[key,row['regime']].append(row)
    require(len(groups)==54,f'expected 54 scenario groupings, got {len(groups)}')
    keys=set()
    output=[]
    empties=[]
    for row in sorted(original,key=lambda r:(r['method'],r['endpoint'],r['regime'])):
        key=(row['method'],row['endpoint'],row['regime'])
        require(key not in keys,f'duplicate aggregate row {key}')
        keys.add(key)
        members=groups[key[:2],key[2]]
        n=150 if key[2]=='all' else 30
        require(len(members)==n==int(row['scenarios']),f'scenario count mismatch {key}')
        tp,fp,fn=(int(row[k]) for k in ('TP','FP','FN'))
        require(all(v>=0 for v in (tp,fp,fn)),f'negative counts {key}')
        require(tuple(sum(int(r[k]) for r in members) for k in ('TP','FP','FN'))==(tp,fp,fn),
                f'aggregate does not match scenario-level source: {key}')
        pd=tp+fp; rd=tp+fn; fd=2*tp+fp+fn
        if pd:
            require(math.isclose(float(row['precision']),tp/pd,abs_tol=1e-12),f'precision mismatch {key}')
        if rd:
            require(math.isclose(float(row['recall']),tp/rd,abs_tol=1e-12),f'recall mismatch {key}')
        if fd:
            require(math.isclose(float(row['F1']),2*tp/fd,abs_tol=1e-12),f'F1 mismatch {key}')
        else:
            # Original aggregation's documented empty-set convention is 1.0.
            require(float(row['precision'])==float(row['recall'])==float(row['F1'])==1.0,
                    f'unexpected original zero-denominator convention {key}')
            empties.append(key)
        status=('undefined_F1_no_positive_truth_or_predictions' if fd==0
                else 'defined_F1_other_metric_undefined' if pd==0 or rd==0
                else 'defined_F1')
        output.append(dict(method=key[0],endpoint=key[1],regime=key[2],scenarios=n,
                           TP=tp,FP=fp,FN=fn,precision_pct=display(tp,pd),
                           recall_pct=display(tp,rd),F1_pct=display(2*tp,fd),status=status))
    require(len(empties)==5, f'expected 5 original empty truth/prediction aggregate rows, got {len(empties)}')
    require(all(k[2]=='unique_only' and k[1].startswith('recurrent_site_') for k in empties),
            'unexpected zero-denominator regime or endpoint')
    full=[r for r in output if r['endpoint']=='recurrent_site_full' and r['regime']=='reversal']
    require(len(full)==4 and all(r['TP']==0 and r['FN']==600 for r in full),
            'reversal recurrence did not match expected 0/600 recovered sites per method')
    return output

def render(rows):
    out=io.StringIO(newline='')
    writer=csv.DictWriter(out,fieldnames=COLUMNS,delimiter='\t',lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    return out.getvalue().encode('utf-8')

def main():
    expected=render(expected_rows())
    existing=(HERE/'reported_regime_scores.tsv').read_bytes()
    require(existing==expected,'reader-facing table has changed or is not reproducible from original evidence')
    print('EXP07_REPORTING_SEMANTICS=PASS')
    print('AGGREGATE_ROWS=54 SCENARIO_ROWS=1350')
    print('ORIGINAL_TRUTH_NEGATIVE_F1_EQUALS_ONE=5 (retained, not claimed as performance)')
    print('READER_FACING_ZERO_DENOMINATOR_F1=NA')
    print('RECURRENT_REVERSAL_RECOVERED=0_OF_600_PER_METHOD')
    print('SEALED_SOURCE_FILES_CHANGED=NO')

if __name__=='__main__':main()
