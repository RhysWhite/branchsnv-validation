from __future__ import annotations

from collections import Counter
from pathlib import Path
import copy
import hashlib
import json
import unittest

import retrieve_metadata_resolution_queue as transport
import pre_review_triage_future_text_wave_b_guard_v1 as guard
import pre_review_triage_future_text_wave_b_transport_evidence_adapter_v1 as adapter
import pre_review_triage_future_text_wave_b_runner_core_v1 as core


ROOT = Path(
    "experiments/07_comparative_landscape"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


class FutureWaveBExecutionPhase1Tests(
    unittest.TestCase
):

    def test_frozen_execution_design_validates(
        self,
    ):
        design = guard.load_frozen_design()

        self.assertEqual(
            design["design_id"],
            "PRE_REVIEW_TRIAGE_FUTURE_TEXT_WAVE_B_EXECUTION_V1",
        )

        self.assertEqual(
            design["status"],
            "FROZEN_PRE_IMPLEMENTATION",
        )

        self.assertEqual(
            design["wave_id"],
            "TRIAGE_FUTURE_TEXT_LIVE_WAVE_B",
        )


    def test_manifest_population_is_exact_40(
        self,
    ):
        rows = guard.read_manifest()

        self.assertEqual(
            len(rows),
            40,
        )

        self.assertEqual(
            Counter(
                row["frozen_route"]
                for row in rows
            ),
            Counter({
                "exact_work_id": 31,
                "exact_doi": 8,
                "exact_pmid": 1,
            }),
        )

        self.assertEqual(
            [
                int(row["request_sequence"])
                for row in rows
            ],
            list(
                range(
                    1,
                    41,
                )
            ),
        )


    def test_exact_pmid_is_request_32(
        self,
    ):
        row = (
            guard.manifest_row_for_sequence(
                32
            )
        )

        self.assertEqual(
            row["provider"],
            "openalex",
        )

        self.assertEqual(
            row["frozen_route"],
            "exact_pmid",
        )

        self.assertEqual(
            row["transport_route"],
            "work_by_pmid",
        )

        self.assertEqual(
            row["identifier_namespace"],
            "pmid",
        )


    def test_all_manifest_request_identities_reproduce(
        self,
    ):
        for row in guard.read_manifest():

            self.assertEqual(
                row[
                    "request_identity_sha256"
                ],
                guard.expected_request_identity(
                    row
                ),
            )


    def test_adapter_accepts_all_frozen_routes(
        self,
    ):
        rows = guard.read_manifest()

        observed = Counter()

        for row in rows:

            transport_row = (
                adapter.manifest_to_transport_row(
                    row
                )
            )

            self.assertTrue(
                transport_row[
                    "logical_lookup_id"
                ].startswith(
                    "triage_future_text_wave_b:"
                )
            )

            observed[
                transport_row[
                    "route"
                ]
            ] += 1

        self.assertEqual(
            observed,
            Counter({
                "work_by_openalex_id": 31,
                "work_by_doi": 8,
                "work_by_pmid": 1,
            }),
        )


    def test_pmid_normalization(
        self,
    ):
        self.assertEqual(
            adapter.normalize_pmid(
                "12345678"
            ),
            "12345678",
        )

        self.assertEqual(
            adapter.normalize_pmid(
                "PMID:12345678"
            ),
            "12345678",
        )

        self.assertEqual(
            adapter.normalize_pmid(
                "https://pubmed.ncbi.nlm.nih.gov/12345678/"
            ),
            "12345678",
        )

        with self.assertRaises(
            adapter.ProviderIdentityMismatch
        ):
            adapter.normalize_pmid(
                "1234x"
            )


    def _pmid_success_fixture(
        self,
    ):
        row = (
            guard.manifest_row_for_sequence(
                32
            )
        )

        transport_row = (
            adapter.manifest_to_transport_row(
                row
            )
        )

        work = (
            "https://openalex.org/W9999999999"
        )

        body = json.dumps({
            "id":
                work,

            "ids": {
                "openalex":
                    work,

                "pmid":
                    (
                        "https://pubmed.ncbi.nlm.nih.gov/"
                        + transport_row[
                            "identifier"
                        ]
                    ),
            },
        }).encode(
            "utf-8"
        )

        terminal = {
            "provider_identifier":
                work,
        }

        return (
            transport_row,
            terminal,
            body,
        )


    def test_exact_pmid_success_identity(
        self,
    ):
        (
            transport_row,
            terminal,
            body,
        ) = self._pmid_success_fixture()

        provider_record_id, status = (
            adapter.validate_success_provider_identity(
                transport_row=
                    transport_row,
                terminal=
                    terminal,
                body=
                    body,
                lookup_root=
                    Path("."),
                transport_module=
                    transport,
            )
        )

        self.assertEqual(
            provider_record_id,
            terminal[
                "provider_identifier"
            ],
        )

        self.assertEqual(
            status,
            "matched",
        )


    def test_exact_pmid_missing_identity_fails_closed(
        self,
    ):
        (
            transport_row,
            terminal,
            body,
        ) = self._pmid_success_fixture()

        value = json.loads(
            body.decode(
                "utf-8"
            )
        )

        value[
            "ids"
        ].pop(
            "pmid"
        )

        body = json.dumps(
            value
        ).encode(
            "utf-8"
        )

        with self.assertRaises(
            adapter.ProviderIdentityMismatch
        ):
            adapter.validate_success_provider_identity(
                transport_row=
                    transport_row,
                terminal=
                    terminal,
                body=
                    body,
                lookup_root=
                    Path("."),
                transport_module=
                    transport,
            )


    def test_exact_pmid_wrong_identity_fails_closed(
        self,
    ):
        (
            transport_row,
            terminal,
            body,
        ) = self._pmid_success_fixture()

        value = json.loads(
            body.decode(
                "utf-8"
            )
        )

        value[
            "ids"
        ][
            "pmid"
        ] = (
            "https://pubmed.ncbi.nlm.nih.gov/99999999"
        )

        body = json.dumps(
            value
        ).encode(
            "utf-8"
        )

        with self.assertRaises(
            adapter.ProviderIdentityMismatch
        ):
            adapter.validate_success_provider_identity(
                transport_row=
                    transport_row,
                terminal=
                    terminal,
                body=
                    body,
                lookup_root=
                    Path("."),
                transport_module=
                    transport,
            )


    def test_non_openalex_adapter_route_rejected(
        self,
    ):
        row = copy.deepcopy(
            guard.manifest_row_for_sequence(
                32
            )
        )

        row["provider"] = "pubmed"
        row["transport_route"] = (
            "record_by_pmid"
        )

        with self.assertRaises(
            adapter.AdapterError
        ):
            adapter.manifest_to_transport_row(
                row
            )


    def test_runner_preflight_is_openalex_only(
        self,
    ):
        row = copy.deepcopy(
            guard.manifest_row_for_sequence(
                32
            )
        )

        row["provider"] = "pubmed"

        with self.assertRaises(
            core.RunnerHalt
        ):
            core.preflight_environment(
                manifest_row=row,
                environ={},
            )


    def test_low_level_transport_builds_exact_pmid_request(
        self,
    ):
        row = (
            guard.manifest_row_for_sequence(
                32
            )
        )

        transport_row = (
            adapter.manifest_to_transport_row(
                row
            )
        )

        request = transport.build_request(
            transport_row,
            environ={},
        )

        self.assertEqual(
            request.provider,
            "openalex",
        )

        self.assertIn(
            "/works/pmid:",
            request.url,
        )


    def test_frozen_development_and_transport_sources_unchanged(
        self,
    ):
        expected = {
            (
                ROOT
                / "triage_pre_review_text_wave_b_guard_v1.py"
            ):
                "dfbd56b90ae47068f880328e21f3c3cc52aa86ef7c80db9c5f069342bc025cb3",

            (
                ROOT
                / "triage_pre_review_text_wave_b_transport_evidence_adapter_v1.py"
            ):
                "d6d04019521f1bec3d1d9b27014fb5718a774488d93b8a48852a483b51664a79",

            (
                ROOT
                / "triage_pre_review_text_wave_b_runner_core_v1.py"
            ):
                "3bdbf2d827eadc2c5d7d25593cba9231da65336722f70e01e59aeba3248f1b3f",

            (
                ROOT
                / "retrieve_metadata_resolution_queue.py"
            ):
                "9c8c11edbbec86e5cbf857f25c1bf576a0638ba5cdcf69d1fa2a8b8bfc1a994f",

            (
                ROOT
                / "t000002_authoritative_source_network_transport.py"
            ):
                "cc68579ff66af7633b7dd79520f748cfbe09cf8f95eaaf5cc927b833c4a7d962",

            (
                ROOT
                / "triage_pre_review_text_normalizer_v1.py"
            ):
                "cbe66fc9ab406fa5ee3745e099c16250c404a949c0f301e40a7397c285dc459d",
        }

        for path, digest in expected.items():

            self.assertEqual(
                sha256_file(
                    path
                ),
                digest,
                str(
                    path
                ),
            )


if __name__ == "__main__":
    unittest.main()
