# BRANCHSNV v0.2.0: public record versus independent reproduction

**Read-only comparison of committed Git objects. No release approval is implied.**

- Public `main` commit: `b3bbdb10b4ee08df278b53eaefaf5c32b73eda77`
- Reviewed reproduction commit: `2979e984c2c8301b253c9df809c7d15fe02b4dcd`
- GitHub/public frozen record: 50 files; independent reproduction: 64 files
- Exact byte-identical shared files: **36**
- Differing shared files: **14**
- Public-only: 0; reproduction-only: 14
- Canonical manifest checks: public=47/47; review=47/47; review supplementary=13/13

## Scientific invariant comparison

**PASS for measured invariant fields; metadata still needs review**

- results/04_scalability/raw_runs.tsv: public 39 rows, review 39 rows; 39 row(s) have differing machine-dependent measurements
- results/04_scalability/benchmark_summary.tsv: public 13 rows, review 13 rows; 13 row(s) have differing machine-dependent measurements
- results/04_scalability/scaling_models.tsv: public 4 rows, review 4 rows; 4 row(s) have differing machine-dependent measurements
- Experiment 04 summary.json: all non-performance fields equal

## Record-level provenance differences

- `production_commit_at_run`: public `b63b6dbdde46162570dd0d17902e619467771624` → reviewed `65eb791d9f1a202c3ca8816332a58c036794bd1f`
- `validation_framework_commit`: public `f48bd14048866820c7a252d935ed2d26cb9407e5` → reviewed `3c64a1d367253ddcaef06c2f07012f347606358e`
- `experiment04_input_manifest_sha256`: public `<absent>` → reviewed `ba8326e312321a46e4244703336662756b58ded8dc5244a8c6f82fffde026a67`
- `validation_date`: public `2026-10-06` → reviewed `2026-10-21`
- `approval_status`: public `<absent>` → reviewed `REPRODUCTION_PASS_SCIENTIFIC_AND_PUBLICATION_RELEASE_PENDING`
- `zenodo_publication`: public `<absent>` → reviewed `NOT_PERFORMED`
- `keys present in only one record`: public `approval_status,benchmark_note,experiment04_input_manifest_sha256,limitations,orientation_equivalence,production_python_source_files,supplementary_checksum_manifest_sha256,validation_date_timezone,zenodo_publication` → reviewed `review required`

## Changed run-metadata keys (values intentionally not reproduced)

- `results/01_exact_oracle/run_metadata.json`: `completed_utc`, `cpu_count`, `elapsed_seconds`, `platform`, `python_version`
- `results/02_deliberate_faults/run_metadata.json`: `completed_utc`, `elapsed_seconds`, `output_dir`, `platform`, `python_version`, `started_utc`
- `results/03_published_datasets/run_metadata.json`: `completed_utc`, `cpu_count`, `elapsed_seconds`, `output_dir`, `platform`, `public_input_dir`, `python_version`, `started_utc`
- `results/04_scalability/run_metadata.json`: `cpu_model`, `logical_cpus_visible`, `memory_total_bytes_visible`, `platform`, `python`, `python_executable`
- `results/05_published_focal_branches/run_metadata.json`: `completed_utc`, `elapsed_seconds`, `platform`, `python_version`, `started_utc`
- `results/06_empirical_cross_classification/analysis_run_metadata.json`: `completed_utc`, `cpu_count`, `elapsed_seconds`, `platform`, `python_version`, `started_utc`
- `results/06_empirical_cross_classification/production_qc_run_metadata.json`: `completed_utc`, `elapsed_seconds`, `platform`, `python_version`, `started_utc`

## Differing shared committed files

- `README.md`
- `checksums.sha256`
- `record.json`
- `results/01_exact_oracle/run_metadata.json`
- `results/02_deliberate_faults/run_metadata.json`
- `results/03_published_datasets/run_metadata.json`
- `results/04_scalability/benchmark_summary.tsv`
- `results/04_scalability/raw_runs.tsv`
- `results/04_scalability/run_metadata.json`
- `results/04_scalability/scaling_models.tsv`
- `results/04_scalability/summary.json`
- `results/05_published_focal_branches/run_metadata.json`
- `results/06_empirical_cross_classification/analysis_run_metadata.json`
- `results/06_empirical_cross_classification/production_qc_run_metadata.json`

## Reproduction-only committed files

- `MANUSCRIPT_CLAIM_CROSSWALK.tsv`
- `MANUSCRIPT_REFERENCE_EXAMPLES.md`
- `environment/conda-explicit.txt`
- `environment/pip-freeze.txt`
- `execution/IDENTITY.txt`
- `execution/PRODUCTION_SOURCE_SHA256SUMS`
- `execution/REPRODUCTION.log`
- `execution/STATUS.txt`
- `experiment04/input_manifest.json`
- `input_equivalence/audit_script.py`
- `input_equivalence/audit_summary.json`
- `input_equivalence/equivalence_records.tsv`
- `supplementary_checksums.sha256`
- `verify_counts.py`

## Archival decision

Do **not** replace the current public v0.2.0 files with the reviewed record. Preserve both execution identities.
If all scientific invariants agree and metadata differences are independently explained, publish the newer record as a separate, explicitly named reproduction, retaining the existing canonical archive byte-for-byte.
Keep Experiment 7 RC3 distinct and marked UNSIGNED/HOLD. GitHub Release, PyPI and Zenodo remain on hold pending publication approval.
