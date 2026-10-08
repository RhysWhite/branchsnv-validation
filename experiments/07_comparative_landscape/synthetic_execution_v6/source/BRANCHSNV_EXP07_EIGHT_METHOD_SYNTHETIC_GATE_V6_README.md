# BRANCHSNV Experiment 07 — Eight-method synthetic gate v6

**SYNTHETIC ONLY — NOT canonical benchmark execution or authorization.** This package is an external validation handoff. It does not edit, amend or commit the frozen Git repository.

## Reason for v6

V5 passed private-root truth isolation for all eight methods and achieved 7/8 real comparator process successes on artificial four-tip fixtures. TreeTime v0.12.1 still exited nonzero: its CLI imports `matplotlib`, which was absent from the pinned TreeTime environment. A package can list plotting as optional while its command-line entry point still imports it.

V6 adds a **separate, synthetic-only, fully enumerated and pinned Matplotlib dependency overlay** containing the binary-wheel packages:

- matplotlib 3.8.4
- contourpy 1.2.1
- cycler 0.12.1
- fonttools 4.53.1
- kiwisolver 1.4.5
- packaging 24.1
- pillow 10.4.0
- pyparsing 3.1.2

The existing previously sealed NumPy + pandas/BioPython overlay and SciPy 1.14.0 overlay are reused unchanged. Every wheel is downloaded to a private wheelhouse and independently SHA-256 recorded; installation is offline `--no-index --no-deps` to an independent overlay; the installed tree is sealed and rechecked on resume. Symlink escaping, special files, shared hardlinks and executable `.pth` are disallowed by the relevant checks. Five representative native extension files are inspected for host system library dependencies, which are then explicitly mounted as readonly leaves (not broad OS directories).

No frozen comparator executable, Conda environment, runtime snapshot, original authorization, Stage 5F implementation or canonical data is modified. V6 preserves v1–v5 evidence and writes fresh `synthetic_v6/` execution records and `~/branchsnv-exp07-eight-method-synthetic-gate-v6.json` with no overwrite. The synthetic-only `--force-overwrite` for POUTINE is still explicitly recorded in both frozen and effective arguments; this **does not validate the frozen production POUTINE command**, and its production output-directory conflict requires separate formal resolution.

## Run on jynx

Place the ZIP in `/home/rwhite` and run the short integrity and logic checks from SSH:

```bash
cd ~
unzip -n branchsnv-exp07-eight-method-synthetic-gate-v6.zip
sha256sum -c branchsnv-exp07-eight-method-v6.sha256
/opt/admin/bioinf/miniforge/24.3.0-0/bin/python3.10 ~/branchsnv_exp07_eight_method_synthetic_gate_v6.py --self-test
/opt/admin/bioinf/miniforge/24.3.0-0/bin/python3.10 ~/branchsnv_exp07_eight_method_v6_local_tests.py
```

Launch the potentially long work in **tmux** (SSH sessions expire after 10 minutes):

```bash
tmux new-session -d -s exp07-synthetic-v6 \
  "bash -lc 'set -o pipefail; /opt/admin/bioinf/miniforge/24.3.0-0/bin/python3.10 /home/rwhite/branchsnv_exp07_eight_method_synthetic_gate_v6.py --prepare-treetime-mpl-overlay --run-eight-synthetic --resume-workspace /home/rwhite/.branchsnv_exp07_eightmethod_x2vkmv0x 2>&1 | tee /home/rwhite/branchsnv-exp07-eight-method-synthetic-v6.log'"
```

Monitor without stopping the tmux job:

```bash
tail -n 50 ~/branchsnv-exp07-eight-method-synthetic-v6.log
tmux has-session -t exp07-synthetic-v6 && echo RUNNING || echo SESSION_ENDED
```

## Acceptance

The desired marker is `EIGHT_METHOD_SYNTHETIC_GATE_V6=ALL_EIGHT_SYNTHETIC_RUNS_SUCCESSFUL`, with eight `truth_isolation=PASS` records and eight real artificial-fixture comparator executions showing `status=SUCCESS`. A method's successful exit is **not by itself evidence of scientifically correct predictions**. Review per-method native outputs, frozen-runner records and checksums independently before publishing anything as verified.

On failure, preserve stderr, stdout, execution JSON, v6 report and previous versions. Never rerun a completed v6 output path or remove a previous provenance record in order to force success.

**Limitations:** The live comparator runs cannot be tested off-host; security probes are synthetic, not a proof against all kernel or filesystem attacks. Wheel version pins and seals do not replace an independent dependency/version approval process. The runtime overlays are not authorized production environments. All 1,200 canonical comparator runs remain blocked pending separate implementation and authorization, including POUTINE command amendment and analysis of method-major dispatch order.
