#!/usr/bin/env python3

from __future__ import annotations

import ast
import json
import re
import stat
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNNER_PATH = (
    ROOT
    / "comparator_benchmark_execution_v1_runner.py"
)

sys.path.insert(
    0,
    str(ROOT),
)

import comparator_benchmark_execution_v1_runner as runner


EXPECTED_METHODS = (
    "ARPIP",
    "FastML",
    "HomoplasyFinder",
    "PAML",
    "PastML",
    "POUTINE",
    "SNPPar",
    "TreeTime",
)


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def expect_failure(
    function,
    label: str,
    contains: str | None = None,
) -> Exception:
    try:
        function()
    except Exception as exc:
        if contains is not None:
            require(
                contains in str(exc),
                (
                    f"{label}: failure message differs: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )
        return exc

    raise AssertionError(
        f"{label}: did not fail closed"
    )


def executable(
    directory: Path,
    name: str,
) -> str:
    path = directory / name

    path.write_text(
        "#!/bin/sh\n"
        "exit 91\n"
    )

    path.chmod(
        path.stat().st_mode
        | stat.S_IXUSR
    )

    return str(
        path.resolve()
    )


def make_scenario(
    root: Path,
):
    scenario = root / "scenario"
    scenario.mkdir()

    sequences = {
        "A": "AAAAAAAAAA",
        "B": "AAAAAAAAAG",
        "C": "AAACAAAAAA",
        "D": "AAACAAAAAA",
    }

    positions = [
        4,
        10,
    ]

    benchmark_tree = (
        "((A:0.1,B:0.1):0.1,"
        "(C:0.1,D:0.1):0.1);"
    )

    (
        scenario
        / "alignment.fasta"
    ).write_text(
        runner.adapters.fasta_text(
            sequences
        )
    )

    (
        scenario
        / "tree.nwk"
    ).write_text(
        benchmark_tree
        + "\n"
    )

    (
        scenario
        / "variable_positions.txt"
    ).write_text(
        runner.adapters.positions_text(
            positions
        )
    )

    (
        scenario
        / "reference.gb"
    ).write_text(
        runner.adapters.minimal_genbank_text(
            "AAAAAAAAAA",
            positions,
            locus="SYNTHREF",
        )
    )

    inputs = (
        runner.scenario_inputs_from_directory(
            "SYNTHETIC_RUNNER_CASE",
            scenario,
        )
    )

    return (
        scenario,
        inputs,
        sequences,
        positions,
        benchmark_tree,
    )


def make_runtime(
    root: Path,
):
    tools = root / "tools"
    tools.mkdir()

    compiled = (
        tools
        / "compiled"
    )
    compiled.mkdir()

    for filename in (
        "coevolution.jar",
        "commons-math3-3.6.1.jar",
        "picocli-4.5.1.jar",
    ):
        (
            compiled
            / filename
        ).write_text(
            "synthetic placeholder\n"
        )

    jar = (
        tools
        / "HomoplasyFinder.jar"
    )

    jar.write_text(
        "synthetic placeholder\n"
    )

    envs = root / "envs"
    envs.mkdir()

    environment_dirs = {}

    for method in (
        "pastml",
        "poutine",
        "snppar",
        "treetime",
    ):
        path = (
            envs
            / method
        )

        (
            path
            / "bin"
        ).mkdir(
            parents=True
        )

        environment_dirs[
            method
        ] = str(
            path.resolve()
        )

    runtime_document = {
        "methods": {
            "ARPIP": {
                "executable":
                    executable(
                        tools,
                        "ARPIP",
                    ),
            },
            "FastML": {
                "executable":
                    executable(
                        tools,
                        "fastml",
                    ),
            },
            "HomoplasyFinder": {
                "java":
                    executable(
                        tools,
                        "java",
                    ),
                "jar":
                    str(
                        jar.resolve()
                    ),
            },
            "PAML": {
                "executable":
                    executable(
                        tools,
                        "baseml",
                    ),
            },
            "PastML": {
                "executable":
                    executable(
                        tools,
                        "pastml",
                    ),
                "environment_dir":
                    environment_dirs[
                        "pastml"
                    ],
            },
            "POUTINE": {
                "script":
                    executable(
                        tools,
                        "poutine.sh",
                    ),
                "environment_dir":
                    environment_dirs[
                        "poutine"
                    ],
            },
            "SNPPar": {
                "executable":
                    executable(
                        tools,
                        "snppar",
                    ),
                "environment_dir":
                    environment_dirs[
                        "snppar"
                    ],
            },
            "TreeTime": {
                "executable":
                    executable(
                        tools,
                        "treetime",
                    ),
                "environment_dir":
                    environment_dirs[
                        "treetime"
                    ],
            },
        }
    }

    runtime_path = (
        root
        / "runtime.json"
    )

    runtime_path.write_text(
        json.dumps(
            runtime_document,
            indent=2,
        )
        + "\n"
    )

    return (
        runner.load_runtime_config(
            runtime_path
        ),
        runtime_document,
        compiled,
    )


def populate_native_outputs(
    plans,
) -> None:

    arpip = plans["ARPIP"]

    (
        arpip.native_dir
        / "anc.fasta"
    ).write_text(
        ">V2\nAAAAAAAAAA\n"
        ">V5\nAAAAAAAAAA\n"
        ">root\nAAAAAAAAAA\n"
    )

    (
        arpip.native_dir
        / "tree.nwk"
    ).write_text(
        "((A:0.1,B:0.1)V2:0.1,"
        "(C:0.1,D:0.1)V5:0.1)root;\n"
    )

    (
        arpip.native_dir
        / "node_rel.txt"
    ).write_text(
        "synthetic node relationships\n"
    )


    fastml = plans["FastML"]

    (
        fastml.native_dir
        / "seq.joint.txt"
    ).write_text(
        ">A\nAAAAAAAAAA\n"
        ">B\nAAAAAAAAAG\n"
        ">C\nAAACAAAAAA\n"
        ">D\nAAACAAAAAA\n"
        ">N2\nAAAAAAAAAA\n"
        ">N3\nAAAAAAAAAA\n"
        ">N1\nAAAAAAAAAA\n"
    )

    (
        fastml.native_dir
        / "tree.newick.txt"
    ).write_text(
        "((A:0.1,B:0.1)N2:0.1,"
        "(C:0.1,D:0.1)N3:0.1)N1;\n"
    )


    hf = plans[
        "HomoplasyFinder"
    ]

    (
        hf.native_dir
        / "consistencyIndexReport_SYNTH.txt"
    ).write_text(
        "Position\tConsistencyIndex\tCountsACGT\t"
        "MinimumNumberChangesOnTree\n"
        "4\t0.5\t2:0:2:0\t2\n"
        "10\t1.0\t3:0:1:0\t1\n"
    )


    paml = plans["PAML"]

    (
        paml.native_dir
        / "rst"
    ).write_text(
        "Branch 1:    20..30\n"
        "Branch 2:    30..1  (A)\n"
        "Branch 3:    30..2  (B)\n"
        "Branch 4:    20..40\n"
        "Branch 5:    40..3  (C)\n"
        "Branch 6:    40..4  (D)\n"
        "List of extant and reconstructed sequences\n"
        "     7    10\n"
        "A                 AAAAAAAAAA\n"
        "B                 AAAAAAAAAG\n"
        "C                 AAACAAAAAA\n"
        "D                 AAACAAAAAA\n"
        "node #20          AAAAAAAAAA\n"
        "node #30          AAAAAAAAAA\n"
        "node #40          AAAAAAAAAA\n"
        "Overall accuracy\n"
    )

    (
        paml.native_dir
        / "main.out"
    ).write_text(
        "synthetic PAML main output\n"
    )


    pastml = plans["PastML"]

    (
        pastml.native_dir
        / "reconstructed_states.tsv"
    ).write_text(
        "node\tsite_4\tsite_10\n"
        "root\tA\tA\n"
        "n0\tA\tA\n"
        "n00\tA\tA\n"
        "A\tA\tA\n"
        "B\tA\tG\n"
        "C\tC\tA\n"
        "D\tC\tA\n"
    )

    (
        pastml.native_dir
        / "named.tree_tree.nwk"
    ).write_text(
        "((A:0.1,B:0.1)n0:0.1,"
        "(C:0.1,D:0.1)n00:0.1)root;\n"
    )


    poutine = plans["POUTINE"]

    (
        poutine.native_dir
        / "poutine.out"
    ).write_text(
        "segsite_ID\tphysical_pos\tallele1\tallele2\t"
        "a1_count\ta2_count\n"
        "1\t4\tA\tC\t1\t1\n"
        "2\t10\tA\tG\t1\t0\n"
    )


    snppar = plans["SNPPar"]

    snppar_tree = (
        "((A:0.1,B:0.1)N2:0.1,"
        "(C:0.1,D:0.1)N3:0.1)N1;"
    )

    (
        snppar.native_dir
        / "node_labelled_newick.tre"
    ).write_text(
        snppar_tree
        + "\n"
    )

    header = (
        "Position\tAncestor_Node\tDerived_Node\t"
        "Ancestor_Call\tDerived_Call\n"
    )

    (
        snppar.native_dir
        / "all_mutation_events.tsv"
    ).write_text(
        header
        + "4\tN2\tA\tA\tC\n"
        + "10\tN2\tB\tA\tG\n"
        + "10\tN3\tC\tA\tG\n"
    )

    (
        snppar.native_dir
        / "homoplasic_events_all_calls.tsv"
    ).write_text(
        header
        + "10\tN2\tB\tA\tG\n"
        + "10\tN3\tC\tA\tG\n"
    )


    treetime = plans["TreeTime"]

    (
        treetime.native_dir
        / "ancestral_sequences.fasta"
    ).write_text(
        ">NODE_0000000\nAAAAAAAAAA\n"
        ">NODE_0000001\nAAAAAAAAAA\n"
        ">A\nAAAAAAAAAG\n"
        ">B\nAAAAAAAAAA\n"
        ">NODE_0000002\nAAAAAAAAAA\n"
        ">C\nAAAAAAAAAG\n"
        ">D\nAAAAAAAAAA\n"
    )

    (
        treetime.native_dir
        / "annotated_tree.nexus"
    ).write_text(
        "#NEXUS\n"
        "Begin Taxa;\n"
        " Dimensions NTax=4;\n"
        " TaxLabels A B C D;\n"
        "End;\n"
        "Begin Trees;\n"
        " Tree tree1="
        "((A:0.1[&mutations=\"A10G\"],"
        "B:0.1)NODE_0000001:0.1,"
        "(C:0.1[&mutations=\"A10G\"],"
        "D:0.1)NODE_0000002:0.1)"
        "NODE_0000000:0.001;\n"
        "End;\n"
    )


def validate_static_boundaries() -> None:
    text = RUNNER_PATH.read_text()

    forbidden_root = (
        "/home/rwhite/"
        + "branchsnv-comparator-"
    )

    require(
        forbidden_root
        not in text,
        "runner hard-codes comparator installation root",
    )

    canonical_identifier = re.compile(
        r"\bS(?:00[1-9]|0[1-9][0-9]|1[0-4][0-9]|150)\b"
    )

    require(
        canonical_identifier.search(
            text
        )
        is None,
        "runner embeds canonical scenario identifier",
    )

    tree = ast.parse(text)

    imports = []

    for node in ast.walk(tree):
        if isinstance(
            node,
            ast.Import,
        ):
            imports.extend(
                alias.name
                for alias
                in node.names
            )

        elif isinstance(
            node,
            ast.ImportFrom,
        ):
            if node.module:
                imports.append(
                    node.module
                )

    require(
        not any(
            name == "metrics"
            or name.endswith(".metrics")
            for name
            in imports
        ),
        "runner imports scoring metrics",
    )

    for node in ast.walk(tree):
        if not isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        arguments = (
            list(
                node.args.posonlyargs
            )
            + list(
                node.args.args
            )
            + list(
                node.args.kwonlyargs
            )
        )

        require(
            not any(
                "truth"
                in arg.arg.lower()
                for arg
                in arguments
            ),
            (
                "runner exposes truth-like "
                f"function parameter: {node.name}"
            ),
        )

    print(
        "PASS | reusable runner has no hard-coded comparator root"
    )
    print(
        "PASS | reusable runner embeds no canonical scenario identifier"
    )
    print(
        "PASS | execution runner does not import scoring metrics"
    )
    print(
        "PASS | execution runner exposes no truth-like function parameter"
    )


def main() -> None:
    print(
        "===== COMPARATOR BENCHMARK RUNNER V3 PERMANENT VALIDATION ====="
    )

    runner.verify_frozen_identities()

    require(
        tuple(
            runner.METHODS
        )
        == EXPECTED_METHODS,
        "frozen method set differs",
    )

    recipes = (
        runner.load_frozen_environment_recipes()
    )

    require(
        len(recipes)
        == len(EXPECTED_METHODS)
        and set(recipes)
        == set(EXPECTED_METHODS),
        "frozen environment recipe set differs",
    )

    print(
        "PASS | frozen identities validate"
    )
    print(
        "PASS | exactly eight comparator workflows are covered"
    )

    validate_static_boundaries()

    with tempfile.TemporaryDirectory(
        prefix="branchsnv_runner_v3_validation_"
    ) as raw:

        tmp = Path(raw)

        (
            scenario,
            inputs,
            sequences,
            positions,
            benchmark_tree,
        ) = make_scenario(
            tmp
        )

        (
            runtime,
            runtime_document,
            poutine_compiled,
        ) = make_runtime(
            tmp
        )

        print(
            "PASS | synthetic comparator-facing fixture created"
        )
        print(
            "PASS | synthetic runtime configuration validates"
        )


        # ---------------------------------------------------------
        # Fail-closed input/configuration boundaries.
        # ---------------------------------------------------------

        preexisting = (
            tmp
            / "already_exists"
        )
        preexisting.mkdir()

        expect_failure(
            lambda:
                runner.assert_new_result_root(
                    preexisting
                ),
            "pre-existing result root",
        )

        missing = (
            tmp
            / "missing_input"
        )
        missing.mkdir()

        (
            missing
            / "alignment.fasta"
        ).write_text(
            runner.adapters.fasta_text(
                sequences
            )
        )

        expect_failure(
            lambda:
                runner.scenario_inputs_from_directory(
                    "SYNTHETIC_MISSING_INPUT",
                    missing,
                ),
            "missing comparator-facing input",
        )

        malformed_runtime = (
            tmp
            / "runtime_malformed.json"
        )

        malformed_runtime.write_text(
            json.dumps(
                {
                    "methods":
                        runtime_document[
                            "methods"
                        ],
                    "unexpected":
                        "field",
                },
                indent=2,
            )
            + "\n"
        )

        expect_failure(
            lambda:
                runner.load_runtime_config(
                    malformed_runtime
                ),
            "malformed runtime configuration",
        )

        expect_failure(
            lambda:
                runner.build_command_plan(
                    method="UNKNOWN_METHOD",
                    inputs=inputs,
                    runtime_config=runtime,
                    plan_root=(
                        tmp
                        / "unknown_method"
                    ),
                    scenario_seed=17,
                ),
            "unknown comparator method",
        )

        print(
            "PASS | missing inputs, malformed config, unknown methods and existing roots fail closed"
        )


        # Frozen identity mismatch must fail closed without modifying
        # any repository artifact.
        original_authorization_path = (
            runner.AUTHORIZATION_PATH
        )

        false_authorization = (
            tmp
            / "authorization.json"
        )

        false_authorization.write_text(
            "{}\n"
        )

        runner.AUTHORIZATION_PATH = (
            false_authorization
        )

        try:
            expect_failure(
                runner.verify_frozen_identities,
                "inconsistent frozen identities",
            )
        finally:
            runner.AUTHORIZATION_PATH = (
                original_authorization_path
            )

        runner.verify_frozen_identities()

        print(
            "PASS | inconsistent frozen identity state fails closed"
        )


        # ---------------------------------------------------------
        # Command-plan construction.
        # ---------------------------------------------------------

        plans_root = (
            tmp
            / "plans"
        )
        plans_root.mkdir()

        plans = {}

        for method in EXPECTED_METHODS:
            plans[
                method
            ] = (
                runner.build_command_plan(
                    method=method,
                    inputs=inputs,
                    runtime_config=runtime,
                    plan_root=(
                        plans_root
                        / method
                    ),
                    scenario_seed=17,
                )
            )

        require(
            set(plans)
            == set(
                EXPECTED_METHODS
            ),
            "not all method plans were built",
        )

        require(
            all(
                plan.cwd
                == plan.native_dir
                for plan
                in plans.values()
            ),
            "a method plan escapes its isolated native working directory",
        )

        poutine = plans[
            "POUTINE"
        ]

        require(
            (
                poutine.native_dir
                / "compiled"
            ).is_symlink(),
            "POUTINE compiled runtime link absent",
        )

        require(
            (
                poutine.native_dir
                / "compiled"
            ).resolve()
            == poutine_compiled.resolve(),
            "POUTINE compiled runtime link differs",
        )

        poutine_environment = (
            runner.build_subprocess_environment(
                plan=poutine,
                runtime_config=runtime,
            )
        )

        require(
            poutine_environment[
                "PATH"
            ].split(
                runner.os.pathsep
            )[0]
            == str(
                Path(
                    runtime[
                        "POUTINE"
                    ][
                        "environment_dir"
                    ]
                )
                / "bin"
            ),
            "POUTINE isolated environment does not lead PATH",
        )

        snppar_environment = (
            runner.build_subprocess_environment(
                plan=plans[
                    "SNPPar"
                ],
                runtime_config=runtime,
            )
        )

        require(
            snppar_environment.get(
                "PYTHONNOUSERSITE"
            )
            == "1",
            "SNPPar frozen environment overlay differs",
        )

        require(
            (
                poutine.generated_dir
                / "positions.map"
            ).read_text()
            == (
                "1\tmarker1\t0\t4\n"
                "1\tmarker2\t0\t10\n"
            ),
            "POUTINE physical-position map differs",
        )

        require(
            (
                plans[
                    "TreeTime"
                ].argv[
                    1
                ]
                == "ancestral"
            ),
            "TreeTime ancestral command differs",
        )

        require(
            not any(
                "homoplasy"
                in token.lower()
                for token
                in plans[
                    "TreeTime"
                ].argv
            ),
            "TreeTime homoplasy CLI entered command plan",
        )

        print(
            "PASS | all eight frozen command plans construct"
        )
        print(
            "PASS | every method uses an isolated working directory"
        )
        print(
            "PASS | POUTINE relative runtime and isolated PATH are preserved"
        )
        print(
            "PASS | SNPPar frozen environment overlay is preserved"
        )
        print(
            "PASS | TreeTime uses ancestral workflow only"
        )


        # ---------------------------------------------------------
        # Native-output normalization.
        # ---------------------------------------------------------

        populate_native_outputs(
            plans
        )

        normalized = {
            method:
                runner.normalize_native_outputs(
                    plan=plan,
                    inputs=inputs,
                )
            for method, plan
            in plans.items()
        }

        branch_only = {
            "ARPIP",
            "FastML",
            "PAML",
            "PastML",
        }

        recurrent_only = {
            "HomoplasyFinder",
            "POUTINE",
        }

        dual = {
            "SNPPar",
            "TreeTime",
        }

        for method in branch_only:
            require(
                normalized[
                    method
                ][
                    "branch_events"
                ],
                f"{method}: branch predictions absent",
            )

            require(
                normalized[
                    method
                ][
                    "recurrent_sites"
                ]
                == [],
                f"{method}: unexpected recurrent predictions",
            )

        for method in recurrent_only:
            require(
                normalized[
                    method
                ][
                    "branch_events"
                ]
                == [],
                f"{method}: unexpected branch predictions",
            )

            require(
                normalized[
                    method
                ][
                    "recurrent_sites"
                ],
                f"{method}: recurrent predictions absent",
            )

        for method in dual:
            require(
                normalized[
                    method
                ][
                    "branch_events"
                ],
                f"{method}: branch predictions absent",
            )

            require(
                normalized[
                    method
                ][
                    "recurrent_sites"
                ],
                f"{method}: recurrent predictions absent",
            )

        require(
            normalized[
                "SNPPar"
            ][
                "recurrent_sites"
            ]
            == [
                {
                    "position":
                        "10",
                    "reported_recurrence_count_if_available":
                        "2",
                }
            ],
            "SNPPar homoplasy normalization differs",
        )

        require(
            normalized[
                "TreeTime"
            ][
                "recurrent_sites"
            ]
            == [
                {
                    "position":
                        "10",
                    "reported_recurrence_count_if_available":
                        "2",
                }
            ],
            "TreeTime recurrence normalization differs",
        )

        pastml_positions = {
            event[
                "position"
            ]
            for event
            in normalized[
                "PastML"
            ][
                "branch_events"
            ]
        }

        require(
            pastml_positions
            <= {
                "4",
                "10",
            },
            "PastML projected coordinates leaked",
        )

        canonical_edges = set(
            runner.adapters
            .canonical_edge_ids_by_node(
                benchmark_tree
            )
            .values()
        )

        for method in (
            branch_only
            | dual
        ):
            for event in normalized[
                method
            ][
                "branch_events"
            ]:
                require(
                    event[
                        "edge_id"
                    ]
                    in canonical_edges,
                    (
                        f"{method}: comparator-specific "
                        "node identity leaked"
                    ),
                )

        print(
            "PASS | all eight native-output contracts normalize"
        )
        print(
            "PASS | endpoint-specific and dual-endpoint behavior is preserved"
        )
        print(
            "PASS | PastML projected positions restore genomic coordinates"
        )
        print(
            "PASS | SNPPar homoplasy source and TreeTime recurrence contracts are preserved"
        )
        print(
            "PASS | normalized branch identities use canonical descendant-tip edges"
        )


        # Ambiguous required native output is an unexpected output-contract
        # state and must fail closed.
        ambiguous_plan = (
            runner.build_command_plan(
                method="HomoplasyFinder",
                inputs=inputs,
                runtime_config=runtime,
                plan_root=(
                    plans_root
                    / "HF_AMBIGUOUS"
                ),
                scenario_seed=17,
            )
        )

        (
            ambiguous_plan.native_dir
            / "consistencyIndexReport_A.txt"
        ).write_text(
            "Position\tConsistencyIndex\n"
            "4\t0.5\n"
        )

        (
            ambiguous_plan.native_dir
            / "consistencyIndexReport_B.txt"
        ).write_text(
            "Position\tConsistencyIndex\n"
            "4\t0.5\n"
        )

        expect_failure(
            lambda:
                runner.normalize_native_outputs(
                    plan=ambiguous_plan,
                    inputs=inputs,
                ),
            "ambiguous native-output contract",
            "expected exactly one native output",
        )

        print(
            "PASS | unexpected ambiguous native-output contract fails closed"
        )


        # ---------------------------------------------------------
        # Mocked execution completion states.
        # ---------------------------------------------------------

        original_popen = (
            runner.subprocess.Popen
        )

        def forbidden_popen(
            *args,
            **kwargs,
        ):
            raise AssertionError(
                "real subprocess execution attempted during validation"
            )

        runner.subprocess.Popen = (
            forbidden_popen
        )

        try:
            execution_root = (
                tmp
                / "execution"
            )
            execution_root.mkdir()


            success_plan = (
                runner.build_command_plan(
                    method="POUTINE",
                    inputs=inputs,
                    runtime_config=runtime,
                    plan_root=(
                        execution_root
                        / "SUCCESS"
                    ),
                    scenario_seed=17,
                )
            )

            def mock_success(
                plan,
                environment,
                timeout_seconds,
            ):
                require(
                    plan.cwd
                    == plan.native_dir,
                    "mock success observed non-isolated cwd",
                )

                (
                    plan.native_dir
                    / "poutine.out"
                ).write_text(
                    "segsite_ID\tphysical_pos\tallele1\tallele2\t"
                    "a1_count\ta2_count\n"
                    "1\t4\tA\tC\t1\t1\n"
                    "2\t10\tA\tG\t1\t0\n"
                )

                return (
                    runner.ExecutionOutcome(
                        returncode=0,
                        stdout="synthetic stdout\n",
                        stderr="synthetic stderr\n",
                        timed_out=False,
                    )
                )

            success = (
                runner.execute_command_plan(
                    plan=success_plan,
                    inputs=inputs,
                    runtime_config=runtime,
                    timeout_seconds=30,
                    executor=mock_success,
                )
            )

            require(
                success[
                    "status"
                ]
                == "SUCCESS",
                "mocked success did not complete successfully",
            )

            require(
                success[
                    "scoring_performed"
                ]
                is False,
                "execution layer claims scoring",
            )

            require(
                success[
                    "normalized_predictions_finalized"
                ]
                is True,
                "successful predictions were not finalized",
            )

            normalized_path = (
                success_plan.plan_root
                / "normalized_predictions.json"
            )

            require(
                normalized_path.is_file(),
                "successful prediction artifact absent",
            )

            require(
                runner.sha256_file(
                    normalized_path
                )
                == success[
                    "normalized_predictions_sha256"
                ],
                "prediction checksum differs",
            )

            require(
                (
                    success_plan.plan_root
                    / "stdout.txt"
                ).read_text()
                == "synthetic stdout\n",
                "stdout preservation differs",
            )

            require(
                (
                    success_plan.plan_root
                    / "stderr.txt"
                ).read_text()
                == "synthetic stderr\n",
                "stderr preservation differs",
            )

            print(
                "PASS | mocked success preserves provenance and finalizes checksummed predictions"
            )


            def new_execution_plan(
                name: str,
            ):
                return (
                    runner.build_command_plan(
                        method="POUTINE",
                        inputs=inputs,
                        runtime_config=runtime,
                        plan_root=(
                            execution_root
                            / name
                        ),
                        scenario_seed=17,
                    )
                )


            nonzero_plan = (
                new_execution_plan(
                    "NONZERO"
                )
            )

            nonzero = (
                runner.execute_command_plan(
                    plan=nonzero_plan,
                    inputs=inputs,
                    runtime_config=runtime,
                    timeout_seconds=30,
                    executor=lambda p, e, t:
                        runner.ExecutionOutcome(
                            returncode=23,
                            stdout="partial stdout\n",
                            stderr="failure stderr\n",
                            timed_out=False,
                        ),
                )
            )

            require(
                nonzero[
                    "status"
                ]
                == "FAILED"
                and nonzero[
                    "failure_type"
                ]
                == "nonzero_exit",
                "non-zero completion state differs",
            )

            require(
                not (
                    nonzero_plan.plan_root
                    / "normalized_predictions.json"
                ).exists(),
                "non-zero exit produced predictions",
            )


            timeout_plan = (
                new_execution_plan(
                    "TIMEOUT"
                )
            )

            timeout = (
                runner.execute_command_plan(
                    plan=timeout_plan,
                    inputs=inputs,
                    runtime_config=runtime,
                    timeout_seconds=30,
                    executor=lambda p, e, t:
                        runner.ExecutionOutcome(
                            returncode=None,
                            stdout="partial stdout\n",
                            stderr="partial stderr\n",
                            timed_out=True,
                        ),
                )
            )

            require(
                timeout[
                    "status"
                ]
                == "FAILED"
                and timeout[
                    "failure_type"
                ]
                == "timeout",
                "timeout completion state differs",
            )

            require(
                not (
                    timeout_plan.plan_root
                    / "normalized_predictions.json"
                ).exists(),
                "timeout produced predictions",
            )


            missing_plan = (
                new_execution_plan(
                    "MISSING_OUTPUT"
                )
            )

            missing_result = (
                runner.execute_command_plan(
                    plan=missing_plan,
                    inputs=inputs,
                    runtime_config=runtime,
                    timeout_seconds=30,
                    executor=lambda p, e, t:
                        runner.ExecutionOutcome(
                            returncode=0,
                            stdout="completed\n",
                            stderr="",
                            timed_out=False,
                        ),
                )
            )

            require(
                missing_result[
                    "status"
                ]
                == "FAILED"
                and missing_result[
                    "failure_type"
                ]
                == "native_output_failure",
                "missing-output completion state differs",
            )

            require(
                not (
                    missing_plan.plan_root
                    / "normalized_predictions.json"
                ).exists(),
                "missing output produced predictions",
            )


            malformed_plan = (
                new_execution_plan(
                    "MALFORMED_OUTPUT"
                )
            )

            def mock_malformed(
                plan,
                environment,
                timeout_seconds,
            ):
                (
                    plan.native_dir
                    / "poutine.out"
                ).write_text(
                    "not\tthe\tfrozen\tschema\n"
                    "1\t2\t3\t4\n"
                )

                return (
                    runner.ExecutionOutcome(
                        returncode=0,
                        stdout="completed\n",
                        stderr="",
                        timed_out=False,
                    )
                )

            malformed = (
                runner.execute_command_plan(
                    plan=malformed_plan,
                    inputs=inputs,
                    runtime_config=runtime,
                    timeout_seconds=30,
                    executor=mock_malformed,
                )
            )

            require(
                malformed[
                    "status"
                ]
                == "FAILED"
                and malformed[
                    "failure_type"
                ]
                == "normalization_failure",
                "malformed-output completion state differs",
            )

            require(
                not (
                    malformed_plan.plan_root
                    / "normalized_predictions.json"
                ).exists(),
                "malformed output produced predictions",
            )


            launch_plan = (
                new_execution_plan(
                    "LAUNCH_FAILURE"
                )
            )

            def mock_launch_failure(
                plan,
                environment,
                timeout_seconds,
            ):
                raise OSError(
                    "synthetic launch failure"
                )

            launch = (
                runner.execute_command_plan(
                    plan=launch_plan,
                    inputs=inputs,
                    runtime_config=runtime,
                    timeout_seconds=30,
                    executor=mock_launch_failure,
                )
            )

            require(
                launch[
                    "status"
                ]
                == "FAILED"
                and launch[
                    "failure_type"
                ]
                == "launch_failure",
                "launch-failure completion state differs",
            )

            require(
                not (
                    launch_plan.plan_root
                    / "normalized_predictions.json"
                ).exists(),
                "launch failure produced predictions",
            )

        finally:
            runner.subprocess.Popen = (
                original_popen
            )

        print(
            "PASS | non-zero, timeout, missing-output, malformed-output and launch failures are explicit"
        )
        print(
            "PASS | failures never become zero-accuracy predictions"
        )
        print(
            "PASS | real subprocess execution is blocked during validator run"
        )


    print(
        "PASS | no third-party comparator executed"
    )
    print(
        "PASS | no canonical benchmark scenario accessed"
    )
    print(
        "PASS | no benchmark truth accessed"
    )
    print(
        "PASS | prediction generation remains separate from scoring"
    )
    print(
        "RUNNER_V3_PERMANENT_VALIDATION=PASS"
    )


if __name__ == "__main__":
    main()
