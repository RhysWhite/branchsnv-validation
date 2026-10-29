#!/usr/bin/env python3
"""Regenerate three editable SVG figures from pinned Experiment 07 review evidence.

Sources: figure_source_data.json, the committed 5,173-request reconciliation
summary + row ledger, and the dated post-freeze audit Markdown. No external
requests, sealed validation data, or original raw provider responses are read.

Run from any directory: python3 manuscript/supplementary/experiment_07/make_figures.py
Optional: --check checks reproducibility without modifying output files.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import html
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUDIT = ROOT / 'results/07_comparative_landscape/oct2026_bibliographic_reconciliation'
POST = ROOT / 'experiments/07_comparative_landscape/POST_FREEZE_AUDIT_20261007.md'

NAVY = '#20364c'; INK = '#23394d'; MUTED = '#536679'; TEAL = '#087984'
BLUE = '#3477a7'; PALE = '#f4f8fa'; LINE = '#d3dfe5'; WHITE = '#ffffff'
ORANGE = '#b87431'; AMBER = '#f8ebd9'; PINK = '#f8eded'; RED = '#a65348'


def esc(x):
    return html.escape(str(x), quote=True)


def node(name, *children, **kw):
    attrs = ' '.join(f'{k.replace("_", "-")}="{esc(v)}"' for k, v in kw.items() if v is not None)
    return f'<{name} {attrs}>' + ''.join(children) + f'</{name}>'


def text(x, y, s, size=22, fill=INK, weight=400, anchor='start', **extra):
    return node('text', esc(s), x=x, y=y, fill=fill, font_size=size, font_weight=weight,
                text_anchor=anchor, font_family='Arial, Liberation Sans, sans-serif', **extra)


def line(x1,y1,x2,y2,stroke=LINE,sw=2,dash=None):
    return node('line',x1=x1,y1=y1,x2=x2,y2=y2,stroke=stroke,stroke_width=sw,
                stroke_dasharray=dash)


def rect(x,y,w,h,fill=WHITE,stroke=LINE,r=14,sw=1.8):
    return node('rect',x=x,y=y,width=w,height=h,rx=r,fill=fill,stroke=stroke,stroke_width=sw)


def path(d,stroke=INK,sw=2,fill='none',dash=None):
    return node('path',d=d,fill=fill,stroke=stroke,stroke_width=sw,stroke_dasharray=dash,
                stroke_linecap='round',stroke_linejoin='round')


def label(x,y,s):
    return text(x,y,s.upper(),17,TEAL,700,letter_spacing='1.4px')


def doc(w,h,title,items):
    prefix=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            'role="img" aria-label="'+esc(title)+'">\n'
            '<rect width="100%" height="100%" fill="#ffffff"/>\n')
    return prefix + '\n'.join(items) + '\n</svg>\n'


def card(x,y,w,h,heading,main,sub=(),fill=WHITE,accent=TEAL):
    a=[rect(x,y,w,h,fill=fill)]
    a += [node('rect',x=x,y=y,width=7,height=h,rx=2,fill=accent)]
    a += [text(x+23,y+37,heading,19,MUTED,650),text(x+23,y+86,main,37,INK,700)]
    for j,s in enumerate(sub): a.append(text(x+23,y+114+j*25,s,17,MUTED))
    return ''.join(a)


def arrows(xs,y):
    return [path(f'M {u} {y} H {v-15}',TEAL,2.5)+path(f'M {v-25} {y-7} L {v-15} {y} L {v-25} {y+7}',TEAL,2.5) for u,v in zip(xs[::2],xs[1::2])]


def load():
    d=json.loads((HERE/'figure_source_data.json').read_text())
    s=json.loads((AUDIT/'reconciliation_summary.json').read_text())
    if d['reconciliation_v09']['class_counts'] != s['class_counts']:
        raise ValueError('Class counts disagree between figure source and committed audit')
    with (AUDIT/'request_level_reconciliation_5173.tsv').open(encoding='utf-8',newline='') as fh:
        rows=list(csv.DictReader(fh,delimiter='\t'))
    observed=Counter(r['identity_evidence'] for r in rows)
    if len(rows)!=s['request_count'] or dict(observed)!=s['class_counts']:
        raise ValueError('Cannot reconcile request-level identities with published summary')
    if any(r['abstract_promoted']!='0' for r in rows):
        raise ValueError('Unexpected automatic abstract promotion')
    audit_md=POST.read_text()
    matrix={}
    for segment in audit_md.splitlines():
        match=re.fullmatch(r'\|\s*(Assessed identities|Retained identities|Direct|Near-direct|Supporting|Noncomparators)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|',segment)
        if match: matrix[match.group(1)]=(int(match.group(2)),int(match.group(3)))
    required={'Assessed identities':(247,251),'Retained identities':(218,222),
              'Direct':(3,3),'Near-direct':(26,27),'Supporting':(189,192),'Noncomparators':(29,29)}
    if matrix!=required: raise ValueError(f'Post-freeze correction does not reconcile: {matrix}')
    orig=d['original_database_search']
    if (orig['initial_method_identities'],orig['initial_landscape_identities'],orig['original_last_review_identity_count'],orig['original_last_review_retained_count']) != (247,218,251,222):
        raise ValueError('Frozen and post-freeze figures disagree')
    if sum(matrix[k][1] for k in ('Direct','Near-direct','Supporting')) != 222:
        raise ValueError('Post-audit classifications do not sum to 222')
    later=d['later_request_level_audit']
    if later['original_missing_metadata']+later['original_abstract_gaps'] != s['request_count']:
        raise ValueError('Later request identity population differs')
    if s['aggregate_abstracts_promoted'] != 0:
        raise ValueError('No aggregate abstract should be promoted')
    return d,s


def fig1(d,s):
    o=d['original_database_search']; later=d['later_request_level_audit']; a=[]
    a += [text(54,77,'S1',25,TEAL,800),text(114,77,'Method discovery and classification',34,NAVY,700),
          text(56,115,'Original software landscape and a separate bibliographic completeness audit',21,MUTED),
          label(56,164,'September 2026 · original search and screening')]
    xs=[56,437,818,1199]; w=343
    boxes=[('Search strategy', f"{o['query_families']} + {o['generic_high_recall_blocks']}",('initial + high-recall query','families')),
           ('Database retrieval',f"{o['candidate_records']:,}",('source-query records',)),
           ('Deduplicated',f"{o['deduplicated_database_records']:,}",('database records',)),
           ('Review universe',f"{o['original_review_records']:,}",('12,156 new + 6 carried forward',))]
    for x,(heading,main,sub) in zip(xs,boxes): a.append(card(x,187,w,150,heading,main,sub))
    for x in [413,794,1175]: a.append(path(f'M {x-11} 263 h 19 m -7 -7 l 7 7 l -7 7',TEAL,2.5))
    a += [text(58,377,f"Citation discovery: {o['wave0_source_verified_anchors']} source-verified starting anchors; initial bidirectional wave completed 23 September",20,MUTED),
          text(58,414,'Initial classification',21,NAVY,700),
          card(56,434,448,150,'Original result freeze',f"{o['initial_method_identities']} assessed",(f"{o['initial_landscape_identities']} retained",),'#f5f9fc',BLUE),
          text(546,511,'+ 4 methods',24,TEAL,700),
          path('M 514 509 H 527 M 519 503 L 527 509 L 519 515',TEAL,2),
          card(715,434,448,150,'7 October source audit',f"{o['original_last_review_identity_count']} assessed",(f"{o['original_last_review_retained_count']} retained",),'#eef8f7',TEAL),
          rect(1196,434,345,150,'#f8fafb'),text(1218,465,'Post-audit retained',20,MUTED,600),
          text(1218,501,'3 direct',25,NAVY,700),text(1218,531,'27 near-direct',24,NAVY,700),
          text(1218,561,'192 supporting',24,NAVY,700),
          text(57,631,'The original 247-identity freeze is unchanged. Classification does not confer benchmark eligibility.',19,MUTED)]
    a += [line(55,680,1542,680,LINE,2,'8 9'),
          label(56,718,'October 2026 · separate blind-safe evidence audit'),
          text(56,758,'Different source population — not added to the original method counts',20,MUTED)]
    # Only backlog → eligible requests → recovery tasks is a flow.
    # The independently prioritised scope review is shown across a divider,
    # without a connecting arrow or a shared denominator.
    starts=[56,404,752]
    seq=[('Backlog',f"{later['candidate_entities']:,}",'publication candidates'),
         ('Eligible',f"{later['eligible_request_rows']:,}",'exact-ID requests'),
         ('Recovery',f"{s['request_count']:,}",'metadata / abstract gaps')]
    for x,(h,m,sub) in zip(starts,seq): a.append(card(x,784,308,135,h,m,(sub,),PALE,BLUE))
    for x in [371,719]: a.append(path(f'M {x} 851 H {x+26} m -7 -7 l 7 7 l -7 7',BLUE,2))
    a += [line(1124,784,1124,922,LINE,2,'6 8'),
          text(1193,775,'INDEPENDENT SCOPE REVIEW',16,TEAL,700),
          card(1173,795,369,124,'Prioritised methods',
               f"{later['provisional_family_count']} families",
               (f"from {later['scope_screening_worklist']:,} scoped records",),
               '#f3f8f8',TEAL)]
    a += [text(56,970,'Units differ across lanes: records, request identities and method identities must not be summed.',18,MUTED),
          text(56,1003,'Source: frozen Experiment 07 result, post-freeze audit and separately versioned reconciliation.',17,MUTED)]
    return doc(1600,1035,'Supplementary Figure S1 method discovery',a)


CLASS_LABELS=[
  ('REGISTRY_DOI_AND_TITLE_EXACT_AGGREGATE_ABSTRACT_UNVERIFIED','Registered DOI + title exact; aggregate abstract unverified',TEAL),
  ('DIRECT_IDENTIFIER_MATCH','Direct identifier match',BLUE),
  ('DOI_EXACT_TITLE_DIFFERENT_REVIEW','DOI exact; different title',ORANGE),
  ('DOI_EXACT_TITLE_NEAR_REVIEW','DOI exact; near title',ORANGE),
  ('DOI_EXACT_TITLE_UNCOMPARABLE','DOI exact; title not comparable',ORANGE),
  ('UNRECOVERED_OR_QUARANTINED','Unrecovered or quarantined',RED),
  ('REGISTRY_RETURNED_DIFFERENT_DOI','Registry returned a different DOI',RED),
  ('REGISTRY_NOT_FOUND','Registration not found',RED),
]


def fig2(d,s):
    a=[text(54,77,'S2',25,TEAL,800),text(114,77,'Publication identity is not abstract identity',34,NAVY,700),
       text(56,115,f"{s['request_count']:,} exact-identifier recovery requests; mutually exclusive classification",21,MUTED),
       label(56,171,'Reconciliation outcomes (number of requests)')]
    maxc=max(s['class_counts'].values()); y=209
    for idx,(k,lab,col) in enumerate(CLASS_LABELS):
        v=s['class_counts'][k]
        a+=[text(57,y,lab,20,INK,600),rect(58,y+14,710,13,'#edf2f4','none',7,0),
            rect(58,y+14,max(4,710*v/maxc),13,col,'none',7,0),
            text(821,y+23,f'{v:,}',23,NAVY,700,anchor='end')]
        y+=70
    a += [text(59,807,'Classified requests',20,MUTED),text(59,856,f"{s['request_count']:,}",44,NAVY,700),
          text(59,891,'5,005 metadata gaps + 168 abstract gaps',18,MUTED),
          rect(887,163,658,690,'#f7f9fb',LINE,18),label(918,207,'Why verification matters'),
          text(919,261,'Requested publication version',24,NAVY,700),
          rect(918,278,595,74,WHITE,LINE,12),text(937,309,'DOI A  ·  specific publication or release',20,INK,600),
          text(937,333,'An exact-version question',18,MUTED),
          path('M 1213 352 V 406 m -8 -11 l 8 11 l 8 -11',BLUE,2.5),
          rect(918,420,595,102,WHITE,LINE,12),text(937,453,'OpenAlex aggregated work',22,NAVY,700),
          text(937,482,'Preferred DOI may refer to a different version',18,MUTED),
          text(937,505,'An abstract can be work-level rather than version-level',18,MUTED),
          path('M 1213 523 V 570 m -8 -11 l 8 11 l 8 -11',BLUE,2.5),
          rect(918,584,595,107,WHITE,LINE,12),text(937,616,'Crossref / DataCite lookup',22,NAVY,700),
          text(937,645,'Registered DOI and title can corroborate identity',18,MUTED),
          text(937,670,'They do not authenticate the aggregated abstract',18,RED,650),
          rect(918,714,595,105,AMBER,'#e6c699',13),
          text(938,751,'0 aggregate abstracts promoted',25,NAVY,700),
          text(938,785,'Unresolved title / version conflicts remain review-only',18,MUTED),
          line(55,917,1543,917),
          text(57,955,'Reconciliation verified request identities, not scientific inclusion or abstract-version equivalence.',19,MUTED),
          text(57,985,'Source: committed request-level reconciliation ledger and v0.9 summary.',17,MUTED)]
    return doc(1600,1010,'Supplementary Figure S2 DOI and abstract identity',a)


def fig3(d,s):
    c=d['comparability_example']; ns=c['node_states']; n=c['substitution_events']; endpoint=c['endpoint_difference']
    a=[text(54,77,'S3',25,TEAL,800),text(114,77,'Shared inputs do not imply shared inference targets',34,NAVY,700),
       text(56,115,'A single-branch substitution history illustrates a difference in the quantities methods estimate',21,MUTED),
       label(56,168,'Conceptual example · one phylogenetic branch'),
       rect(55,190,1490,293,'#f5f9fa',LINE,20)]
    a += [line(245,326,1315,326,BLUE,6),path('M 1302 317 l 13 9 l -13 9',BLUE,4),
          node('circle',cx=245,cy=326,r=41,fill=WHITE,stroke=BLUE,stroke_width=3),
          node('circle',cx=1315,cy=326,r=41,fill=WHITE,stroke=BLUE,stroke_width=3),
          text(245,338,ns[0],32,NAVY,750,anchor='middle'),
          text(1315,338,ns[-1],32,NAVY,750,anchor='middle'),
          text(245,275,'Parent state',20,MUTED,600,anchor='middle'),
          text(1315,275,'Child state',20,MUTED,600,anchor='middle')]
    for x,t in [(600,'A→G'),(975,'G→A')]:
        a += [line(x,312,x,341,ORANGE,5),text(x,287,t,26,ORANGE,750,anchor='middle')]
    a += [text(786,377,'intermediate G is latent, not an observed node',19,MUTED,anchor='middle'),
          rect(282,411,440,52,WHITE,LINE,10),text(502,445,f'Endpoint changes: {endpoint}',22,NAVY,700,anchor='middle'),
          rect(861,411,440,52,WHITE,LINE,10),text(1081,445,f'Substitution events: {n}',22,NAVY,700,anchor='middle'),
          label(55,537,'Distinct analytical endpoints')]
    headers=[('Method output','What is being estimated','Potential comparison')]
    colx=[55,410,1060]
    rows=[
      ('Ancestral state','Nucleotide at an internal phylogenetic node','Node-state agreement'),
      ('Branch endpoint','Parent-to-child state difference','Net change or state-pair agreement'),
      ('Substitution history','Latent events along an evolutionary branch','Event counts / mapped histories'),
      ('Homoplasy','Repeated or convergent changes across branches','Recurrence-specific metrics')
    ]
    a += [rect(55,562,1490,48,NAVY,'none',8),text(75,595,'Analytical output',19,WHITE,700),
          text(428,595,'Question addressed',19,WHITE,700),text(1070,595,'Appropriate endpoint',19,WHITE,700)]
    for k,(l,m,sc) in enumerate(rows):
        yy=610+k*68
        a += [rect(55,yy,1490,68,WHITE if k%2 else '#f5f8fa',LINE,0,.8),
              text(75,yy+41,l,20,NAVY,700),text(428,yy+41,m,20,INK),text(1070,yy+41,sc,19,INK)]
    a += [text(58,923,'Benchmark eligibility also requires compatible rooted trees, branch identities, site coordinates, substitution models and missing-data rules.',19,MUTED),
          text(58,954,'Illustration is not an observed result and does not establish native JC69 compatibility for any new software.',17,MUTED)]
    return doc(1600,981,'Supplementary Figure S3 method comparison estimands',a)


def run(check=False):
    d,s=load()
    svg={1:fig1(d,s),2:fig2(d,s),3:fig3(d,s)}
    if check:
        for n,content in svg.items():
            existing=(HERE/f'Figure_S{n}.svg').read_text()
            if content!=existing:
                raise SystemExit(f'FAIL: Figure S{n}.svg is not regenerated exactly; run make_figures.py')
        print('REGENERATION_CHECK_PASS: 3 SVGs match source-ledger results byte-for-byte')
        return
    try: import cairosvg
    except ImportError as e: raise SystemExit('CairoSVG required to generate PNG previews; SVG output can be generated independently') from e
    for n,content in svg.items():
        (HERE/f'Figure_S{n}.svg').write_text(content,encoding='utf-8')
        cairosvg.svg2png(bytestring=content.encode(),write_to=str(HERE/f'Figure_S{n}.png'),
                        output_width=2200)
        print(f'Figure_S{n}: SVG + PNG from validated source data')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Require SVG output to match regenerated content exactly')
    run(check=parser.parse_args().check)
