# SNPPar environment amendment authorization

## Trigger

Smoke testing of SNPPar v1.2 initially failed during import because the test
environment contained Biopython 1.86 and exposed packages from the user's
Python site directory.

The frozen SNPPar source declares:

- Python >=3.6;
- Biopython >=1.66 and <=1.76;
- ETE3;
- TreeTime >=0.6.3 and <=0.8.6.

The selected TreeTime release remains 0.8.5.

A disposable resolution test demonstrated a functioning isolated environment
with:

- Python 3.8.20;
- Biopython 1.76;
- TreeTime 0.8.5;
- ETE3 3.1.3; and
- Python user-site packages disabled.

The legacy `Bio.Alphabet` interface required by SNPPar was available and the
SNPPar command-line help executed successfully.

## Authorized amendment

Only the SNPPar section of
`comparator_benchmark_execution_v1_impl/environment_recipes.json`
may be changed.

The amended environment must specify the tested dependency set above and must
disable Python user-site packages during installation and execution.

The frozen SNPPar source revision remains:

`0386df8edcff26faf242bc268c5f8865b09c9de9`

The source must not be patched.

## Explicit boundary

This authorization does not permit changes to SNPPar inference settings,
SNPPar output parsing, benchmark metrics, benchmark truth generation,
benchmark scenarios, other comparator environments or source revisions.

It does not authorize generation of the full 150-scenario dataset or execution
of the full benchmark.

## Next gate

`IMPLEMENT_AND_FREEZE_SNPPAR_ENVIRONMENT_AMENDMENT_V1`
