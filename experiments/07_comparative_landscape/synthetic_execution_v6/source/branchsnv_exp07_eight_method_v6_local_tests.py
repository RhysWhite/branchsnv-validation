"""Pure, non-comparator regression for the v6 synthetic-only TreeTime wheel overlay."""
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

source=Path(__file__).with_name('branchsnv_exp07_eight_method_synthetic_gate_v6.py')
spec=importlib.util.spec_from_file_location('exp07_synthetic_v6',source)
v6=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v6)

assert v6.MPL_REQUIREMENTS == (
    'matplotlib==3.8.4','contourpy==1.2.1','cycler==0.12.1',
    'fonttools==4.53.1','kiwisolver==1.4.5','packaging==24.1',
    'pillow==10.4.0','pyparsing==3.1.2')
assert v6.REPORT.name.endswith('-v6.json')
assert v6.synthetic_only_effective_argv('TreeTime', ['treetime','ancestral'])==['treetime','ancestral']
assert v6.synthetic_only_effective_argv('POUTINE',['poutine','--out-dir','/tmp/o']) == [
    'poutine','--out-dir','/tmp/o','--force-overwrite']
print('PASS | plotting wheel pins and frozen command behavior')

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    overlay=root/'treetime_mpl_overlay_v6'
    for pkg in ('matplotlib','contourpy','cycler','fontTools','kiwisolver','packaging','PIL','pyparsing'):
        (overlay/pkg).mkdir(parents=True)
    (overlay/'matplotlib/__init__.py').write_text('')
    m,d=v6.treetime_scoped_mpl_mount(root, '/home/rwhite/branchsnv-comparator-envs/treetime-v0.12.1')
    assert list(m)==[d] and m[d]==str(overlay)
    assert d.startswith('/home/rwhite/branchsnv-comparator-envs/')
    print('PASS | synthetic plotting overlay mounted only at method-scoped destination')

    wheelhouse=root/'treetime_mpl_wheels_v6';wheelhouse.mkdir()
    checks={}
    for i in range(8):
        wheel=wheelhouse/f'pinned-wheel-{i}.whl';wheel.write_bytes(f'wheel-{i}'.encode())
        checks[wheel.name]=v6.sha(wheel)
    req=root/'treetime_mpl_overlay_v6_requirements.txt'
    content='\n'.join(v6.MPL_REQUIREMENTS)+'\n'
    req.write_text(content)
    digest,counts=v6.seal_tree(overlay)
    (root/'treetime_mpl_overlay_v6_manifest.json').write_text(json.dumps({
        'schema':'EXP07_TREETIME_MPL_SYNTHETIC_OVERLAY_V1',
        'overlay_tree_sha256':digest,
        'requirements_sha256':hashlib.sha256(content.encode()).hexdigest(),
        'requirements':list(v6.MPL_REQUIREMENTS),
        'wheel_sha256':checks}))
    v6.prepare_treetime_mpl_overlay(root,False)
    print('PASS | independent wheel hashes and plotting overlay seal verified')
    next(iter(wheelhouse.iterdir())).write_bytes(b'tamper')
    try:
        v6.prepare_treetime_mpl_overlay(root,False)
    except v6.GateError as err:
        assert 'digest mismatch' in str(err)
    else:
        raise AssertionError('tampered wheel accepted')
    print('PASS | tampered wheel rejected')

    (overlay/'PIL').rename(overlay/'PIL-disabled')
    try:
        v6.treetime_scoped_mpl_mount(root, '/home/rwhite/branchsnv-comparator-envs/treetime-v0.12.1')
    except v6.GateError as err:
        assert 'missing package' in str(err)
    else:
        raise AssertionError('missing plotting dependency accepted')
    print('PASS | missing plotting package rejected')

    # Synthetic stand-in compiled modules let us exercise ELF probe coverage
    # without executing the method or mounting anything from actual host data.
    (overlay/'PIL-disabled').rename(overlay/'PIL')
    snapshot_roots=root/'snapshots'
    old_overlay=root/'pastml_overlay_v3'
    num=old_overlay/'numpy/core/_multiarray_umath.cpython-310-x86_64-linux-gnu.so'
    sci=root/'treetime_scipy_overlay_v5/scipy/sparse/_sparsetools.cpython-310-x86_64-linux-gnu.so'
    modules=[num,sci]
    for pkg,name in [
        ('matplotlib','_path.cpython-310-x86_64-linux-gnu.so'),
        ('matplotlib','ft2font.cpython-310-x86_64-linux-gnu.so'),
        ('contourpy','_contourpy.cpython-310-x86_64-linux-gnu.so'),
        ('kiwisolver','_cext.cpython-310-x86_64-linux-gnu.so'),
        ('PIL','_imaging.cpython-310-x86_64-linux-gnu.so')]:
        modules.append(overlay/pkg/name)
    for file in modules:
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_bytes(b'\x7fELF stub')
    old_ldd=v6.ldd_closure
    probed=[]
    v6.ldd_closure=lambda path,library_search_path=None:(probed.append(str(path)) or set())
    auth={'runtime_config':{'TreeTime':{'environment_dir':'/home/rwhite/branchsnv-comparator-envs/treetime-v0.12.1'}},
          'runtime_files':{'TreeTime_executable':{'path':'/bin/sh'}}}
    binds,unused=v6.file_dependency_mounts('TreeTime',auth,snapshot_roots,old_overlay)
    v6.ldd_closure=old_ldd
    assert set(str(f) for f in modules).issubset(set(probed))
    assert not any(str(root) in path for path in binds)
    print('PASS | NumPy/SciPy and five plotting ELF probes; workspace leaves excluded')

    safe=v6.bwrap_args(m,{'/bin/sh':'/bin/sh'},
        {'/synthetic/input':str(root)}, {'/synthetic/output':str(root)},
        '/synthetic/output',['/bin/sh','-c','true'],
        {'PATH':'/usr/bin:/bin','MPLCONFIGDIR':'/tmp/matplotlib'})
    assert '--unshare-net' in safe and '--tmpfs' in safe and '--ro-bind' in safe
    for invalid in ({'/usr':str(root)},{'/home/rwhite':str(root)}):
        try: v6.bwrap_args(invalid,{}, {}, {},'/synthetic/output',['/bin/sh'],{})
        except v6.GateError: pass
        else: raise AssertionError('unsafe mount destination allowed')
    print('PASS | private root and malicious destination rejection')

print('LOCAL_V6_TESTS=PASS; NO_COMPARATORS_EXECUTED; NO_CANONICAL_ACCESS')
