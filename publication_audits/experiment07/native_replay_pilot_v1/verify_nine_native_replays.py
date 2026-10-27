#!/usr/bin/env python3
"""Check retained Experiment 07 nine-replay evidence without executing external tools.

Run from anywhere, Python >=3.10. Exits nonzero on unexpected paths/hashes,
source changes, execution failures, or disagreement in original/fresh predictions.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PREVIOUS = HERE.parent / 'native_execution_provenance_v1' / 'source_versions'
ROOT = 'branchsnv-exp07-nine-replay-pilot-v1'
ORIGINAL_HEAD = '14cc805c068edbf4e0923b7531a96cc1c35556f2'
EXPECTED_ARCHIVE_SHA = '0a9796261f5b4dc23fb61cb3ab1cac08a0ef791367e4cf36e3ebbd3edf84ae33'
TARGETS = {
    ('ARPIP', 'S002', 2, 40, 0),
    ('HomoplasyFinder', 'S002', 152, 0, 0),
    ('PAML', 'S002', 302, 40, 0),
    ('PastML', 'S002', 452, 46, 0),
    ('POUTINE', 'S002', 602, 0, 0),
    ('SNPPar', 'S002', 752, 40, 0),
    ('HomoplasyFinder', 'S011', 161, 0, 20),
    ('POUTINE', 'S011', 611, 0, 18),
    ('SNPPar', 'S011', 761, 60, 20),
}

def fail_if_false(value, message):
    if not value:
        raise ValueError(message)

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def get_json(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    fail_if_false(isinstance(data, dict), f'Object expected: {path}')
    return data

def run():
    # Verify every data/source file in the subtree and reject unauthorized extras.
    hashes = {}
    for line in (HERE / 'SHA256SUMS').read_text().splitlines():
        expected, rel = line.split('  ', 1)
        fail_if_false(rel not in hashes and len(expected) == 64 and all(c in '0123456789abcdef' for c in expected), 'Invalid SHA256SUMS')
        fail_if_false(not Path(rel).is_absolute() and '..' not in Path(rel).parts, f'Unsafe hash path: {rel}')
        hashes[rel] = expected
    actual_files = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
    fail_if_false(actual_files == set(hashes) | {'SHA256SUMS'}, 'Unexpected or missing files')
    for rel, expected in hashes.items():
        path = HERE / rel
        fail_if_false(not path.is_symlink() and digest(path) == expected, f'File identity changed: {rel}')

    archive_marker = (HERE / 'SOURCE_ARCHIVE_SHA256.txt').read_text().split('  ', 1)
    fail_if_false(len(archive_marker) == 2 and archive_marker[0] == EXPECTED_ARCHIVE_SHA, 'Source archive identity changed')
    manifest = get_json(HERE / 'MANIFEST.json')
    fail_if_false(manifest['schema'] == 'branchsnv-exp07-nine-replay-pilot-v1', 'Unexpected manifest schema')
    fail_if_false(manifest['original_repo_head'] == ORIGINAL_HEAD, 'Original checkout HEAD changed')
    fail_if_false(len(manifest['selections']) == len(TARGETS), 'Wrong replay count')
    source = manifest['source']
    paths = {
        'executor_sha256': HERE / 'executor/exp07_execute.py',
        'job_manifest_sha256': HERE / 'executor/remaining_900_jobs.jsonl',
        'runtime_paths_sha256': HERE / 'executor/runtime_paths.json',
        'runtime_reviewed_pins_sha256': HERE / 'executor/runtime_reviewed_pins.json',
        'runner_sha256': PREVIOUS / 'runner_final.py',
        'adapter_sha256': PREVIOUS / 'adapter_final.py',
    }
    for field, path in paths.items():
        fail_if_false(path.is_file() and digest(path) == source[field], f'Source mismatch: {field}')
    # Ensure pin records came from the reviewed pin artifact.
    pins = get_json(HERE / 'executor/runtime_reviewed_pins.json')
    for key, record in manifest['verified_executable_pins'].items():
        fail_if_false(pins.get(key) == record, f'Runtime pin record changed: {key}')

    jobs = [json.loads(line) for line in (HERE / 'executor/remaining_900_jobs.jsonl').read_text().splitlines() if line.strip()]
    fail_if_false(len(jobs) == 900, '900-job manifest incomplete')
    fail_if_false(len({(j['method'], j['scenario_id']) for j in jobs}) == 900, 'Duplicate source jobs')
    expected_targets = {
        (r['method'], r['scenario_id'], r['job_index_1based'], r['branch_events'], r['recurrent_sites'])
        for r in manifest['selections']
    }
    fail_if_false(expected_targets == TARGETS, 'Unexpected selection or event counts')
    total_branch = total_recurrent = 0
    for r in manifest['selections']:
        method, sid = r['method'], r['scenario_id']
        job = jobs[r['job_index_1based'] - 1]
        fail_if_false((job['method'], job['scenario_id']) == (method, sid), f'Wrong job index {method}/{sid}')
        fail_if_false(job['alignment_sha256'] == r['canonical_alignment_sha256'] and job['rooted_tree_sha256'] == r['canonical_tree_sha256'], 'Input hash mismatch')
        fail_if_false(r['runner_sha256'] == source['runner_sha256'] and r['adapter_sha256'] == source['adapter_sha256'], 'Scenario source mismatch')
        prefix = HERE / 'runs' / method / sid
        receipts = {}
        predictions = {}
        for phase in ('original', 'fresh'):
            rp = prefix / phase / 'execution_result.json'
            pp = prefix / phase / 'predictions.json'
            record, pred = get_json(rp), get_json(pp)
            receipts[phase], predictions[phase] = record, pred
            fail_if_false(digest(rp) == r[f'{phase}_receipt_sha256'], f'Receipt SHA failure: {method}/{sid}/{phase}')
            fail_if_false(digest(pp) == r['prediction_sha256'], f'Predictions SHA failure: {method}/{sid}/{phase}')
            fail_if_false(record['status'] == 'EXECUTION_PASS' and record['exit_code'] == 0 and record['timed_out'] is False, f'Execution failure: {method}/{sid}/{phase}')
            fail_if_false(record['truth_read'] is False, f'Truth-read assertion missing: {method}/{sid}/{phase}')
            fail_if_false(record['predictions_sha256'] == r['prediction_sha256'], f'Embedded prediction SHA mismatch: {method}/{sid}/{phase}')
            fail_if_false(record['original_repo_head'] == ORIGINAL_HEAD and record['job'] == job, 'Receipt job/checkout mismatch')
            fail_if_false(record['source_runner_sha256'] == source['runner_sha256'] and record['source_adapters_sha256'] == source['adapter_sha256'], 'Receipt implementation mismatch')
            fail_if_false(pred['method'] == method and pred['scenario_id'] == sid, 'Wrong prediction identity')
            for endpoint, expected in (('branch_events',r['branch_events']), ('recurrent_sites', r['recurrent_sites'])):
                fail_if_false(isinstance(pred[endpoint], list) and len(pred[endpoint]) == expected and record['n_'+endpoint] == expected, f'Count mismatch: {method}/{sid}/{phase}/{endpoint}')
        fail_if_false(receipts['original']['runtime_sha256'] == receipts['fresh']['runtime_sha256'] == r['source_runtime_sha256'], 'Native runtime source changed')
        fail_if_false(receipts['original']['cwd'] != receipts['fresh']['cwd'], 'Original and fresh working directories are the same')
        fail_if_false((prefix/'original/predictions.json').read_bytes() == (prefix/'fresh/predictions.json').read_bytes(), 'Fresh predictions not byte-identical')
        for endpoint in ('branch_events', 'recurrent_sites'):
            def multiset(data):
                return Counter(json.dumps(x, sort_keys=True, separators=(',', ':')) for x in data[endpoint])
            fail_if_false(multiset(predictions['original']) == multiset(predictions['fresh']), f'Event identity mismatch: {method}/{sid}/{endpoint}')
        total_branch += r['branch_events']
        total_recurrent += r['recurrent_sites']
        print(f'{method:18s} {sid} branch={r["branch_events"]:3d} recurrent={r["recurrent_sites"]:3d} BYTE_IDENTICAL=PASS')
    fail_if_false((total_branch, total_recurrent) == (226,58), 'Aggregate total mismatch')
    raw_logs = (HERE / 'raw_log_hashes.tsv').read_text().splitlines()
    fail_if_false(len(raw_logs) == 37 and raw_logs[0] == 'sha256\tarchive_relative_path', 'Raw log digest inventory incomplete')
    for row in raw_logs[1:]:
        expected, rel = row.split('\t', 1)
        fail_if_false(len(expected) == 64 and rel.startswith('runs/') and rel.endswith(('/stdout.txt','/stderr.txt')), 'Malformed excluded log inventory')
    print('NINE_REPLAY_GIT_EVIDENCE=PASS')
    print('PAIRED_PREDICTION_BYTES=9_OF_9; BRANCH_CALLS=226; RECURRENT_CALLS=58')
    print('BOUNDARY=Same-host selected replays; no fresh execution on CI; native inputs, environments and log bytes excluded')

if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        print(f'NINE_REPLAY_GIT_EVIDENCE=FAIL: {type(exc).__name__}: {exc}', file=sys.stderr)
        raise
