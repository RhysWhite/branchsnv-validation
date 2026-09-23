#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

import screening_entity_identity as impl


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent


def citation_row(
    *,
    source="openalex",
    direction="forward",
    doi="",
    pmid="",
    openalex_id="",
    omid="",
    title="",
    year="",
    source_record_id=None,
    anchor_id="W0A01",
):
    if source_record_id is None:
        source_record_id = (
            openalex_id
            or omid
            or doi
            or pmid
        )

    return {
        "wave": "0",
        "anchor_id": anchor_id,
        "anchor_tool": "Synthetic",
        "source": source,
        "direction": direction,
        "doi": doi,
        "pmid": pmid,
        "openalex_id": openalex_id,
        "omid": omid,
        "title": title,
        "year": year,
        "source_record_id":
            source_record_id,
    }


def keyed(result):
    return {
        row["provisional_entity_key"]: row
        for row in result["entities"]
    }


# ------------------------------------------------------------
# Same DOI across providers collapses conservatively.
# ------------------------------------------------------------

rows = [
    citation_row(
        doi="10.2/a",
        pmid="1000",
        openalex_id="W1",
        title="Tool A",
        year="2020",
        source="openalex",
    ),
    citation_row(
        doi="10.2/A",
        pmid="PMID:1000",
        omid="br/1",
        source="opencitations",
    ),
]

result = (
    impl.build_citation_publication_entities(
        rows
    )
)

entities = keyed(result)

assert list(entities) == [
    "publication:doi:10.2/a"
]

assert result["identity_conflict_count"] == 0

print(
    "PASS | exact DOI joins citation providers"
)


# ------------------------------------------------------------
# DOI-less PMID may attach to one DOI only.
# ------------------------------------------------------------

rows = [
    citation_row(
        doi="10.2/b",
        pmid="2000",
        openalex_id="W2",
    ),
    citation_row(
        source="opencitations",
        pmid="2000",
        omid="br/2",
    ),
]

result = (
    impl.build_citation_publication_entities(
        rows
    )
)

entities = keyed(result)

assert list(entities) == [
    "publication:doi:10.2/b"
]

print(
    "PASS | citation PMID attaches to unique DOI group"
)


# ------------------------------------------------------------
# PMID cannot bridge different DOI groups.
# ------------------------------------------------------------

rows = [
    citation_row(
        doi="10.2/c",
        pmid="3000",
        openalex_id="W3",
    ),
    citation_row(
        doi="10.2/d",
        pmid="3000",
        openalex_id="W4",
    ),
    citation_row(
        source="opencitations",
        pmid="3000",
        omid="br/3",
    ),
]

result = (
    impl.build_citation_publication_entities(
        rows
    )
)

entities = keyed(result)

for key in (
    "publication:doi:10.2/c",
    "publication:doi:10.2/d",
    "publication:conflict:pmid:3000",
):
    assert key in entities
    assert (
        entities[key]["identity_status"]
        == "conflict_hold"
    )

print(
    "PASS | citation PMID cannot bridge different DOI groups"
)


# ------------------------------------------------------------
# OpenAlex ID cannot bridge different DOI groups.
# ------------------------------------------------------------

rows = [
    citation_row(
        doi="10.2/e",
        pmid="4000",
        openalex_id="W999",
    ),
    citation_row(
        doi="10.2/f",
        pmid="4001",
        openalex_id="W999",
    ),
]

result = (
    impl.build_citation_publication_entities(
        rows
    )
)

entities = keyed(result)

assert (
    entities[
        "publication:doi:10.2/e"
    ]["identity_status"]
    == "conflict_hold"
)

assert (
    entities[
        "publication:doi:10.2/f"
    ]["identity_status"]
    == "conflict_hold"
)

assert any(
    row["conflict_type"]
    == "openalex_id_multiple_doi"
    for row in result[
        "identity_conflicts"
    ]
)

print(
    "PASS | OpenAlex ID cannot bridge different DOI groups"
)


# ------------------------------------------------------------
# OMID cannot bridge different DOI groups.
# ------------------------------------------------------------

rows = [
    citation_row(
        source="opencitations",
        doi="10.2/g",
        pmid="5000",
        omid="br/shared",
    ),
    citation_row(
        source="opencitations",
        doi="10.2/h",
        pmid="5001",
        omid="br/shared",
    ),
]

result = (
    impl.build_citation_publication_entities(
        rows
    )
)

assert any(
    row["conflict_type"]
    == "omid_multiple_doi"
    for row in result[
        "identity_conflicts"
    ]
)

print(
    "PASS | OMID cannot bridge different DOI groups"
)


# ------------------------------------------------------------
# One DOI associated with multiple PMIDs enters conflict hold.
# ------------------------------------------------------------

rows = [
    citation_row(
        doi="10.2/i",
        pmid="6000",
        openalex_id="W10",
        source_record_id="one",
    ),
    citation_row(
        doi="10.2/i",
        pmid="6001",
        openalex_id="W10",
        source_record_id="two",
    ),
]

result = (
    impl.build_citation_publication_entities(
        rows
    )
)

entity = keyed(result)[
    "publication:doi:10.2/i"
]

assert (
    entity["identity_status"]
    == "conflict_hold"
)

assert any(
    row["conflict_type"]
    == "doi_multiple_pmids"
    for row in result[
        "identity_conflicts"
    ]
)

print(
    "PASS | one DOI with multiple PMIDs is conflict-held"
)


# ------------------------------------------------------------
# Provider-only identities remain unresolved, not merged.
# ------------------------------------------------------------

rows = [
    citation_row(
        openalex_id="W20",
        title="",
        source="openalex",
    ),
    citation_row(
        omid="br/20",
        source="opencitations",
    ),
]

result = (
    impl.build_citation_publication_entities(
        rows
    )
)

entities = keyed(result)

assert (
    entities[
        "publication:openalex:W20"
    ]["identity_status"]
    == "provider_specific_unresolved"
)

assert (
    entities[
        "publication:omid:br/20"
    ]["identity_status"]
    == "provider_specific_unresolved"
)

print(
    "PASS | provider-only identities remain unresolved and separate"
)


# ------------------------------------------------------------
# A row with both provider-local IDs but no DOI/PMID fails closed.
# ------------------------------------------------------------

rows = [
    citation_row(
        openalex_id="W30",
        omid="br/30",
    ),
]

try:
    impl.build_citation_publication_entities(
        rows
    )

except RuntimeError as exc:
    assert (
        "provider-specific fallback would be ambiguous"
        in str(exc)
    )

else:
    raise AssertionError(
        "Ambiguous provider-local fallback did not fail closed"
    )

print(
    "PASS | ambiguous provider-only fallback fails closed"
)


# ------------------------------------------------------------
# Identical title/year does not merge different DOI groups.
# ------------------------------------------------------------

rows = [
    citation_row(
        doi="10.2/j",
        title="Same title",
        year="2022",
        openalex_id="W40",
    ),
    citation_row(
        doi="10.2/k",
        title="Same title",
        year="2022",
        openalex_id="W41",
    ),
]

result = (
    impl.build_citation_publication_entities(
        rows
    )
)

assert result["entity_count"] == 2

print(
    "PASS | citation title/year equality does not establish identity"
)


# ------------------------------------------------------------
# Synthetic order independence.
# ------------------------------------------------------------

rows = [
    citation_row(
        doi="10.2/a",
        pmid="1",
        openalex_id="W1",
    ),
    citation_row(
        source="opencitations",
        doi="10.2/a",
        pmid="1",
        omid="br/1",
    ),
    citation_row(
        doi="10.2/b",
        pmid="2",
        openalex_id="W2",
    ),
    citation_row(
        doi="10.2/c",
        pmid="2",
        openalex_id="W3",
    ),
    citation_row(
        openalex_id="W4",
    ),
    citation_row(
        source="opencitations",
        omid="br/4",
    ),
]

forward = (
    impl.build_citation_publication_entities(
        rows
    )
)

reverse = (
    impl.build_citation_publication_entities(
        list(reversed(rows))
    )
)

assert (
    impl.result_bytes(forward)
    ==
    impl.result_bytes(reverse)
)

print(
    "PASS | synthetic citation identity is order-independent"
)


# ------------------------------------------------------------
# Frozen Wave-0 smoke/regression test.
# ------------------------------------------------------------

path = (
    REPO
    / "results"
    / "07_comparative_landscape"
    / "citation_wave_0"
    / "neighbour_records.tsv"
)

real_rows = impl.read_tsv(path)

assert len(real_rows) == 33071

forward = (
    impl.build_citation_publication_entities(
        real_rows
    )
)

reverse = (
    impl.build_citation_publication_entities(
        list(reversed(real_rows))
    )
)

assert (
    impl.result_bytes(forward)
    ==
    impl.result_bytes(reverse)
)

assert forward["input_row_count"] == 33071

assert (
    sum(
        len(entity["source_row_sha256s"])
        for entity in forward["entities"]
    )
    == 33071
)

print(
    "PASS | frozen 33,071-row citation corpus preserves every provenance row"
)

print(
    "INFO | provisional citation publication entities = "
    f"{forward['entity_count']:,}"
)

print(
    "INFO | resolved citation identities = "
    f"{forward['resolved_identity_count']:,}"
)

print(
    "INFO | provider-specific unresolved identities = "
    f"{forward['provider_specific_unresolved_count']:,}"
)

print(
    "INFO | conflict-hold citation entities = "
    f"{forward['conflict_hold_entity_count']:,}"
)

print(
    "INFO | citation identity conflicts = "
    f"{forward['identity_conflict_count']:,}"
)

print()
print(
    "PASS | all citation publication-identity tests"
)
