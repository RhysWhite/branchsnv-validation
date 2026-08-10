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

mkdir -p "$OUTPUT_ROOT"

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
