#!/usr/bin/env python3
"""Experiment 07: standalone, SYNTHETIC-ONLY eight-method sandbox gate v6.

No canonical inputs, benchmark truth, canonical result roots, repo edits, scoring,
or canonical authorization.  Sources remain untouched. Requires real pinned
comparator runtimes on jynx; off-host validation tests only pure logic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

COMMIT = '8c6c0aeded8948160e88528809e4b147a7a20b15'
AUTH_HASH = '934bf529136b34b5d39c1f22816aed19dedcd4b4c1aeddd34d1341e54e752cb5'
CANDIDATE_HASH = '4b9ac5f9dc61d4639560159a5a6eee78937fb03125a3621a2994791414fd0d42'
REPO = Path.home() / 'github/branchsnv-validation-exp07-finalize'
ROOT = REPO / 'experiments/07_comparative_landscape'
AUTH = ROOT / 'comparator_benchmark_execution_v1_harness_implementation_authorization.json'
CANDIDATE = Path.home() / 'branchsnv-exp07-runtime-mount-closure-CANDIDATE.json'
METHODS = ('ARPIP', 'FastML', 'HomoplasyFinder', 'PAML', 'PastML', 'POUTINE', 'SNPPar', 'TreeTime')
CANONICAL = REPO / 'results/07_comparative_landscape/comparator_benchmark_execution_v1'
REPORT = Path.home() / 'branchsnv-exp07-eight-method-synthetic-gate-v6.json'
ENV_METHODS = ('POUTINE', 'PastML', 'SNPPar', 'TreeTime')
# Explicit synthetic-only overlay; does NOT change the frozen PastML environment.
# Exact distribution pins allow archived wheel hashes to define the final environment.
PASTML_OVERLAY_REQUIREMENTS = (
    'numpy==1.26.4',
    'pandas==2.2.3',
    'jinja2==3.1.6',
    'biopython==1.85',
    'python-dateutil==2.9.0.post0',
    'pytz==2025.2',
    'tzdata==2025.2',
    'MarkupSafe==3.0.3',
    'six==1.17.0',
)
# Independent, pinned synthetic-only Matplotlib wheel overlay for TreeTime.
# Other dependencies (NumPy, pandas, SciPy, dateutil, BioPython) remain in
# the previously sealed synthetic overlays, NOT the frozen Conda prefix.
MPL_REQUIREMENTS = (
    'matplotlib==3.8.4',
    'contourpy==1.2.1',
    'cycler==0.12.1',
    'fonttools==4.53.1',
    'kiwisolver==1.4.5',
    'packaging==24.1',
    'pillow==10.4.0',
    'pyparsing==3.1.2',
)
# External JRE symlink target. This is a specific, read-only leaf, not /usr/share.
TZDB = Path('/usr/share/javazi-1.8/tzdb.dat')


class GateError(RuntimeError):
    pass

def require(condition, message):
    if not condition:
        raise GateError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as fp:
        for chunk in iter(lambda: fp.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def checked_repo():
    require(subprocess.check_output(['git','rev-parse','HEAD'], cwd=REPO, text=True).strip() == COMMIT,
            'frozen implementation commit differs')
    require(not subprocess.check_output(['git','status','--porcelain','--untracked-files=all'], cwd=REPO, text=True).strip(),
            'repository has modifications')
    require(not CANONICAL.exists() and not CANONICAL.is_symlink(), 'canonical result root exists')
    require(sha(AUTH) == AUTH_HASH, 'frozen authorization identity changed')
    sys.path.insert(0, str(ROOT))
    import comparator_benchmark_execution_v1_runner as runner
    import comparator_benchmark_execution_v1_harness as harness
    harness.verify_authorization_contract()
    harness.verify_security_amendment_002()
    runner.verify_frozen_identities()
    auth = json.loads(AUTH.read_text())
    require(tuple(auth['scenario_contract']['method_order']) == METHODS, 'method order differs')
    for label, spec in sorted(auth['runtime_files'].items()):
        path = Path(spec['path'])
        require(path.is_file() and sha(path) == spec['sha256'], f'pinned runtime mismatch: {label}')
    return runner, harness, auth

def seal_tree(root):
    """Independent reimplementation of previous candidate content-seal format.

    Reject symlink escapes, mutable-during-read source, special files, missing
    files. Group-writable source modes are audited, not automatic failures.
    """
    root = Path(root).resolve(strict=True)
    require(root.is_dir(), 'runtime tree missing')
    h = hashlib.sha256()
    counts = {'files':0, 'directories':0, 'symlinks':0, 'hardlink_files':0,
              'writable_mode_warnings':0, 'bytes':0}
    stack = [root]
    while stack:
        base = stack.pop()
        for name in sorted(os.listdir(base)):
            p = base / name
            rel = str(p.relative_to(root))
            before = p.lstat()
            if (before.st_mode & 0o022) and not stat.S_ISLNK(before.st_mode):
                counts['writable_mode_warnings'] += 1
            if stat.S_ISLNK(before.st_mode):
                target = p.resolve(strict=True)
                require(target.is_relative_to(root), 'runtime symlink escapes: ' + rel)
                kind, payload, size = 'L', os.readlink(p), 0
                counts['symlinks'] += 1
            elif stat.S_ISDIR(before.st_mode):
                kind, payload, size = 'D', oct(before.st_mode & 0o777), 0
                counts['directories'] += 1
                stack.append(p)
            elif stat.S_ISREG(before.st_mode):
                kind, payload, size = 'F', sha(p), before.st_size
                counts['files'] += 1
                counts['bytes'] += size
                counts['hardlink_files'] += (before.st_nlink > 1)
            else:
                raise GateError('runtime tree contains special file: ' + rel)
            after = p.lstat()
            require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                    == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                    'runtime file changed while hashing: ' + rel)
            h.update(json.dumps([rel, kind, payload, size], ensure_ascii=True, separators=(',', ':')).encode()+b'\n')
    return h.hexdigest(), counts

def snapshot_environment(method, dest, auth, candidate):
    orig = Path(auth['runtime_config'][method]['environment_dir'])
    expected = candidate['runtime_environment_directories'][method]['tree_content_seal_sha256']
    actual, before_counts = seal_tree(orig)
    require(actual == expected, f'{method} source tree changed from candidate seal')
    require(not dest.exists(), f'{method} snapshot destination already exists')
    shutil.copytree(orig, dest, symlinks=True, copy_function=shutil.copy2)
    copied, after_counts = seal_tree(dest)
    require(copied == expected and after_counts['hardlink_files'] == 0,
            f'{method} snapshot checksum or hardlink independence mismatch')
    # Staging parent is private 0700. Preserve directory modes for exact seal
    # verification; the sandbox bind is read-only, and copied files share no
    # hardlinks with the host Conda package cache.
    return {'source_sha256': actual, 'snapshot_sha256': copied,
            'source_files': before_counts['files'], 'snapshot_hardlinks': after_counts['hardlink_files'],
            'source_permission_warnings': before_counts['writable_mode_warnings']}

def ldd_closure(binary, library_search_path=None):
    """Resolve immediate/transitive DT_NEEDED for a known trusted binary only.
    This is not an exhaustive map of libraries loaded via dlopen().
    """
    p = Path(binary)
    with p.open('rb') as stream:
        signature = stream.read(4)
    if signature != b'\x7fELF':
        return set()
    loader_env={'PATH':'/usr/bin:/bin','LANG':'C'}
    if library_search_path:
        loader_env['LD_LIBRARY_PATH']=library_search_path
    proc = subprocess.run(['ldd', str(p)], capture_output=True, text=True, timeout=30, check=False,
                          env=loader_env)
    require(proc.returncode == 0, f'ldd failed: {p}: {proc.stderr[:400]}')
    result = set()
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        require('not found' not in stripped, f'missing dynamic dependency of {p}: {stripped}')
        for token in stripped.replace('=>', ' ').split():
            if token.startswith('/') and Path(token).is_file():
                result.add(Path(token))
                break
    # Dynamic ELF interpreter is not necessarily included in ldd output.
    proc = subprocess.run(['readelf', '-l', str(p)], capture_output=True, text=True, timeout=10, check=False,
                          env={'PATH':'/usr/bin:/bin','LANG':'C'})
    require(proc.returncode == 0, 'readelf failed for ' + str(p))
    for interp in re.findall(r'Requesting program interpreter:\s*([^\]]+)\]', proc.stdout):
        result.add(Path(interp.strip()))
    return result

def is_beneath(p, root):
    return p == root or root in p.parents

def file_dependency_mounts(method, auth, snapshot_roots, pastml_overlay=None):
    """Mount ldd-resolved leaf files, never whole host / or /usr/lib directories."""
    cfg = auth['runtime_config'][method]
    tree_destinations = {Path(cfg['environment_dir'])} if 'environment_dir' in cfg else set()
    method_files = {
        'ARPIP': ['ARPIP_executable'], 'FastML': ['FastML_executable'],
        'HomoplasyFinder': ['HomoplasyFinder_java', 'HomoplasyFinder_jar'],
        'PAML': ['PAML_executable'], 'POUTINE': ['POUTINE_java', 'POUTINE_script','POUTINE_treetime'],
        'PastML': ['PastML_executable'], 'SNPPar': ['SNPPar_executable'],
        'TreeTime': ['TreeTime_executable'],
    }[method]
    binary_sources = [Path(auth['runtime_files'][label]['path']) for label in method_files]
    if method == 'HomoplasyFinder':
        tree_destinations.add(Path(cfg['java']).parents[1]) # /.../jre
    extras = {Path('/bin/sh')}
    extras.update(binary_sources)
    if 'environment_dir' in cfg:
        for name in ('bin/python', 'bin/python3', 'bin/java'):
            p = Path(cfg['environment_dir']) / name
            if p.is_file(): extras.add(p)
    if method == 'HomoplasyFinder':
        extras.add(TZDB)
        jre = Path(cfg['java']).parents[1]
        for part in ('lib/amd64/server/libjvm.so','lib/amd64/jli/libjli.so'):
            q = jre / part
            if q.is_file(): extras.add(q)
    # These ELF modules are loaded at runtime (dlopen / Python extension
    # imports), so ldd of the interpreter alone cannot discover their
    # system-library needs. Resolve *only* observed modules, not entire host
    # /lib, /usr or a Conda environment parent. Missing probes fail closed.
    if method == 'POUTINE':
        extras.add(Path(cfg['environment_dir']) / 'lib/jvm/lib/server/libjvm.so')
    if method in ('PastML', 'SNPPar', 'TreeTime'):
        require(method != 'PastML' or (pastml_overlay is not None and Path(pastml_overlay).is_dir()),
                'synthetic PastML overlay unavailable')
        probes = []
        if method == 'PastML':
            probes.append((Path(pastml_overlay) / 'pandas/_libs/window', 'aggregations*.so'))
        elif method == 'SNPPar':
            probes.append((Path(snapshot_roots) / 'SNPPar/lib/python3.8/site-packages/scipy/sparse',
                           '_sparsetools*.so'))
        else:  # TreeTime uses two independent, sealed SYNTHETIC-ONLY sources.
            probes.append((Path(pastml_overlay) / 'numpy/core', '_multiarray_umath*.so'))
            # TreeTime's frozen environment has no SciPy. Probe the separately
            # pinned, sealed, synthetic-only SciPy wheel overlay. This avoids
            # exposing PastML's Conda ABI/linker closure in TreeTime's sandbox.
            scipy_sparse = Path(snapshot_roots).parent / 'treetime_scipy_overlay_v5/scipy/sparse'
            probes.append((scipy_sparse, '_sparsetools*.so'))
            # The Matplotlib CLI import and its native wheel dependencies are
            # synthetic-only and independently verified, never host imports.
            mpl_root = Path(snapshot_roots).parent / 'treetime_mpl_overlay_v6'
            for subdir,pattern in (
                ('matplotlib','_path*.so'),
                ('matplotlib','ft2font*.so'),
                ('contourpy','_contourpy*.so'),
                ('kiwisolver','_cext*.so'),
                ('PIL','_imaging.cpython*.so'),
            ):
                probes.append((mpl_root/subdir,pattern))
        for directory, pattern in probes:
            matches = sorted(directory.glob(pattern))
            require(0 < len(matches) <= 2 and all(x.is_file() and not x.is_symlink() for x in matches),
                    f'{method}: missing/unexpected dynamically loaded ELF probe {directory}/{pattern}')
            extras.update(matches)
    for target in extras:
        require(target.is_file(), f'{method}: required runtime dependency disappeared: {target}')
    binaries = set()
    loader_path=None
    if method=='POUTINE':
        loader_path=str(Path(cfg['environment_dir'])/'lib/jvm/lib')
        require(Path(loader_path,'libjli.so').is_file(), 'POUTINE libjli.so absent')
    for exe in extras:
        binaries |= ldd_closure(exe, loader_path)
    # File binds for binaries not covered by method runtime directory mount.
    # Guard against trusting arbitrary paths returned by dependency inspection.
    allowed_external=(Path('/lib'),Path('/lib64'),Path('/usr/lib'),Path('/usr/lib64'),
       Path('/bin'),Path('/usr/bin'),Path('/home/rwhite/branchsnv-comparator-build'),
       Path('/home/rwhite/branchsnv-comparator-envs'),
       Path('/home/rwhite/branchsnv-comparator-src'), Path('/usr/share/javazi-1.8'))
    mounts = {}
    for p in extras | binaries:
        if not p.is_file(): continue
        if any(is_beneath(p, tree) for tree in tree_destinations):
            continue
        # Probed extension modules reside inside the independently sealed
        # snapshot or overlay that will be bound at its frozen runtime path.
        # Never create another bind at the host's synthetic snapshot path.
        if (is_beneath(p, Path(snapshot_roots)) or
                is_beneath(p, Path(snapshot_roots).parent/'treetime_scipy_overlay_v5') or
                is_beneath(p, Path(snapshot_roots).parent/'treetime_mpl_overlay_v6') or
                (pastml_overlay is not None and is_beneath(p, Path(pastml_overlay)))):
            continue
        # Never map a source file anywhere under the canonical data/results.
        require(not is_beneath(p, REPO), 'dependency unexpectedly in repository')
        require(any(is_beneath(p,root) for root in allowed_external),
                'unapproved dependency path: '+str(p))
        src = p.resolve(strict=True)
        require(any(is_beneath(src,root) for root in allowed_external),
                'dependency resolves outside allowlist: '+str(src))
        require(src.is_file(), 'dependency disappeared')
        mounts[str(p)] = str(src)
    # /bin/sh may resolve to /usr/bin/bash; bind it at its literal destination.
    # A loader SONAME can refer to a second symlink path: ldd covers known ones.
    return mounts, tree_destinations

def bwrap_args(mount_dirs, files, readonly, writable, cwd, argv, env):
    """Private-root sandbox, with explicit source/destination mount pairs."""
    assert isinstance(argv, (list,tuple)) and argv
    destinations = [Path(p) for p in mount_dirs] + [Path(p) for p in files] + [Path(p) for p in readonly] + [Path(p) for p in writable]
    forbidden={Path('/'),Path('/home'),Path('/home/rwhite'),Path('/usr'),Path('/usr/lib'),
               Path('/usr/lib64'),Path('/lib'),Path('/lib64'),Path('/bin'),Path('/etc'),
               REPO, REPO/'results',CANONICAL}
    for p in destinations:
        require(p.is_absolute() and '..' not in p.parts and p not in forbidden,
                'unsafe mount destination: '+str(p))
    # In particular, directory mounts may NEVER expose a host parent of
    # arbitrary data. Only frozen runtime/JRE/POUTINE support roots are legal.
    allowed_trees=(Path('/home/rwhite/branchsnv-comparator-envs'),
                   Path('/home/rwhite/branchsnv-comparator-src/poutine-smoke'),
                   Path('/usr/lib/jvm'))
    for path in map(Path,mount_dirs):
        require(any(root in path.parents for root in allowed_trees),
                'unapproved directory mount: '+str(path))
    forbidden_sources={Path('/'),Path('/home'),Path('/home/rwhite'),
                       Path('/usr'),Path('/usr/lib'),Path('/usr/lib64'),
                       Path('/bin'),Path('/lib'),Path('/lib64'), REPO, REPO/'results', CANONICAL}
    for group in (mount_dirs, files, readonly, writable):
        for src in group.values():
            source=Path(src)
            require(source.is_absolute() and source not in forbidden_sources and
                    not is_beneath(source,REPO), 'unapproved mount source: '+str(source))
    for src in mount_dirs.values():
        require(Path(src).is_dir(), 'runtime directory source missing')
    for src in files.values():
        require(Path(src).is_file(), 'runtime file source missing')
    for group in (readonly, writable):
        for src in group.values():
            require(Path(src).is_dir() and not Path(src).is_symlink(),
                    'synthetic workspace mount source unsafe')
    for i,p in enumerate(destinations):
        require(all(not is_beneath(p,q) and not is_beneath(q,p)
                    for j,q in enumerate(destinations) if j!=i),
                'mount destination overlap: '+str(p))
    # Mount target types matter: --dir <file> creates a directory at the
    # target path, causing bubblewrap to reject the later --ro-bind of a file.
    # In v1, `p in files` compared Path keys with string keys and was ALWAYS
    # false.  Create only parents for individual file targets, not the target.
    file_targets = {Path(p) for p in files}
    directory_targets = {Path(p) for group in (mount_dirs, readonly, writable)
                         for p in group}
    require(not file_targets.intersection(directory_targets),
            'file/directory destination type collision')
    folders = {Path('/tmp'), Path('/dev'), Path('/proc'), Path(cwd)}
    folders.update(p.parent for p in file_targets)
    folders.update(directory_targets)
    all_dirs = set()
    for p in folders:
        all_dirs.update(q for q in (p,*p.parents) if q!=Path('/'))
    cmd=['/usr/bin/env','-i','/usr/bin/bwrap','--tmpfs','/']
    for p in sorted(all_dirs, key=lambda a:(len(a.parts),str(a))):
        cmd+=['--dir',str(p)]
    for dest, src in sorted(mount_dirs.items()): cmd+=['--ro-bind',str(src),str(dest)]
    for dest, src in sorted(files.items()): cmd+=['--ro-bind',str(src),str(dest)]
    for dest, src in sorted(readonly.items()): cmd+=['--ro-bind',str(src),str(dest)]
    for dest, src in sorted(writable.items()): cmd+=['--bind',str(src),str(dest)]
    cmd+=['--tmpfs','/tmp','--dev','/dev','--proc','/proc',
          '--unshare-pid','--unshare-net','--unshare-uts','--unshare-ipc',
          '--die-with-parent','--new-session']
    for key,val in sorted(env.items()):
        require(key in ('PATH','HOME','TMPDIR','LANG','LC_ALL','PYTHONNOUSERSITE',
                        'OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','PYTHONHASHSEED','MPLCONFIGDIR',
                        'PYTHONPATH','LD_LIBRARY_PATH'),
                'unapproved subprocess env var: '+key)
        require('\x00' not in val, 'NUL environment value')
        cmd+=['--setenv',key,str(val)]
    cmd+=['--chdir',str(cwd),'--',*map(str,argv)]
    require('--ro-bind' in cmd and '--unshare-net' in cmd and '--tmpfs' in cmd,
            'sandbox isolation missing')
    return cmd

def spawn(command, timeout, cwd):
    start=time.monotonic()
    # close_fds prevents inherited truth handles; process group killed at timeout.
    p=subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       stdin=subprocess.DEVNULL, close_fds=True, start_new_session=True,
                       env={'PATH':'/usr/bin:/bin'})
    timed_out=False
    try:
        out,err=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out=True
        os.killpg(p.pid, signal.SIGKILL)
        out,err=p.communicate()
    elapsed=time.monotonic()-start
    return {'returncode':p.returncode, 'timed_out':timed_out,'elapsed_seconds':elapsed,
            'stdout':out.decode('utf-8','replace'), 'stderr':err.decode('utf-8','replace')}

def synthetic_input(runner, dest):
    """Frozen serializers; fixed artificial four-tip, 200-base alignment."""
    dest.mkdir(mode=0o700)
    reference = 'ACGT' * 50
    def changed(seq, positions):
        values = list(seq)
        for position in positions:
            i = position - 1
            values[i] = 'A' if values[i] != 'A' else 'C'
        return ''.join(values)
    sequences = {
        'tipA': reference,
        'tipB': changed(reference, [200]),
        'tipC': changed(reference, [40]),
        'tipD': changed(reference, [40, 200]),
    }
    positions = [40, 200]
    (dest/'alignment.fasta').write_text(runner.adapters.fasta_text(sequences))
    (dest/'tree.nwk').write_text('((tipA:0.1,tipB:0.1):0.1,(tipC:0.1,tipD:0.1):0.1);\n')
    (dest/'variable_positions.txt').write_text(runner.adapters.positions_text(positions))
    (dest/'reference.gb').write_text(runner.adapters.minimal_genbank_text(
        reference, positions, locus='SYNTHETIC'))

def check_synthetic_sandbox(method, command, truth_path, expected_input, expected_bin, cwd):
    # Shell builtins only (no awk/cat/grep). If truth readable via any alias, fail.
    # This test is NOT a claim of absolute confinement against all kernel bugs.
    script='''set -eu
[ -r "$INPUT" ] || exit 90
[ -r "$BIN" ] || exit 91
if [ -w "$BIN" ]; then exit 95; fi
if [ -r "$TRUTH" ] || [ -r "/proc/1/root$TRUTH" ] || [ -r "/proc/self/root$TRUTH" ]; then exit 92; fi
if [ -w "$INPUT" ]; then exit 93; fi
if [ -r /etc/shadow ] || [ -e /home/rwhite/.ssh/id_ed25519 ]; then exit 94; fi
printf 'ISOLATION_OK\\n'
'''
    # Command ends with '--', executable and argv. Swap only the child command.
    pos=command.index('--')
    isolated=command[:pos+1]+['/bin/sh','-c',script]
    env_start={'INPUT':str(expected_input),'BIN':str(expected_bin),'TRUTH':str(truth_path)}
    # Append approved probe-only env vars before -- separator.
    for k,v in sorted(env_start.items()):
        isolated[pos:pos]=['--setenv',k,v]
        pos += 3
    outcome=spawn(isolated,20,cwd)
    require(not outcome['timed_out'] and outcome['returncode']==0 and
            outcome['stdout'].strip()=='ISOLATION_OK',
            f'{method}: synthetic truth/input/runtime isolation failed: '
            +repr((outcome['returncode'],outcome['stderr'][:700],outcome['stdout'][:300])))



def prepare_pastml_overlay(root, allow_download):
    """Pinned wheels -> separate, sealed overlay. Never mutate original env/snapshots.

    Pip is only invoked under explicit --prepare-pastml-overlay. All wheels are
    separately archived and SHA-256 recorded; install uses --no-index --no-deps.
    """
    dest=root/'pastml_overlay_v3'
    wheelhouse=root/'pastml_wheels_v3'
    manifest=root/'pastml_overlay_v3_manifest.json'
    requirement_file=root/'pastml_overlay_v3_requirements.txt'
    content='\n'.join(PASTML_OVERLAY_REQUIREMENTS)+'\n'
    require(root.is_dir() and root.stat().st_uid==os.getuid(), 'workspace unsafe')
    require(not any(p.is_symlink() for p in (dest,wheelhouse,manifest,requirement_file)),
            'PastML overlay contains top-level symlink')
    if manifest.is_file():
        require(dest.is_dir() and wheelhouse.is_dir() and requirement_file.is_file(),
                'partial PastML overlay')
        meta=json.loads(manifest.read_text())
        actual,_=seal_tree(dest)
        require(meta.get('schema')=='EXP07_PASTML_SYNTHETIC_OVERLAY_V1' and
                meta['overlay_tree_sha256']==actual and
                meta['requirements_sha256']==hashlib.sha256(content.encode()).hexdigest() and
                requirement_file.read_text()==content,
                'PastML overlay manifest integrity drift')
        for name,checksum in meta['wheel_sha256'].items():
            file=wheelhouse/name
            require(file.is_file() and sha(file)==checksum, 'PastML wheel digest differs: '+name)
        print('PASS | previously pinned PastML overlay resealed: '+actual,flush=True)
        return meta
    require(allow_download, 'PastML dependency overlay missing: first run with --prepare-pastml-overlay')
    require(sys.version_info[:2]==(3,10), 'wheel preparation requires Python 3.10 to match pinned PastML ABI')
    require(not dest.exists() and not wheelhouse.exists() and not requirement_file.exists(),
            'PastML overlay partial state: do not overwrite')
    require(not manifest.exists(), 'PastML manifest path already exists')
    requirement_file.write_text(content)
    wheelhouse.mkdir(mode=0o700)
    dest.mkdir(mode=0o700)
    print('PREPARING | independent synthetic-only PastML dependency wheels',flush=True)
    # Download only binary wheels matching the actual host Python. No source
    # builds, editable packages, implicit upgrades, or mutation of frozen env.
    pip_env=os.environ.copy()
    pip_env['PIP_DISABLE_PIP_VERSION_CHECK']='1'
    subprocess.run([sys.executable,'-m','pip','download','--disable-pip-version-check',
                    '--no-deps','--only-binary=:all:','--dest',str(wheelhouse),
                    '-r',str(requirement_file)],check=True,timeout=1800,
                   env=pip_env)
    wheel_files=sorted(wheelhouse.glob('*.whl'))
    require(len(wheel_files)==len(PASTML_OVERLAY_REQUIREMENTS),
            'unexpected PastML wheel count; expected one wheel per pinned package')
    for name in wheelhouse.iterdir():
        require(name.is_file() and not name.is_symlink() and name.suffix=='.whl',
                'unapproved wheelhouse entry')
    wheel_sha={f.name:sha(f) for f in wheel_files}
    subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check',
                    '--no-index','--no-deps','--no-compile','--target',str(dest),
                    '--find-links',str(wheelhouse),'-r',str(requirement_file)],
                   check=True,timeout=900,
                   env=pip_env)
    # Auditable caution: reject .pth startup code in the overlay. Such .pth
    # files could otherwise execute code upon interpreter startup.
    for p in dest.rglob('*.pth'):
        require(not p.is_symlink() and all(not line.lstrip().startswith('import ')
                for line in p.read_text().splitlines()),
                'executable .pth installation unsupported: '+str(p))
    tree_hash,tree_counts=seal_tree(dest)
    require(tree_counts['hardlink_files']==0,'PastML overlay has shared hardlinks')
    meta={'schema':'EXP07_PASTML_SYNTHETIC_OVERLAY_V1',
          'method':'PastML','status':'SYNTHETIC_DEPENDENCY_RECOVERY_ONLY',
          'source_environment_unchanged':True,'frozen_authorization_unchanged':True,
          'requirements':list(PASTML_OVERLAY_REQUIREMENTS),
          'requirements_sha256':hashlib.sha256(content.encode()).hexdigest(),
          'wheel_sha256':wheel_sha,'overlay_tree_sha256':tree_hash,
          'overlay_files':tree_counts['files'],'overlay_hardlinks':0,
          'wheel_installation':'offline_no_index_no_deps_from_wheelhouse',
          'underlying_pastml_version':'1.9.51'}
    with manifest.open('x') as stream:
        json.dump(meta,stream,sort_keys=True,indent=2);stream.write('\n')
    print('PASS | independent PastML overlay pinned and sealed: '+tree_hash,flush=True)
    return meta

def synthetic_only_effective_argv(method, frozen_argv):
    """Return actual synthetic argv, explicitly recording any divergence.

    The frozen POUTINE plan pre-creates --out-dir (which contains ./compiled),
    but POUTINE refuses existing output directories without -X. We may test
    this synthetic fixture with -X, but MUST NOT claim frozen production argv
    is repaired or authorize a canonical run using this synthetic change.
    """
    require(method in METHODS, 'unexpected method in synthetic argv bridge')
    result=list(frozen_argv)
    if method == 'POUTINE':
        require('--out-dir' in result and '--force-overwrite' not in result and '-X' not in result,
                'POUTINE frozen command contract changed unexpectedly')
        result.append('--force-overwrite')
    return result


def treetime_scoped_scipy_mounts(root, method_env):
    """Read-only mount of an independently sealed SciPy-only wheel overlay."""
    source_root = Path(root) / 'treetime_scipy_overlay_v5'
    destination_root = Path(method_env).parent / 'treetime-exp07-synthetic-scipy'
    package = source_root / 'scipy'
    libs = source_root / 'scipy.libs'
    require(package.is_dir() and not package.is_symlink(), 'TreeTime SciPy overlay package absent')
    require((package/'__init__.py').is_file(), 'TreeTime SciPy __init__ absent')
    mounts={str(destination_root/'scipy'):str(package)}
    if libs.is_dir():
        require(not libs.is_symlink(), 'TreeTime scipy.libs symlink rejected')
        mounts[str(destination_root/'scipy.libs')]=str(libs)
    return mounts,str(destination_root)


def prepare_treetime_scipy_overlay(root, allow_download):
    """Pinned SciPy 1.14.0 wheel, separate from all comparator environments.

    Re-validates the seal and downloaded wheel hash on every resume. No source
    builds; never copies executable files from another method's Conda prefix.
    """
    dest=root/'treetime_scipy_overlay_v5'
    wheelhouse=root/'treetime_scipy_wheels_v5'
    manifest=root/'treetime_scipy_overlay_v5_manifest.json'
    requirement_file=root/'treetime_scipy_overlay_v5_requirements.txt'
    content='scipy==1.14.0\n'
    require(not any(p.is_symlink() for p in (dest,wheelhouse,manifest,requirement_file)),
            'TreeTime SciPy overlay symlinked path')
    if manifest.is_file():
        require(dest.is_dir() and wheelhouse.is_dir() and requirement_file.is_file(),
                'partial TreeTime SciPy overlay')
        meta=json.loads(manifest.read_text())
        tree_hash,counts=seal_tree(dest)
        require(meta.get('schema')=='EXP07_TREETIME_SCIPY_SYNTHETIC_OVERLAY_V1' and
                meta.get('overlay_tree_sha256')==tree_hash and
                requirement_file.read_text()==content and
                meta.get('requirements_sha256')==hashlib.sha256(content.encode()).hexdigest() and
                counts['hardlink_files']==0,
                'TreeTime SciPy overlay integrity drift')
        require(len(meta.get('wheel_sha256',{}))==1,'TreeTime SciPy wheel count invalid')
        for name,digest in meta['wheel_sha256'].items():
            require(Path(name).name==name and (wheelhouse/name).is_file() and
                    sha(wheelhouse/name)==digest, 'TreeTime SciPy wheel hash differs')
        print('PASS | previously pinned TreeTime SciPy overlay resealed: '+tree_hash,flush=True)
        return meta
    require(allow_download, 'TreeTime SciPy overlay missing: use --prepare-treetime-scipy-overlay')
    require(sys.version_info[:2]==(3,10),'SciPy wheel preparation requires Python 3.10')
    require(not any(p.exists() for p in (dest,wheelhouse,manifest,requirement_file)),
            'partial TreeTime SciPy overlay: no overwrite')
    require(root.is_dir() and root.stat().st_uid==os.getuid(), 'synthetic workspace unsafe')
    requirement_file.write_text(content)
    wheelhouse.mkdir(mode=0o700)
    dest.mkdir(mode=0o700)
    print('PREPARING | separate synthetic-only TreeTime SciPy 1.14.0 wheel',flush=True)
    pip_env=os.environ.copy()
    pip_env['PIP_DISABLE_PIP_VERSION_CHECK']='1'
    subprocess.run([sys.executable,'-m','pip','download','--disable-pip-version-check',
                    '--no-deps','--only-binary=:all:','--dest',str(wheelhouse),
                    '-r',str(requirement_file)], check=True, timeout=900, env=pip_env)
    wheel_files=list(wheelhouse.iterdir())
    require(len(wheel_files)==1 and wheel_files[0].is_file() and
            not wheel_files[0].is_symlink() and wheel_files[0].suffix=='.whl',
            'SciPy wheelhouse must contain one pinned wheel')
    wheel_sha={wheel_files[0].name:sha(wheel_files[0])}
    subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check',
                    '--no-index','--no-deps','--no-compile','--target',str(dest),
                    '--find-links',str(wheelhouse),'-r',str(requirement_file)],
                   check=True,timeout=900,env=pip_env)
    require((dest/'scipy/__init__.py').is_file(),'installed SciPy overlay incomplete')
    for pth in dest.rglob('*.pth'):
        require(not pth.is_symlink() and all(not l.lstrip().startswith('import ')
                for l in pth.read_text().splitlines()),'executable .pth in SciPy overlay')
    tree_hash,counts=seal_tree(dest)
    require(counts['hardlink_files']==0,'SciPy overlay has shared hardlinks')
    meta={'schema':'EXP07_TREETIME_SCIPY_SYNTHETIC_OVERLAY_V1',
          'status':'SYNTHETIC_DEPENDENCY_RECOVERY_ONLY',
          'underlying_treetime_version':'0.12.1',
          'source_environment_unchanged':True,'frozen_authorization_unchanged':True,
          'requirements':['scipy==1.14.0'],
          'requirements_sha256':hashlib.sha256(content.encode()).hexdigest(),
          'wheel_sha256':wheel_sha,'overlay_tree_sha256':tree_hash,
          'overlay_hardlinks':0,'overlay_files':counts['files'],
          'wheel_installation':'offline_no_index_no_deps_from_wheelhouse'}
    with manifest.open('x') as stream:
        json.dump(meta,stream,sort_keys=True,indent=2);stream.write('\n')
    print('PASS | independently pinned TreeTime SciPy overlay sealed: '+tree_hash,flush=True)
    return meta



def treetime_scoped_mpl_mount(root, method_env):
    """Mount only the independently sealed synthetic plotting package tree."""
    source = Path(root) / 'treetime_mpl_overlay_v6'
    dest = Path(method_env).parent / 'treetime-exp07-synthetic-mpl'
    require(source.is_dir() and not source.is_symlink(), 'TreeTime plotting overlay missing')
    for pkg in ('matplotlib', 'contourpy', 'cycler', 'fontTools', 'kiwisolver',
                'packaging', 'PIL', 'pyparsing'):
        require((source/pkg).is_dir() and not (source/pkg).is_symlink(),
                'TreeTime plotting overlay missing package: '+pkg)
    return {str(dest):str(source)},str(dest)


def prepare_treetime_mpl_overlay(root, allow_download):
    """Explicit synthetic-only pinned matplotlib wheels and dependency seal.

    Does not mutate TreeTime, PastML, SciPy, or any frozen environment. On
    resume, SHA-256-validate every original wheel and the installed overlay.
    """
    dest=Path(root)/'treetime_mpl_overlay_v6'
    wheelhouse=Path(root)/'treetime_mpl_wheels_v6'
    manifest=Path(root)/'treetime_mpl_overlay_v6_manifest.json'
    requirement_file=Path(root)/'treetime_mpl_overlay_v6_requirements.txt'
    content='\n'.join(MPL_REQUIREMENTS)+'\n'
    require(not any(p.is_symlink() for p in (dest,wheelhouse,manifest,requirement_file)),
            'TreeTime plotting overlay symlinked path')
    if manifest.is_file():
        require(dest.is_dir() and wheelhouse.is_dir() and requirement_file.is_file(),
                'partial TreeTime plotting overlay')
        meta=json.loads(manifest.read_text())
        digest,counts=seal_tree(dest)
        require(meta.get('schema')=='EXP07_TREETIME_MPL_SYNTHETIC_OVERLAY_V1' and
                meta.get('overlay_tree_sha256')==digest and
                requirement_file.read_text()==content and
                meta.get('requirements_sha256')==hashlib.sha256(content.encode()).hexdigest() and
                tuple(meta.get('requirements',()))==MPL_REQUIREMENTS and
                counts['hardlink_files']==0,
                'TreeTime plotting overlay manifest integrity drift')
        require(len(meta.get('wheel_sha256',{}))==len(MPL_REQUIREMENTS),
                'TreeTime plotting wheel count mismatch')
        actual_names={p.name for p in wheelhouse.iterdir() if p.is_file() and not p.is_symlink()}
        require(actual_names==set(meta['wheel_sha256']), 'plotting wheelhouse changed')
        for name,digest_expected in meta['wheel_sha256'].items():
            require(Path(name).name==name and (wheelhouse/name).is_file() and
                    sha(wheelhouse/name)==digest_expected,'TreeTime plotting wheel digest mismatch: '+name)
        treetime_scoped_mpl_mount(root,'/home/rwhite/branchsnv-comparator-envs/treetime-v0.12.1')
        print('PASS | TreeTime plotting overlay independently resealed: '+digest,flush=True)
        return meta
    require(allow_download,'TreeTime matplotlib dependency overlay missing: --prepare-treetime-mpl-overlay')
    require(sys.version_info[:2]==(3,10), 'Matplotlib preparation requires Python 3.10')
    require(root.is_dir() and root.stat().st_uid==os.getuid(), 'workspace owner mismatch')
    require(not any(p.exists() for p in (dest,wheelhouse,manifest,requirement_file)),
            'partial plotting overlay; refuse to overwrite')
    requirement_file.write_text(content)
    wheelhouse.mkdir(mode=0o700)
    dest.mkdir(mode=0o700)
    pip_env=os.environ.copy();pip_env['PIP_DISABLE_PIP_VERSION_CHECK']='1'
    print('PREPARING | pinned synthetic-only TreeTime matplotlib dependency wheels',flush=True)
    subprocess.run([sys.executable,'-m','pip','download','--disable-pip-version-check',
                    '--no-deps','--only-binary=:all:','--dest',str(wheelhouse),
                    '-r',str(requirement_file)],check=True,timeout=900,env=pip_env)
    wheels=list(wheelhouse.iterdir())
    require(len(wheels)==len(MPL_REQUIREMENTS) and all(p.is_file() and
            not p.is_symlink() and p.suffix=='.whl' for p in wheels),
            'TreeTime plotting wheel count or wheel type invalid')
    wheel_sha={p.name:sha(p) for p in sorted(wheels)}
    subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check',
                    '--no-index','--no-deps','--no-compile','--target',str(dest),
                    '--find-links',str(wheelhouse),'-r',str(requirement_file)],
                   check=True,timeout=900,env=pip_env)
    for pth in dest.rglob('*.pth'):
        require(not pth.is_symlink() and all(not line.lstrip().startswith('import ')
                for line in pth.read_text().splitlines()),'executable .pth in plotting overlay')
    treetime_scoped_mpl_mount(root,'/home/rwhite/branchsnv-comparator-envs/treetime-v0.12.1')
    tree_hash,counts=seal_tree(dest)
    require(counts['hardlink_files']==0, 'TreeTime plotting overlay hardlinks detected')
    meta={'schema':'EXP07_TREETIME_MPL_SYNTHETIC_OVERLAY_V1',
          'status':'SYNTHETIC_DEPENDENCY_RECOVERY_ONLY',
          'underlying_treetime_version':'0.12.1',
          'source_environment_unchanged':True,'frozen_authorization_unchanged':True,
          'requirements':list(MPL_REQUIREMENTS),
          'requirements_sha256':hashlib.sha256(content.encode()).hexdigest(),
          'wheel_sha256':wheel_sha,'overlay_tree_sha256':tree_hash,
          'overlay_hardlinks':0,'overlay_files':counts['files'],
          'wheel_installation':'offline_no_index_no_deps_from_wheelhouse'}
    with manifest.open('x') as fp:
        json.dump(meta,fp,sort_keys=True,indent=2);fp.write('\n')
    print('PASS | TreeTime plotting dependency overlay sealed: '+tree_hash,flush=True)
    return meta

def main():
    parser=argparse.ArgumentParser(description='Truth-blind eight-method synthetic gate; NEVER canonical execution')
    parser.add_argument('--self-test',action='store_true',help='local pure validation only')
    parser.add_argument('--run-eight-synthetic',action='store_true',help='execute each pinned comparator with artificial inputs')
    parser.add_argument('--resume-workspace',type=Path,help='reuse sealed runtime snapshots; create fresh v6 synthetic plans')
    parser.add_argument('--prepare-pastml-overlay',action='store_true',help='prepare the existing synthetic-only PastML dependency overlay')
    parser.add_argument('--prepare-treetime-scipy-overlay',action='store_true',help='explicitly prepare isolated pinned SciPy 1.14.0 wheel')
    parser.add_argument('--prepare-treetime-mpl-overlay',action='store_true',help='prepare separate pinned matplotlib and plotting dependencies')
    args=parser.parse_args()
    if args.self_test:
        pure_tests();return
    require(args.run_eight_synthetic or args.prepare_pastml_overlay or args.prepare_treetime_scipy_overlay or args.prepare_treetime_mpl_overlay,
            'explicit synthetic or dependency overlay operation required')
    require(args.resume_workspace is not None, 'v6 requires validated existing snapshots via --resume-workspace')
    if args.run_eight_synthetic:
        require(not REPORT.exists() and not REPORT.is_symlink(), 'report already exists; no overwrite')
    runner,harness,auth=checked_repo()
    require(CANDIDATE.is_file(), 'candidate runtime tree seals missing')
    require(sha(CANDIDATE) == CANDIDATE_HASH,
            'candidate runtime tree report checksum differs from the audited source')
    candidate=json.loads(CANDIDATE.read_text())
    require(candidate.get('schema') == 'EXP07_RUNTIME_MOUNT_CANDIDATE_V1'
            and candidate.get('frozen_commit') == COMMIT,
            'candidate tree report schema or commit mismatch')
    for method in ENV_METHODS:
        source = candidate['runtime_environment_directories'][method]
        require(all(source['problem_counts'][name] == 0 for name in
                ('dangling_links','escaping_links','special_files',
                 'unreadable_files','unstable_files')),
                method + ': candidate reported non-permission integrity failures')
    require(Path('/usr/bin/bwrap').is_file(), 'bubblewrap absent')
    require(os.getuid()!=0, 'must execute as unprivileged user')
    # Each run uses fresh plans. With --resume-workspace, reuse ONLY sealed,
    # hardlink-independent runtime snapshots, not failed synthetic outputs.
    if args.resume_workspace is not None:
        root=args.resume_workspace.expanduser().absolute()
        require(root.parent == Path.home() and
                root.name.startswith('.branchsnv_exp07_eightmethod_'),
                'resume requires an existing private eight-method workspace directly in HOME')
        require(not root.is_symlink() and root.is_dir() and
                root.stat().st_uid == os.getuid() and
                stat.S_IMODE(root.stat().st_mode) == 0o700,
                'resume workspace must be privately owned, 0700 and not a symlink')
        workspace=root/'synthetic_v6';workspace.mkdir(mode=0o700)
        snapshots=root/'snapshots'
        require(snapshots.is_dir() and not snapshots.is_symlink(),
                'previous runtime snapshots not found')
        sentinel=root/'hidden_truth_sentinel.txt'
        require(sentinel.is_file() and not sentinel.is_symlink() and
                sentinel.read_text() == 'SYNTHETIC SENTINEL ONLY -- NO BENCHMARK DATA\n',
                'expected synthetic-only sentinel missing or changed')
    else:
        root=Path(tempfile.mkdtemp(prefix='.branchsnv_exp07_eightmethod_',dir=Path.home()))
        root.chmod(0o700)
        workspace=root/'synthetic_v6';workspace.mkdir(mode=0o700)
        snapshots=root/'snapshots';snapshots.mkdir(mode=0o700)
        sentinel=root/'hidden_truth_sentinel.txt'
        sentinel.write_text('SYNTHETIC SENTINEL ONLY -- NO BENCHMARK DATA\n')
    overlay_data=prepare_pastml_overlay(root, args.prepare_pastml_overlay)
    scipy_data=prepare_treetime_scipy_overlay(root,args.prepare_treetime_scipy_overlay)
    mpl_data=prepare_treetime_mpl_overlay(root,args.prepare_treetime_mpl_overlay)
    if not args.run_eight_synthetic:
        print('SYNTHETIC_OVERLAYS_READY=PASS; CANONICAL_RUNS_STARTED=0; NO_COMPARATORS_EXECUTED')
        return
    report={'schema':'EXP07_EIGHT_METHOD_ISOLATED_SYNTHETIC_V1', 'frozen_commit':COMMIT,
            'status':'INCOMPLETE','gate_revision':'v6-sealed-matplotlib-plotting-dependencies',
            'resuming_prior_snapshot':args.resume_workspace is not None,
            'canonical_runs_started':0,'canonical_inputs_read':False,
            'benchmark_truth_read':False,'scoring_performed':False,
            'canonical_execution_authorized':False, 'synthetic_workspace':str(root),
            'environment_snapshots':{},'methods':{}, 'pastml_overlay':overlay_data,
            'treetime_scipy_overlay':scipy_data, 'treetime_mpl_overlay':mpl_data,
            'limitations':['Synthetic scenarios only; no canonical input or truth access',
                           'ldd is not exhaustive for dlopen() and JVM/Python plugins',
                           'Production runtime closures and separate authorization are not frozen',
                           'PastML and TreeTime use sealed synthetic NumPy; TreeTime additionally uses sealed SciPy and Matplotlib plotting dependency overlays; NOT frozen environments' ]}
    try:
        for m in ENV_METHODS:
            dest=snapshots/m
            if args.resume_workspace is not None:
                print('REVALIDATING SNAPSHOT | '+m,flush=True)
                expected=candidate['runtime_environment_directories'][m]['tree_content_seal_sha256']
                actual,counts=seal_tree(dest)
                require(actual==expected and counts['hardlink_files']==0,
                        m+': reused snapshot drift or unexpected hardlink')
                report['environment_snapshots'][m]={
                    'source_sha256':expected,'snapshot_sha256':actual,
                    'source_files':counts['files'],'snapshot_hardlinks':0,
                    'source_permission_warnings':counts['writable_mode_warnings'],
                    'reused_independently_sealed_snapshot':True,
                    'original_source_rehashed_on_resume':False}
                print('PASS | '+m+' independently resealed snapshot; no hardlinks',flush=True)
            else:
                print('SNAPSHOTTING | '+m,flush=True)
                report['environment_snapshots'][m]=snapshot_environment(m,dest,auth,candidate)
                print('PASS | '+m+' source and independent snapshot seals; no hardlinks',flush=True)
        config=auth['runtime_config']
        for method in METHODS:
            try:
                print('SYNTHETIC | '+method,flush=True)
                stage=workspace/method;stage.mkdir(mode=0o700)
                inp=stage/'public_input'
                synthetic_input(runner,inp)
                inputs=runner.scenario_inputs_from_directory('SYNTHETIC_EXP07_'+method,inp)
                plan=runner.build_command_plan(method=method,inputs=inputs,runtime_config=config,
                                               plan_root=stage/'plan',scenario_seed=271828182)
                native=plan.native_dir;generated=plan.generated_dir
                mounts={}
                if method in ENV_METHODS:
                    mounts[config[method]['environment_dir']]=str(snapshots/method)
                if method=='HomoplasyFinder':
                    jre=Path(config[method]['java']).parents[1]
                    mounts[str(jre)]=str(jre) # synthetic-only, production tree still unsealed
                    require(TZDB.is_file() and not TZDB.is_symlink(), 'external Java tzdb missing or symlinked')
                if method in ('PastML','TreeTime'):
                    overlay_dest=str(Path(config[method]['environment_dir']).parent/
                                     (method.lower()+'-exp07-synthetic-overlay'))
                    mounts[overlay_dest]=str(root/'pastml_overlay_v3')
                treetime_scipy_path=None
                treetime_mpl_path=None
                if method=='POUTINE':
                    compiled=Path(config[method]['script']).parent/'compiled'
                    require(compiled.is_dir() and not compiled.is_symlink(), 'POUTINE compiled classes absent')
                    mounts[str(compiled)]=str(compiled) # synthetic-only source mount
                if method=='TreeTime':
                    scipy_mounts,treetime_scipy_path=treetime_scoped_scipy_mounts(
                        root,config[method]['environment_dir'])
                    require(not set(mounts).intersection(scipy_mounts),
                            'TreeTime SciPy synthetic mount destinations overlap')
                    mounts.update(scipy_mounts)
                    mpl_mounts,treetime_mpl_path=treetime_scoped_mpl_mount(
                        root, config[method]['environment_dir'])
                    require(not set(mounts).intersection(mpl_mounts),
                            'TreeTime plotting mount destination overlap')
                    mounts.update(mpl_mounts)
                extra,tree_dest=file_dependency_mounts(method,auth,snapshots,root/'pastml_overlay_v3')
                env=runner.build_subprocess_environment(plan=plan,runtime_config=config)
                allowed={k:v for k,v in env.items() if k in ('PYTHONNOUSERSITE','OMP_NUM_THREADS',
                            'OPENBLAS_NUM_THREADS','PYTHONHASHSEED')}
                allowed.update({'HOME':str(native), 'TMPDIR':'/tmp','LANG':'C',
                                'PATH': ((str(Path(config[method]['environment_dir'])/'bin')+':')
                                         if method in ENV_METHODS else '')+'/usr/bin:/bin'})
                if method=='POUTINE':
                    allowed['LD_LIBRARY_PATH']=str(Path(config[method]['environment_dir'])/'lib/jvm/lib')
                if method in ('PastML','TreeTime'):
                    allowed['PYTHONPATH']=(overlay_dest if method=='PastML' else
                                           overlay_dest+':'+treetime_scipy_path+':'+treetime_mpl_path)
                if method=='TreeTime':
                    allowed['MPLCONFIGDIR']='/tmp/matplotlib'
                input_file=inp/'alignment.fasta'
                binary={'ARPIP':config['ARPIP']['executable'],'FastML':config['FastML']['executable'],
                        'HomoplasyFinder':config['HomoplasyFinder']['java'],
                        'PAML':config['PAML']['executable'], 'PastML':config['PastML']['executable'],
                        'POUTINE':config['POUTINE']['script'],'SNPPar':config['SNPPar']['executable'],
                        'TreeTime':config['TreeTime']['executable']}[method]
                effective_argv=synthetic_only_effective_argv(method,plan.argv)
                argv=bwrap_args(mounts,extra,{str(inp):str(inp),str(generated):str(generated)},
                                {str(native):str(native)},str(native),effective_argv,allowed)
                check_synthetic_sandbox(method,argv,sentinel,input_file,binary,native)
                print('PASS | '+method+' private root + synthetic truth denial',flush=True)
                captured={}
                def executor(p, e, timeout):
                    # Always attest frozen plan identity; the only effective
                    # command difference is the explicit POUTINE synthetic-only
                    # --force-overwrite workaround, recorded in the report.
                    # Never fallback to host executor.
                    require(p.argv==plan.argv and p.scenario_id.startswith('SYNTHETIC_'),
                            'synthetic plan identity changed')
                    result=spawn(argv,timeout,native)
                    captured.update(result)
                    diagnostic=result['stderr'].lower()
                    if (result['returncode'] in (126,127) or diagnostic.startswith('bwrap:')
                            or 'error while loading shared libraries' in diagnostic):
                        raise GateError('sandbox/loader launch failure for '+method+': '+result['stderr'][:500])
                    return runner.ExecutionOutcome(returncode=result['returncode'],
                       stdout=result['stdout'],stderr=result['stderr'],timed_out=result['timed_out'])
                normalized=runner.execute_command_plan(plan=plan,inputs=inputs,
                              runtime_config=config,timeout_seconds=(300 if method=='POUTINE' else 150),
                              executor=executor)
                report['methods'][method]={'truth_isolation':'PASS',
                    'status':normalized.get('status'),'failure_type':normalized.get('failure_type'),
                    'exit_code':captured.get('returncode'), 'timed_out':captured.get('timed_out'),
                    'elapsed_seconds':captured.get('elapsed_seconds'),
                    'runner_record':str(plan.plan_root/'execution.json'),
                    'runner_record_sha256':sha(plan.plan_root/'execution.json'),
                    'os_file_mounts':len(extra),
                    'os_file_mount_identities':{dest:sha(source) for dest,source in sorted(extra.items())},
                    'runtime_directory_mounts':sorted(mounts),
                    'synthetic_overlay_applied':method in ('PastML','TreeTime'),
                    'treetime_synthetic_scipy_from_sealed_wheel_overlay':method=='TreeTime',
                    'treetime_synthetic_matplotlib_from_sealed_wheel_overlay':method=='TreeTime',
                    'frozen_plan_argv':list(plan.argv),
                    'effective_synthetic_argv':effective_argv,
                    'effective_argv_matches_frozen_plan':effective_argv==list(plan.argv),
                    'synthetic_only_poutine_existing_outdir_override':method=='POUTINE',
                    'production_poutine_runner_outdir_contract_unresolved':method=='POUTINE',
                    'dynamic_elf_probe_policy':'known-pinned-native-wheels-and-jvm-libjvm-only',
                    'comparator_executed_on_synthetic_input':True,
                    'sandbox_environment':allowed,
                    'frozen_runner_used_custom_sandbox_executor':True}
                print(('PASS' if normalized.get('status')=='SUCCESS' else 'FAILED') +
                      ' | '+method+' comparator '+str(normalized.get('status'))+
                      ' | '+str(normalized.get('failure_type')),flush=True)
            except GateError as exc:
                reason=str(exc)
                # Method-scoped loader failures must never fall back to host
                # execution. Record the blocked comparator and continue to
                # obtain independent diagnostic coverage for later methods.
                # Security/isolation failures remain fatal for the entire run.
                recoverable=('missing dynamic dependency', 'ldd failed',
                             'sandbox/loader launch failure',
                             'POUTINE libjli.so absent')
                if not reason.startswith(recoverable):
                    raise
                report['methods'][method]={
                    'status':'BLOCKED_INFRASTRUCTURE',
                    'failure_type':'method_scoped_loader_failure',
                    'blocking_error':reason,
                    'comparator_execution_authorized':False,
                    'synthetic_input_only':True,
                    'truth_isolation':'NOT_ESTABLISHED',
                }
                print('BLOCKED | '+method+' runtime: '+reason[:280],flush=True)
        report['status']= ('ALL_EIGHT_SYNTHETIC_RUNS_SUCCESSFUL' if
                           all(row['status']=='SUCCESS' for row in report['methods'].values())
                           else 'INCOMPLETE_SYNTHETIC_COMPARATOR_RESULTS')
    except Exception as exc:
        report['status']='BLOCKED_INFRASTRUCTURE_OR_INTEGRITY'
        report['blocking_error']=type(exc).__name__+': '+str(exc)
        print('BLOCKED | '+report['blocking_error'],flush=True)
    finally:
        with REPORT.open('x') as fp:
            json.dump(report,fp,sort_keys=True,indent=2);fp.write('\n')
        print('EIGHT_METHOD_SYNTHETIC_GATE_V6='+report['status'])
        print('CANONICAL_RUNS_STARTED=0')
        print('CANONICAL_EXECUTION_AUTHORIZED=FALSE')
        print('REPORT='+str(REPORT))
        print('WORKSPACE='+str(root))
    if report['status']!='ALL_EIGHT_SYNTHETIC_RUNS_SUCCESSFUL':
        raise SystemExit(2)

def pure_tests():
    require(PASTML_OVERLAY_REQUIREMENTS[0]=='numpy==1.26.4', 'fixed wheel versions')
    require(MPL_REQUIREMENTS[0]=='matplotlib==3.8.4' and len(MPL_REQUIREMENTS)==8, 'fixed plotting wheel versions')
    require(str(TZDB)=='/usr/share/javazi-1.8/tzdb.dat', 'tzdb path')
    frozen=('poutine.sh','--out-dir','/synthetic/native')
    amended=synthetic_only_effective_argv('POUTINE',frozen)
    require(amended==list(frozen)+['--force-overwrite'] and list(frozen)==list(frozen),
            'synthetic-only POUTINE override regression')
    require(synthetic_only_effective_argv('TreeTime',('treetime','--help'))==['treetime','--help'],
            'foreign comparator argv mutated')
    require(METHODS==tuple(['ARPIP','FastML','HomoplasyFinder','PAML',
                            'PastML','POUTINE','SNPPar','TreeTime']), 'frozen method list')
    require(not is_beneath(Path('/tmp/test'),Path('/home')), 'unexpected containment')
    require(is_beneath(Path('/a/b'),Path('/a')), 'containment mismatch')
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)
        (p/'sub').mkdir();(p/'sub'/'file').write_text('abc')
        h,c=seal_tree(p)
        require(len(h)==64 and c['files']==1 and c['directories']==1, 'seal logic failure')
        (p/'sub'/'escape').symlink_to('/etc/passwd')
        try: seal_tree(p)
        except GateError: pass
        else: raise AssertionError('escaping symlink not rejected')
        (p/'sub'/'escape').unlink()
        (p/'data').mkdir(); (p/'work').mkdir()
        ok=bwrap_args({}, {'/bin/sh':'/bin/sh'}, {'/data':str(p/'data')}, {'/work':str(p/'work')},
                      '/work', ['/bin/sh','-c','exit 0'], {'HOME':'/work','PATH':'/bin'})
        require('--tmpfs' in ok and '--unshare-net' in ok and '--ro-bind' in ok,
                'sandbox flags omitted')
        directory_nodes=[ok[i+1] for i,arg in enumerate(ok[:-1]) if arg=='--dir']
        require('/bin' in directory_nodes and '/bin/sh' not in directory_nodes,
                'file mount destination accidentally declared a directory')
        require('/data' in directory_nodes and '/work' in directory_nodes,
                'directory mount destination missing')
        require(ok.count('/bin/sh') >= 2,
                'shell file mount or executable missing')
        for malicious in ({'/':'/'},{'/home':'/home'}):
            try: bwrap_args(malicious,{}, {}, {},'/work',['/bin/sh'],{})
            except GateError: pass
            else: raise AssertionError('unsafe mount accepted')
        try: bwrap_args({'/x':'/x'}, {}, {'/x/data':'/y'}, {}, '/work',['/bin/sh'],{})
        except GateError: pass
        else: raise AssertionError('overlap accepted')
    print('PASS | pure schema, tree seal, symlink escapes, private-root mounts, overlaps')
    # Under a synthetic root, an external tzdb leaf mount must remain a file mount.
    require('LD_LIBRARY_PATH' in ('LD_LIBRARY_PATH',), 'explicit loader-path allowlist')
    print('SELF_TEST_V6=PASS; NO_COMPARATORS_EXECUTED; NO_CANONICAL_ACCESS')

if __name__=='__main__':
    main()
