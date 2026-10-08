# Comparator benchmark dataset-generation results v1

The one-use benchmark dataset-generation authorization was consumed successfully from commit `e79d47fce7e60fc1af1c36a45904a23b272b3055`.

Exactly 150 frozen benchmark scenarios were generated. The dataset contains 600 comparator-facing input files and 300 truth files, with inputs and truth stored separately. The dataset manifest records all 900 per-scenario files, and the checksum ledger contains 901 entries including the manifest itself.

Independent post-generation validation confirmed the frozen scenario matrix, deterministic seeds, 40 true event sites per scenario, regime-specific recurrence counts, missing-data contract, 10,000-bp sequence lengths, matching tip sets, resolved truth sequences, observed-alignment-derived input position files, and all recorded file identities.

Generation completed with exit code 0 and empty stderr. The one-use generation authorization is consumed; rerun is not authorized.

The generated payload is approximately 516 MB and is retained outside ordinary Git history for inclusion in the external validation/release archive. The manifest, checksum ledger and execution evidence remain Git-visible.

Benchmark execution has not occurred. No third-party comparator has been run against the generated benchmark, benchmark truth has not been used for comparator parameter tuning, and no production bridge has been performed.

The next gate is `AUTHORIZE_COMPARATOR_BENCHMARK_EXECUTION_V1`. Benchmark execution requires a separate one-use authorization frozen against this dataset-generation result.
