# Wave A live entrypoint v1

## Status

`FROZEN_PRE_IMPLEMENTATION`

This freeze creates no authorization and performs no network traffic.

## Authorization lifecycle

The frozen guard requires `authorized_execution_commit` to equal the
current Git HEAD and requires the tracked tree to be clean.

Therefore the executable authorization is not committed before the
run. The sequence is:

1. commit the final live-entrypoint implementation;
2. stop;
3. obtain explicit human authorization;
4. create the canonical untracked `authorization.json` whose
   `authorized_execution_commit` is exactly that final HEAD;
5. execute or resume under the same HEAD and same execution ID.

Any tracked commit between steps 4 and 5 invalidates the authorization.

The first claim durably binds the exact authorization bytes and
execution ID. The authorization remains one-use.

## Architecture

The existing adapter, authorization guard and exact transport remain
unchanged.

The current mocked runner is refactored so transport-independent
execution logic lives in a shared core. The mock wrapper continues to
reject the real HTTP executor.

A separate live entrypoint is the only component permitted to bind the
shared core to the already-frozen `default_http_executor`. No second
HTTP stack may be introduced.

## Pre-claim safety

All non-mutating checks occur before `guard.open_execution`:

- explicit live confirmation;
- explicit execution ID;
- canonical untracked authorization path;
- frozen implementation verification;
- authorization validation;
- NCBI contact-policy validation;
- adapter-contract validation.

Only after all of those pass may the one-use claim/state be created or
resumed.

## Execution

Wave A remains serial and manifest-ordered. One provider pacer and one
paced executor are retained for the process. Every request initiation,
including retries and redirects, remains subject to the provider pacing
contract.

Verified terminal evidence is durable before checkpoint advancement.

Ambiguous partial archives, identity failures, authentication failures,
redirect failures, integrity failures and retry exhaustion halt the run.
They are not automatically replayed.

There is no Wave B fallback.

## Human gate

After the live entrypoint is implemented, hostile-tested and committed,
execution stops again.

Creation of the real authorization file and initiation of network
traffic require a separate explicit human authorization.
