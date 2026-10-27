#!/usr/bin/env python3
"""Rebuild publication figures in scratch space, compare, never overwrite the release."""
from pathlib import Path
import hashlib, shutil, subprocess, tempfile, sys
HERE=Path(__file__).resolve().parent
NAMES=['BRANCHSNV_Exp07_MAIN_FIGURE','BRANCHSNV_Exp07_SUPPLEMENTARY_FIGURE']
REQUIRED=['plot_final_figures.py','BRANCHSNV_Experiment07_FINAL_RESULTS.tar.gz',
          'paired_stratum_bootstrap_differences.csv','recurrent_scenario_bootstrap_differences.csv']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='branchsnv_figures_') as d:
    out=Path(d)
    for name in REQUIRED:shutil.copy2(HERE/name,out/name)
    subprocess.run([sys.executable,str(out/'plot_final_figures.py')],cwd=out,check=True,timeout=600)
    for base in NAMES:
        for extension in ('pdf','svg','png'):
            filename=base+'.'+extension
            wanted=HERE/'figures'/filename
            actual=out/'figures'/filename
            if not actual.exists() or sha(wanted)!=sha(actual):
                raise SystemExit(f'FIGURE_RERENDER_DIFFERENCE {filename}; original artwork unchanged')
    print('SCRATCH_FIGURE_REBUILD=PASS (both figures × PDF/SVG/PNG)')
