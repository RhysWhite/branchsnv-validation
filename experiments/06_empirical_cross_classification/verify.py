#!/usr/bin/env python3
"""Combine Experiment 06 analysis and production-QC pass criteria."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def parse_args():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--results-dir',required=True,type=Path); return p.parse_args()

def main():
    out=parse_args().results_dir.resolve()
    analysis=json.loads((out/'analysis_summary.json').read_text(encoding='utf-8'))
    qc=json.loads((out/'production_qc_summary.json').read_text(encoding='utf-8'))
    expected={'taxa':912,'variable_sites':31457,'eligible_non_root_adjacent_branches':1804,'branch_site_comparisons':16073690,'informative':31644,'both':30817,'unambiguous_not_fixed':675,'placement_ambiguous':152,'outside_intersection':827}
    totals_match=all(analysis['totals'].get(k)==v for k,v in expected.items())
    passed=bool(analysis.get('overall_pass') and qc.get('passed') and totals_match)
    summary={'schema_version':1,'experiment':'06_empirical_cross_classification','analysis':analysis,'production_qc':qc,'headline_totals_match':totals_match,'overall_pass':passed}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print('PASS' if passed else 'FAIL')
    return 0 if passed else 1
if __name__=='__main__': raise SystemExit(main())
