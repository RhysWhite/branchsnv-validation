# Experiment 07 — Eight-method isolated synthetic execution (v6)

**Scope: synthetic execution evidence only.** No canonical S001–S150 scenario was run, no benchmark truth was read, and no scientific scoring was performed. This evidence supplements but does not modify the frozen Stage 5F implementation and does **not** authorize real comparator execution.

## Recorded result

Eight real third-party comparator processes exited successfully against artificial, four-tip inputs: ARPIP, FastML, HomoplasyFinder, PAML, PastML, POUTINE, SNPPar and TreeTime. The captured runner records report `SUCCESS`, finalized normalized predictions, and `truth_isolation=PASS` for the synthetic private-root checks. An independent verifier checks the preserved file bytes, outcome metadata, native outputs and normalized-prediction checksums; it does not rerun comparators or independently prove scientific prediction correctness.

The repository artifact is arranged under:

- `experiments/07_comparative_landscape/synthetic_execution_v6/source/`: unmodified v6 handoff source, self-tests, original README, and upstream source checksums.
- `experiments/07_comparative_landscape/synthetic_execution_v6/verify.py`: independent, standard-library-only offline verifier.
- `experiments/07_comparative_landscape/synthetic_execution_v6/test_verify.py`: regression and deliberate-tamper tests of the independent verifier.
- `results/07_comparative_landscape/eight_method_synthetic_v6/`: exact execution JSON, stdout/stderr, native output files, normalized predictions, fixture inputs, method summary, original execution log and SHA-256 manifest.

Run from repository root:

```bash
python3 experiments/07_comparative_landscape/synthetic_execution_v6/verify.py
python3 experiments/07_comparative_landscape/synthetic_execution_v6/test_verify.py
```

These checks run offline with Python's standard library only, take seconds, and never invoke a third-party comparator. They are suitable for a GitHub Actions integrity workflow.

## Interpretation and unresolved boundaries

1. **POUTINE command mismatch.** The v6 synthetic invocation uses `--force-overwrite` because the frozen runner pre-creates POUTINE's output directory. The source record contains both the frozen and effective argv; the synthetic exception does not validate or amend the frozen production plan. Production output-directory semantics require separate formal resolution.
2. **Runtime dependency overlays.** PastML and TreeTime succeeded using independently sealed *synthetic-only* dependency overlays absent from the original environments (NumPy, pandas, Jinja2, Biopython, SciPy and Matplotlib dependencies). Versions, tree seals and wheel digests are recorded in the top-level v6 report. This is not an approved production closure.
3. **Snapshot provenance.** Four runtime snapshots were independently resealed (reported zero shared hardlinks) during the resumed execution, but original host source trees were not rehashed in that particular run. The report retains the source hashes and warning counts from prior discovery; reproducing production runtime integrity requires fresh source-versus-snapshot verification.
4. **Dynamic dependencies.** `ldd`, representative extension checks and one synthetic run do not establish complete dynamic-loader or plugin closure for every canonical scenario.
5. **External POUTINE link.** The v6 native directory contained `compiled -> /home/rwhite/branchsnv-comparator-src/poutine-smoke/compiled`. This absolute, nonportable link is omitted from the publication tree, and its exact text is recorded in `EXCLUDED_HOST_SYMLINKS.json`. No contents behind this link are claimed verified or preserved.
6. **No scientific acceptance claim.** Successful exits and normalized-file checksums are execution/integrity evidence, not accuracy, sensitivity, specificity, or fairness measurements. The 1,200 canonical invocations, method-major ordering versus scenario-major enumeration, runtime closure and independent scoring all remain separate gates.

## Source and execution provenance

Original frozen harness commit: `8c6c0aeded8948160e88528809e4b147a7a20b15`.
Source is preserved byte-for-byte from the uploaded v6 handoff. The original v6 source `branchsnv-exp07-eight-method-v6.sha256` was checked before packaging. The integrity manifest covers the complete portable execution-results tree; the verifier additionally checks each runner-declared output against its original hash and size.

No absolute host paths in the original evidence have been rewritten; those paths are historical provenance, not portable re-execution instructions. The raw wheel archives and large environment snapshots are not embedded. Their SHA-256 identities and dependency version lists remain in the JSON report, but the reported tree seals cannot be recomputed from this small publication snapshot alone.

For source-to-output reproduction on another system, a separately provisioned and validated set of comparator runtimes is required. CI tests *verification of the preserved execution record*, not replay of third-party software.
