# Experiment 07 — nine same-host native replay evidence pairs

**Scope:** Nine selected original/fresh execution pairs from the 900-job extension: six S002 runs (all six comparator workflows) and three S011 positive recurrent-site runs (HomoplasyFinder, POUTINE, SNPPar). All nine fresh and original `predictions.json` files have identical SHA-256 digests, as checked against the retained original and fresh `execution_result.json` receipts. The aggregate matching calls are **226 branch events** and **58 recurrent sites**. These totals count reconstructed calls, **not** independently verified true positives.

Source: `BRANCHSNV_Exp07_NINE_REPLAY_EVIDENCE_CANDIDATE_20261027.zip`, SHA-256 `0a9796261f5b4dc23fb61cb3ab1cac08a0ef791367e4cf36e3ebbd3edf84ae33`, collected 2026-10-27. The nine replays used the original Jynx host, existing comparator executable/runtime installations, frozen original input datasets, and isolated fresh output directories.

## Contents

- `MANIFEST.json`: selected jobs, canonical alignment/tree **hash claims**, full source identities, nine prediction and receipt checksum identities, reviewed executable pins.
- `runs/{method}/{scenario}/{original,fresh}/{execution_result,predictions}.json`: **unaltered** original and fresh execution records and predictions, including native executable arguments and paths.
- `executor/`: **exact archived** `exp07_execute.py`, `generator.py`, 900-job manifest, runtime configuration and reviewed runtime pins.
- `raw_log_hashes.tsv`: SHA-256s of **excluded** original and fresh stdout/stderr files. The raw log bytes are not committed in this subtree; see the source ZIP.
- `verify_nine_native_replays.py`: independent, library-free checksum + result reconciliation verifier.
- `SHA256SUMS`: integrity manifest for the retained files.

The exact *final* `frozen_runner.py` and `adapters.py` already exist at `../native_execution_provenance_v1/source_versions/{runner_final,adapter_final}.py`; their SHA-256s and all selected receipt references are checked by this verifier, so redundant copies were omitted. Source identities link to the 900-run provenance matrix but do not replace the historical matrix.

Run at repository root:

```bash
python3 publication_audits/experiment07/native_replay_pilot_v1/verify_nine_native_replays.py
```

## Boundaries and limitations

- **Same-host selected scenario replay**, not a fresh independent tool build, all-900 rerun, or reproduction of the separate original 300 external executions / 150 BRANCHSNV scenarios.
- Canonical input **hashes** and original job-manifest records are preserved here, not the actual FASTA/tree input bytes. Native tool binaries, installed environments and full generated outputs are not included. Executable pins are historical recorded hashes, **not independently reverified on CI**.
- All nine native return codes were zero; `truth_read=false` is an execution-record assertion, not a proof of source-code isolation from truth.
- Raw stdout/stderr bytes are preserved in the source ZIP, **not** in Git; their listed SHA-256 hashes cannot be recomputed from the repository alone.
- Paths in preserved execution receipts and runtime configuration expose the original local `/home/rwhite/` layout; these are historical data, not expected to work on a different machine.
- The separate SNPPar S001 recovered normalization lacks its original failed-record bytes; this panel intentionally avoids S001. Bubblewrap's separate binary pin differs from the current host binary and is not a directly recorded dependency in these nine native `argv` entries.
- The publication claim is limited to **nine original/fresh prediction pairs**, not validation of the entire benchmark by independent rerun.

This package is additive to the existing Experiment 07 provenance and does not alter frozen scores, figures, or historical result checksums.
