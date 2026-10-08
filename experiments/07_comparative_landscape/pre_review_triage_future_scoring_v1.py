from __future__ import annotations

from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile

import joblib
import numpy as np
import scipy
import sklearn
import threadpoolctl
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC


ROOT = Path(
    "experiments/07_comparative_landscape"
)

DEVROOT = Path(
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1"
)

DEVRESULTS = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_evaluator_v1/"
    "development_evaluation_v1"
)

FUTROOT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_text_retrieval_v1"
)

OUTPUT_ROOT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_scoring_v1"
)

AUTHORIZATION = (
    ROOT
    / "pre_review_triage_future_scoring_v1_execution_authorization.json"
)

IMPLEMENTATION_SUMS = (
    ROOT
    / "pre_review_triage_future_scoring_v1_implementation.sha256"
)

DESIGN_SUMS = (
    ROOT
    / "pre_review_triage_future_scoring_v1_design.sha256"
)

AMENDMENT_SUMS = (
    ROOT
    / "pre_review_triage_future_scoring_v1_design_amendment_001.sha256"
)

RECONCILIATION_COMPLETION_SUMS = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_completion.sha256"
)

EVALUATOR_IMPLEMENTATION_SUMS = (
    ROOT
    / "pre_review_triage_evaluator_v1_implementation.sha256"
)

DEVELOPMENT_RESULTS_SUMS = (
    ROOT
    / "pre_review_triage_development_evaluation_results_v1.sha256"
)

DEVELOPMENT_TEXT = (
    DEVROOT
    / "reconciled_normalized_text.tsv"
)

DEVELOPMENT_OUTER_SCORES = (
    DEVRESULTS
    / "outer_scores.tsv"
)

FUTURE_TEXT = (
    FUTROOT
    / "reconciled_normalized_text.tsv"
)

FUTURE_RESOLUTION = (
    FUTROOT
    / "reconciled_resolution.tsv"
)

FUTURE_SUMMARY = (
    FUTROOT
    / "reconciliation_summary.json"
)


EXPECTED_DESIGN_SUMS_SHA256 = (
    "f5c3548c370af87c5964a3eff1db590d"
    "0800d7b5655bf9076fee0d757d52eaba"
)

EXPECTED_AMENDMENT_SUMS_SHA256 = (
    "a81a90797ae05db3c8139cdade02069f"
    "c722d9abb7f815df2619f39f29e317c2"
)

EXPECTED_RECONCILIATION_COMPLETION_SHA256 = (
    "0798d80b10c6fa4beb53cf1074bef959"
    "283c2cb0ef2e2be998c6ead4bbc048b1"
)

EXPECTED_EVALUATOR_SHA256 = (
    "bd5520bbbb7bad1bc33cab131d21ce90"
    "701815a927076fee159ede3045843a10"
)

EXPECTED_DEVELOPMENT_TEXT_SHA256 = (
    "8c897444fe1a4d26226c8ecb798cd9d"
    "08bd3acc362aead972fdbee80d326785b"
)

EXPECTED_FUTURE_TEXT_SHA256 = (
    "8ee30e1bbd94140710e943fc222780581"
    "9fa88e84e31207ff64965d67489a1d3"
)

EXPECTED_FUTURE_RESOLUTION_SHA256 = (
    "437f21bde9c29ddc2ef531a356bd5649"
    "1fb088f3a37e35ee5aa9be1609ec31f7"
)

EXPECTED_FUTURE_SUMMARY_SHA256 = (
    "14b8099cecff8787a3a62efe5c796beeb"
    "ddf8635a66a38588f089435fdd14209"
)

SELECTED_CANDIDATE = (
    "linear_svc_balanced_l2_v1"
)

EXPECTED_PYTHON_EXECUTABLE = (
    "/home/rwhite/.conda/envs/"
    "branchsnv-triage-v1/bin/python"
)

EXPECTED_PYTHON_MAJOR_MINOR = (
    3,
    11,
)

EXPECTED_NUMPY_VERSION = "1.26.4"
EXPECTED_SCIPY_VERSION = "1.12.0"
EXPECTED_SKLEARN_VERSION = "1.9.0"
EXPECTED_JOBLIB_VERSION = "1.6.0"
EXPECTED_THREADPOOLCTL_VERSION = "3.7.0"

POSITIVE_LABEL = (
    "retain_for_method_assessment"
)

EXECUTION_CONFIRMATION = (
    "EXECUTE-FROZEN-FUTURE-SCORING-V1"
)

SCORED_FIELDS = [
    "retrieval_record_index",
    "screening_entity_id",
    "selected_candidate_id",
    "continuous_score",
]

COVERAGE_FIELDS = [
    "retrieval_record_index",
    "screening_entity_id",
    "abstract_status",
    "coverage_status",
]


class FutureScoringError(
    RuntimeError
):
    pass


def sha256_file(
    path: Path,
) -> str:

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def read_json(
    path: Path,
) -> dict:

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def read_tsv(
    path: Path,
) -> list[dict[str, str]]:

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as fh:

        return list(
            csv.DictReader(
                fh,
                delimiter="\t",
            )
        )


def verify_checksum_manifest(
    path: Path,
) -> None:

    if not path.is_file():
        raise FutureScoringError(
            "Checksum manifest absent: "
            + str(path)
        )

    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():

        if not line.strip():
            continue

        try:
            digest, relative = line.split(
                "  ",
                1,
            )
        except ValueError as exc:
            raise FutureScoringError(
                "Malformed checksum line in "
                + str(path)
            ) from exc

        target = Path(
            relative
        )

        if not target.is_file():
            raise FutureScoringError(
                "Checksum target absent: "
                + relative
            )

        if sha256_file(
            target
        ) != digest:
            raise FutureScoringError(
                "Checksum mismatch: "
                + relative
            )


def make_document(
    row: dict[str, str],
) -> str:

    return (
        row[
            "title_text"
        ]
        + "\n\n"
        + row[
            "abstract_text"
        ]
    )


def make_vectorizer() -> TfidfVectorizer:

    return TfidfVectorizer(
        analyzer="word",
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
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


def make_model() -> LinearSVC:

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


def _integer_index(
    row: dict[str, str],
) -> int:

    try:
        return int(
            row[
                "retrieval_record_index"
            ]
        )
    except Exception as exc:
        raise FutureScoringError(
            "Invalid retrieval_record_index"
        ) from exc


def assemble_training(
    text_rows: list[dict[str, str]],
    score_rows: list[dict[str, str]],
    *,
    expected_rows: int,
    expected_positive: int,
) -> list[dict[str, object]]:

    text_by_id: dict[
        str,
        dict[str, str],
    ] = {}

    for row in text_rows:

        entity = row.get(
            "screening_entity_id",
            "",
        )

        if not entity:
            raise FutureScoringError(
                "Blank development screening_entity_id"
            )

        if entity in text_by_id:
            raise FutureScoringError(
                "Duplicate development text identity: "
                + entity
            )

        if row.get(
            "abstract_status"
        ) not in {
            "usable_abstract_pubmed",
            "usable_abstract_openalex",
        }:
            raise FutureScoringError(
                "Non-usable development abstract entered model lane"
            )

        text_by_id[
            entity
        ] = row

    score_by_id: dict[
        str,
        dict[str, str],
    ] = {}

    for row in score_rows:

        entity = row.get(
            "screening_entity_id",
            "",
        )

        if not entity:
            raise FutureScoringError(
                "Blank development score identity"
            )

        if entity in score_by_id:
            raise FutureScoringError(
                "Duplicate development score identity: "
                + entity
            )

        if row.get(
            "selected_candidate_id"
        ) != SELECTED_CANDIDATE:
            raise FutureScoringError(
                "Development result candidate-family drift"
            )

        if row.get(
            "label_numeric"
        ) not in {
            "0",
            "1",
        }:
            raise FutureScoringError(
                "Invalid development numeric label"
            )

        score_by_id[
            entity
        ] = row

    if set(
        text_by_id
    ) != set(
        score_by_id
    ):
        raise FutureScoringError(
            "Development text/label identity sets differ"
        )

    if len(
        text_by_id
    ) != expected_rows:
        raise FutureScoringError(
            "Development training cardinality changed"
        )

    positive = sum(
        1
        for row in score_by_id.values()
        if row[
            "label_numeric"
        ] == "1"
    )

    if positive != expected_positive:
        raise FutureScoringError(
            "Development positive count changed"
        )

    combined = []

    seen_indices = set()

    for entity, text_row in (
        text_by_id.items()
    ):

        index = _integer_index(
            text_row
        )

        if index in seen_indices:
            raise FutureScoringError(
                "Duplicate development retrieval_record_index"
            )

        seen_indices.add(
            index
        )

        combined.append(
            {
                "retrieval_record_index":
                    index,

                "screening_entity_id":
                    entity,

                "title_text":
                    text_row[
                        "title_text"
                    ],

                "abstract_text":
                    text_row[
                        "abstract_text"
                    ],

                "label_numeric":
                    int(
                        score_by_id[
                            entity
                        ][
                            "label_numeric"
                        ]
                    ),
            }
        )

    combined.sort(
        key=lambda row:
            row[
                "retrieval_record_index"
            ]
    )

    return combined


def assemble_future(
    text_rows: list[dict[str, str]],
    resolution_rows: list[dict[str, str]],
    *,
    expected_scored: int,
    expected_total: int,
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
]:

    text_by_id: dict[
        str,
        dict[str, str],
    ] = {}

    for row in text_rows:

        entity = row.get(
            "screening_entity_id",
            "",
        )

        if not entity:
            raise FutureScoringError(
                "Blank future text identity"
            )

        if entity in text_by_id:
            raise FutureScoringError(
                "Duplicate future text identity: "
                + entity
            )

        if row.get(
            "abstract_status"
        ) not in {
            "usable_abstract_pubmed",
            "usable_abstract_openalex",
        }:
            raise FutureScoringError(
                "Non-usable future abstract entered score lane"
            )

        text_by_id[
            entity
        ] = row

    resolution_by_id = {}

    for row in resolution_rows:

        entity = row.get(
            "screening_entity_id",
            "",
        )

        if not entity:
            raise FutureScoringError(
                "Blank future resolution identity"
            )

        if entity in resolution_by_id:
            raise FutureScoringError(
                "Duplicate future resolution identity: "
                + entity
            )

        resolution_by_id[
            entity
        ] = row

    if len(
        resolution_by_id
    ) != expected_total:
        raise FutureScoringError(
            "Future resolution cardinality changed"
        )

    if len(
        text_by_id
    ) != expected_scored:
        raise FutureScoringError(
            "Future normalized-text cardinality changed"
        )

    if not set(
        text_by_id
    ).issubset(
        resolution_by_id
    ):
        raise FutureScoringError(
            "Future text contains identity absent from resolution"
        )

    sorted_text = sorted(
        text_rows,
        key=_integer_index,
    )

    coverage = []

    scored_count = 0
    no_text_count = 0

    for row in sorted(
        resolution_rows,
        key=_integer_index,
    ):

        entity = row[
            "screening_entity_id"
        ]

        present = (
            entity
            in text_by_id
        )

        expected_present = (
            row.get(
                "normalized_text_present"
            )
            == "1"
        )

        if present != expected_present:
            raise FutureScoringError(
                "Future normalized-text presence mismatch: "
                + entity
            )

        if present:
            status = "scored"
            scored_count += 1

        else:
            status = "no_normalized_text"
            no_text_count += 1

        coverage.append(
            {
                "retrieval_record_index":
                    row[
                        "retrieval_record_index"
                    ],

                "screening_entity_id":
                    entity,

                "abstract_status":
                    row[
                        "abstract_status"
                    ],

                "coverage_status":
                    status,
            }
        )

    if scored_count != expected_scored:
        raise FutureScoringError(
            "Future scored coverage count changed"
        )

    if no_text_count != (
        expected_total
        - expected_scored
    ):
        raise FutureScoringError(
            "Future no-text coverage count changed"
        )

    return (
        sorted_text,
        coverage,
    )


def fit_and_score(
    training_rows: list[dict[str, object]],
    future_rows: list[dict[str, str]],
    *,
    vectorizer_factory=make_vectorizer,
    model_factory=make_model,
) -> tuple[
    list[float],
    dict[str, object],
]:

    train_documents = [
        (
            str(
                row[
                    "title_text"
                ]
            )
            + "\n\n"
            + str(
                row[
                    "abstract_text"
                ]
            )
        )
        for row in training_rows
    ]

    labels = np.asarray(
        [
            int(
                row[
                    "label_numeric"
                ]
            )
            for row in training_rows
        ],
        dtype=int,
    )

    future_documents = [
        make_document(
            row
        )
        for row in future_rows
    ]

    vectorizer = (
        vectorizer_factory()
    )

    train_matrix = (
        vectorizer.fit_transform(
            train_documents
        )
    )

    model = (
        model_factory()
    )

    model.fit(
        train_matrix,
        labels,
    )

    classes = [
        int(value)
        for value in (
            model.classes_
        )
    ]

    if classes != [
        0,
        1,
    ]:
        raise FutureScoringError(
            "Unexpected classifier class orientation"
        )

    future_matrix = (
        vectorizer.transform(
            future_documents
        )
    )

    raw_scores = (
        model.decision_function(
            future_matrix
        )
    )

    values = np.asarray(
        raw_scores,
        dtype=float,
    ).reshape(
        -1
    )

    if len(
        values
    ) != len(
        future_rows
    ):
        raise FutureScoringError(
            "Future score cardinality mismatch"
        )

    scores = []

    for value in values:

        score = float(
            value
        )

        if not math.isfinite(
            score
        ):
            raise FutureScoringError(
                "Non-finite future score"
            )

        scores.append(
            score
        )

    metadata = {
        "candidate_id":
            SELECTED_CANDIDATE,

        "positive_numeric_class":
            1,

        "positive_label":
            POSITIVE_LABEL,

        "score_type":
            "raw_linear_svc_decision_function",

        "score_orientation":
            (
                "larger_values_support_"
                "retain_for_method_assessment"
            ),

        "training_rows":
            len(
                training_rows
            ),

        "future_rows":
            len(
                future_rows
            ),

        "training_positive_rows":
            int(
                labels.sum()
            ),

        "feature_count":
            int(
                train_matrix.shape[
                    1
                ]
            ),

        "threshold_selected":
            False,

        "hard_predictions_generated":
            False,

        "probability_calibration_performed":
            False,
    }

    return (
        scores,
        metadata,
    )


def format_score(
    value: float,
) -> str:

    return format(
        float(
            value
        ),
        ".17g",
    )


def verify_runtime_environment() -> None:

    observed_executable = str(
        Path(
            sys.executable
        ).resolve()
    )

    expected_executable = str(
        Path(
            EXPECTED_PYTHON_EXECUTABLE
        ).resolve()
    )

    if observed_executable != expected_executable:
        raise FutureScoringError(
            "Future scoring requires exact frozen Python executable"
        )

    if (
        sys.version_info.major,
        sys.version_info.minor,
    ) != EXPECTED_PYTHON_MAJOR_MINOR:
        raise FutureScoringError(
            "Future scoring Python major/minor changed"
        )

    exact_versions = {
        "numpy":
            (
                numpy_version := np.__version__
            ),

        "scipy":
            scipy.__version__,

        "scikit-learn":
            sklearn.__version__,

        "joblib":
            joblib.__version__,

        "threadpoolctl":
            threadpoolctl.__version__,
    }

    expected_versions = {
        "numpy":
            EXPECTED_NUMPY_VERSION,

        "scipy":
            EXPECTED_SCIPY_VERSION,

        "scikit-learn":
            EXPECTED_SKLEARN_VERSION,

        "joblib":
            EXPECTED_JOBLIB_VERSION,

        "threadpoolctl":
            EXPECTED_THREADPOOLCTL_VERSION,
    }

    if exact_versions != expected_versions:
        raise FutureScoringError(
            "Future scoring package versions differ from frozen runtime: "
            + repr(
                exact_versions
            )
        )


def verify_real_dependencies() -> None:

    verify_runtime_environment()

    exact_hashes = {
        DESIGN_SUMS:
            EXPECTED_DESIGN_SUMS_SHA256,

        AMENDMENT_SUMS:
            EXPECTED_AMENDMENT_SUMS_SHA256,

        RECONCILIATION_COMPLETION_SUMS:
            EXPECTED_RECONCILIATION_COMPLETION_SHA256,

        ROOT
        / "pre_review_triage_evaluator_v1.py":
            EXPECTED_EVALUATOR_SHA256,

        DEVELOPMENT_TEXT:
            EXPECTED_DEVELOPMENT_TEXT_SHA256,

        FUTURE_TEXT:
            EXPECTED_FUTURE_TEXT_SHA256,

        FUTURE_RESOLUTION:
            EXPECTED_FUTURE_RESOLUTION_SHA256,

        FUTURE_SUMMARY:
            EXPECTED_FUTURE_SUMMARY_SHA256,
    }

    for path, expected in (
        exact_hashes.items()
    ):

        if not path.is_file():
            raise FutureScoringError(
                "Frozen dependency absent: "
                + str(path)
            )

        if sha256_file(
            path
        ) != expected:
            raise FutureScoringError(
                "Frozen dependency hash changed: "
                + str(path)
            )

    verify_checksum_manifest(
        IMPLEMENTATION_SUMS
    )

    verify_checksum_manifest(
        DESIGN_SUMS
    )

    verify_checksum_manifest(
        AMENDMENT_SUMS
    )

    verify_checksum_manifest(
        RECONCILIATION_COMPLETION_SUMS
    )

    verify_checksum_manifest(
        EVALUATOR_IMPLEMENTATION_SUMS
    )

    verify_checksum_manifest(
        DEVELOPMENT_RESULTS_SUMS
    )

    summary = read_json(
        FUTURE_SUMMARY
    )

    if summary[
        "row_counts"
    ] != {
        "normalized_text": 11905,
        "resolution": 12162,
    }:
        raise FutureScoringError(
            "Future reconciliation row counts changed"
        )

    if summary[
        "abstract_status_counts"
    ] != {
        "abstract_absent": 246,
        "openalex_position_gap": 1,
        "provider_not_found": 10,
        "usable_abstract_openalex": 3406,
        "usable_abstract_pubmed": 8499,
    }:
        raise FutureScoringError(
            "Future abstract-status counts changed"
        )

    for key, value in (
        summary[
            "safety_boundaries"
        ].items()
    ):
        if value is not False:
            raise FutureScoringError(
                "Future reconciliation safety boundary changed: "
                + key
            )


def load_real_training() -> list[
    dict[str, object]
]:

    return assemble_training(
        read_tsv(
            DEVELOPMENT_TEXT
        ),
        read_tsv(
            DEVELOPMENT_OUTER_SCORES
        ),
        expected_rows=4190,
        expected_positive=168,
    )


def load_real_future() -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
]:

    return assemble_future(
        read_tsv(
            FUTURE_TEXT
        ),
        read_tsv(
            FUTURE_RESOLUTION
        ),
        expected_scored=11905,
        expected_total=12162,
    )


def validate_authorization_payload(
    value: dict,
    *,
    implementation_freeze_sha256: str,
    output_root: Path,
) -> None:

    expected = {
        "schema_version":
            1,

        "status":
            "AUTHORIZED_ONE_USE",

        "authorization_id":
            "PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_EXECUTION_001",

        "future_scoring_authorized":
            True,

        "final_deployment_fit_authorized":
            True,

        "one_use":
            True,

        "consumed_before_execution":
            False,

        "blind_validation_content_use_authorized":
            False,

        "threshold_selection_authorized":
            False,

        "hard_prediction_authorized":
            False,

        "probability_calibration_authorized":
            False,

        "selected_candidate_id":
            SELECTED_CANDIDATE,

        "design_checksum_manifest_sha256":
            EXPECTED_DESIGN_SUMS_SHA256,

        "design_amendment_001_checksum_manifest_sha256":
            EXPECTED_AMENDMENT_SUMS_SHA256,

        "reconciliation_completion_sha256":
            EXPECTED_RECONCILIATION_COMPLETION_SHA256,

        "implementation_freeze_sha256":
            implementation_freeze_sha256,

        "expected_development_rows":
            4190,

        "expected_development_positive_rows":
            168,

        "expected_future_scored_rows":
            11905,

        "expected_future_coverage_rows":
            12162,

        "output_root":
            str(
                output_root
            ),

        "confirmation":
            EXECUTION_CONFIRMATION,
    }

    if value != expected:
        raise FutureScoringError(
            "Future-scoring authorization payload mismatch"
        )


def validate_production_authorization(
    authorization_path: Path,
    confirmation: str,
) -> None:

    if authorization_path.resolve() != (
        AUTHORIZATION.resolve()
    ):
        raise FutureScoringError(
            "Only the canonical frozen authorization is permitted"
        )

    if confirmation != (
        EXECUTION_CONFIRMATION
    ):
        raise FutureScoringError(
            "Exact future-scoring confirmation required"
        )

    if not authorization_path.is_file():
        raise FutureScoringError(
            "Future-scoring authorization is absent"
        )

    if not IMPLEMENTATION_SUMS.is_file():
        raise FutureScoringError(
            "Implementation freeze checksum is absent"
        )

    validate_authorization_payload(
        read_json(
            authorization_path
        ),
        implementation_freeze_sha256=
            sha256_file(
                IMPLEMENTATION_SUMS
            ),
        output_root=
            OUTPUT_ROOT,
    )


def write_tsv(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:

        writer = csv.DictWriter(
            fh,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )

        writer.writeheader()
        writer.writerows(
            rows
        )


def execute_authorized(
    *,
    authorization_path: Path,
    confirmation: str,
) -> dict[str, object]:

    # Authorization is deliberately checked before any fit,
    # scoring, or output-directory creation.
    validate_production_authorization(
        authorization_path,
        confirmation,
    )

    if OUTPUT_ROOT.exists():
        raise FutureScoringError(
            "Future-scoring production root already exists"
        )

    verify_real_dependencies()

    training = (
        load_real_training()
    )

    (
        future_rows,
        coverage_rows,
    ) = load_real_future()

    scores, model_metadata = (
        fit_and_score(
            training,
            future_rows,
        )
    )

    scored_rows = []

    for row, score in zip(
        future_rows,
        scores,
        strict=True,
    ):

        scored_rows.append(
            {
                "retrieval_record_index":
                    row[
                        "retrieval_record_index"
                    ],

                "screening_entity_id":
                    row[
                        "screening_entity_id"
                    ],

                "selected_candidate_id":
                    SELECTED_CANDIDATE,

                "continuous_score":
                    format_score(
                        score
                    ),
            }
        )

    if len(
        scored_rows
    ) != 11905:
        raise FutureScoringError(
            "Final scored-record cardinality changed"
        )

    parent = (
        OUTPUT_ROOT.parent
    )

    parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    staging = Path(
        tempfile.mkdtemp(
            prefix=".pre_review_triage_future_scoring_v1.",
            dir=str(
                parent
            ),
        )
    )

    try:

        scored_path = (
            staging
            / "scored_records.tsv"
        )

        coverage_path = (
            staging
            / "coverage.tsv"
        )

        manifest_path = (
            staging
            / "execution_manifest.json"
        )

        checksums_path = (
            staging
            / "checksums.sha256"
        )

        completion_path = (
            staging
            / "execution_completion.json"
        )

        write_tsv(
            scored_path,
            SCORED_FIELDS,
            scored_rows,
        )

        write_tsv(
            coverage_path,
            COVERAGE_FIELDS,
            coverage_rows,
        )

        manifest = {
            "schema_version":
                1,

            "status":
                "FUTURE_SCORING_EXECUTED_PRE_UNBLINDING",

            "selected_candidate_id":
                SELECTED_CANDIDATE,

            "source_hashes": {
                "development_normalized_text":
                    sha256_file(
                        DEVELOPMENT_TEXT
                    ),

                "development_outer_scores":
                    sha256_file(
                        DEVELOPMENT_OUTER_SCORES
                    ),

                "future_normalized_text":
                    sha256_file(
                        FUTURE_TEXT
                    ),

                "future_resolution":
                    sha256_file(
                        FUTURE_RESOLUTION
                    ),

                "future_reconciliation_summary":
                    sha256_file(
                        FUTURE_SUMMARY
                    ),

                "implementation_freeze":
                    sha256_file(
                        IMPLEMENTATION_SUMS
                    ),
            },

            "training": {
                "rows":
                    4190,

                "positive_rows":
                    168,

                "negative_rows":
                    4022,

                "text_fields": [
                    "title_text",
                    "abstract_text",
                ],

                "document_join":
                    "title_text + '\\n\\n' + abstract_text",
            },

            "future": {
                "scored_rows":
                    11905,

                "coverage_rows":
                    12162,

                "no_normalized_text_rows":
                    257,
            },

            "model":
                model_metadata,

            "decision_boundary": {
                "threshold_selected":
                    False,

                "hard_predictions_generated":
                    False,

                "review_fraction_selected":
                    False,

                "probability_calibration_performed":
                    False,
            },

            "blind_validation_boundary": {
                "blind_validation_content_used":
                    False,

                "future_labels_used":
                    False,

                "unblinding_performed":
                    False,
            },
        }

        manifest_path.write_text(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        checksum_targets = [
            scored_path,
            coverage_path,
            manifest_path,
        ]

        checksums_path.write_text(
            "\n".join(
                (
                    sha256_file(
                        path
                    )
                    + "  "
                    + path.name
                )
                for path in (
                    checksum_targets
                )
            )
            + "\n",
            encoding="utf-8",
        )

        completion = {
            "schema_version":
                1,

            "status":
                "FUTURE_SCORING_COMPLETED_PRE_UNBLINDING",

            "scored_rows":
                11905,

            "coverage_rows":
                12162,

            "no_normalized_text_rows":
                257,

            "selected_candidate_id":
                SELECTED_CANDIDATE,

            "threshold_selected":
                False,

            "hard_predictions_generated":
                False,

            "blind_validation_content_used":
                False,

            "future_labels_used":
                False,

            "checksums_sha256":
                sha256_file(
                    checksums_path
                ),

            "scored_records_sha256":
                sha256_file(
                    scored_path
                ),

            "coverage_sha256":
                sha256_file(
                    coverage_path
                ),

            "execution_manifest_sha256":
                sha256_file(
                    manifest_path
                ),
        }

        completion_path.write_text(
            json.dumps(
                completion,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        actual_names = {
            path.name
            for path in (
                staging.iterdir()
            )
            if path.is_file()
        }

        expected_names = {
            "scored_records.tsv",
            "coverage.tsv",
            "execution_manifest.json",
            "checksums.sha256",
            "execution_completion.json",
        }

        if actual_names != expected_names:
            raise FutureScoringError(
                "Future-scoring staged artifact set differs"
            )

        if OUTPUT_ROOT.exists():
            raise FutureScoringError(
                "Production root appeared during staging"
            )

        os.replace(
            staging,
            OUTPUT_ROOT,
        )

        return completion

    except Exception:

        if staging.exists():
            shutil.rmtree(
                staging
            )

        raise


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--authorization",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--confirm",
        required=True,
    )

    args = parser.parse_args()

    result = execute_authorized(
        authorization_path=
            args.authorization,

        confirmation=
            args.confirm,
    )

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
