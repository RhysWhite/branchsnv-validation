from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from dataclasses import dataclass
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Iterable, Sequence


ROOT_REL = "experiments/07_comparative_landscape"

CANDIDATE_DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_model_candidates_v1_design.json"
)

AMENDMENT_REL = (
    ROOT_REL
    + "/pre_review_triage_model_candidates_v1_amendment_001_design.json"
)

ENVIRONMENT_STATE_REL = (
    ROOT_REL
    + "/pre_review_triage_environment_state_v1_design.json"
)

CANONICAL_TEXT_REL = (
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1/"
    "reconciled_normalized_text.tsv"
)

CAMPAIGN_REL = (
    ROOT_REL
    + "/c000001_campaign_execution_v4.py"
)

# This file is intentionally absent in the implementation freeze.
# A later, separately frozen execution-authorization stage may create it.
EXECUTION_AUTHORIZATION_REL = (
    ROOT_REL
    + "/pre_review_triage_evaluator_v1_execution_authorization.json"
)

EVALUATOR_IMPLEMENTATION_REL = (
    ROOT_REL
    + "/pre_review_triage_evaluator_v1.py"
)

AUTHORIZED_OUTPUT_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_evaluator_v1/"
    "development_evaluation_v1"
)

EXECUTION_ID = (
    "TRIAGE-DEV-EVAL-V1-001"
)

EXPECTED_IMPLEMENTATION_PARENT = (
    "b0c068d7abd9853088ae3134249fdf89ffa79ba0"
)

EXPECTED_TEXT_SHA256 = (
    "8c897444fe1a4d26226c8ecb798cd9d08bd3acc362aead972fdbee80d326785b"
)

EXPECTED_ENVIRONMENT_PREFIX = str(
    Path.home()
    / ".conda/envs/branchsnv-triage-v1"
)

POSITIVE_LABEL = "retain_for_method_assessment"
NEGATIVE_LABEL = "exclude"

POSITIVE_NUMERIC = 1
NEGATIVE_NUMERIC = 0

BATCH_IDS = (
    "B000001",
    "B000002",
    "B000003",
    "B000004",
    "B000005",
    "B000006",
    "B000007",
    "B000008",
    "B000009",
)

CANDIDATE_ORDER = (
    "logistic_regression_balanced_l2_v1",
    "linear_svc_balanced_l2_v1",
    "complement_nb_v1",
)


class EvaluatorError(RuntimeError):
    pass


class ExecutionNotAuthorized(EvaluatorError):
    pass


@dataclass(frozen=True)
class DevelopmentRecord:
    screening_entity_id: str
    batch_id: str
    label_text: str
    label_numeric: int
    document: str


@dataclass(frozen=True)
class CandidateAggregate:
    candidate_id: str
    macro_mean_ap: float
    minimum_ap: float
    median_ap: float


def repo_root() -> Path:
    return Path(
        subprocess.check_output(
            [
                "git",
                "rev-parse",
                "--show-toplevel",
            ],
            text=True,
        ).strip()
    ).resolve()


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        return list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


def load_campaign_module():
    path = (
        repo_root()
        / CAMPAIGN_REL
    )

    spec = importlib.util.spec_from_file_location(
        "branchsnv_triage_campaign",
        path,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise EvaluatorError(
            "Unable to load campaign execution layer"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        spec.name
    ] = module

    spec.loader.exec_module(
        module
    )

    return module


def reconstruct_development_labels() -> tuple[
    dict[str, str],
    dict[str, str],
]:
    """
    Reconstruct the frozen 4,500 development labels and batch membership.

    Returns
    -------
    labels
        screening_entity_id -> terminal development disposition.
    batches
        screening_entity_id -> historical development batch.
    """

    m = load_campaign_module()
    guard = m.load_guard()

    _, membership = guard.read_tsv(
        m.EXECUTION_ROOT
        / "batch_membership.tsv"
    )

    _, ledger = guard.read_tsv(
        m.LEDGER
    )

    membership_ids = {
        row["screening_entity_id"]
        for row in membership
    }

    latest = {}

    for row in ledger:
        latest[
            row["screening_entity_id"]
        ] = row

    labels: dict[str, str] = {}
    batches: dict[str, str] = {}

    terminal_events = {
        "record_decision",
        "superseding_record_decision",
    }

    terminal_decisions = {
        NEGATIVE_LABEL,
        POSITIVE_LABEL,
    }

    for entity_id, row in latest.items():

        if entity_id not in membership_ids:
            continue

        if row["event_type"] not in terminal_events:
            continue

        if row["record_decision"] not in terminal_decisions:
            continue

        labels[
            entity_id
        ] = row[
            "record_decision"
        ]

        batches[
            entity_id
        ] = row[
            "batch_id"
        ]

    for batch in m.BATCHES:

        batch_id = batch[
            "batch_id"
        ]

        transaction_id = batch[
            "transaction_id"
        ]

        identity = m.build_target_identity(
            guard=guard,
            batch_id=batch_id,
        )

        _, proposals = guard.read_tsv(
            m.proposal_path(
                batch_id,
                transaction_id,
            )
        )

        if (
            len(
                identity["entities"]
            )
            != len(
                proposals
            )
        ):
            raise EvaluatorError(
                "Campaign proposal/entity cardinality mismatch"
            )

        for entity, proposal in zip(
            identity["entities"],
            proposals,
            strict=True,
        ):

            entity_id = entity[
                "screening_entity_id"
            ]

            decision = proposal[
                "record_decision"
            ]

            if decision not in terminal_decisions:
                raise EvaluatorError(
                    "Unexpected development decision: "
                    + decision
                )

            labels[
                entity_id
            ] = decision

            batches[
                entity_id
            ] = batch_id

    if len(labels) != 4500:
        raise EvaluatorError(
            "Expected 4,500 frozen development labels; observed "
            + str(
                len(labels)
            )
        )

    if set(labels) != set(batches):
        raise EvaluatorError(
            "Development label/batch identity mismatch"
        )

    return (
        labels,
        batches,
    )


def load_development_records() -> list[DevelopmentRecord]:
    repo = repo_root()

    text_path = (
        repo
        / CANONICAL_TEXT_REL
    )

    if not text_path.is_file():
        raise EvaluatorError(
            "Canonical normalized-text artifact missing"
        )

    observed_sha = sha256(
        text_path
    )

    if (
        observed_sha
        != EXPECTED_TEXT_SHA256
    ):
        raise EvaluatorError(
            "Canonical normalized-text SHA256 mismatch"
        )

    rows = read_tsv(
        text_path
    )

    if len(rows) != 4190:
        raise EvaluatorError(
            "Expected 4,190 text-bearing development rows"
        )

    labels, batches = (
        reconstruct_development_labels()
    )

    required_fields = {
        "screening_entity_id",
        "title_text",
        "abstract_text",
    }

    if not rows:
        raise EvaluatorError(
            "Canonical text table is empty"
        )

    missing_fields = (
        required_fields
        - set(
            rows[0]
        )
    )

    if missing_fields:
        raise EvaluatorError(
            "Canonical text table missing fields: "
            + ",".join(
                sorted(
                    missing_fields
                )
            )
        )

    records: list[DevelopmentRecord] = []
    seen: set[str] = set()

    for row in rows:

        entity_id = row[
            "screening_entity_id"
        ]

        if not entity_id:
            raise EvaluatorError(
                "Blank screening_entity_id"
            )

        if entity_id in seen:
            raise EvaluatorError(
                "Duplicate screening_entity_id: "
                + entity_id
            )

        seen.add(
            entity_id
        )

        if entity_id not in labels:
            raise EvaluatorError(
                "Text-bearing record lacks frozen development label: "
                + entity_id
            )

        if entity_id not in batches:
            raise EvaluatorError(
                "Text-bearing record lacks frozen development batch: "
                + entity_id
            )

        title = (
            row[
                "title_text"
            ]
            or ""
        ).strip()

        abstract = (
            row[
                "abstract_text"
            ]
            or ""
        ).strip()

        if not abstract:
            raise EvaluatorError(
                "Text-development lane contains blank abstract: "
                + entity_id
            )

        label_text = labels[
            entity_id
        ]

        if label_text == POSITIVE_LABEL:
            label_numeric = POSITIVE_NUMERIC
        elif label_text == NEGATIVE_LABEL:
            label_numeric = NEGATIVE_NUMERIC
        else:
            raise EvaluatorError(
                "Unexpected frozen development label"
            )

        batch_id = batches[
            entity_id
        ]

        if batch_id not in BATCH_IDS:
            raise EvaluatorError(
                "Unexpected development batch: "
                + batch_id
            )

        document = (
            title
            + "\n\n"
            + abstract
        )

        records.append(
            DevelopmentRecord(
                screening_entity_id=entity_id,
                batch_id=batch_id,
                label_text=label_text,
                label_numeric=label_numeric,
                document=document,
            )
        )

    positives = sum(
        record.label_numeric
        == POSITIVE_NUMERIC
        for record in records
    )

    negatives = sum(
        record.label_numeric
        == NEGATIVE_NUMERIC
        for record in records
    )

    if (
        positives != 168
        or negatives != 4022
    ):
        raise EvaluatorError(
            "Frozen development label counts changed"
        )

    observed_batches = {
        record.batch_id
        for record in records
    }

    if observed_batches != set(
        BATCH_IDS
    ):
        raise EvaluatorError(
            "Development batch set changed"
        )

    return records


def records_for_batches(
    records: Sequence[DevelopmentRecord],
    batch_ids: Iterable[str],
) -> list[DevelopmentRecord]:
    wanted = set(
        batch_ids
    )

    return [
        record
        for record in records
        if record.batch_id in wanted
    ]


def validate_split(
    train: Sequence[DevelopmentRecord],
    test: Sequence[DevelopmentRecord],
) -> None:
    train_ids = {
        record.screening_entity_id
        for record in train
    }

    test_ids = {
        record.screening_entity_id
        for record in test
    }

    if train_ids & test_ids:
        raise EvaluatorError(
            "Train/test identity leakage"
        )

    if not train:
        raise EvaluatorError(
            "Training partition empty"
        )

    if not test:
        raise EvaluatorError(
            "Test partition empty"
        )

    train_labels = {
        record.label_numeric
        for record in train
    }

    test_labels = {
        record.label_numeric
        for record in test
    }

    if train_labels != {
        0,
        1,
    }:
        raise EvaluatorError(
            "Training partition does not contain both classes"
        )

    if test_labels != {
        0,
        1,
    }:
        raise EvaluatorError(
            "Test partition does not contain both classes"
        )


def outer_splits(
    records: Sequence[DevelopmentRecord],
):
    for held_out_batch in BATCH_IDS:

        training_batches = tuple(
            batch
            for batch in BATCH_IDS
            if batch != held_out_batch
        )

        train = records_for_batches(
            records,
            training_batches,
        )

        test = records_for_batches(
            records,
            (
                held_out_batch,
            ),
        )

        validate_split(
            train,
            test,
        )

        yield (
            held_out_batch,
            training_batches,
            train,
            test,
        )


def inner_splits(
    outer_training_records: Sequence[DevelopmentRecord],
    outer_training_batches: Sequence[str],
):
    if len(
        outer_training_batches
    ) != 8:
        raise EvaluatorError(
            "Expected eight outer-training batches"
        )

    for held_out_batch in outer_training_batches:

        training_batches = tuple(
            batch
            for batch in outer_training_batches
            if batch != held_out_batch
        )

        train = records_for_batches(
            outer_training_records,
            training_batches,
        )

        test = records_for_batches(
            outer_training_records,
            (
                held_out_batch,
            ),
        )

        validate_split(
            train,
            test,
        )

        yield (
            held_out_batch,
            training_batches,
            train,
            test,
        )


def candidate_design() -> dict:
    design = read_json(
        repo_root()
        / CANDIDATE_DESIGN_REL
    )

    ids = tuple(
        item[
            "candidate_id"
        ]
        for item in design[
            "candidate_models"
        ]
    )

    if ids != CANDIDATE_ORDER:
        raise EvaluatorError(
            "Frozen candidate order changed"
        )

    return design


def verify_environment_contract() -> None:
    repo = repo_root()

    amendment = read_json(
        repo
        / AMENDMENT_REL
    )

    target = amendment[
        "amended_environment_target"
    ]

    if target != {
        "python_major_minor":
            "3.11",
        "scikit_learn":
            "1.9.0",
        "numpy":
            "1.26.4",
        "scipy":
            "1.12.0",
    }:
        raise EvaluatorError(
            "Amended environment target changed"
        )

    state = read_json(
        repo
        / ENVIRONMENT_STATE_REL
    )

    if (
        state[
            "environment_identity"
        ][
            "name"
        ]
        != "branchsnv-triage-v1"
    ):
        raise EvaluatorError(
            "Frozen environment identity changed"
        )


def require_dedicated_runtime() -> None:
    expected_prefix = Path(
        EXPECTED_ENVIRONMENT_PREFIX
    ).resolve()

    executable = Path(
        sys.executable
    ).resolve()

    try:
        executable.relative_to(
            expected_prefix
        )
    except ValueError as exc:
        raise EvaluatorError(
            "Evaluator fitting must run inside the frozen "
            "branchsnv-triage-v1 environment"
        ) from exc

    if sys.version_info[:2] != (
        3,
        11,
    ):
        raise EvaluatorError(
            "Python major/minor differs from frozen runtime"
        )

    import importlib.metadata

    expected = {
        "numpy":
            "1.26.4",
        "scipy":
            "1.12.0",
        "scikit-learn":
            "1.9.0",
    }

    observed = {
        package:
            importlib.metadata.version(
                package
            )
        for package in expected
    }

    if observed != expected:
        raise EvaluatorError(
            "Live modelling-library versions differ from frozen state"
        )


def build_vectorizer():
    require_dedicated_runtime()

    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer

    return TfidfVectorizer(
        analyzer="word",
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(
            1,
            2,
        ),
        min_df=2,
        max_df=1.0,
        max_features=None,
        norm="l2",
        use_idf=True,
        smooth_idf=True,
        sublinear_tf=True,
        stop_words=None,
        token_pattern=r"(?u)\b\w\w+\b",
        dtype=np.float64,
    )


def build_model(
    candidate_id: str,
):
    require_dedicated_runtime()

    if candidate_id not in CANDIDATE_ORDER:
        raise EvaluatorError(
            "Unknown candidate: "
            + candidate_id
        )

    if (
        candidate_id
        == "logistic_regression_balanced_l2_v1"
    ):
        from sklearn.linear_model import LogisticRegression

        return LogisticRegression(
            penalty="l2",
            C=1.0,
            solver="liblinear",
            class_weight="balanced",
            max_iter=5000,
            random_state=0,
        )

    if (
        candidate_id
        == "linear_svc_balanced_l2_v1"
    ):
        from sklearn.svm import LinearSVC

        return LinearSVC(
            penalty="l2",
            loss="squared_hinge",
            dual=True,
            C=1.0,
            class_weight="balanced",
            tol=1e-4,
            max_iter=10000,
            random_state=0,
        )

    if candidate_id == "complement_nb_v1":
        from sklearn.naive_bayes import ComplementNB

        return ComplementNB(
            alpha=1.0,
            norm=False,
        )

    raise AssertionError(
        candidate_id
    )


def positive_scores(
    model,
    candidate_id: str,
    matrix,
):
    if candidate_id in {
        "logistic_regression_balanced_l2_v1",
        "complement_nb_v1",
    }:
        probabilities = model.predict_proba(
            matrix
        )

        classes = list(
            model.classes_
        )

        try:
            index = classes.index(
                POSITIVE_NUMERIC
            )
        except ValueError as exc:
            raise EvaluatorError(
                "Positive class missing from fitted model"
            ) from exc

        return probabilities[
            :,
            index
        ]

    if candidate_id == "linear_svc_balanced_l2_v1":
        scores = model.decision_function(
            matrix
        )

        classes = list(
            model.classes_
        )

        if classes != [
            NEGATIVE_NUMERIC,
            POSITIVE_NUMERIC,
        ]:
            raise EvaluatorError(
                "Unexpected LinearSVC class order"
            )

        return scores

    raise EvaluatorError(
        "Unknown candidate score interface"
    )


def average_precision(
    labels: Sequence[int],
    scores,
) -> float:
    require_dedicated_runtime()

    from sklearn.metrics import average_precision_score

    value = float(
        average_precision_score(
            labels,
            scores,
            pos_label=POSITIVE_NUMERIC,
        )
    )

    if not math.isfinite(
        value
    ):
        raise EvaluatorError(
            "Non-finite average precision"
        )

    return value


def aggregate_candidate(
    candidate_id: str,
    batch_average_precision: Sequence[float],
) -> CandidateAggregate:
    values = [
        float(
            value
        )
        for value in batch_average_precision
    ]

    if not values:
        raise EvaluatorError(
            "No batch metrics supplied"
        )

    if not all(
        math.isfinite(
            value
        )
        for value in values
    ):
        raise EvaluatorError(
            "Non-finite batch metric supplied"
        )

    return CandidateAggregate(
        candidate_id=candidate_id,
        macro_mean_ap=statistics.fmean(
            values
        ),
        minimum_ap=min(
            values
        ),
        median_ap=statistics.median(
            values
        ),
    )


def select_candidate(
    aggregates: Sequence[CandidateAggregate],
) -> CandidateAggregate:
    by_id = {
        item.candidate_id:
            item
        for item in aggregates
    }

    if set(
        by_id
    ) != set(
        CANDIDATE_ORDER
    ):
        raise EvaluatorError(
            "Candidate aggregate set differs from frozen candidate set"
        )

    if len(
        by_id
    ) != len(
        aggregates
    ):
        raise EvaluatorError(
            "Duplicate candidate aggregate"
        )

    order_index = {
        candidate_id:
            index
        for index, candidate_id in enumerate(
            CANDIDATE_ORDER
        )
    }

    return max(
        aggregates,
        key=lambda item: (
            item.macro_mean_ap,
            item.minimum_ap,
            item.median_ap,
            -order_index[
                item.candidate_id
            ],
        ),
    )


def execution_authorization_path() -> Path:
    return (
        repo_root()
        / EXECUTION_AUTHORIZATION_REL
    )


def validate_execution_authorization_payload(
    authorization: dict,
) -> None:
    repo = repo_root()

    required_exact = {
        "schema_version":
            1,

        "authorization_status":
            "AUTHORIZED_DEVELOPMENT_EVALUATION",

        "authorization_scope":
            "ONE_TIME_FROZEN_DEVELOPMENT_EVALUATION",

        "execution_id":
            EXECUTION_ID,

        "authorized_output_rel":
            AUTHORIZED_OUTPUT_REL,

        "implementation_sha256":
            sha256(
                repo
                / EVALUATOR_IMPLEMENTATION_REL
            ),

        "environment_state_design_sha256":
            sha256(
                repo
                / ENVIRONMENT_STATE_REL
            ),

        "canonical_text_sha256":
            EXPECTED_TEXT_SHA256,

        "model_fit_authorized":
            True,

        "vectorizer_fit_authorized":
            True,

        "hyperparameter_selection_authorized":
            False,

        "threshold_selection_authorized":
            False,

        "future_scoring_authorized":
            False,

        "blind_validation_content_use_authorized":
            False,

        "scientific_screening_decisions_authorized":
            False,

        "production_mutation_authorized":
            False,
    }

    for field, expected in required_exact.items():

        if authorization.get(
            field
        ) != expected:
            raise ExecutionNotAuthorized(
                "Execution authorization field invalid: "
                + field
            )

    implementation_freeze_commit = (
        authorization.get(
            "implementation_freeze_commit"
        )
    )

    if not isinstance(
        implementation_freeze_commit,
        str,
    ) or len(
        implementation_freeze_commit
    ) != 40:
        raise ExecutionNotAuthorized(
            "Execution authorization lacks valid implementation-freeze commit"
        )

    result = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            implementation_freeze_commit,
            "HEAD",
        ],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if result.returncode != 0:
        raise ExecutionNotAuthorized(
            "Authorized implementation-freeze commit is not ancestor of HEAD"
        )


def require_execution_authorization() -> dict:
    repo = repo_root()
    path = execution_authorization_path()

    if not path.is_file():
        raise ExecutionNotAuthorized(
            "Development evaluation execution is not yet authorized; "
            "the separately frozen execution-authorization artifact is absent"
        )

    relative = str(
        path.relative_to(
            repo
        )
    )

    tracked = subprocess.run(
        [
            "git",
            "ls-files",
            "--error-unmatch",
            relative,
        ],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if tracked.returncode != 0:
        raise ExecutionNotAuthorized(
            "Execution authorization artifact is not tracked"
        )

    clean = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            "HEAD",
            "--",
            relative,
        ],
        cwd=repo,
    )

    if clean.returncode != 0:
        raise ExecutionNotAuthorized(
            "Execution authorization artifact differs from committed HEAD"
        )

    authorization = read_json(
        path
    )

    validate_execution_authorization_payload(
        authorization
    )

    return authorization


def fit_and_score_partition(
    candidate_id: str,
    train: Sequence[DevelopmentRecord],
    test: Sequence[DevelopmentRecord],
):
    """
    This is the only low-level path that performs vectorizer/model fitting.

    It must only be reached after the separate execution authorization gate.
    """

    # Direct invocation of the only fit-capable function must not
    # bypass the separately frozen execution authorization.
    require_execution_authorization()

    validate_split(
        train,
        test,
    )

    vectorizer = build_vectorizer()

    train_documents = [
        record.document
        for record in train
    ]

    test_documents = [
        record.document
        for record in test
    ]

    train_labels = [
        record.label_numeric
        for record in train
    ]

    test_labels = [
        record.label_numeric
        for record in test
    ]

    train_matrix = vectorizer.fit_transform(
        train_documents
    )

    test_matrix = vectorizer.transform(
        test_documents
    )

    model = build_model(
        candidate_id
    )

    model.fit(
        train_matrix,
        train_labels,
    )

    scores = positive_scores(
        model,
        candidate_id,
        test_matrix,
    )

    ap = average_precision(
        test_labels,
        scores,
    )

    return (
        scores,
        ap,
    )


def run_development_evaluation(
    output_dir: Path,
):
    """
    Execute the frozen nested whole-batch development evaluation.

    This function is intentionally authorization-gated.
    """

    authorization = require_execution_authorization()
    require_dedicated_runtime()
    verify_environment_contract()
    candidate_design()

    if output_dir.exists():
        raise EvaluatorError(
            "Output directory already exists; refusing overwrite"
        )

    expected_output = (
        repo_root()
        / AUTHORIZED_OUTPUT_REL
    ).resolve()

    if output_dir.resolve() != expected_output:
        raise EvaluatorError(
            "Output directory differs from frozen execution authorization"
        )

    records = load_development_records()

    # The output directory itself is the one-time execution claim.
    # It is created only after all pre-fit validation has passed.
    # If execution subsequently fails, it remains in place so an
    # automatic rerun cannot silently occur.
    output_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    claim = {
        "schema_version":
            1,

        "execution_id":
            EXECUTION_ID,

        "status":
            "CLAIMED_BEFORE_FIRST_FIT",

        "authorization_sha256":
            sha256(
                execution_authorization_path()
            ),

        "implementation_sha256":
            sha256(
                repo_root()
                / EVALUATOR_IMPLEMENTATION_REL
            ),

        "authorized_output_rel":
            AUTHORIZED_OUTPUT_REL,

        "threshold_selection_authorized":
            False,

        "future_scoring_authorized":
            False,

        "blind_validation_content_use_authorized":
            False,

        "scientific_screening_decisions_authorized":
            False,

        "production_mutation_authorized":
            False,
    }

    (
        output_dir
        / "execution_claim.json"
    ).write_text(
        json.dumps(
            claim,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    inner_rows = []
    outer_rows = []
    outer_score_rows = []

    for (
        outer_batch,
        outer_training_batches,
        outer_train,
        outer_test,
    ) in outer_splits(
        records
    ):

        inner_candidate_values = {
            candidate_id:
                []
            for candidate_id in CANDIDATE_ORDER
        }

        for (
            inner_batch,
            _inner_training_batches,
            inner_train,
            inner_test,
        ) in inner_splits(
            outer_train,
            outer_training_batches,
        ):

            for candidate_id in CANDIDATE_ORDER:

                _scores, ap = (
                    fit_and_score_partition(
                        candidate_id,
                        inner_train,
                        inner_test,
                    )
                )

                inner_candidate_values[
                    candidate_id
                ].append(
                    ap
                )

                inner_rows.append(
                    {
                        "outer_held_out_batch":
                            outer_batch,
                        "inner_held_out_batch":
                            inner_batch,
                        "candidate_id":
                            candidate_id,
                        "average_precision":
                            format(
                                ap,
                                ".17g",
                            ),
                    }
                )

        aggregates = [
            aggregate_candidate(
                candidate_id,
                values,
            )
            for candidate_id, values in (
                inner_candidate_values.items()
            )
        ]

        selected = select_candidate(
            aggregates
        )

        outer_scores, outer_ap = (
            fit_and_score_partition(
                selected.candidate_id,
                outer_train,
                outer_test,
            )
        )

        outer_rows.append(
            {
                "outer_held_out_batch":
                    outer_batch,
                "selected_candidate_id":
                    selected.candidate_id,
                "inner_macro_mean_ap":
                    format(
                        selected.macro_mean_ap,
                        ".17g",
                    ),
                "inner_minimum_ap":
                    format(
                        selected.minimum_ap,
                        ".17g",
                    ),
                "inner_median_ap":
                    format(
                        selected.median_ap,
                        ".17g",
                    ),
                "outer_average_precision":
                    format(
                        outer_ap,
                        ".17g",
                    ),
            }
        )

        for record, score in zip(
            outer_test,
            outer_scores,
            strict=True,
        ):
            outer_score_rows.append(
                {
                    "screening_entity_id":
                        record.screening_entity_id,
                    "batch_id":
                        record.batch_id,
                    "label_numeric":
                        str(
                            record.label_numeric
                        ),
                    "selected_candidate_id":
                        selected.candidate_id,
                    "continuous_score":
                        format(
                            float(
                                score
                            ),
                            ".17g",
                        ),
                }
            )

    final_candidate_rows = []
    final_candidate_aggregates = []

    for candidate_id in CANDIDATE_ORDER:

        batch_values = []

        for (
            held_out_batch,
            _training_batches,
            train,
            test,
        ) in outer_splits(
            records
        ):

            _scores, ap = fit_and_score_partition(
                candidate_id,
                train,
                test,
            )

            batch_values.append(
                ap
            )

            final_candidate_rows.append(
                {
                    "held_out_batch":
                        held_out_batch,
                    "candidate_id":
                        candidate_id,
                    "average_precision":
                        format(
                            ap,
                            ".17g",
                        ),
                }
            )

        final_candidate_aggregates.append(
            aggregate_candidate(
                candidate_id,
                batch_values,
            )
        )

    final_selected = select_candidate(
        final_candidate_aggregates
    )

    write_tsv(
        output_dir
        / "inner_metrics.tsv",
        inner_rows,
        (
            "outer_held_out_batch",
            "inner_held_out_batch",
            "candidate_id",
            "average_precision",
        ),
    )

    write_tsv(
        output_dir
        / "outer_metrics.tsv",
        outer_rows,
        (
            "outer_held_out_batch",
            "selected_candidate_id",
            "inner_macro_mean_ap",
            "inner_minimum_ap",
            "inner_median_ap",
            "outer_average_precision",
        ),
    )

    write_tsv(
        output_dir
        / "outer_scores.tsv",
        outer_score_rows,
        (
            "screening_entity_id",
            "batch_id",
            "label_numeric",
            "selected_candidate_id",
            "continuous_score",
        ),
    )

    write_tsv(
        output_dir
        / "final_candidate_batch_metrics.tsv",
        final_candidate_rows,
        (
            "held_out_batch",
            "candidate_id",
            "average_precision",
        ),
    )

    summary = {
        "schema_version":
            1,
        "status":
            "DEVELOPMENT_EVALUATION_COMPLETE",
        "development_records":
            4190,
        "positive_records":
            168,
        "negative_records":
            4022,
        "outer_fold_count":
            9,
        "candidate_count":
            3,
        "final_selected_candidate_id":
            final_selected.candidate_id,
        "final_candidate_aggregates": [
            {
                "candidate_id":
                    item.candidate_id,
                "macro_mean_ap":
                    item.macro_mean_ap,
                "minimum_ap":
                    item.minimum_ap,
                "median_ap":
                    item.median_ap,
            }
            for item in final_candidate_aggregates
        ],
        "threshold_selected":
            False,
        "hard_predictions_generated":
            False,
        "future_scoring_performed":
            False,
        "blind_validation_content_used":
            False,
        "scientific_screening_decisions_made":
            False,
        "production_mutated":
            False,
    }

    (
        output_dir
        / "summary.json"
    ).write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    completion = {
        "schema_version":
            1,

        "execution_id":
            EXECUTION_ID,

        "status":
            "DEVELOPMENT_EVALUATION_COMPLETED",

        "development_records":
            4190,

        "final_selected_candidate_id":
            final_selected.candidate_id,

        "threshold_selected":
            False,

        "hard_predictions_generated":
            False,

        "future_scoring_performed":
            False,

        "blind_validation_content_used":
            False,

        "scientific_screening_decisions_made":
            False,

        "production_mutated":
            False,
    }

    (
        output_dir
        / "execution_completion.json"
    ).write_text(
        json.dumps(
            completion,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return summary


def write_tsv(
    path: Path,
    rows: Sequence[dict[str, str]],
    fieldnames: Sequence[str],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=list(
                fieldnames
            ),
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                row
            )


def development_plan() -> dict:
    verify_environment_contract()
    design = candidate_design()
    records = load_development_records()

    batch_counts = {}

    for batch in BATCH_IDS:

        batch_records = [
            record
            for record in records
            if record.batch_id == batch
        ]

        batch_counts[
            batch
        ] = {
            "records":
                len(
                    batch_records
                ),
            "positive":
                sum(
                    record.label_numeric
                    == POSITIVE_NUMERIC
                    for record in batch_records
                ),
            "negative":
                sum(
                    record.label_numeric
                    == NEGATIVE_NUMERIC
                    for record in batch_records
                ),
        }

    # Materialize split geometry without fitting anything.
    outer_geometry = []

    for (
        outer_batch,
        outer_training_batches,
        outer_train,
        outer_test,
    ) in outer_splits(
        records
    ):

        inner_count = sum(
            1
            for _ in inner_splits(
                outer_train,
                outer_training_batches,
            )
        )

        outer_geometry.append(
            {
                "held_out_batch":
                    outer_batch,
                "train_records":
                    len(
                        outer_train
                    ),
                "test_records":
                    len(
                        outer_test
                    ),
                "inner_fold_count":
                    inner_count,
            }
        )

    return {
        "schema_version":
            1,
        "status":
            "IMPLEMENTATION_PLAN_ONLY_NO_FIT",
        "development_records":
            len(
                records
            ),
        "positive_records":
            sum(
                record.label_numeric
                == POSITIVE_NUMERIC
                for record in records
            ),
        "negative_records":
            sum(
                record.label_numeric
                == NEGATIVE_NUMERIC
                for record in records
            ),
        "batch_counts":
            batch_counts,
        "candidate_order":
            list(
                CANDIDATE_ORDER
            ),
        "outer_geometry":
            outer_geometry,
        "inner_fold_count_per_outer":
            8,
        "vectorizer_fit_scope":
            design[
                "text_representation"
            ][
                "vectorizer"
            ][
                "fit_scope"
            ],
        "model_fit_performed":
            False,
        "vectorizer_fit_performed":
            False,
        "threshold_selected":
            False,
        "future_scoring_performed":
            False,
        "blind_validation_content_used":
            False,
        "scientific_screening_decisions_made":
            False,
        "production_mutated":
            False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(
        required=True
    )

    group.add_argument(
        "--plan",
        action="store_true",
        help=(
            "Validate development geometry and print a no-fit execution plan."
        ),
    )

    group.add_argument(
        "--execute-development-evaluation",
        action="store_true",
        help=(
            "Run the frozen development evaluation. "
            "Requires separately frozen execution authorization."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
    )

    args = parser.parse_args()

    if args.plan:

        if args.output_dir is not None:
            raise EvaluatorError(
                "--output-dir is not permitted with --plan"
            )

        print(
            json.dumps(
                development_plan(),
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    if args.execute_development_evaluation:

        if args.output_dir is None:
            raise EvaluatorError(
                "--output-dir is required for execution"
            )

        # Authorization is checked before any fit-capable development work.
        require_execution_authorization()

        run_development_evaluation(
            args.output_dir
        )

        return 0

    raise AssertionError(
        "unreachable"
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
