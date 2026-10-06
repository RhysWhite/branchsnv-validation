# SNPPar environment amendment v1

Authorized smoke testing showed that the initial SNPPar environment was not
consistent with SNPPar's declared dependency bounds and also exposed packages
from the user's Python site directory.

The SNPPar environment recipe is therefore amended to the tested dependency
combination:

- Python 3.8.20;
- Biopython 1.76;
- TreeTime 0.8.5;
- ETE3 3.1.3; and
- `PYTHONNOUSERSITE=1` during installation and execution.

The SNPPar release, exact source revision, command-line run contract and output
contract are unchanged. The source is not patched.

No other comparator recipe is changed.

This amendment does not authorize generation of the full 150-scenario dataset
or execution of the full comparator benchmark.

## Next gate

`RERUN_SNPPAR_AUTHORIZED_TOY_SMOKE_WITH_FROZEN_ENVIRONMENT_V1`
