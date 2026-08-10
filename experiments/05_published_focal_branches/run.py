#!/usr/bin/env python3
"""Reproduce published focal-branch SNV lists with BRANCHSNV v0.1.0a1."""
from __future__ import annotations
import argparse, csv, hashlib, json, os, platform, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

DATASETS = {
    "ak3": {
        "publication": "White et al. Microbial Genomics 2025;11:001452",
        "doi": "10.1099/mgen.0.001452",
        "alignment": "ak3_alignment.nex",
        "tree": "ak3_tree.nwk",
        "alignment_sha256": "40c49b026c52e04530ecbbee7044567ac3355eccf7adda42a7d96bf977df9014",
        "tree_sha256": "18322b2808baf621d09dd5292027205e68a0f207d7be44f043bd044d0d314bd0",
        "descendants": "focal_descendants/ak3_360.txt",
        "descendant_count": 360,
        "outgroup": ["SRR13968194"],
        "expected": [
            (99286,"T>C"),(237606,"G>T"),(268432,"A>G"),(297655,"C>A"),(541577,"C>T"),
            (643271,"A>G"),(728512,"T>C"),(1032205,"C>A"),(1067855,"C>T"),(1167367,"A>C"),
            (1193138,"A>T"),(1217440,"A>G"),(1435784,"G>C"),(1680288,"T>G"),(1751961,"T>C"),
            (1800235,"A>T"),(1837199,"G>A"),(2122507,"C>T"),(2144733,"C>T"),(2266325,"G>A"),
            (2310728,"C>T"),(2537681,"C>T"),(2777570,"C>T"),
        ],
        "published_indel_outside_scope": {"position":1465812,"change":"ATTGTTGTTTTGC>A","type":"deletion"},
    },
    "st97": {
        "publication": "White et al. Microbial Genomics 2024;10:001273",
        "doi": "10.1099/mgen.0.001273",
        "alignment": "st97_alignment.nex",
        "tree": "st97_tree.nwk",
        "alignment_sha256": "3e7a631c2780e1aeb7f6d3b600f2d7a08742b2351eb22edbd10a3ca0b3ca591c",
        "tree_sha256": "7f71657597b9dd62db8c93570c0afd251e5677c3657b1654e71b58a2a15949ad",
        "descendants": "focal_descendants/st97_2.txt",
        "descendant_count": 2,
        "outgroup": ["ERR4911723"],
        "expected": [
            (223985,"C>T"),(581603,"T>G"),(692084,"C>T"),(1389986,"C>T"),(1516856,"C>A"),
            (2039493,"T>A"),(2165308,"T>C"),(2402921,"A>G"),(2620177,"T>C"),(2648091,"G>T"),
        ],
        "published_indel_outside_scope": {"position":1249340,"change":"CA>C","type":"deletion"},
        "note": "The publication isolate 23MR1425 is represented as REF in the working matrix/tree; the focal descendants are REF and 23MR1427.",
    },
    "oxa48": {
        "publication": "White et al. Drug Resistance Updates 2026;84:101327",
        "doi": "10.1016/j.drup.2025.101327",
        "alignment": "oxa48_alignment.nex",
        "tree": "oxa48_tree.nwk",
        "alignment_sha256": "60940e7fca31849396ed070f79299055a762f4b5192dd18918fb84f300deda9b",
        "tree_sha256": "fb1895907fbbff4cb2e74d7ad564c12e9b80d07f5800b6007618dcb3b82f2540",
        "descendants": "focal_descendants/oxa48_39.txt",
        "descendant_count": 39,
        "outgroup": ["ERR1852604","ERR1791001","ERR1791000","ERR1791004"],
        "expected": [
            (48403,"G>A"),(128874,"G>A"),(585558,"C>T"),(592973,"C>T"),(1035621,"C>T"),
            (1244322,"C>T"),(1343549,"C>T"),(1397339,"G>A"),(2276376,"C>T"),(2716612,"A>G"),
            (3423672,"G>A"),(3434752,"C>G"),(4766134,"A>G"),
        ],
        "published_indel_outside_scope": {"position":4871038,"change":"A>AAACCTGC","type":"insertion"},
        "note": "The alignment taxon label REF denotes reference isolate 18AR0845; this experiment performs and records the deterministic REF→18AR0845 taxon-label normalization required for exact tree/alignment correspondence.",
    },
}

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def parse_args():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--branchsnv-root',required=True,type=Path)
    p.add_argument('--input-dir',required=True,type=Path)
    p.add_argument('--output-dir',required=True,type=Path)
    return p.parse_args()

def run_find(branchsnv_root:Path, alignment:Path, tree:Path, descendants:Path, outgroup:list[str], output_dir:Path, dataset:str):
    out=output_dir/f'{dataset}_results.tsv'; members=output_dir/f'{dataset}_members.txt'; report=output_dir/f'{dataset}_report.json'
    cmd=[sys.executable,'-m','branchsnv','find','--alignment',str(alignment),'--tree',str(tree),'--outgroup',*outgroup,'--clade-tips',str(descendants),'--mode','both','--include-ambiguous','--output',str(out),'--members-output',str(members),'--report',str(report)]
    env=os.environ.copy(); env['PYTHONPATH']=str(branchsnv_root/'src') + (os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    cp=subprocess.run(cmd,cwd=branchsnv_root,env=env,capture_output=True,text=True)
    if cp.returncode!=0: raise RuntimeError(f'{dataset} BRANCHSNV failed:\n{cp.stdout}\n{cp.stderr}')
    return out,members,report,cp.stdout.strip()

def main():
    a=parse_args(); root=a.branchsnv_root.resolve(); inp=a.input_dir.resolve(); out=a.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
    source_root=root/'src'; sys.path.insert(0,str(source_root)); import branchsnv  # type: ignore
    start=time.perf_counter(); started=datetime.now(timezone.utc).isoformat(); comparisons=[]; ds_summary=[]; transforms=[]
    with tempfile.TemporaryDirectory(prefix='branchsnv_focal_') as td:
        td=Path(td)
        for ds,cfg in DATASETS.items():
            aln=inp/cfg['alignment']; tree=inp/cfg['tree']; desc=inp/cfg['descendants']
            ah=sha256_file(aln); th=sha256_file(tree)
            if ah!=cfg['alignment_sha256']: raise ValueError(f'{ds} alignment checksum mismatch: {ah}')
            if th!=cfg['tree_sha256']: raise ValueError(f'{ds} tree checksum mismatch: {th}')
            run_aln=aln
            if ds=='oxa48':
                text=aln.read_text(encoding='utf-8'); old='taxlabels REF\t'; new='taxlabels 18AR0845\t'
                if text.count(old)!=1: raise ValueError('OXA-48 alignment normalization expected exactly one taxlabels REF token')
                run_aln=td/'oxa48_alignment_ref18AR0845.nex'; run_aln.write_text(text.replace(old,new,1),encoding='utf-8',newline='\n')
                transforms.append({'dataset':ds,'operation':'rename alignment taxon label REF to 18AR0845','input_sha256':ah,'output_sha256':sha256_file(run_aln)})
            res,members,report,stdout=run_find(root,run_aln,tree,desc,cfg['outgroup'],out,ds)
            obs={}
            with res.open(newline='',encoding='utf-8') as f:
                for row in csv.DictReader(f,delimiter='\t'): obs[int(row['position'])]=row
            expected=dict(cfg['expected']); allpos=sorted(set(expected)|set(obs)); exact=0
            for pos in allpos:
                row=obs.get(pos); exp=expected.get(pos,''); observed=row['change'] if row else ''
                status='exact' if row and observed==exp else ('published_only' if exp and not row else 'output_only' if row and not exp else 'difference')
                if status=='exact': exact+=1
                fixed = bool(row and row['fixed_within_clade']=='true' and row['exclusive_to_clade']=='true')
                unamb = bool(row and row['parsimony_status']=='unambiguous_change')
                comparisons.append((ds,cfg['doi'],pos,exp,observed,status,int(fixed),int(unamb),row['possible_pairs'] if row else '',row['parsimony_score'] if row else ''))
            report_json=json.loads(report.read_text())
            branch=report_json['branch']
            passed=(exact==len(expected)==len(obs) and branch['descendant_count']==cfg['descendant_count'] and all(r[6]==1 and r[7]==1 for r in comparisons if r[0]==ds))
            ds_summary.append({'dataset':ds,'doi':cfg['doi'],'descendant_count':branch['descendant_count'],'branch_id':branch['branch_id'],'published_snvs':len(expected),'reported_snvs':len(obs),'exact_position_direction':exact,'all_fixed_exclusive':all(r[6]==1 for r in comparisons if r[0]==ds),'all_unambiguous_change':all(r[7]==1 for r in comparisons if r[0]==ds),'passed':passed,'stdout':stdout})
    with (out/'focal_branch_comparison.tsv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(['dataset','publication_doi','position','published_change','branchsnv_change','comparison','fixed_exclusive','unambiguous_change','possible_pairs','parsimony_score']); w.writerows(comparisons)
    total_expected=sum(x['published_snvs'] for x in ds_summary); total_exact=sum(x['exact_position_direction'] for x in ds_summary)
    summary={'schema_version':1,'experiment':'05_published_focal_branches','branchsnv_version':branchsnv.__version__,'datasets':ds_summary,'totals':{'published_snvs':total_expected,'exact_position_direction':total_exact,'all_fixed_exclusive':all(x['all_fixed_exclusive'] for x in ds_summary),'all_unambiguous_change':all(x['all_unambiguous_change'] for x in ds_summary)},'input_transformations':transforms,'published_non_snv_events_outside_scope':{k:v.get('published_indel_outside_scope') for k,v in DATASETS.items() if v.get('published_indel_outside_scope')},'notes':{k:v.get('note') for k,v in DATASETS.items() if v.get('note')},'overall_pass':all(x['passed'] for x in ds_summary) and total_exact==46}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    meta={'experiment':'05_published_focal_branches','started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':round(time.perf_counter()-start,6),'python_version':platform.python_version(),'platform':platform.platform(),'branchsnv_version':branchsnv.__version__,'branchsnv_analysis_sha256':sha256_file(source_root/'branchsnv'/'analysis.py'),'branchsnv_parsimony_sha256':sha256_file(source_root/'branchsnv'/'parsimony.py'),'validation_script_sha256':sha256_file(Path(__file__).resolve()),'exit_status':'PASS' if summary['overall_pass'] else 'FAIL'}
    (out/'run_metadata.json').write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(f"Published focal-branch SNVs: {total_exact}/{total_expected} exact")
    for x in ds_summary: print(f"  {x['dataset']}: {x['exact_position_direction']}/{x['published_snvs']} exact; branch {x['branch_id'][:18]} ({x['descendant_count']} descendants)")
    print('PASS' if summary['overall_pass'] else 'FAIL')
    return 0 if summary['overall_pass'] else 1
if __name__=='__main__': raise SystemExit(main())
