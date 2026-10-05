# Comparator benchmark feasibility v1

The source-backed pre-execution assessment covers all 29 frozen direct/near-direct method families. No comparator software was installed or executed.

## Result

- Quantitative benchmark candidates: **2** — SNPPar, TreeTime
- Endpoint-specific benchmark candidates: **6** — ARPIP, FastML, HomoplasyFinder, PAML, PastML, POUTINE
- Contextual comparators only: **21**
- Blocked-reproducibility: **0**
- Unresolved: **0**
- Total methods retained for a later executable benchmark design: **8**

The executable benchmark candidate set is therefore:

**ARPIP, FastML, HomoplasyFinder, PAML, PastML, POUTINE, SNPPar, TreeTime**

## Key interpretation

SNPPar and TreeTime have the strongest native overlap with BRANCHSNV because both operate on nucleotide/SNP data and expose branch mutation and/or homoplasy outputs. HomoplasyFinder provides a clean homoplasy-specific comparison. ARPIP, FastML and PAML provide nucleotide ancestral reconstruction suitable for a branch-change endpoint after deterministic output normalization. PastML can support an endpoint-specific categorical-state reconstruction comparison only through a pre-specified per-site encoding wrapper. POUTINE can support a homoplasy endpoint comparison, but its broader microbial-GWAS task must be excluded from scoring.

SubRecon remains a **direct scientific comparator** in the frozen landscape, but its implementation is protein-only. It is therefore **contextual_comparator_only** for the nucleotide/SNV benchmark rather than being demoted scientifically.

## Dependency warning

SNPPar uses TreeTime by default for ancestral state reconstruction, and POUTINE also incorporates TreeTime. They must not be interpreted as three algorithmically independent competitors.

## Boundary

This assessment did not install or execute any comparator, build environments, run benchmark datasets, alter the frozen direct/near classifications, bridge review decisions into production, or modify the production event ledger.

Next gate: `FREEZE_COMPARATOR_BENCHMARK_FEASIBILITY_RESULTS_V1`.
