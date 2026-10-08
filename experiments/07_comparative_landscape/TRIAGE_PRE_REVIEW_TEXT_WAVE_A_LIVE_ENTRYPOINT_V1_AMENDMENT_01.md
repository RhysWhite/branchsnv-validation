# Wave A live entrypoint v1 — amendment 01

## Status

`FROZEN_PRE_IMPLEMENTATION`

This amendment creates no authorization and performs no network
traffic.

## Why this amendment is required

The base live-entrypoint design proposed moving the existing mock
runner into a shared core.

That mock runner had already been committed and checksum-pinned by the
previous transport-adapter/runner implementation boundary. Altering it
would therefore invalidate an earlier frozen boundary.

The previous implementation remains authoritative and byte-identical.

## Revised architecture

The existing mock runner remains unchanged and continues to serve as a
regression oracle.

A new `triage_pre_review_text_wave_a_runner_core_v1.py` implements the
same state, archive, adapter-evidence and checkpoint orchestration for
the live path, but has no default network executor.

A new live entrypoint is the only new component permitted to inject the
already-frozen `default_http_executor`, and only after all frozen
preclaim checks succeed.

This deliberately accepts a small amount of duplicated orchestration
code in preference to mutating a previously frozen implementation.

## Pacing

The live entrypoint constructs one `ProviderPacer` and one paced
executor for the process. That executor is reused across all manifest
requests, retries and redirects.

## Authorization path

The canonical authorization path is currently untracked and not
gitignored.

No `.gitignore` change is required. The frozen guard deliberately
ignores untracked files when checking tracked-tree cleanliness, while
the live entrypoint separately rejects an authorization if it has
become tracked.

## Human gate

After the live core and live entrypoint have been implemented,
hostile-tested and committed, execution stops again.

No production authorization file and no real network request are
permitted before a separate explicit human authorization.
