#!/usr/bin/env python3

from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import importlib.util
import json
import sys


HERE = Path(__file__).resolve().parent

MODULE_PATH = (
    HERE
    / "scientific_screening_infrastructure.py"
)


spec = importlib.util.spec_from_file_location(
    "scientific_screening_infrastructure",
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
    fn,
):
    try:
        fn()

    except mod.ScreeningInfrastructureError:
        print(
            "PASS |",
            label,
        )
        return

    raise AssertionError(
        "Expected ScreeningInfrastructureError: "
        + label
    )


# ------------------------------------------------------------
# Historical subsidiary-hash contract.
# ------------------------------------------------------------

value = [
    {
        "b": 2,
        "a": 1,
    }
]

expected = hashlib.sha256(
    b'[{"a":1,"b":2}]'
).hexdigest()

assert mod.historical_compact_sha256(
    value
) == expected

assert mod.historical_compact_sha256(
    value
) != hashlib.sha256(
    b'[{"a":1,"b":2}]\n'
).hexdigest()

print(
    "PASS | historical no-newline subsidiary hash contract exact"
)


# ------------------------------------------------------------
# Publication title state.
# ------------------------------------------------------------

publication = {
    "screening_component_id":
        "publication_component:test",

    "screening_entity_class":
        "publication",

    "titles":
        [
            "Existing title",
        ],
}


assert mod.title_screenability(
    component=publication,
    overlay=None,
) == (
    "screenable",
    "Existing title",
    [
        "Existing title",
    ],
    "ready",
)

print(
    "PASS | ordinary titled publication ready"
)


assert mod.title_screenability(
    component=publication,
    overlay={
        "title_status":
            "title_resolved_exact",

        "resolved_title":
            "Recovered title",

        "title_variants_json":
            '["Recovered title"]',
    },
) == (
    "screenable",
    "Recovered title",
    [
        "Recovered title",
    ],
    "ready",
)

print(
    "PASS | exact recovered title ready"
)


equivalent = mod.title_screenability(
    component=publication,
    overlay={
        "title_status":
            "title_equivalent_variants",

        "resolved_title":
            "",

        "title_variants_json":
            '["Example title","Example title."]',
    },
)

assert equivalent[
    0
] == "screenable"

assert equivalent[
    1
] == ""

assert equivalent[
    3
] == "ready"

print(
    "PASS | equivalent title variants remain unselected but screenable"
)


assert mod.title_screenability(
    component=publication,
    overlay={
        "title_status":
            "title_unresolved",

        "resolved_title":
            "",

        "title_variants_json":
            "[]",
    },
) == (
    "blocked_title_unresolved",
    "",
    [],
    "blocked_metadata",
)

print(
    "PASS | unresolved title blocks metadata without exclusion"
)


conflict = mod.title_screenability(
    component=publication,
    overlay={
        "title_status":
            "title_conflict_hold",

        "resolved_title":
            "",

        "title_variants_json":
            '["Title A","Title B"]',
    },
)

assert conflict[
    0
] == "blocked_title_conflict"

assert conflict[
    3
] == "blocked_metadata"

print(
    "PASS | title conflict blocks metadata without winner"
)


expect_error(
    "title conflict cannot contain selected winner",
    lambda:
        mod.title_screenability(
            component=publication,
            overlay={
                "title_status":
                    "title_conflict_hold",

                "resolved_title":
                    "Title A",

                "title_variants_json":
                    '["Title A","Title B"]',
            },
        ),
)


expect_error(
    "unresolved title cannot contain inferred variant",
    lambda:
        mod.title_screenability(
            component=publication,
            overlay={
                "title_status":
                    "title_unresolved",

                "resolved_title":
                    "",

                "title_variants_json":
                    '["Invented"]',
            },
        ),
)


registry = {
    "screening_component_id":
        "software_registry_component:test",

    "screening_entity_class":
        "software_registry",

    "titles":
        [
            "Software tool",
        ],
}


assert mod.title_screenability(
    component=registry,
    overlay=None,
) == (
    "screenable",
    "Software tool",
    [
        "Software tool",
    ],
    "ready",
)

print(
    "PASS | software registry independently screenable"
)


expect_error(
    "software registry without name fails closed",
    lambda:
        mod.title_screenability(
            component={
                **registry,
                "titles": [],
            },
            overlay=None,
        ),
)


# ------------------------------------------------------------
# Output safety.
# ------------------------------------------------------------

with TemporaryDirectory() as tmp:
    root = Path(
        tmp
    )

    recon = root / "reconciliation"
    recon.mkdir()

    expect_error(
        "screening output cannot overwrite reconciliation root",
        lambda:
            mod.output_root_is_safe(
                output_root=recon,
                recon_root=recon,
            ),
    )

    expect_error(
        "screening output cannot live inside reconciliation root",
        lambda:
            mod.output_root_is_safe(
                output_root=
                    recon / "screening",
                recon_root=recon,
            ),
    )


print(
    "PASS | reconciliation evidence protected"
)

print(
    "PASS | hostile infrastructure tests complete"
)
