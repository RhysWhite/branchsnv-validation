#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 /path/to/branchsnv [public-input-dir]" >&2
  exit 2
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BRANCHSNV_ROOT=$1
PUBLIC_INPUT_DIR=${2:-"$ROOT/public_inputs/03_published_datasets"}
OUTPUT_ROOT=${BRANCHSNV_VALIDATION_OUTPUT_ROOT:-"$ROOT/reproduced_results"}
BENCHMARK_REPETITIONS=${BRANCHSNV_BENCHMARK_REPETITIONS:-3}
EMPIRICAL_INPUT_DIR="$ROOT/inputs/empirical"

# Exclude per-user site packages so the active validation environment is authoritative.
export PYTHONNOUSERSITE=1

OUTPUT_ROOT=$(python - "$OUTPUT_ROOT" "$ROOT" <<'PY'
from pathlib import Path
import sys

output = Path(sys.argv[1]).expanduser().resolve()
root = Path(sys.argv[2]).resolve()
canonical = (root / "results").resolve()
try:
    output.relative_to(canonical)
except ValueError:
    pass
else:
    raise SystemExit(f"Refusing to write reproduced results into canonical snapshot tree: {output}")

if output.is_relative_to(root):
    allowed = (root / "reproduced_results").resolve()
    try:
        output.relative_to(allowed)
    except ValueError:
        raise SystemExit(
            "Validation outputs inside the repository must be under "
            f"{allowed}; got {output}"
        )
print(output)
PY
)

if [[ -e "$OUTPUT_ROOT" ]]; then
  if [[ ! -d "$OUTPUT_ROOT" ]]; then
    echo "Validation output path exists and is not a directory: $OUTPUT_ROOT" >&2
    exit 2
  fi
  if [[ -n "$(find "$OUTPUT_ROOT" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    echo "Refusing to reuse non-empty validation output directory: $OUTPUT_ROOT" >&2
    echo "Remove it explicitly or set BRANCHSNV_VALIDATION_OUTPUT_ROOT to a new directory." >&2
    exit 2
  fi
else
  mkdir -p "$OUTPUT_ROOT"
fi

python - <<'PY'
import sys
import numba
import numpy
import pandas

expected = {"numpy": "2.3.5", "pandas": "2.2.3", "numba": "0.65.1"}
observed = {"numpy": numpy.__version__, "pandas": pandas.__version__, "numba": numba.__version__}
if observed != expected:
    raise SystemExit(f"Locked Experiment 06 dependency versions required: expected {expected}, observed {observed}")
if sys.version_info < (3, 10):
    raise SystemExit(f"Python 3.10 or later is required; observed {sys.version.split()[0]}")
print(f"Validation environment: Python {sys.version.split()[0]}; NumPy {numpy.__version__}; pandas {pandas.__version__}; Numba {numba.__version__}")
PY

python "$ROOT/experiments/01_exact_oracle/run.py" \
  --branchsnv-root "$BRANCHSNV_ROOT" \
  --output-dir "$OUTPUT_ROOT/01_exact_oracle"

python "$ROOT/experiments/02_deliberate_faults/run.py" \
  --branchsnv-root "$BRANCHSNV_ROOT" \
  --output-dir "$OUTPUT_ROOT/02_deliberate_faults"

python "$ROOT/experiments/03_published_datasets/download_public_inputs.py" \
  --output-dir "$PUBLIC_INPUT_DIR"

python "$ROOT/experiments/03_published_datasets/run.py" \
  --branchsnv-root "$BRANCHSNV_ROOT" \
  --public-input-dir "$PUBLIC_INPUT_DIR" \
  --output-dir "$OUTPUT_ROOT/03_published_datasets"

python "$ROOT/experiments/04_scalability/generate_inputs.py" \
  --output-root "$ROOT/experiments/04_scalability/inputs"

python "$ROOT/experiments/04_scalability/run.py" \
  --validation-root "$ROOT" \
  --branchsnv-source "$BRANCHSNV_ROOT" \
  --repetitions "$BENCHMARK_REPETITIONS" \
  --results-dir "$OUTPUT_ROOT/04_scalability"

python "$ROOT/experiments/04_scalability/summarize_models.py" \
  --summary "$OUTPUT_ROOT/04_scalability/benchmark_summary.tsv" \
  --output "$OUTPUT_ROOT/04_scalability/scaling_models.tsv"

if python -c 'import matplotlib' >/dev/null 2>&1; then
  python "$ROOT/experiments/04_scalability/plot_results.py" \
    --summary "$OUTPUT_ROOT/04_scalability/benchmark_summary.tsv" \
    --output-dir "$OUTPUT_ROOT/04_scalability/figures"
else
  echo "Matplotlib is unavailable; Experiment 04 figures were not regenerated." >&2
fi

python "$ROOT/experiments/05_published_focal_branches/run.py" \
  --branchsnv-root "$BRANCHSNV_ROOT" \
  --input-dir "$EMPIRICAL_INPUT_DIR" \
  --output-dir "$OUTPUT_ROOT/05_published_focal_branches"

python "$ROOT/experiments/06_empirical_cross_classification/run.py" \
  --branchsnv-root "$BRANCHSNV_ROOT" \
  --input-dir "$EMPIRICAL_INPUT_DIR" \
  --output-dir "$OUTPUT_ROOT/06_empirical_cross_classification"

python "$ROOT/experiments/06_empirical_cross_classification/production_qc.py" \
  --branchsnv-root "$BRANCHSNV_ROOT" \
  --input-dir "$EMPIRICAL_INPUT_DIR" \
  --analysis-results-dir "$OUTPUT_ROOT/06_empirical_cross_classification"

python "$ROOT/experiments/06_empirical_cross_classification/verify.py" \
  --results-dir "$OUTPUT_ROOT/06_empirical_cross_classification"

python "$ROOT/verify_reproduced_results.py" \
  --results-dir "$OUTPUT_ROOT" \
  --branchsnv-root "$BRANCHSNV_ROOT" \
  --benchmark-repetitions "$BENCHMARK_REPETITIONS"
