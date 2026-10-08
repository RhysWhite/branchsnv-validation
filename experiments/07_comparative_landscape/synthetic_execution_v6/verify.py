#!/usr/bin/env python3
"""Independent, offline Experiment 07 v6 synthetic-execution evidence verification.

This verifier DOES NOT execute comparators, inspect canonical inputs/truth, or score
predictions. It validates internal consistency and byte integrity of a saved record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

METHODS = frozenset({"ARPIP", "FastML", "HomoplasyFinder", "PAML", "PastML", "POUTINE", "SNPPar", "TreeTime"})
FROZEN_COMMIT = "8c6c0aeded8948160e88528809e4b147a7a20b15"
EXPERIMENT = "experiments/07_comparative_landscape/synthetic_execution_v6"
RESULTS = "results/07_comparative_landscape/eight_method_synthetic_v6"
HEX = re.compile(r"[a-f0-9]{64}\Z")

class VerificationError(ValueError):
    pass


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise VerificationError(reason)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_path(base: Path, rel: str) -> Path:
    need(isinstance(rel, str), 'non-string manifest path')
    p = PurePosixPath(rel)
    need(rel and rel == p.as_posix() and not p.is_absolute() and '..' not in p.parts and '.' not in p.parts,
         f'unsafe evidence path: {rel!r}')
    q = base / Path(*p.parts)
    need(q.is_file() and not q.is_symlink(), f'missing or symlink evidence file: {rel}')
    need(q.resolve().is_relative_to(base.resolve()), f'evidence path escapes base: {rel}')
    return q


def read_json(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding='utf-8'))
    need(isinstance(obj, dict), f'expected JSON object: {path}')
    return obj


def check_sha_manifest(base: Path) -> int:
    manifest = base / 'SHA256SUMS'
    need(manifest.is_file() and not manifest.is_symlink(), 'missing SHA256SUMS')
    listed = {}
    for row in manifest.read_text(encoding='utf-8').splitlines():
        need('  ' in row, 'malformed SHA256SUMS entry')
        d,rel = row.split('  ',1)
        need(HEX.fullmatch(d) is not None, 'invalid manifest SHA256')
        need(rel not in listed and rel != 'SHA256SUMS', f'duplicate/recursive manifest path: {rel}')
        listed[rel] = d
        need(digest(safe_path(base,rel)) == d, f'manifest checksum mismatch: {rel}')
    actual = set()
    for path in base.rglob('*'):
        need(not path.is_symlink(),f'symlink in evidence tree: {path}')
        if path.is_file():
            actual.add(path.relative_to(base).as_posix())
    actual.discard('SHA256SUMS')
    need(set(listed) == actual, f'file inventory mismatch missing={sorted(actual-set(listed))[:5]} extra={sorted(set(listed)-actual)[:5]}')
    return len(listed)


def verify(repo: Path, verbose: bool = True) -> dict:
    repo = repo.resolve()
    results = repo / RESULTS
    code = repo / EXPERIMENT
    need(results.is_dir() and code.is_dir(), 'Experiment 07 v6 results/source not installed')
    num_files = check_sha_manifest(results)
    # Check upstream source bytes against the handoff's own (original) source manifest.
    lines = (code/'source/branchsnv-exp07-eight-method-v6.sha256').read_text().splitlines()
    need(len(lines)==3, 'unexpected v6 upstream source manifest shape')
    for line in lines:
        need('  ' in line, 'bad source checksum line')
        h,name=line.split('  ',1)
        need(name in {
            'branchsnv_exp07_eight_method_synthetic_gate_v6.py',
            'branchsnv_exp07_eight_method_v6_local_tests.py',
            'BRANCHSNV_EXP07_EIGHT_METHOD_SYNTHETIC_GATE_V6_README.md'}, 'unexpected source checksum member')
        need(HEX.fullmatch(h) is not None and digest(safe_path(code/'source',name))==h,
             f'source checksum mismatch: {name}')
    d = read_json(results/'branchsnv-exp07-eight-method-synthetic-gate-v6.json')
    need(d.get('schema')=='EXP07_EIGHT_METHOD_ISOLATED_SYNTHETIC_V1','unexpected run schema')
    need(d.get('frozen_commit')==FROZEN_COMMIT,'frozen source commit disagreement')
    need(d.get('status')=='ALL_EIGHT_SYNTHETIC_RUNS_SUCCESSFUL','run overall status not successful')
    for key,value in [('benchmark_truth_read',False),('canonical_inputs_read',False),('scoring_performed',False),('canonical_execution_authorized',False),('canonical_runs_started',0)]:
        need(type(d.get(key))==type(value) and d[key]==value, f'prohibited execution claim: {key}')
    methods = d.get('methods')
    need(isinstance(methods,dict) and set(methods)==METHODS,'method inventory mismatch')
    snapshots=d.get('environment_snapshots')
    need(isinstance(snapshots,dict) and set(snapshots)=={'POUTINE','PastML','SNPPar','TreeTime'},'snapshot inventory mismatch')
    for name,s in snapshots.items():
        need(s.get('reused_independently_sealed_snapshot') is True and s.get('snapshot_hardlinks')==0,
             f'snapshot not sealed: {name}')
        need(s.get('original_source_rehashed_on_resume') is False,
             f'unsupported changed source rehash provenance: {name}')
        need(s.get('snapshot_sha256') == s.get('source_sha256') and HEX.fullmatch(s['snapshot_sha256']),
             f'snapshot/source seal disagreement: {name}')
    for name in ('pastml_overlay','treetime_scipy_overlay','treetime_mpl_overlay'):
        ov=d.get(name)
        need(isinstance(ov,dict) and HEX.fullmatch(ov.get('overlay_tree_sha256','')) is not None,
             f'overlay seal missing: {name}')
        need(ov.get('frozen_authorization_unchanged') is True and ov.get('overlay_hardlinks')==0,
             f'overlay attribution mismatch: {name}')
        need(isinstance(ov.get('wheel_sha256'),dict) and ov['wheel_sha256'], f'overlay wheel inventory missing: {name}')
        need(all(HEX.fullmatch(x) for x in ov['wheel_sha256'].values()),f'invalid overlay wheel SHA: {name}')
    external = read_json(results/'EXCLUDED_HOST_SYMLINKS.json')
    need(external.get('no_symlinks_in_published_snapshot') is True and len(external.get('items',[]))==1,
         'host symlink exclusion metadata changed')
    link=external['items'][0]
    need(link.get('relative_path')=='synthetic_v6/POUTINE/plan/native/compiled' and
         link.get('original_target')=='/home/rwhite/branchsnv-comparator-src/poutine-smoke/compiled',
         'original nonportable POUTINE link not correctly recorded')
    method_rows=[]
    for name in sorted(METHODS):
        m=methods[name]
        plan=results/'synthetic_v6'/name/'plan'
        exe=read_json(plan/'execution.json')
        pred=read_json(plan/'normalized_predictions.json')
        need(m.get('truth_isolation')=='PASS' and m.get('status')=='SUCCESS' and
             m.get('comparator_executed_on_synthetic_input') is True and
             m.get('frozen_runner_used_custom_sandbox_executor') is True, f'method not isolated/successful: {name}')
        need(m.get('timed_out') is False and m.get('exit_code')==0 and m.get('failure_type') is None,
             f'method high-level exit mismatch: {name}')
        need(exe.get('status')=='SUCCESS' and exe.get('exit_code')==0 and
             exe.get('failure_type') is None and exe.get('timed_out') is False and
             exe.get('normalized_predictions_finalized') is True and
             exe.get('scoring_performed') is False and
             exe.get('method')==name and exe.get('scenario_id')=='SYNTHETIC_EXP07_'+name,
             f'runner completion/identity mismatch: {name}')
        need(m.get('runner_record_sha256')==digest(plan/'execution.json'),f'runner report hash mismatch: {name}')
        need(m.get('runner_record','').endswith(f'/synthetic_v6/{name}/plan/execution.json'),
             f'runner record trace mismatch: {name}')
        need(isinstance(exe.get('native_outputs'),list) and len(exe['native_outputs'])>=1,
             f'empty native outputs: {name}')
        for obj in exe['native_outputs']:
            q=safe_path(plan/'native',obj['path'])
            need(obj['size_bytes']==q.stat().st_size and obj['sha256']==digest(q),
                 f'native output integrity mismatch: {name}/{obj["path"]}')
        for filename,info in exe['comparator_inputs'].items():
            q=safe_path(results/'synthetic_v6'/name/'public_input',filename)
            need(info.get('size_bytes')==q.stat().st_size and info.get('sha256')==digest(q),
                 f'fixture mismatch: {name}/{filename}')
        need(pred.get('method')==name and pred.get('scenario_id')=='SYNTHETIC_EXP07_'+name,
             f'normalized prediction context mismatch: {name}')
        normalized_sha=digest(plan/'normalized_predictions.json')
        need(exe.get('normalized_predictions_sha256')==normalized_sha,
             f'normalized checksum disagrees with runner: {name}')
        need((plan/'normalized_predictions.sha256').read_text().strip()==
             normalized_sha+'  normalized_predictions.json',
             f'normalized SHA256SUMS mismatch: {name}')
        frozen=m.get('frozen_plan_argv')
        effective=m.get('effective_synthetic_argv')
        need(isinstance(frozen,list) and isinstance(effective,list) and all(isinstance(a,str) for a in frozen+effective),
             f'missing argv provenance: {name}')
        need(exe.get('argv')==frozen, f'frozen runner argv not preserved: {name}')
        if name=='POUTINE':
            need(m.get('synthetic_only_poutine_existing_outdir_override') is True and
                 m.get('production_poutine_runner_outdir_contract_unresolved') is True and
                 m.get('effective_argv_matches_frozen_plan') is False,
                 'POUTINE exception misrepresented')
            need(effective == frozen+['--force-overwrite'],
                 'POUTINE effective argv differs by more than the authorized synthetic-only override')
        else:
            need(m.get('synthetic_only_poutine_existing_outdir_override') is False and
                 m.get('effective_argv_matches_frozen_plan') is True and effective==frozen,
                 f'unrecorded effective command change: {name}')
        method_rows.append(name)
    summary=(results/'METHOD_SUMMARY.tsv').read_text().splitlines()
    need(len(summary)==9 and len(summary[0].split('\t'))==7, 'method summary missing or malformed')
    need(set(line.split('\t')[0] for line in summary[1:])==METHODS,'method summary names disagree')
    result={'passed':True,'source_commit':FROZEN_COMMIT,'methods':method_rows,
            'files_checked':num_files,'canonical_runs_started':0,'scientific_scoring':False}
    if verbose:
        print('PASS | source handoff SHA-256 identities')
        print(f'PASS | {num_files} publication evidence files verified')
        print('PASS | eight method runner records, native outputs, inputs and normalized predictions')
        print('PASS | truth-isolation records and POUTINE synthetic-only command discrepancy preserved')
        print('PASS | seal and dependency-overlay provenance retained with explicit limitations')
        print('EXP07_SYNTHETIC_V6_PUBLICATION_VERIFY=PASS')
        print('CANONICAL_EXECUTION_AUTHORIZED=FALSE; CANONICAL_RUNS_STARTED=0')
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[3])
    args=parser.parse_args()
    try: verify(args.repo_root)
    except (OSError,ValueError,KeyError,TypeError,AssertionError) as e:
        print(f'EXP07_SYNTHETIC_V6_PUBLICATION_VERIFY=FAIL | {type(e).__name__}: {e}',file=sys.stderr)
        return 1
    return 0

if __name__=='__main__': raise SystemExit(main())
