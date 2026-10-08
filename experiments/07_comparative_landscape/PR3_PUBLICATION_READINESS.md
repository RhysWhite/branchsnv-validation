# Experiment 07 — PR #3 publication review (pre-canonical execution)

Status: **DRAFT — NOT APPROVED FOR MERGE OR CANONICAL EXECUTION**.

Reviewed evidence branch anchor: `017fefe32e1b86c955b8957e1be6a4bdf49e7506`.
Original implementation freeze: `f48bd14048866820c7a252d935ed2d26cb9407e5`.
Base at read-only export (not a claim about current `main`): `4af4b120dabc27055b8146132e5846c0771ad337`.

## Review evidence and limits

- Independent synthetic-v6 evidence records eight successful artificial-input comparator workflows and eight isolation probes, **not** scientific accuracy estimates.
- The 8 original implementation-file SHA-256 hashes were checked on `jynx` against the original freeze commit and all matched. The current equivalents differ for five files in association with later committed changes; the original copies are retained in Git history.
- Original freeze validator `comparator_benchmark_execution_v1_implementation_freeze.py` **fails at the current head** at `IMPLEMENTATION.md` because it checks original content hashes. It must **not** be relabelled as a passing current-head freeze. The additive CI provenance check independently verifies original frozen Git objects, subsequent change counts and integrity of the reviewed v6 anchor; it does not replay the original validation program or adjudicate the legitimacy of every amendment.
- Historical harness authorization validator `comparator_benchmark_execution_v1_harness_implementation_authorization_freeze.py` **fails on this host** because `/home/rwhite/branchsnv-comparator-src/paml-smoke` does not exist. This remains an environment/provenance issue, not a PASS.
- PR #3 local publication review: 12 of 17 entries PASS, two FAIL as above, two require pinned arguments, and GitHub Actions status was not verified at report time. Python/JSON syntax parsing is not functional test coverage.
- `.gitignore` only adds exclusions for archived search evidence and canonical input/truth directories. It does not untrack already committed paths.

## Unclosed merge checks

1. **Credential review:** Eight credential-related tracked files and their history require **local human review**. Pattern scan reported zero candidates but is not proof of non-disclosure. If real secrets were ever exposed in public history, revoke/rotate them and consider controlled remediation.
2. **Canonical manifest:** `results/07_comparative_landscape/comparator_benchmark_dataset_v1/benchmark_dataset_manifest.tsv` remains unreviewed for publication suitability. This CI and local check **do not open** it or grant canonical truth/data access.
3. **Licenses and data provenance:** Review third-party comparator pins, literature/full-text redistribution, logs, and generated screening materials in the complete changed-path inventory.
4. **Independent validators and CI:** Record results for validators requiring external pinned release/reproduction arguments; confirm live GitHub checks before merge. Keep environment-dependent historical failure explanations distinct from true PASS.
5. **Full amendment chain:** Review all amendments and authorizations, including POUTINE output handling and method-major dispatch, rather than assuming a commit subject establishes scientific authorization.

## Production and interpretation boundaries

- Canonical dataset access, 1,200 production comparator calls, independent truth scoring, and benchmark accuracy comparisons remain **unauthorized**.
- POUTINE synthetic-v6 required an explicitly synthetic-only overwrite option; production output-directory handling is unresolved.
- Synthetic-only PastML/TreeTime dependency overlays and dynamic runtime closures need separate production assessment.
- Original scenario-major enumeration versus method-major dispatch requirement needs an independently documented scheduling resolution that preserves invocation identities.
- A 10,000-bp balanced-tree, fixed-event-site synthetic design does not establish broad generalizability to natural bacterial phylogenies. Comparator families may have shared dependencies and are not necessarily independent algorithmic validations.

## New additive CI check

`.github/workflows/exp07-pr3-historical-provenance.yml` runs a standard-library, offline Git object verification and negative regression tests. It makes only this narrow claim:

> Eight implementation artifacts match their original frozen SHA-256 hashes at the original freeze commit, their reviewed amendment *counts* match the documented repository history, and those artifact bytes and the original freeze validator have not changed since the reviewed v6 evidence anchor.

This check neither scans canonical files nor runs tools, and **does not** replace scientific authorization, site-specific historical environment verification, or human publication review. A green workflow **does not** authorize merge or canonical execution.
