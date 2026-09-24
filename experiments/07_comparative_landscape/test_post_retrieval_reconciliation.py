#!/usr/bin/env python3

from pathlib import Path
from tempfile import TemporaryDirectory
import copy
import csv
import importlib.util
import json
import sys


HERE = Path(__file__).resolve().parent

MODULE_PATH = (
    HERE
    / "post_retrieval_reconciliation.py"
)

spec = importlib.util.spec_from_file_location(
    "post_retrieval_reconciliation",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

mod = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = mod

spec.loader.exec_module(
    mod
)


def expect_error(
    label,
    function,
):
    try:
        function()

    except mod.ReconciliationError:
        print(
            "PASS |",
            label,
        )

        return

    raise AssertionError(
        "Expected ReconciliationError: "
        + label
    )


# ------------------------------------------------------------
# Title classification.
# ------------------------------------------------------------

status, values = mod.classify_title_values(
    [
        "Example title",
        "Example title",
    ]
)

assert status == "title_resolved_exact"
assert values == [
    "Example title"
]

print(
    "PASS | exact title resolves"
)


status, values = mod.classify_title_values(
    [
        "Example Title.",
        "example title",
    ]
)

assert (
    status
    == "title_equivalent_variants"
)

assert len(values) == 2

print(
    "PASS | token-equivalent titles remain unselected variants"
)


status, values = mod.classify_title_values(
    [
        "Alpha-beta",
        "Alphabeta",
    ]
)

assert (
    status
    == "title_equivalent_variants"
)

print(
    "PASS | compact-equivalent titles remain unselected variants"
)


status, values = mod.classify_title_values(
    [
        "Publication A",
        "Completely different publication",
    ]
)

assert status == "title_conflict_hold"

print(
    "PASS | substantive title disagreement remains conflict-held"
)


status, values = mod.classify_title_values(
    []
)

assert status == "title_unresolved"
assert values == []

print(
    "PASS | absent title remains unresolved"
)


# ------------------------------------------------------------
# Identifier conflict can never auto-resolve.
# ------------------------------------------------------------

conflict_component = {
    "component_id":
        "component:conflict",

    "questions":
        "adjudicate_identifier_conflict",

    "attention_reasons":
        "citation_identity_conflict",

    "source_providers":
        "openalex",

    "assignment_count":
        "1",
}

conflict_assignment = {
    "assignment_id":
        "assignment:1",

    "component_id":
        "component:conflict",

    "logical_lookup_id":
        "lookup:1",

    "provider":
        "openalex",

    "route":
        "work_by_doi",

    "identifier_namespace":
        "doi",

    "identifier":
        "10.1/example",

    "policy_class":
        "conflict_all_exact_evidence",

    "purposes":
        "adjudicate_identifier_conflict",
}

state = mod.derive_identifier_state(
    component=conflict_component,
    assignments=[
        conflict_assignment
    ],
    lookup_evidence={
        "lookup:1": {
            "status":
                "success",

            "requested_identifier":
                "doi:10.1/example",

            "identifiers": [
                "doi:10.1/example",
            ],

            "titles": [
                "Perfect agreement",
            ],
        },
    },
)

assert state[
    "identifier_status"
] == "identifier_conflict_hold"

assert state[
    "derived_doi"
] == ""

assert state[
    "derived_pmid"
] == ""

print(
    "PASS | identifier conflict never auto-resolves even with coherent evidence"
)


# ------------------------------------------------------------
# Native provider identity exact anchoring.
# ------------------------------------------------------------

native_component = {
    "component_id":
        "component:native",

    "questions":
        "resolve_provider_identity",

    "attention_reasons":
        "provider_specific_unresolved",

    "source_providers":
        "openalex",

    "assignment_count":
        "1",
}

native_assignment = {
    "assignment_id":
        "assignment:native",

    "component_id":
        "component:native",

    "logical_lookup_id":
        "lookup:native",

    "provider":
        "openalex",

    "route":
        "work_by_openalex_id",

    "identifier_namespace":
        "openalex",

    "identifier":
        "W1",

    "policy_class":
        "native_provider_identity",

    "purposes":
        "resolve_provider_identity",
}


anchored = mod.derive_identifier_state(
    component=native_component,
    assignments=[
        native_assignment
    ],
    lookup_evidence={
        "lookup:native": {
            "status":
                "success",

            "requested_identifier":
                "openalex:W1",

            "identifiers": [
                "doi:10.1234/example",
                "openalex:W1",
                "pmid:12345",
            ],

            "titles": [],
        },
    },
)

assert anchored == {
    "identifier_status":
        "provider_identity_anchored",

    "derived_doi":
        "10.1234/example",

    "derived_pmid":
        "12345",

    "identifier_evidence_lookup_ids":
        "lookup:native",
}

print(
    "PASS | one DOI plus one PMID creates exact native-provider anchors"
)


unanchored = mod.derive_identifier_state(
    component=native_component,
    assignments=[
        native_assignment
    ],
    lookup_evidence={
        "lookup:native": {
            "status":
                "success",

            "requested_identifier":
                "openalex:W1",

            "identifiers": [
                "openalex:W1",
            ],

            "titles": [],
        },
    },
)

assert (
    unanchored[
        "identifier_status"
    ]
    == "provider_identity_confirmed_unanchored"
)

print(
    "PASS | self-confirmed provider identity without DOI/PMID remains unanchored"
)


not_found = mod.derive_identifier_state(
    component=native_component,
    assignments=[
        native_assignment
    ],
    lookup_evidence={
        "lookup:native": {
            "status":
                "not_found",

            "requested_identifier":
                "openalex:W1",

            "identifiers": [],

            "titles": [],
        },
    },
)

assert (
    not_found[
        "identifier_status"
    ]
    == "provider_identity_not_found"
)

print(
    "PASS | provider not_found remains explicit"
)


expect_error(
    "successful native-provider lookup must self-confirm requested identity",
    lambda: mod.derive_identifier_state(
        component=native_component,
        assignments=[
            native_assignment
        ],
        lookup_evidence={
            "lookup:native": {
                "status":
                    "success",

                "requested_identifier":
                    "openalex:W1",

                "identifiers": [
                    "openalex:W2",
                ],

                "titles": [],
            },
        },
    ),
)


expect_error(
    "multiple DOI anchors fail closed",
    lambda: mod.derive_identifier_state(
        component=native_component,
        assignments=[
            native_assignment
        ],
        lookup_evidence={
            "lookup:native": {
                "status":
                    "success",

                "requested_identifier":
                    "openalex:W1",

                "identifiers": [
                    "openalex:W1",
                    "doi:10.1/a",
                    "doi:10.1/b",
                ],

                "titles": [],
            },
        },
    ),
)


expect_error(
    "multiple PMID anchors fail closed",
    lambda: mod.derive_identifier_state(
        component=native_component,
        assignments=[
            native_assignment
        ],
        lookup_evidence={
            "lookup:native": {
                "status":
                    "success",

                "requested_identifier":
                    "openalex:W1",

                "identifiers": [
                    "openalex:W1",
                    "pmid:1",
                    "pmid:2",
                ],

                "titles": [],
            },
        },
    ),
)


# ------------------------------------------------------------
# Title resolution must not infer or choose variant spelling.
# ------------------------------------------------------------

title_component = {
    "component_id":
        "component:title",

    "questions":
        "recover_title",

    "attention_reasons":
        "missing_title",

    "source_providers":
        "openalex",

    "assignment_count":
        "1",
}

title_assignment = {
    "assignment_id":
        "assignment:title",

    "component_id":
        "component:title",

    "logical_lookup_id":
        "lookup:title",

    "provider":
        "openalex",

    "route":
        "work_by_openalex_id",

    "identifier_namespace":
        "openalex",

    "identifier":
        "W1",

    "policy_class":
        "native_title_evidence",

    "purposes":
        "recover_title",
}


title_state = mod.derive_title_state(
    component=title_component,
    assignments=[
        title_assignment
    ],
    lookup_evidence={
        "lookup:title": {
            "status":
                "success",

            "requested_identifier":
                "openalex:W1",

            "identifiers": [
                "openalex:W1",
            ],

            "titles": [
                "Recovered title",
            ],
        },
    },
)

assert (
    title_state[
        "title_status"
    ]
    == "title_resolved_exact"
)

assert (
    title_state[
        "resolved_title"
    ]
    == "Recovered title"
)

print(
    "PASS | single exact title is recovered"
)


variant_state = mod.derive_title_state(
    component=title_component,
    assignments=[
        title_assignment
    ],
    lookup_evidence={
        "lookup:title": {
            "status":
                "success",

            "requested_identifier":
                "openalex:W1",

            "identifiers": [
                "openalex:W1",
            ],

            "titles": [
                "Recovered Title.",
                "recovered title",
            ],
        },
    },
)

assert (
    variant_state[
        "title_status"
    ]
    == "title_equivalent_variants"
)

assert (
    variant_state[
        "resolved_title"
    ]
    == ""
)

print(
    "PASS | equivalent title variants do not silently select a display string"
)


conflict_title_state = (
    mod.derive_title_state(
        component=title_component,
        assignments=[
            title_assignment
        ],
        lookup_evidence={
            "lookup:title": {
                "status":
                    "success",

                "requested_identifier":
                    "openalex:W1",

                "identifiers": [
                    "openalex:W1",
                ],

                "titles": [
                    "Publication A",
                    "Publication B",
                ],
            },
        },
    )
)

assert (
    conflict_title_state[
        "title_status"
    ]
    == "title_conflict_hold"
)

assert (
    conflict_title_state[
        "resolved_title"
    ]
    == ""
)

print(
    "PASS | residual title disagreement does not choose a winner"
)


# ------------------------------------------------------------
# Parser scope tests.
# ------------------------------------------------------------

openalex = mod.parse_openalex_record(
    json.dumps({
        "id":
            "https://openalex.org/W123",

        "ids": {
            "openalex":
                "https://openalex.org/W123",

            "doi":
                "https://doi.org/10.1000/example",

            "pmid":
                "https://pubmed.ncbi.nlm.nih.gov/12345",
        },

        "display_name":
            "Example",

        "title":
            "Example",
    }).encode(
        "utf-8"
    )
)

assert openalex[
    "identifiers"
] == [
    "doi:10.1000/example",
    "openalex:W123",
    "pmid:12345",
]

assert openalex[
    "titles"
] == [
    "Example"
]

print(
    "PASS | OpenAlex focal identifiers parse exactly"
)


opencitations = (
    mod.parse_opencitations_record(
        json.dumps([
            {
                "id":
                    (
                        "doi:10.1000/example "
                        "openalex:W123 "
                        "pmid:12345 "
                        "omid:br/01"
                    ),

                "title":
                    "Example",
            },
        ]).encode(
            "utf-8"
        )
    )
)

assert opencitations[
    "identifiers"
] == [
    "doi:10.1000/example",
    "omid:br/01",
    "openalex:W123",
    "pmid:12345",
]

print(
    "PASS | OpenCitations focal ID bundle parses exactly"
)


pubmed_xml = b"""<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345</PMID>
      <Article>
        <ArticleTitle>Focal title</ArticleTitle>
      </Article>
      <CommentsCorrectionsList>
        <CommentsCorrections>
          <PMID>99999</PMID>
        </CommentsCorrections>
      </CommentsCorrectionsList>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="pubmed">12345</ArticleId>
        <ArticleId IdType="doi">10.1000/focal</ArticleId>
      </ArticleIdList>
      <ReferenceList>
        <Reference>
          <ArticleIdList>
            <ArticleId IdType="pubmed">88888</ArticleId>
            <ArticleId IdType="doi">10.1000/reference</ArticleId>
          </ArticleIdList>
        </Reference>
      </ReferenceList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""

pubmed = mod.parse_pubmed_record(
    pubmed_xml,
    "pmid:12345",
)

assert pubmed[
    "identifiers"
] == [
    "doi:10.1000/focal",
    "pmid:12345",
]

assert "pmid:99999" not in (
    pubmed[
        "identifiers"
    ]
)

assert "pmid:88888" not in (
    pubmed[
        "identifiers"
    ]
)

assert "doi:10.1000/reference" not in (
    pubmed[
        "identifiers"
    ]
)

assert pubmed[
    "titles"
] == [
    "Focal title"
]

print(
    "PASS | PubMed parser excludes nested correction/reference identifiers"
)


# ------------------------------------------------------------
# Output boundary.
# ------------------------------------------------------------

with TemporaryDirectory() as tmp:
    tmp = Path(
        tmp
    )

    archive = (
        tmp
        / "archive"
    )

    archive.mkdir()

    expect_error(
        "derived output cannot equal retrieval archive",
        lambda: mod.output_root_is_safe(
            output_root=archive,
            archive_root=archive,
            source_root=HERE,
        ),
    )

    expect_error(
        "derived output cannot live inside retrieval archive",
        lambda: mod.output_root_is_safe(
            output_root=archive / "derived",
            archive_root=archive,
            source_root=HERE,
        ),
    )


print(
    "PASS | output boundary prevents retrieval-archive mutation"
)


# ------------------------------------------------------------
# Frozen expected count contract.
# ------------------------------------------------------------

fake_result = {
    "manifest": {
        "component_count":
            1342,

        "evidence_row_count":
            1847,

        "identifier_status_counts":
            copy.deepcopy(
                mod.EXPECTED_IDENTIFIER_STATUS_COUNTS
            ),

        "title_status_counts":
            copy.deepcopy(
                mod.EXPECTED_TITLE_STATUS_COUNTS
            ),

        "component_merge_performed":
            False,

        "scientific_screening_performed":
            False,
    },
}

mod.assert_frozen_counts(
    fake_result
)

print(
    "PASS | frozen reconciliation count contract accepted"
)


bad_result = copy.deepcopy(
    fake_result
)

bad_result[
    "manifest"
][
    "identifier_status_counts"
][
    "provider_identity_anchored"
] -= 1

expect_error(
    "frozen count drift fails closed",
    lambda: mod.assert_frozen_counts(
        bad_result
    ),
)


print(
    "PASS | hostile reconciliation tests complete"
)
