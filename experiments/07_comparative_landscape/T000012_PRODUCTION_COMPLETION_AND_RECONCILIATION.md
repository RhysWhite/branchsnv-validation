# Experiment 07 T000012 production completion and reconciliation

Status:

`T000012_EXECUTION_COMPLETE`

## Transaction

T000012 completed the complete B000003 baseline-screening batch:

- positions: **1-500**
- global active indices: **1001-1500**
- events published: **500**
- assigned event IDs: `E000001012-E000001511`

Authorization commit:

`d955d234ba8e7f9782c50dcfdec3fccd7de839b9`

Fixed transaction timestamp:

`2026-09-26T23:21:00Z`

## Scientific outcomes

- retain for method assessment: **11**
- exclude: **489**
- source escalation: **0**

Exclusion breakdown:

- application only / no reusable method: **483**
- unrelated variant or data type: **6**
- duplicate record / no distinct capability: **0**
- unsupported source: **0**

## Production ledger

Pre-T000012:

- event count: **1,011**
- SHA-256: `ab183ceb88b2cd9f09072dc9a2e819c735cb95ef723b73a732b99d065410deae`

Post-T000012:

- event count: **1,511**
- SHA-256: `edb131a6381f0d3afb03549c4773d55762c738eec435b3b5d8dfa0448865f08b`

The pre-T000012 production ledger is an exact byte prefix of the
post-T000012 ledger.

## Reconciled baseline state

- complete: **1,500**
- ready: **93,122**
- blocked metadata: **484**
- awaiting source escalation: **0**
- current retained for method assessment: **112**
- current exclusions: **1,388**

B000003 is **500/500 terminal** with **0 remaining**.

## Persistent checkpoint

T000012 has the exact required checkpoint:

1. `authorization.json`
2. `proposal.tsv`
3. `receipt.json`

The checkpoint authorization is byte-identical to the tracked one-use
authorization.

The checkpoint proposal is byte-identical to the frozen approved proposal.

Receipt SHA-256:

`0dac72173b6bdd57ff6e8ce0df33395504f9549f57f6e3910df6c09389fe1e21`

Replay state:

`FINAL_CHECKPOINT_EXISTS`

## Next gate

`BUILD_B000004_T000013_DESIGN`
