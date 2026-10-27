# Experiment 07 — native execution source-provenance record (900-run extension)

**Scope: historical-source and receipt-reference verification; NOT a complete native re-execution release.**

This record derives from the local collection archive `BRANCHSNV_Exp07_native_provenance_CANDIDATE_20261027.zip` (SHA-256 `6ae47fae1f37e8c90ed80d3adb79152cf7d2178a264314141e2033b63de00640`). Its ten original payload files passed byte-level manifest checks. The archived copy of the scorer exactly matched the already-published `experiments/07_comparative_landscape/accuracy_benchmark_v1/exp07_score_archived.py`; it is not duplicated here. The other eight original payload files are retained byte-for-byte. `SHA256SUMS` covers the new README, two Git attributes lines, and every preserved archived payload.

The `execution_source_matrix.tsv` maps **900 distinct executions** (six methods × 150 scenarios) to 900 original execution receipt hashes, 900 prediction hashes, their source runner and adapter hashes, native exit codes, and any subsequent normalization recovery. The matrix is an **index into locally retained execution records**, not an export of those 1,800 per-run files. An upstream Jynx collection script reported verifying the original 900 receipt and prediction files against their hashes, but those files are not part of this repository record. CI can independently verify the matrix's coverage and consistency, the five archived source bytes, and SNPPar S001's recovery metadata and stdout, **not the absent per-run file bytes**.

The 900 receipts reference these SHA-256-pinned versions:

| Version | Execution receipts |
| --- | ---: |
| Runner early A (`63a5e45a…`) | 11 |
| Runner early B (`8e9bbcc9…`) | 1 |
| Runner final (`a1ec5c68…`) | 888 |
| Adapter early (`206f8914…`) | 7 |
| Adapter final (`155e3e6f…`) | 893 |

The versioned source copies have original bytes, but are not presented as standalone runnable programs inside this directory. Running them requires their original imported files, input datasets and comparator environments. The original executed wrapper `exp07_execute.py` is also not included in this record; receipt version hashes identify the versioned runner and adapters.

## SNPPar S001: original execution and saved-output recovery

The original SNPPar native invocation exited 0 with a zero-homoplasy result but did not produce `homoplasic_events_all_calls.tsv`. The historical runner B required a terminal phrase that the saved stdout did not contain. The separately recorded recovery re-normalized already-saved native outputs with runner final; it **did not rerun SNPPar** and recorded no simulator truth read. The sealed `SNPPar_S001_receipt.json` and original stdout support this distinction, and its prediction SHA-256 is linked to the matrix row.

The recovery receipt also cites a prior failed execution/normalization record with SHA-256 `c42a2b1b2269706b8683e77847779cd9ecf4c22245d2aeadb00f0df5bea58a5d`. **That original failed record is not in this collection and has not been independently verified here.** Retaining its hash does not imply that its content has been recovered.

## Public-source limitations and remaining release work

1. Original 900 receipt and prediction bytes and complete canonical per-run comparator inputs are retained outside this archive and are not independently rehashed by GitHub CI.
2. Original failed SNPPar S001 record is not included; find and verify it before claiming an unbroken recovery chain.
3. Native comparator executables, versioned environments, pinned dependency artifacts, wrapper entry point, Slurm invocation records, and all original run inputs remain necessary for **fresh native execution reproduction**.
4. SNPPar stdout is byte-for-byte preserved and contains `/home/rwhite/…` filesystem paths (not passwords in the reviewed file). Confirm that publishing these local paths is acceptable before opening a non-draft PR or merging.
5. This record covers the 900-execution extension, not the earlier 300 external executions or the 150 BRANCHSNV scenarios. The published numerical scores and figures are verified by separate gates.

Run `python3 publication_audits/experiment07/native_execution_provenance_v1/verify_native_execution_provenance.py` from the repository root. This is a *provenance-integrity* gate, not a native rerun gate. Keep the pull request in **Draft** until the complete native rerun record has been checked.
