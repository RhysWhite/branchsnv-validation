from __future__ import annotations

import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import triage_pre_review_text_normalizer_v1 as n


RESULTS = Path(
    "results/07_comparative_landscape"
)


FORBIDDEN_PARTS = {
    "triage_validation_v1",
}


def allowed(
    path: Path,
) -> bool:

    return not any(
        part in FORBIDDEN_PARTS
        for part in path.parts
    )


def archived_success_records():

    for terminal_path in sorted(
        RESULTS.rglob(
            "terminal.json"
        )
    ):

        if not allowed(
            terminal_path
        ):
            continue

        try:
            terminal = json.loads(
                terminal_path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            continue

        provider = terminal.get(
            "provider"
        )

        if provider not in {
            "pubmed",
            "openalex",
        }:
            continue

        if (
            terminal.get(
                "terminal_status"
            )
            != "success"
        ):
            continue

        attempt_count = terminal.get(
            "attempt_count"
        )

        expected_sha = terminal.get(
            "terminal_body_sha256"
        )

        lookup_id = terminal.get(
            "logical_lookup_id"
        )

        if (
            attempt_count is None
            or not expected_sha
            or not lookup_id
        ):
            continue

        attempt_root = (
            terminal_path.parent
            / f"attempt_{int(attempt_count):02d}"
        )

        hops = sorted(
            attempt_root.glob(
                "hop_*_response.json"
            )
        )

        if not hops:
            continue

        metadata = json.loads(
            hops[-1].read_text(
                encoding="utf-8"
            )
        )

        body_path = (
            attempt_root
            / metadata[
                "body_file"
            ]
        )

        body = body_path.read_bytes()

        actual_sha = n.sha256_bytes(
            body
        )

        if (
            actual_sha
            != metadata[
                "body_sha256"
            ]
        ):
            raise AssertionError(
                "archived hop checksum mismatch"
            )

        if (
            actual_sha
            != expected_sha
        ):
            raise AssertionError(
                "terminal checksum mismatch"
            )

        yield {
            "provider":
                provider,
            "terminal":
                terminal,
            "body":
                body,
            "path":
                body_path,
        }


def pubmed_primary_pmid_from_body(
    body: bytes,
) -> str:

    root = ET.fromstring(
        body
    )

    records = [
        element
        for element in root.iter()
        if n.localname(
            element.tag
        ) in {
            "PubmedArticle",
            "PubmedBookArticle",
        }
    ]

    if len(records) != 1:
        raise AssertionError(
            "expected one PubMed record"
        )

    return n.primary_pubmed_pmid(
        records[0]
    )


class SyntheticTests(
    unittest.TestCase,
):

    def test_pubmed_multisection_order_and_metadata(
        self,
    ):

        body = b"""
        <PubmedArticleSet>
          <PubmedArticle>
            <MedlineCitation>
              <PMID>12345</PMID>
              <Article>
                <ArticleTitle>
                  Example title
                </ArticleTitle>
                <Abstract>
                  <AbstractText
                    Label="BACKGROUND"
                    NlmCategory="BACKGROUND"
                  >
                    First section.
                  </AbstractText>
                  <AbstractText
                    Label="RESULTS"
                    NlmCategory="RESULTS"
                  >
                    Second section.
                  </AbstractText>
                </Abstract>
              </Article>
            </MedlineCitation>
          </PubmedArticle>
        </PubmedArticleSet>
        """

        result = n.normalize_pubmed(
            body,
            "12345",
        )

        self.assertEqual(
            result[
                "abstract_status"
            ],
            "usable_abstract_pubmed",
        )

        self.assertEqual(
            result[
                "abstract_text"
            ],
            "First section. Second section.",
        )

        metadata = json.loads(
            result[
                "abstract_section_metadata_json"
            ]
        )

        self.assertEqual(
            [
                x[
                    "label"
                ]
                for x in metadata
            ],
            [
                "BACKGROUND",
                "RESULTS",
            ],
        )


    def test_pubmed_identity_mismatch(
        self,
    ):

        body = b"""
        <PubmedArticleSet>
          <PubmedArticle>
            <MedlineCitation>
              <PMID>999</PMID>
              <Article>
                <ArticleTitle>X</ArticleTitle>
                <Abstract>
                  <AbstractText>Y</AbstractText>
                </Abstract>
              </Article>
            </MedlineCitation>
          </PubmedArticle>
        </PubmedArticleSet>
        """

        result = n.normalize_pubmed(
            body,
            "123",
        )

        self.assertEqual(
            result[
                "abstract_status"
            ],
            "provider_identity_mismatch",
        )


    def test_openalex_ordering(
        self,
    ):

        body = json.dumps({
            "id":
                "https://openalex.org/W1",
            "display_name":
                "Title",
            "abstract_inverted_index": {
                "world":
                    [1],
                "Hello":
                    [0],
            },
        }).encode(
            "utf-8"
        )

        result = n.normalize_openalex(
            body
        )

        self.assertEqual(
            result[
                "abstract_status"
            ],
            "usable_abstract_openalex",
        )

        self.assertEqual(
            result[
                "abstract_text"
            ],
            "Hello world",
        )


    def test_openalex_duplicate_position_fails(
        self,
    ):

        body = json.dumps({
            "id":
                "https://openalex.org/W1",
            "abstract_inverted_index": {
                "A":
                    [0],
                "B":
                    [0],
            },
        }).encode(
            "utf-8"
        )

        result = n.normalize_openalex(
            body
        )

        self.assertEqual(
            result[
                "parser_status"
            ],
            "parser_failure",
        )

        self.assertEqual(
            result[
                "abstract_status"
            ],
            "parser_failure",
        )


    def test_openalex_gap_is_explicit(
        self,
    ):

        body = json.dumps({
            "id":
                "https://openalex.org/W1",
            "abstract_inverted_index": {
                "A":
                    [0],
                "C":
                    [2],
            },
        }).encode(
            "utf-8"
        )

        result = n.normalize_openalex(
            body
        )

        self.assertEqual(
            result[
                "abstract_status"
            ],
            "openalex_position_gap",
        )

        self.assertEqual(
            result[
                "abstract_text"
            ],
            "A C",
        )


    def test_openalex_null_is_absent(
        self,
    ):

        body = json.dumps({
            "id":
                "https://openalex.org/W1",
            "abstract_inverted_index":
                None,
        }).encode(
            "utf-8"
        )

        result = n.normalize_openalex(
            body
        )

        self.assertEqual(
            result[
                "abstract_status"
            ],
            "abstract_absent",
        )


class ArchivedPayloadTests(
    unittest.TestCase,
):

    @classmethod
    def setUpClass(
        cls,
    ):

        cls.records = list(
            archived_success_records()
        )

        cls.pubmed = [
            row
            for row in cls.records
            if row[
                "provider"
            ] == "pubmed"
        ]

        cls.openalex = [
            row
            for row in cls.records
            if row[
                "provider"
            ] == "openalex"
        ]


    def test_archived_provider_counts(
        self,
    ):

        self.assertEqual(
            len(
                self.pubmed
            ),
            62,
        )

        self.assertEqual(
            len(
                self.openalex
            ),
            1149,
        )


    def test_all_archived_pubmed_payloads(
        self,
    ):

        statuses = []

        multisection = 0

        for row in self.pubmed:

            pmid = (
                pubmed_primary_pmid_from_body(
                    row[
                        "body"
                    ]
                )
            )

            result = n.normalize_pubmed(
                row[
                    "body"
                ],
                pmid,
            )

            statuses.append(
                result[
                    "abstract_status"
                ]
            )

            metadata = json.loads(
                result[
                    "abstract_section_metadata_json"
                ]
            )

            if len(
                metadata
            ) > 1:
                multisection += 1


        self.assertEqual(
            statuses.count(
                "usable_abstract_pubmed"
            ),
            62,
        )

        self.assertGreater(
            multisection,
            0,
        )


    def test_all_archived_openalex_payloads(
        self,
    ):

        statuses = []

        for row in self.openalex:

            result = n.normalize_openalex(
                row[
                    "body"
                ]
            )

            statuses.append(
                result[
                    "abstract_status"
                ]
            )


        self.assertEqual(
            statuses.count(
                "usable_abstract_openalex"
            ),
            1023,
        )

        self.assertEqual(
            statuses.count(
                "abstract_absent"
            ),
            124,
        )

        self.assertEqual(
            statuses.count(
                "openalex_position_gap"
            ),
            2,
        )

        self.assertEqual(
            statuses.count(
                "parser_failure"
            ),
            0,
        )


if __name__ == "__main__":
    unittest.main()
