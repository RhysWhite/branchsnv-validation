#!/usr/bin/env python3
"""Record-by-record production BRANCHSNV check for Experiment 06."""
from __future__ import annotations
import argparse, csv, hashlib, json, os, platform, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

QC_BRANCH_IDS = {
    "clade_a": [
        "b_2b41a42cc0bfff2665c9e2cece08c26492a3b82f05270f96924b300a66122c9a",
        "b_d05b4d77876d37552e94b5224b5bb56db3ce179cfff26a427e0f1d1992238c90",
        "b_cdf924511695d05bb6da1da7155a0f36cad448a30f1e11f79f6e318e60feafd3",
        "b_aef508be3c947ef142fbe662d61963fd2d6c8ac15c691f28ec85670526ec42a8",
    ],
    "clade_b": [
        "b_d1ba3750e88beec884d93515ea9eeee50a81dc56502ef8b45281ea16cdc6a12a",
        "b_12e34a97727d2bced6e44adfbc13266287a554938d326d61c0e6988400e95d36",
        "b_594b833f6a361de2ebed55204840c0809dd40a5b39aeac4b51eb590c09eea511",
        "b_e145ad95a184f5487ad58fe00b36f4b986e5c358ef4fee5e72554884932727ac",
    ],
}

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def write_tsv(path:Path, header, rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(header); w.writerows(rows)

def parse_args():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--branchsnv-root',required=True,type=Path)
    p.add_argument('--input-dir',required=True,type=Path)
    p.add_argument('--analysis-results-dir',required=True,type=Path)
    return p.parse_args()

def main():
    a=parse_args(); root=a.branchsnv_root.resolve(); inp=a.input_dir.resolve(); out=a.analysis_results_dir.resolve()
    started=datetime.now(timezone.utc).isoformat(); start=time.perf_counter()
    events=out/'informative_events.tsv'
    if not events.is_file(): raise FileNotFoundError(f'Missing accelerated results: {events}')
    with events.open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f,delimiter='\t'))
    by_key={(r['dataset'],r['branch_id'],r['site_id']):r for r in rows}
    env=os.environ.copy(); env['PYTHONPATH']=str(root/'src')+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    qc_rows=[]; discrepancies=[]; total_sites=total_records=total_exact=0
    for dsid, ids in QC_BRANCH_IDS.items():
        aln=inp/f'{dsid}_alignment.nex'; tree=inp/f'{dsid}_tree.nwk'; nsites=3911 if dsid=='clade_a' else 12148
        for bid in ids:
            total_sites += nsites
            with tempfile.TemporaryDirectory(prefix='branchsnv_empirical_qc_') as td0:
                td=Path(td0); res=td/'results.tsv'; mem=td/'members.txt'; rep=td/'report.json'
                cmd=[sys.executable,'-m','branchsnv','find','--alignment',str(aln),'--tree',str(tree),'--accept-existing-root','--branch-id',bid,'--mode','both','--include-ambiguous','--output',str(res),'--members-output',str(mem),'--report',str(rep)]
                cp=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True)
                if cp.returncode!=0: raise RuntimeError(f'Production QC failed for {dsid} {bid}:\n{cp.stdout}\n{cp.stderr}')
                with res.open(encoding='utf-8',newline='') as f: prod=list(csv.DictReader(f,delimiter='\t'))
                exact=0
                for pr in prod:
                    ar=by_key.get((dsid,bid,pr['site_id'])); total_records += 1
                    if ar is None:
                        discrepancies.append((dsid,bid,pr['site_id'],'missing_accelerated','','')); continue
                    prod_fixed=pr['fixed_within_clade']=='true' and pr['exclusive_to_clade']=='true'
                    accel_fixed=ar['fixed_exclusive']=='1'
                    ok=(pr['parsimony_status']==ar['parsimony_status'] and pr['possible_pairs']==ar['possible_pairs'] and int(pr['parsimony_score'])==int(ar['parsimony_score']) and prod_fixed==accel_fixed)
                    if ok: exact+=1; total_exact+=1
                    else: discrepancies.append((dsid,bid,pr['site_id'],'difference',f"{pr['parsimony_score']}|{pr['possible_pairs']}|{pr['parsimony_status']}|{int(prod_fixed)}",f"{ar['parsimony_score']}|{ar['possible_pairs']}|{ar['parsimony_status']}|{ar['fixed_exclusive']}"))
                accel_count=sum(1 for r in rows if r['dataset']==dsid and r['branch_id']==bid)
                if accel_count!=len(prod): discrepancies.append((dsid,bid,'','record_count',str(len(prod)),str(accel_count)))
                qc_rows.append((dsid,bid,nsites,len(prod),exact,len(prod)-exact))
    write_tsv(out/'production_qc.tsv',['dataset','branch_id','branch_site_analyses','informative_records','exact_records','discrepant_records'],qc_rows)
    write_tsv(out/'production_qc_discrepancies.tsv',['dataset','branch_id','site_id','issue','production','accelerated'],discrepancies)
    passed=total_sites==64236 and total_records==1617 and total_exact==1617 and not discrepancies
    summary={'schema_version':1,'experiment':'06_empirical_cross_classification_production_qc','selected_branches':8,'branch_site_analyses':total_sites,'informative_records':total_records,'exact_records':total_exact,'discrepancies':len(discrepancies),'passed':passed,'accelerated_event_table_sha256':sha256_file(events),'branchsnv_analysis_sha256':sha256_file(root/'src'/'branchsnv'/'analysis.py'),'branchsnv_parsimony_sha256':sha256_file(root/'src'/'branchsnv'/'parsimony.py')}
    (out/'production_qc_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    meta={'experiment':summary['experiment'],'started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':round(time.perf_counter()-start,6),'python_version':platform.python_version(),'platform':platform.platform(),'validation_script_sha256':sha256_file(Path(__file__).resolve()),'exit_status':'PASS' if passed else 'FAIL'}
    (out/'production_qc_run_metadata.json').write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(f'Production QC: {total_exact}/{total_records} informative records exact across 8 branches')
    print('QC PASS' if passed else 'QC FAIL')
    return 0 if passed else 1
if __name__=='__main__': raise SystemExit(main())
