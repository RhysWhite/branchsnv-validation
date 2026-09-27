# Experiment 07 T000013 production completion and reconciliation

Status:

`T000013_EXECUTION_COMPLETE`

## Transaction

T000013 completed the complete B000004 baseline-screening batch:

- positions: **1-500**
- global active indices: **1501-2000**
- events published: **500**
- assigned event IDs: `E000001512-E000002011`

Authorization commit:

`ed621e914be72b8852e8698d6d4977d121ad5dc9`

Fixed transaction timestamp:

`2026-09-27T01:00:00Z`

## Scientific outcomes

- retain for method assessment: **10**
- exclude: **490**
- source escalation: **0**

Exclusion breakdown:

- application only / no reusable method: **480**
- unrelated variant or data type: **10**
- duplicate record / no distinct capability: **0**
- unsupported source: **0**

## Production ledger

Pre-T000013:

- event count: **1,511**
- SHA-256: `edb131a6381f0d3afb03549c4773d55762c738eec435b3b5d8dfa0448865f08b`

Post-T000013:

- event count: **2,011**
- SHA-256: `f7175d03bb559a8996e7a2fb1aba3959abab87429b86adbd19df74f0f0cbf45e`

The pre-T000013 production ledger is an exact byte prefix of the
post-T000013 ledger.

## Reconciled baseline state

- complete: **2,000**
- ready: **92,622**
- blocked metadata: **484**
- awaiting source escalation: **0**
- current retained for method assessment: **122**
- current exclusions: **1,878**

B000004 is **500/500 terminal** with **0 remaining**.

## Persistent checkpoint

T000013 has the exact required checkpoint:

1. `authorization.json`
2. `proposal.tsv`
3. `receipt.json`

The checkpoint authorization is byte-identical to the tracked one-use
authorization.

The checkpoint proposal is byte-identical to the frozen approved proposal.

Receipt SHA-256:

`75ef74104ef236e24c6b80fdcf895c970bc5eb2260eaf7b81793f748b8117dc8`

Replay state:

`FINAL_CHECKPOINT_EXISTS`

## Next gate

The next step is not another manually operated single-batch transaction.

`DESIGN_BASELINE_SCREENING_CAMPAIGN_ORCHESTRATION_V4`

The campaign layer will preserve individual batch transactions,
authorizations, receipts, checkpoints, replay barriers, and scientific
decision provenance while reducing repetitive human gate interaction.
