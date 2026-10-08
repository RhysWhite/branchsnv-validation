# Comparator benchmark environment and smoke results v1

Environment construction and non-production smoke validation are complete for all eight frozen benchmark methods: ARPIP, FastML, HomoplasyFinder, PAML, PastML, POUTINE, SNPPar and TreeTime.

The result preserves successful runs, failed attempts and the evidence used to justify each separately authorized remediation. Fifteen implementation amendments were applied after the original implementation freeze; each freeze commit directly follows its recorded authorization commit.

The final amended implementation passes the full toy-only validation suite. The result tree contains 319 checksummed evidence files plus its checksum manifest.

The 150-scenario benchmark dataset has not been generated, benchmark execution has not occurred, benchmark truth has not been used for parameter tuning, and no production bridge has been performed.

The one-use environment/smoke authorization is consumed by this frozen result. Rerun is not authorized.

The next gate is `AUTHORIZE_COMPARATOR_BENCHMARK_DATASET_GENERATION_V1`. Dataset generation must be separately authorized and frozen before benchmark execution can be authorized.
