# Comparator benchmark execution harness v1 implementation

## Authorization

Implementation is governed by:

`COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_IMPLEMENTATION_001`

Authorization commit:

`6dd22db80ea0f34fad868d196e65b3847749e403`

Exactly three implementation artifacts are permitted:

1. `comparator_benchmark_execution_v1_harness.py`
2. `comparator_benchmark_execution_v1_harness_validation.py`
3. `COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_IMPLEMENTATION.md`

## Current implementation state

`PARTIAL_STAGE_4`

### Stage 1 — orchestration foundation

Implemented:

- harness authorization/frozen-boundary validation;
- frozen runner identity validation;
- exact runtime-file SHA-256 validation;
- frozen scenario-matrix order;
- frozen `generator.scenario_seed()` use;
- deterministic scenario/method invocation enumeration; and
- unique invocation plan-root derivation.

### Stage 2 — fresh worker and resource accounting

Implemented:

- fresh Python worker process;
- JSON request/response isolation;
- invocation-specific child peak RSS using
  `resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss`; and
- explicit rejection of canonical S001-S150 in synthetic worker paths.

### Stage 3 — strict bubblewrap sandbox

Implemented and synthetically validated:

- `/usr/bin/bwrap`;
- host root read-only;
- designated worker root writable;
- private `/tmp`;
- explicit `/dev` and `/proc`;
- `--unshare-net`;
- `--die-with-parent`;
- distinct parent/worker network namespaces; and
- sandboxed synthetic RSS measurement.

### Stage 4 — frozen runner integration with mock executor

Implemented and synthetically validated:

- synthetic comparator-facing alignment, tree, GenBank reference and
  variable-position files created using frozen adapter serializers;
- `runner.scenario_inputs_from_directory()` used to load the fixture;
- `runner.build_command_plan()` used for the frozen HomoplasyFinder command;
- `runner.execute_command_plan()` called inside the network-isolated fresh
  sandbox worker;
- a custom mock executor supplied explicitly to the runner;
- no default runner executor called;
- no HomoplasyFinder/Java comparator process launched;
- mock non-zero exit preserved as `FAILED / nonzero_exit`;
- stdout/stderr preserved by the frozen runner;
- `execution.json` produced by the frozen runner;
- failed invocation does not finalize normalized predictions; and
- scoring remains false.

This tests the runner/harness boundary without duplicating any native-output or
normalization logic.

The permanent runner validator remains responsible for successful mocked
native-output normalization tests across all eight frozen methods.

## Still not implemented

The following remain deliberately absent:

- real third-party comparator execution;
- calls to `runner.default_executor`;
- canonical comparator-facing S001-S150 input loading;
- canonical benchmark execution;
- benchmark truth access;
- scoring or metrics;
- automatic comparator reruns;
- batch execution across the 1,200 canonical invocations; and
- canonical execution-ledger finalization.

## Scientific ownership

The harness does not reimplement comparator-specific scientific logic.

The frozen runner remains responsible for:

- comparator-facing input validation;
- command construction;
- environment construction;
- comparator execution semantics;
- native-output requirements;
- output normalization;
- branch-event normalization;
- recurrent-site normalization;
- failure classification;
- execution provenance; and
- prediction finalization/checksums.

Scenario-seed derivation remains owned by the frozen generator and is imported
directly.

## Execution boundary

Canonical benchmark execution remains unauthorized.

Benchmark truth and scoring remain unauthorized.

The canonical execution result root must remain absent until a later,
separate canonical-execution authorization is frozen.

### Stage 4.5 — independently approved timeout amendment

The timeout amendment was committed separately at:

`10981a2c4e34ebfc14350f74b84b35d5775216d0`

Amendment identity:

`COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_TIMEOUT_AMENDMENT_001`

The original 86,400-second authorization clause is preserved as historical
evidence but superseded by the approved scenario-specific policy:

| Scenarios | Tips | Classification | Timeout (seconds) |
|---|---:|---|---:|
| S001–S050 | 32 | Core | 3600 |
| S051–S100 | 128 | Core | 3600 |
| S101–S150 | 512 | Scale | 14400 |

The time limits originate from the frozen execution design. The core/scale
classification is a subsequent explicit approval, not an inferred historical
requirement.

The harness now checks the committed amendment identity, its checksum
manifest, the original authorization identity, and the frozen design and
scenario-matrix identities.

The timeout selector validates the complete 150-row frozen scenario matrix,
including scenario order and tip-count group, before returning a timeout.

Stage 4.5 does not implement or execute a third-party comparator, create the
canonical result root, access benchmark truth, or perform scoring.

Canonical execution remains unauthorized.

### Stage 5A — writable-root isolation hardening

A read-only preflight found that the original Stage 3 bubblewrap command
builder permitted `/`, the entire home directory, and the repository
as writable bind mounts. These unsafe commands were constructed only,
not executed.

The writable-root validator now requires:

- an existing, absolute directory;
- a dedicated Stage 3–5 workspace directly beneath HOME;
- an approved harness-workspace filename prefix;
- a sufficiently formed temporary workspace name;
- ownership by the current user and private `0700` permissions;
- no symlink used as the selected writable directory; and
- exclusion of `/tmp`, which the sandbox replaces with private tmpfs.

This prevents broad writable binds and rejects directories elsewhere in
the filesystem, including the repository.

The hardening is tested against broad roots, nested directories,
symlinks, unrelated HOME directories and unsafe permissions.

The existing frozen bubblewrap argument contract and read-only host
mount remain unchanged. This is a writable-mount safeguard, not a
claim that the sandbox makes all host files unreadable.

No third-party comparator is executed during this validation.
Canonical benchmark execution, truth access and scoring remain
unauthorized.

### Stage 5B — synthetic frozen-executor and RSS integration

Stage 5B uses the frozen runner's existing `default_executor`, without
altering its subprocess behavior.

A restricted sandboxed worker accepts only three predefined synthetic
Python programs:

- successful exit with controlled stdout/stderr, environment and cwd;
- non-zero exit with preserved partial output;
- timeout involving a forked process-group descendant.

Each invocation uses a new isolated Python worker and bubblewrap network
namespace. Peak direct-child RSS is captured using
`resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss`, reported in KiB
on the canonical Linux host.

The timeout case verifies that the forked descendant is no longer
executing after the frozen runner terminates the process group.

This resource measurement does not purport to capture the combined
simultaneous RSS of every process in a multi-process comparator tree.
That limitation must be retained when interpreting eventual benchmark
resource measurements.

The synthetic execution interface does not accept arbitrary subprocess
commands, comparator names, canonical scenario identifiers, or canonical
dataset paths.

No third-party comparator execution, canonical benchmark execution,
benchmark truth access, or scoring is authorized.

### Stage 5C — measured frozen-runner integration

Stage 5C joins the frozen runner's command construction, execution
provenance and failure handling with the synthetic measured subprocess
executor.

The actual comparator-facing command plan is built using the frozen
runner and the existing Stage 4 synthetic scenario fixture.

The explicitly supplied executor callback never executes the planned
comparator argv. It constructs a separate, locally defined synthetic
Python command and passes only that command to the frozen runner's
unchanged default subprocess implementation.

The original plan remains authoritative for runner provenance, while
the synthetic substitution is explicitly recorded as a validation-only
property. No Stage 5C record represents a genuine comparator run.

Three cases are exercised in separate fresh network-isolated workers:

- zero process exit without required comparator-native outputs;
- non-zero process exit with preserved stdout/stderr;
- timeout with process-group descendant termination.

All three must remain failed runner invocations, with no finalized
predictions and no scoring.

The original runner environment is supplied unchanged to the synthetic
subprocess; the synthetic success program checks its working directory
and PATH.

Peak child RSS is recorded using RUSAGE_CHILDREN in each fresh worker.
This is not a claim of aggregate simultaneous process-tree RSS.

Stage 5C neither activates canonical execution nor permits a method
command to be launched. Canonical input and benchmark truth access
remain unauthorized.

The frozen runner, original authorization, timeout amendment and
scientific implementations remain unchanged.

### Stage 5D — production-shaped metadata-only dispatch contract

Stage 5D combines the frozen invocation enumeration with the approved
scenario-specific timeout policy. The dispatch entries preserve:

- frozen invocation ordinal and method/scenario indexes;
- scenario identity, comparator identity and deterministic seed;
- canonical input and result path identifiers; and
- approved timeout in seconds.

The contract contains 1,200 unique comparator/scenario pairs:
150 scenarios multiplied by eight methods.

The 100 core scenarios produce 800 planned invocations, each with
a 3,600-second timeout. The 50 scale scenarios produce 400 planned
invocations, each with a 14,400-second timeout.

Dispatch construction is metadata-only. It does not open canonical
scenario inputs, create canonical result directories, construct
third-party commands, launch subprocesses, or access benchmark truth.

The independent validation checks exact ordering, uniqueness,
coverage, timeouts, determinism and mutation rejection. It also
blocks frozen runner execution functions during schedule generation.

Stage 5D is not an authorization for benchmark execution.

### Stage 5E — durable synthetic provenance and failure continuation

Stage 5E validates durable execution accounting using the three
predefined Stage 5C synthetic runner probes.

Each synthetic invocation produces an independent JSON record with:

- synthetic invocation identity and order;
- frozen runner execution metadata and execution-record SHA-256;
- subprocess stdout, stderr, exit code and failure classification;
- runner-measured elapsed time;
- fresh-worker peak child RSS in KiB and bytes; and
- explicit prohibitions on finalized predictions and scoring.

Record creation is no-clobber and uses a temporary file, fsync and
hard-link publication. A final checksummed manifest is produced only
after all expected synthetic cases have been recorded.

Expected completion failures do not terminate orchestration. An
unexpected harness/infrastructure failure stops immediately, retains
the partial ledger and produces no false completion manifest.

Previously populated ledger roots are rejected. No automatic rerun
or record overwrite is permitted.

The resource metric reflects Linux RUSAGE_CHILDREN maximum child RSS.
It is not an estimate of aggregate simultaneous process-tree memory.

This is a synthetic-only provenance and continuation validation.
It is not a production comparator dispatcher and does not establish
that canonical benchmark truth is inaccessible to a future comparator.

Canonical benchmark execution, truth access and scoring remain
unauthorized.

### Stage 5F — Security Amendment 002 implementation

The production-facing sandbox *construction contract* now starts with an
empty private filesystem root (`--tmpfs /`), not a readable bind of the host
root. The synthetic isolation pathway admits only SHA-256-pinned operating
system **files**, a read-only synthetic input directory and a private writable
workspace. It does not mount the repository, HOME, any canonical dataset
parent, or a runtime directory wholesale. The writable alias of the input
inside the workspace is masked by a private tmpfs. Child processes receive a
cleared, explicitly populated environment, a private `/proc` in a new PID
namespace, a private `/tmp`, no network and no intentionally passed host file
descriptors.

The adversarial acceptance test uses `/bin/sh` plus its independently inspected
and hashed runtime file dependencies on the validation host. It checks that a
synthetic truth sentinel outside the sandbox is inaccessible by direct path,
parent directory, symlink, `/proc/1/root`, and inherited high-numbered file
descriptor. A synthetic public input must remain readable. Mount overlap,
unapproved system paths, file hash changes, symlinks and hardlinks in the
synthetic input tree are rejected. These tests use no canonical data and no
comparator binary.

All 1,200 frozen invocations may be written to an independent **metadata-only**,
checksummed, no-clobber dispatch journal, with 800 core and 400 scale timeout
assignments. Entries are marked `NOT_EXECUTED`; no resource or performance
observations are fabricated. Interruption leaves a partial journal and no
completion manifest. Stage 5E separately exercises measured synthetic
subprocesses and preserves genuine synthetic runner failure provenance.

**Important release boundary:** this implementation is not an operational
production comparator runner. `stage5f_production_execution()` always refuses
to launch an actual comparator, including when supplied with fabricated
approval arguments. A separately frozen and validated execution authorization
and per-method pinned runtime dependency/mount closure are required before
any future canonical run. The synthetic private-root test does not establish
runtime completeness or truth isolation for all eight comparator environments.

The original frozen runner, scientific code, scenario matrix, historical
sandbox authorization, timeout Amendment 001 and Security Amendment 002
remain unmodified. The original Stage 3–5 synthetic regressions remain
available but are not a substitute for the Stage 5F private-root checks.

### Stage 5F host bubblewrap compatibility

The pinned bubblewrap on the execution host does not support its newer
`--clearenv` argument. Instead, the private-root command now starts via
`/usr/bin/env -i /usr/bin/bwrap ...`, using an absolute, root-owned,
non-group/other-writable host environment-clearing launcher. Only the
explicit `--setenv PATH`, `--setenv HOME`, and `--setenv LANG` values
reach the sandbox child. This preserves environment isolation independently
of the Python caller's inherited environment, without requiring an
unsupported bubblewrap option. The empty mount root, restricted binds,
network/PID namespaces, and test-only comparator prohibition are unchanged.

This compatibility adjustment must pass a real host-side bubblewrap
synthetic isolation probe before implementation freeze. No production
comparator execution is permitted.
