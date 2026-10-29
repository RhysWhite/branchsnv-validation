#!/usr/bin/env python3
"""Check exported Experiment 07 manuscript data without accessing sealed material."""
from pathlib import Path
from collections import Counter
import json,csv,hashlib,sys

here=Path(__file__).resolve().parent
repo=here.parents[2]
assert here.parts[-3:]==('manuscript','supplementary','experiment_07')
audit=repo/'results/07_comparative_landscape/oct2026_bibliographic_reconciliation'
s=json.loads((audit/'reconciliation_summary.json').read_text())
d=json.loads((here/'figure_source_data.json').read_text())
def need(cond,reason):
    if not cond: raise SystemExit('FAILED: '+reason)
need(s['request_count']==5173,'request plan')
need(s['original_missing_metadata_requests']+s['original_missing_abstract_requests']==s['request_count'],'backlog split')
need(sum(s['class_counts'].values())==5173,'class population')
need(sum(s['registry_status_counts'].values())==4672,'registry population')
need(sum(s['registry_title_relation_counts'].values())==4672,'title relation population')
need(s['registry_status_counts']['REGISTRY_DOI_EXACT']==4555,'exact registry DOI')
need(s['aggregate_abstracts_promoted']==0,'unpromoted aggregate abstracts')
need(s['sealed_sample_files_accessed'] is False,'sealed sample status')
need(d['reconciliation_v09']['class_counts']==s['class_counts'],'figure reconciliation classes')
need(d['reconciliation_v09']['registry_status_counts']==s['registry_status_counts'],'figure registry classes')
need(d['later_request_level_audit']['original_missing_metadata']+d['later_request_level_audit']['original_abstract_gaps']==5173,'figure audit plan')
need(d['original_database_search']['new_review_rows']+d['original_database_search']['carried_prior_rows']==12162,'original review universe')
need(d['original_database_search']['initial_method_identities']==247,'v1 initial identities')
need(d['original_database_search']['initial_landscape_identities']==218,'v1 initial retained')
need(d['comparability_example']['node_states']==['A','G','A'] and d['comparability_example']['substitution_events']==2 and d['comparability_example']['endpoint_difference']==0,'conceptual example')
with (audit/'request_level_reconciliation_5173.tsv').open(encoding='utf-8',newline='') as fh:
  rows=list(csv.DictReader(fh,delimiter='\t'))
need(len(rows)==5173,'row ledger size')
need(len({row['request_sequence'] for row in rows})==5173,'unique request sequences')
need(Counter(row['identity_evidence'] for row in rows)==s['class_counts'],'row evidence class totals')
need(all(row['abstract_promoted']=='0' for row in rows),'no abstract promotion')
need(all(row['final_comparator_eligible'] in ('UNDETERMINED','NOT_DETERMINED') for row in rows),'unexpected comparator approval')
for n in (1,2,3):
 need((here/f'Figure_S{n}.svg').is_file() and (here/f'Figure_S{n}.png').is_file(),'figure source present')
print('EXP07_MANUSCRIPT_EVIDENCE_REVIEW_PASS; 5173 identity rows; no new comparator approvals')
print('WARNING: original 251-identity correction and graphical labels require authoritative independent signoff')

# Independent regeneration test: post-freeze table plus committed row-level
# reconciliation must regenerate the rendered SVG labels and geometry exactly.
from make_figures import load as load_review_sources, run as regenerate_figures
load_review_sources()
regenerate_figures(check=True)
print('EXP07_SUPPLEMENT_FIGURE_SOURCE_REGENERATION_PASS')
