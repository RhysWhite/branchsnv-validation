from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess


ROOT = Path("experiments/07_comparative_landscape")
OUT = Path(
    "results/07_comparative_landscape/"
    "triage_validation_v1"
)

LAYER = ROOT / "c000001_campaign_execution_v4.py"

DESIGN_PATH = (
    ROOT
    / "triage_validation_sampling_v1_design.json"
)

DOC_PATH = (
    ROOT
    / "TRIAGE_VALIDATION_SAMPLING_V1.md"
)

SUMS_PATH = (
    ROOT
    / "triage_validation_sampling_v1.sha256"
)

SAMPLE_PATH = OUT / "sample.tsv"

DESIGN_ID = "TRIAGE_VALIDATION_SAMPLING_V1"
TARGET_N = 2000
STRATUM_WIDTH = 5000


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def tsv_bytes(fields, rows) -> bytes:
    handle = io.StringIO(newline="")

    writer = csv.DictWriter(
        handle,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )

    writer.writeheader()

    for row in rows:
        writer.writerow(row)

    return handle.getvalue().encode("utf-8")


spec = importlib.util.spec_from_file_location(
    "campaign",
    LAYER,
)

assert spec is not None
assert spec.loader is not None

m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

guard = m.load_guard()

production = m.validate_production_boundary()
scientific = m.validate_scientific_freeze()

queue_fields, queue = guard.read_tsv(
    m.QUEUE
)

membership_path = (
    m.EXECUTION_ROOT
    / "batch_membership.tsv"
)

membership_fields, membership = guard.read_tsv(
    membership_path
)

ledger_fields, ledger = guard.read_tsv(
    m.LEDGER
)

queue_by_id = {
    row["screening_entity_id"]: row
    for row in queue
}

membership_by_id = {
    row["screening_entity_id"]: row
    for row in membership
}

if len(membership_by_id) != 94622:
    raise SystemExit(
        "FAIL | active membership count changed"
    )


# ------------------------------------------------------------
# Current terminal production entities.
# ------------------------------------------------------------

latest = {}

for row in ledger:
    latest[row["screening_entity_id"]] = row


terminal_event_types = {
    "record_decision",
    "superseding_record_decision",
}

terminal_decisions = {
    "exclude",
    "retain_for_method_assessment",
}


terminal_ids = {
    entity_id
    for entity_id, row in latest.items()
    if (
        entity_id in membership_by_id
        and row["event_type"] in terminal_event_types
        and row["record_decision"] in terminal_decisions
    )
}

if len(terminal_ids) != 2000:
    raise SystemExit(
        "FAIL | expected exactly 2000 current "
        "terminal active entities"
    )


# ------------------------------------------------------------
# Frozen C000001 development labels.
#
# These 2,500 records must NEVER enter the blind validation
# sample.
# ------------------------------------------------------------

development_ids = set()

for batch in m.BATCHES:

    identity = m.build_target_identity(
        guard=guard,
        batch_id=batch["batch_id"],
    )

    development_ids.update(
        row["screening_entity_id"]
        for row in identity["entities"]
    )


if len(development_ids) != 2500:
    raise SystemExit(
        "FAIL | expected exactly 2500 C000001 "
        "development entities"
    )

if terminal_ids & development_ids:
    raise SystemExit(
        "FAIL | production history overlaps C000001 "
        "development set"
    )


# ------------------------------------------------------------
# Blind triage-validation universe.
#
# This is the population that would remain ready after the
# already-reviewed C000001 campaign were executed.
# ------------------------------------------------------------

active_ids = set(
    membership_by_id
)

validation_universe_ids = (
    active_ids
    - terminal_ids
    - development_ids
)

if len(validation_universe_ids) != 90122:
    raise SystemExit(
        "FAIL | expected validation universe of 90122, got "
        f"{len(validation_universe_ids)}"
    )


# ------------------------------------------------------------
# Strata by frozen global active index.
# ------------------------------------------------------------

def stratum_for(index: int) -> tuple[int, int]:
    start = (
        ((index - 1) // STRATUM_WIDTH)
        * STRATUM_WIDTH
        + 1
    )

    end = start + STRATUM_WIDTH - 1

    return start, end


population_by_stratum = defaultdict(list)

for entity_id in validation_universe_ids:

    membership_row = membership_by_id[
        entity_id
    ]

    index = int(
        membership_row["global_active_index"]
    )

    population_by_stratum[
        stratum_for(index)
    ].append(entity_id)


population_counts = {
    key: len(value)
    for key, value in population_by_stratum.items()
}

if sum(population_counts.values()) != 90122:
    raise SystemExit(
        "FAIL | stratum population count mismatch"
    )


# ------------------------------------------------------------
# Proportional allocation using deterministic largest
# remainders.
# ------------------------------------------------------------

raw_allocations = {
    stratum:
        TARGET_N
        * count
        / len(validation_universe_ids)

    for stratum, count
    in population_counts.items()
}

allocation = {
    stratum: int(value)
    for stratum, value
    in raw_allocations.items()
}

remaining = (
    TARGET_N
    - sum(allocation.values())
)

ranked_remainders = sorted(
    population_counts,
    key=lambda stratum: (
        -(
            raw_allocations[stratum]
            - allocation[stratum]
        ),
        stratum,
    ),
)

for stratum in ranked_remainders[:remaining]:
    allocation[stratum] += 1


if sum(allocation.values()) != TARGET_N:
    raise SystemExit(
        "FAIL | sample allocation does not sum to 2000"
    )


# ------------------------------------------------------------
# Deterministic pseudorandom selection within each stratum.
#
# No title, DOI, journal, keyword, provenance or model output
# participates in selection.
# ------------------------------------------------------------

queue_sha = sha256_file(m.QUEUE)
membership_sha = sha256_file(membership_path)
ledger_sha = sha256_file(m.LEDGER)
freeze_sha = sha256_file(m.SCIENTIFIC_FREEZE)

selection_salt = "|".join([
    DESIGN_ID,
    queue_sha,
    membership_sha,
    ledger_sha,
    freeze_sha,
])


def selection_hash(entity_id: str) -> str:
    return sha256_bytes(
        (
            selection_salt
            + "\t"
            + entity_id
        ).encode("utf-8")
    )


selected = []

for stratum in sorted(
    population_by_stratum
):

    population = population_by_stratum[
        stratum
    ]

    ranked = sorted(
        population,
        key=lambda entity_id: (
            selection_hash(entity_id),
            entity_id,
        ),
    )

    take = allocation[
        stratum
    ]

    selected.extend(
        ranked[:take]
    )


if len(selected) != TARGET_N:
    raise SystemExit(
        "FAIL | selected sample count differs from 2000"
    )

if len(set(selected)) != TARGET_N:
    raise SystemExit(
        "FAIL | duplicate sampled entities"
    )

if set(selected) & terminal_ids:
    raise SystemExit(
        "FAIL | validation sample contains production-labelled entity"
    )

if set(selected) & development_ids:
    raise SystemExit(
        "FAIL | validation sample contains C000001 development entity"
    )


# ------------------------------------------------------------
# Freeze a separate deterministic review order.
#
# This avoids reviewing the sample in DOI/index order.
# ------------------------------------------------------------

review_salt = (
    selection_salt
    + "|BLIND_REVIEW_ORDER"
)


def review_hash(entity_id: str) -> str:
    return sha256_bytes(
        (
            review_salt
            + "\t"
            + entity_id
        ).encode("utf-8")
    )


selected = sorted(
    selected,
    key=lambda entity_id: (
        review_hash(entity_id),
        entity_id,
    ),
)


sample_fields = [
    "validation_sample_id",
    "validation_stage",
    "sampling_stratum",
    "stratum_population_n",
    "stratum_sample_n",
    "inclusion_probability",
    "selection_sha256",
    "review_order_sha256",
    "global_active_index",
] + list(queue_fields)


sample_rows = []

for number, entity_id in enumerate(
    selected,
    start=1,
):

    membership_row = membership_by_id[
        entity_id
    ]

    q = queue_by_id[
        entity_id
    ]

    index = int(
        membership_row[
            "global_active_index"
        ]
    )

    stratum = stratum_for(
        index
    )

    pop_n = population_counts[
        stratum
    ]

    sample_n = allocation[
        stratum
    ]

    row = {
        "validation_sample_id":
            f"TV1-{number:04d}",

        "validation_stage":
            "1",

        "sampling_stratum":
            (
                f"{stratum[0]:05d}-"
                f"{stratum[1]:05d}"
            ),

        "stratum_population_n":
            str(pop_n),

        "stratum_sample_n":
            str(sample_n),

        "inclusion_probability":
            f"{sample_n / pop_n:.12f}",

        "selection_sha256":
            selection_hash(
                entity_id
            ),

        "review_order_sha256":
            review_hash(
                entity_id
            ),

        "global_active_index":
            str(index),
    }

    for field in queue_fields:
        row[field] = q[field]

    sample_rows.append(
        row
    )


sample_payload = tsv_bytes(
    sample_fields,
    sample_rows,
)

OUT.mkdir(
    parents=True,
    exist_ok=True,
)

SAMPLE_PATH.write_bytes(
    sample_payload
)


# ------------------------------------------------------------
# Diagnostics only — never affect sample selection.
# ------------------------------------------------------------

def doi_prefix(doi: str) -> str:
    value = doi.strip().lower()

    if not value:
        return "<NO_DOI>"

    if "/" not in value:
        return value

    return value.split("/", 1)[0]


universe_prefix = Counter(
    doi_prefix(
        queue_by_id[
            entity_id
        ]["doi"]
    )
    for entity_id
    in validation_universe_ids
)

sample_prefix = Counter(
    doi_prefix(
        queue_by_id[
            entity_id
        ]["doi"]
    )
    for entity_id
    in selected
)


stratum_records = []

for stratum in sorted(
    population_counts
):

    pop_n = population_counts[
        stratum
    ]

    sample_n = allocation[
        stratum
    ]

    stratum_records.append({
        "start_global_active_index":
            stratum[0],

        "end_global_active_index":
            stratum[1],

        "population_n":
            pop_n,

        "sample_n":
            sample_n,

        "sampling_fraction":
            sample_n / pop_n,
    })


head = subprocess.check_output(
    [
        "git",
        "rev-parse",
        "HEAD",
    ],
    text=True,
).strip()


design = {
    "schema_version":
        1,

    "design_id":
        DESIGN_ID,

    "status":
        "FROZEN_BLIND_SAMPLE_MEMBERSHIP_NO_LABELS",

    "repo_head":
        head,

    "purpose":
        (
            "Create a representative blind holdout sample "
            "for validating scalable high-recall triage of "
            "the remaining Experiment 07 baseline "
            "scientific-screening universe."
        ),

    "source_identity": {
        "baseline_queue_path":
            str(m.QUEUE.relative_to(
                m.REPO_ROOT
            )),

        "baseline_queue_sha256":
            queue_sha,

        "batch_membership_path":
            str(membership_path.relative_to(
                m.REPO_ROOT
            )),

        "batch_membership_sha256":
            membership_sha,

        "production_ledger_path":
            str(m.LEDGER.relative_to(
                m.REPO_ROOT
            )),

        "production_ledger_sha256":
            ledger_sha,

        "c000001_scientific_freeze_path":
            str(m.SCIENTIFIC_FREEZE.relative_to(
                m.REPO_ROOT
            )),

        "c000001_scientific_freeze_sha256":
            freeze_sha,
    },

    "population_accounting": {
        "active_membership":
            len(active_ids),

        "current_terminal_production_entities":
            len(terminal_ids),

        "c000001_development_entities":
            len(development_ids),

        "blind_validation_sampling_universe":
            len(validation_universe_ids),
    },

    "development_validation_separation": {
        "c000001_is_development_only":
            True,

        "validation_sample_excludes_all_c000001_entities":
            True,

        "validation_sample_excludes_all_current_terminal_entities":
            True,

        "validation_labels_available_at_sampling":
            False,

        "triage_model_output_used_for_sampling":
            False,

        "titles_or_keywords_used_for_sampling":
            False,

        "doi_or_publisher_used_for_sampling":
            False,

        "citation_provenance_used_for_sampling":
            False,
    },

    "sampling": {
        "stage":
            1,

        "target_n":
            TARGET_N,

        "stratification_variable":
            "frozen_global_active_index",

        "stratum_width":
            STRATUM_WIDTH,

        "allocation":
            "proportional_largest_remainder",

        "within_stratum_selection":
            "lowest_sha256_rank",

        "selection_salt_sha256":
            sha256_bytes(
                selection_salt.encode(
                    "utf-8"
                )
            ),

        "blind_review_order":
            "independent_sha256_rank",

        "strata":
            stratum_records,
    },

    "sample_artifact": {
        "path":
            str(SAMPLE_PATH),

        "row_count":
            TARGET_N,

        "sha256":
            sha256_file(
                SAMPLE_PATH
            ),
    },

    "prespecified_sequential_validation_rule": {
        "stage_1_n":
            2000,

        "minimum_retained_positive_records_for_primary_recall_assessment":
            60,

        "if_fewer_than_60_retained_positives":
            (
                "Draw an additional pre-specified "
                "probability sample from the remaining "
                "unsampled validation universe before "
                "final recall interpretation."
            ),

        "validation_labels_must_not_be_used_to_tune_the_triage_model":
            True,
    },

    "authority": {
        "creates_scientific_decisions":
            False,

        "creates_production_authority":
            False,

        "creates_ledger_events":
            False,

        "changes_batch_membership":
            False,

        "changes_baseline_queue":
            False,
    },
}


DESIGN_PATH.write_bytes(
    (
        json.dumps(
            design,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
)


doc = f"""# Triage validation sampling v1

## Status

`{design["status"]}`

This artifact freezes a blind probability sample for later validation of
the scalable Experiment 07 scientific-triage layer.

It does not contain validation labels and it does not create scientific
decisions or production authority.

## Population

- Frozen active membership: {len(active_ids):,}
- Current terminal production entities: {len(terminal_ids):,}
- C000001 development entities: {len(development_ids):,}
- Blind validation sampling universe: {len(validation_universe_ids):,}
- Stage-1 validation sample: {TARGET_N:,}

The 2,500 C000001 human-reviewed entities are development data only and are
excluded completely from the validation sample.

## Sampling

The remaining 90,122 entities are stratified by frozen global active index
in 5,000-record strata. Allocation is proportional to stratum population
using deterministic largest remainders.

Within each stratum, records are selected by a SHA256 rank pinned to the
frozen queue, membership, production-ledger and C000001-freeze identities.

Titles, DOI prefixes, publisher identity, keywords, citation provenance and
future model scores do not influence selection.

An independent deterministic SHA256 ordering is used for eventual human
review so that records are not reviewed in active-index/DOI order.

## Validation discipline

The validation sample is frozen before development of the scalable triage
model.

Validation labels must not be used to train, tune or choose the triage
model or its threshold.

Stage 1 contains 2,000 records. If fewer than 60 retained-positive records
are found during later blinded review, a supplemental probability sample
will be drawn from the remaining unsampled universe before final recall
interpretation.

## Authority

This sampling freeze:

- creates no scientific screening decision;
- creates no event-ledger entry;
- creates no live authorization;
- does not modify the baseline queue;
- does not modify active batch membership;
- does not authorize or execute C000001.
"""

DOC_PATH.write_text(
    doc,
    encoding="utf-8",
)


manifest_paths = [
    Path(__file__),
    DESIGN_PATH,
    DOC_PATH,
    SAMPLE_PATH,
]

with SUMS_PATH.open(
    "w",
    encoding="utf-8",
) as handle:

    for path in manifest_paths:

        rel = path.resolve().relative_to(
            m.REPO_ROOT
        )

        handle.write(
            f"{sha256_file(path)}  {rel}\n"
        )


print(
    "PASS | blind validation sample frozen"
)

print(
    "validation universe =",
    len(validation_universe_ids),
)

print(
    "sample n =",
    len(sample_rows),
)

print()
print("stratum allocations:")

for row in stratum_records:
    print(
        f"{row['start_global_active_index']:05d}-"
        f"{row['end_global_active_index']:05d}",
        "| population =",
        row["population_n"],
        "| sample =",
        row["sample_n"],
        "| fraction =",
        f"{row['sampling_fraction']:.4%}",
    )


print()
print("top DOI-prefix comparison:")
print(
    "prefix\tuniverse_n\tuniverse_pct\t"
    "sample_n\tsample_pct"
)

for prefix, count in universe_prefix.most_common(
    20
):
    sample_count = sample_prefix[
        prefix
    ]

    print(
        f"{prefix}\t"
        f"{count}\t"
        f"{count / len(validation_universe_ids):.3%}\t"
        f"{sample_count}\t"
        f"{sample_count / TARGET_N:.3%}"
    )


print()
print(
    "sample_sha256 =",
    sha256_file(SAMPLE_PATH),
)

print(
    "design_sha256 =",
    sha256_file(DESIGN_PATH),
)

print(
    "documentation_sha256 =",
    sha256_file(DOC_PATH),
)

print(
    "manifest_sha256 =",
    sha256_file(SUMS_PATH),
)
