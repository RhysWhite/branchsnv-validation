from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
import tempfile
import unittest

import triage_pre_review_text_reconciliation_v1 as reconciliation


class ReconciliationContractTests(
    unittest.TestCase
):

    def test_frozen_contract_validates(
        self,
    ):

        contract = (
            reconciliation.assert_frozen_contract()
        )

        self.assertEqual(
            contract[
                "design"
            ][
                "expected_reconciliation"
            ][
                "total_records"
            ],
            4499,
        )

        self.assertEqual(
            contract[
                "amendment"
            ][
                "historical_cache_dependency"
            ][
                "selected_lookup_count"
            ],
            9,
        )

    def test_selected_historical_dependency_validates(
        self,
    ):

        contract = (
            reconciliation.assert_frozen_contract()
        )

        mapping = (
            reconciliation.validate_historical_selected_dependency(
                contract
            )
        )

        self.assertEqual(
            len(
                mapping
            ),
            8666,
        )

    def test_output_schemas_have_no_scientific_decision_fields(
        self,
    ):

        contract = (
            reconciliation.assert_frozen_contract()
        )

        columns = (
            reconciliation.resolution_columns(
                contract
            )
            + reconciliation.normalized_text_columns(
                contract
            )
        )

        forbidden = {
            "decision",
            "scientific_label",
            "eligibility",
            "model_score",
            "threshold",
            "review_evidence",
            "operator",
            "notes",
        }

        self.assertTrue(
            forbidden.isdisjoint(
                columns
            )
        )

    def test_canonical_output_requires_exact_confirmation(
        self,
    ):

        with self.assertRaises(
            reconciliation.ReconciliationError
        ):
            reconciliation.validate_output_destination(
                reconciliation.RROOT,
                canonical_confirmation=None,
            )

        path = (
            reconciliation.validate_output_destination(
                reconciliation.RROOT,
                canonical_confirmation=(
                    reconciliation.CANONICAL_CONFIRMATION
                ),
            )
        )

        self.assertEqual(
            path,
            reconciliation.RROOT.resolve(),
        )

    def test_provider_identity_canonicalization(
        self,
    ):

        self.assertEqual(
            reconciliation.canonical_provider_id(
                "pubmed",
                "PMID:12345",
            ),
            "12345",
        )

        self.assertEqual(
            reconciliation.canonical_provider_id(
                "pubmed",
                "https://pubmed.ncbi.nlm.nih.gov/12345/",
            ),
            "12345",
        )

        self.assertEqual(
            reconciliation.canonical_provider_id(
                "openalex",
                "https://openalex.org/W123",
            ),
            "W123",
        )

    def test_three_usable_cached_rows_preserve_frozen_provenance(
        self,
    ):

        contract = (
            reconciliation.assert_frozen_contract()
        )

        checksum_map = (
            reconciliation.validate_historical_selected_dependency(
                contract
            )
        )

        amendment = contract[
            "amendment"
        ]

        _header, resolution_rows = (
            reconciliation.read_tsv(
                reconciliation.RROOT
                / "offline_cache_resolution.tsv"
            )
        )

        _header, cached_rows = (
            reconciliation.read_tsv(
                reconciliation.RROOT
                / "offline_cached_normalized_text.tsv"
            )
        )

        resolution_by_index = {
            int(
                row[
                    "retrieval_record_index"
                ]
            ):
                row
            for row in resolution_rows
        }

        cached_by_index = {
            int(
                row[
                    "retrieval_record_index"
                ]
            ):
                row
            for row in cached_rows
        }

        selected_by_index = {
            int(
                item[
                    "retrieval_record_index"
                ]
            ):
                item
            for item in amendment[
                "historical_cache_dependency"
            ][
                "selected_lookups"
            ]
        }

        self.assertEqual(
            set(
                cached_by_index
            ),
            {
                2595,
                4164,
                4248,
            },
        )

        allowed = {
            "provider_record_id",
            "provider_identity_status",
        }

        text_columns = (
            reconciliation.normalized_text_columns(
                contract
            )
        )

        for idx in sorted(
            cached_by_index
        ):

            cache_resolution = (
                resolution_by_index[
                    idx
                ]
            )

            normalized = (
                reconciliation._historical_normalized_record(
                    offline_resolution_row=cache_resolution,
                    selected_item=selected_by_index[
                        idx
                    ],
                    checksum_map=checksum_map,
                    amendment=amendment,
                )
            )

            reconstructed = (
                reconciliation._text_row(
                    retrieval_record_index=str(
                        idx
                    ),
                    screening_entity_id=cache_resolution[
                        "screening_entity_id"
                    ],
                    provider_used=cache_resolution[
                        "chosen_provider"
                    ],
                    provider_lookup_type=cache_resolution[
                        "chosen_lookup_type"
                    ],
                    normalized=normalized,
                    columns=text_columns,
                )
            )

            cached = (
                cached_by_index[
                    idx
                ]
            )

            differing = {
                key
                for key in text_columns
                if (
                    cached[
                        key
                    ]
                    != reconstructed[
                        key
                    ]
                )
            }

            self.assertEqual(
                differing,
                allowed,
            )

            self.assertEqual(
                cached[
                    "provider_identity_status"
                ],
                "matched_or_transport_validated",
            )

            self.assertTrue(
                cached[
                    "provider_record_id"
                ].strip()
            )


    def test_tsv_serialization_is_deterministic(
        self,
    ):

        columns = [
            "a",
            "b",
        ]

        rows = [
            {
                "a":
                    "1",
                "b":
                    "x",
            },
            {
                "a":
                    "2",
                "b":
                    "y",
            },
        ]

        with tempfile.TemporaryDirectory() as td:

            p1 = (
                Path(td)
                / "one.tsv"
            )

            p2 = (
                Path(td)
                / "two.tsv"
            )

            reconciliation.write_tsv(
                path=p1,
                columns=columns,
                rows=rows,
            )

            reconciliation.write_tsv(
                path=p2,
                columns=columns,
                rows=rows,
            )

            self.assertEqual(
                p1.read_bytes(),
                p2.read_bytes(),
            )


class ReconciliationStaticTests(
    unittest.TestCase
):

    def test_implementation_has_no_network_client_import(
        self,
    ):

        source = (
            Path(
                reconciliation.__file__
            ).read_text(
                encoding="utf-8"
            )
        )

        tree = ast.parse(
            source
        )

        imports = []

        for node in ast.walk(
            tree
        ):

            if isinstance(
                node,
                ast.Import,
            ):
                imports.extend(
                    alias.name
                    for alias in node.names
                )

            elif isinstance(
                node,
                ast.ImportFrom,
            ):
                imports.append(
                    node.module
                    or ""
                )

        forbidden = (
            "requests",
            "urllib",
            "httpx",
            "aiohttp",
            "socket",
        )

        for prefix in forbidden:

            self.assertFalse(
                any(
                    item == prefix
                    or item.startswith(
                        prefix
                        + "."
                    )
                    for item in imports
                ),
                prefix,
            )

    def test_final_output_names_exact(
        self,
    ):

        self.assertEqual(
            reconciliation.OUTPUT_FILENAMES,
            (
                "reconciled_resolution.tsv",
                "reconciled_normalized_text.tsv",
                "reconciliation_summary.json",
                "reconciliation_outputs.sha256",
            ),
        )


if __name__ == "__main__":
    unittest.main()
