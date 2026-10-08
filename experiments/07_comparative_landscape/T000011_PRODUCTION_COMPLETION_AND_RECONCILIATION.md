# Experiment 07 T000011 production completion and reconciliation

Status:

`T000011_EXECUTION_COMPLETE`

## Transaction

T000011 completed the complete B000002 baseline-screening batch:

- positions: **1-500**
- global active indices: **501-1000**
- events published: **500**
- assigned event IDs: `E000000512-E000001011`

Authorization commit:

`7c5e6342b961dcccd6269a68bcaaef991522f437`

Fixed transaction timestamp:

`2026-09-26T22:14:00Z`

## Scientific outcomes

- retain for method assessment: **10**
- exclude: **490**
- source escalation: **0**

Exclusion breakdown:

- application only / no reusable method: **475**
- unrelated variant or data type: **15**
- duplicate record / no distinct capability: **0**
- unsupported source: **0**

## Production ledger

Pre-T000011:

- event count: **511**
- SHA-256: `080b60b63c46524fe3f97d7db37ca56aba255e8633170b8f709f648ab11cd413`

Post-T000011:

- event count: **1011**
- SHA-256: `ab183ceb88b2cd9f09072dc9a2e819c735cb95ef723b73a732b99d065410deae`

The pre-T000011 production ledger is an exact byte prefix of the
post-T000011 ledger.

## Reconciled baseline state

- complete: **1,000**
- ready: **93,622**
- blocked metadata: **484**
- awaiting source escalation: **0**
- current retained for method assessment: **101**
- current exclusions: **899**

B000002 is **500/500 terminal** with **0 remaining**.

## Persistent checkpoint

T000011 has the exact required checkpoint:

1. `authorization.json`
2. `proposal.tsv`
3. `receipt.json`

The checkpoint authorization is byte-identical to the tracked one-use
authorization.

The checkpoint proposal is byte-identical to the frozen approved proposal.

Receipt SHA-256:

`58b17481e82c7ab29f84486cf675a08d49aa5a2097c1a4aec2a9c787f3706686`

Replay state:

`FINAL_CHECKPOINT_EXISTS`

## Next gate

`BUILD_B000003_T000012_DESIGN`
