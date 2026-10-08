#!/usr/bin/env python3
"""Synthetic-only tests of the independent evidence verifier; no comparators run."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('exp07_verify',HERE/'verify.py')
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
REPO = HERE.parents[2]

def reject(repo:Path, label:str) -> None:
    try: v.verify(repo,verbose=False)
    except (ValueError,OSError,KeyError,TypeError):
        print('PASS | tamper rejected:',label)
        return
    raise AssertionError('Tamper was not rejected: '+label)

def reseal(results:Path) -> None:
    lines=[]
    for p in sorted(results.rglob('*')):
        if p.is_file() and p.name!='SHA256SUMS':
            lines.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(results).as_posix())
    (results/'SHA256SUMS').write_text('\n'.join(lines)+'\n')

def fixture():
    temp=tempfile.TemporaryDirectory()
    root=Path(temp.name)
    exp='experiments/07_comparative_landscape/synthetic_execution_v6'
    res='results/07_comparative_landscape/eight_method_synthetic_v6'
    shutil.copytree(REPO/exp,root/exp)
    shutil.copytree(REPO/res,root/res)
    return temp,root,root/res

def main() -> None:
    v.verify(REPO,verbose=False)
    print('PASS | original evidence accepted')

    tmp,root,r=fixture()
    with tmp:
        f=r/'synthetic_v6/FastML/plan/native/log.txt'
        f.write_bytes(f.read_bytes()+b'\nFABRICATED\n')
        reject(root,'native output changed')
        reseal(r)
        reject(root,'native output changed and manifest recomputed')

    tmp,root,r=fixture()
    with tmp:
        f=r/'branchsnv-exp07-eight-method-synthetic-gate-v6.json'
        d=json.loads(f.read_text())
        d['methods']['POUTINE']['effective_synthetic_argv']=['/bin/false']
        f.write_text(json.dumps(d,indent=2)+'\n')
        reseal(r)
        reject(root,'POUTINE effective argv changed and manifest recomputed')

    tmp,root,r=fixture()
    with tmp:
        f=r/'branchsnv-exp07-eight-method-synthetic-gate-v6.json'
        d=json.loads(f.read_text());d['scoring_performed']=True
        f.write_text(json.dumps(d,indent=2)+'\n')
        reseal(r)
        reject(root,'invented scoring claim')

    tmp,root,r=fixture()
    with tmp:
        f=r/'synthetic_v6/PastML/plan/normalized_predictions.json'
        f.unlink()
        reject(root,'missing prediction file')

    tmp,root,r=fixture()
    with tmp:
        (r/'synthetic_v6/POUTINE/plan/native/compiled').symlink_to('/etc/passwd')
        reject(root,'unexpected external symlink')

    print('EXP07_SYNTHETIC_V6_TAMPER_TESTS=PASS')

if __name__=='__main__':main()
