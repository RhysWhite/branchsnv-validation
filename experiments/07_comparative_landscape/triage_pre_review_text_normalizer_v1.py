from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET


_WHITESPACE = re.compile(r"\s+")


class TextNormalizationError(RuntimeError):
    pass


def sha256_bytes(
    value: bytes,
) -> str:
    return hashlib.sha256(
        value
    ).hexdigest()


def normalize_whitespace(
    value: str,
) -> str:
    return _WHITESPACE.sub(
        " ",
        value,
    ).strip()


def localname(
    tag: str,
) -> str:
    return tag.split(
        "}",
        1,
    )[-1]


def element_text(
    element: ET.Element | None,
) -> str:

    if element is None:
        return ""

    return normalize_whitespace(
        "".join(
            element.itertext()
        )
    )


def descendants_named(
    root: ET.Element,
    name: str,
) -> list[ET.Element]:

    return [
        element
        for element in root.iter()
        if localname(
            element.tag
        ) == name
    ]


def first_nonempty_named(
    root: ET.Element,
    names: tuple[str, ...],
) -> str:

    for element in root.iter():

        if localname(
            element.tag
        ) not in names:
            continue

        value = element_text(
            element
        )

        if value:
            return value

    return ""


def primary_pubmed_pmid(
    record: ET.Element,
) -> str:

    # PubmedArticle:
    #   MedlineCitation / PMID
    #
    # PubmedBookArticle:
    #   BookDocument / PMID
    #
    # Do not select reference-list PMIDs.

    for container_name in (
        "MedlineCitation",
        "BookDocument",
    ):

        for container in record.iter():

            if localname(
                container.tag
            ) != container_name:
                continue

            for child in container:

                if localname(
                    child.tag
                ) != "PMID":
                    continue

                value = element_text(
                    child
                )

                if value:
                    return value

    raise TextNormalizationError(
        "PubMed record lacks primary PMID"
    )


def normalize_pubmed(
    body: bytes,
    requested_pmid: str,
) -> dict:

    body_sha256 = sha256_bytes(
        body
    )

    try:
        root = ET.fromstring(
            body
        )
    except ET.ParseError as exc:
        return {
            "provider_used":
                "pubmed",
            "source_body_sha256":
                body_sha256,
            "provider_record_id":
                "",
            "provider_identity_status":
                "unresolved",
            "parser_status":
                "parser_failure",
            "abstract_status":
                "parser_failure",
            "title_text":
                "",
            "abstract_text":
                "",
            "abstract_section_metadata_json":
                "[]",
            "error":
                str(exc),
        }


    records = [
        element
        for element in root.iter()
        if localname(
            element.tag
        ) in {
            "PubmedArticle",
            "PubmedBookArticle",
        }
    ]


    if len(records) != 1:

        return {
            "provider_used":
                "pubmed",
            "source_body_sha256":
                body_sha256,
            "provider_record_id":
                "",
            "provider_identity_status":
                "unresolved",
            "parser_status":
                "parser_failure",
            "abstract_status":
                "parser_failure",
            "title_text":
                "",
            "abstract_text":
                "",
            "abstract_section_metadata_json":
                "[]",
            "error":
                (
                    "expected exactly one PubMed "
                    f"record, found {len(records)}"
                ),
        }


    record = records[0]

    try:
        returned_pmid = primary_pubmed_pmid(
            record
        )
    except TextNormalizationError as exc:

        return {
            "provider_used":
                "pubmed",
            "source_body_sha256":
                body_sha256,
            "provider_record_id":
                "",
            "provider_identity_status":
                "unresolved",
            "parser_status":
                "parser_failure",
            "abstract_status":
                "parser_failure",
            "title_text":
                "",
            "abstract_text":
                "",
            "abstract_section_metadata_json":
                "[]",
            "error":
                str(exc),
        }


    expected = requested_pmid.strip()

    identity_ok = (
        returned_pmid
        == expected
    )


    title = first_nonempty_named(
        record,
        (
            "ArticleTitle",
            "BookTitle",
        ),
    )


    sections = []

    for element in descendants_named(
        record,
        "AbstractText",
    ):

        text = element_text(
            element
        )

        if not text:
            continue

        sections.append({
            "index":
                len(sections) + 1,
            "label":
                normalize_whitespace(
                    element.attrib.get(
                        "Label",
                        "",
                    )
                ),
            "nlm_category":
                normalize_whitespace(
                    element.attrib.get(
                        "NlmCategory",
                        "",
                    )
                ),
            "text":
                text,
        })


    abstract_text = normalize_whitespace(
        " ".join(
            section[
                "text"
            ]
            for section in sections
        )
    )


    if not identity_ok:

        return {
            "provider_used":
                "pubmed",
            "source_body_sha256":
                body_sha256,
            "provider_record_id":
                returned_pmid,
            "provider_identity_status":
                "mismatch",
            "parser_status":
                "ok",
            "abstract_status":
                "provider_identity_mismatch",
            "title_text":
                title,
            "abstract_text":
                abstract_text,
            "abstract_section_metadata_json":
                json.dumps(
                    sections,
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(
                        ",",
                        ":",
                    ),
                ),
            "error":
                "",
        }


    return {
        "provider_used":
            "pubmed",
        "source_body_sha256":
            body_sha256,
        "provider_record_id":
            returned_pmid,
        "provider_identity_status":
            "matched",
        "parser_status":
            "ok",
        "abstract_status":
            (
                "usable_abstract_pubmed"
                if abstract_text
                else
                "abstract_absent"
            ),
        "title_text":
            title,
        "abstract_text":
            abstract_text,
        "abstract_section_metadata_json":
            json.dumps(
                sections,
                sort_keys=True,
                ensure_ascii=False,
                separators=(
                    ",",
                    ":",
                ),
            ),
        "error":
            "",
    }


def normalize_openalex(
    body: bytes,
) -> dict:

    body_sha256 = sha256_bytes(
        body
    )

    try:
        value = json.loads(
            body.decode(
                "utf-8"
            )
        )
    except Exception as exc:

        return {
            "provider_used":
                "openalex",
            "source_body_sha256":
                body_sha256,
            "provider_record_id":
                "",
            "provider_identity_status":
                "transport_validated",
            "parser_status":
                "parser_failure",
            "abstract_status":
                "parser_failure",
            "title_text":
                "",
            "abstract_text":
                "",
            "abstract_section_metadata_json":
                "[]",
            "error":
                str(exc),
        }


    if not isinstance(
        value,
        dict,
    ):

        return {
            "provider_used":
                "openalex",
            "source_body_sha256":
                body_sha256,
            "provider_record_id":
                "",
            "provider_identity_status":
                "transport_validated",
            "parser_status":
                "parser_failure",
            "abstract_status":
                "parser_failure",
            "title_text":
                "",
            "abstract_text":
                "",
            "abstract_section_metadata_json":
                "[]",
            "error":
                "OpenAlex payload is not an object",
        }


    record_id = str(
        value.get(
            "id",
            "",
        )
        or ""
    )


    title = normalize_whitespace(
        str(
            value.get(
                "display_name"
            )
            or value.get(
                "title"
            )
            or ""
        )
    )


    inverted = value.get(
        "abstract_inverted_index"
    )


    if inverted is None:

        return {
            "provider_used":
                "openalex",
            "source_body_sha256":
                body_sha256,
            "provider_record_id":
                record_id,
            "provider_identity_status":
                "transport_validated",
            "parser_status":
                "ok",
            "abstract_status":
                "abstract_absent",
            "title_text":
                title,
            "abstract_text":
                "",
            "abstract_section_metadata_json":
                "[]",
            "error":
                "",
        }


    if not isinstance(
        inverted,
        dict,
    ):

        return {
            "provider_used":
                "openalex",
            "source_body_sha256":
                body_sha256,
            "provider_record_id":
                record_id,
            "provider_identity_status":
                "transport_validated",
            "parser_status":
                "parser_failure",
            "abstract_status":
                "parser_failure",
            "title_text":
                title,
            "abstract_text":
                "",
            "abstract_section_metadata_json":
                "[]",
            "error":
                (
                    "abstract_inverted_index "
                    "is not an object"
                ),
        }


    positioned_tokens = []

    seen_positions = set()


    for token, positions in (
        inverted.items()
    ):

        if not isinstance(
            token,
            str,
        ):

            return {
                "provider_used":
                    "openalex",
                "source_body_sha256":
                    body_sha256,
                "provider_record_id":
                    record_id,
                "provider_identity_status":
                    "transport_validated",
                "parser_status":
                    "parser_failure",
                "abstract_status":
                    "parser_failure",
                "title_text":
                    title,
                "abstract_text":
                    "",
                "abstract_section_metadata_json":
                    "[]",
                "error":
                    "non-string abstract token",
            }


        if not isinstance(
            positions,
            list,
        ):

            return {
                "provider_used":
                    "openalex",
                "source_body_sha256":
                    body_sha256,
                "provider_record_id":
                    record_id,
                "provider_identity_status":
                    "transport_validated",
                "parser_status":
                    "parser_failure",
                "abstract_status":
                    "parser_failure",
                "title_text":
                    title,
                "abstract_text":
                    "",
                "abstract_section_metadata_json":
                    "[]",
                "error":
                    (
                        "abstract token position "
                        "vector is not a list"
                    ),
            }


        for position in positions:

            if (
                not isinstance(
                    position,
                    int,
                )
                or isinstance(
                    position,
                    bool,
                )
            ):

                return {
                    "provider_used":
                        "openalex",
                    "source_body_sha256":
                        body_sha256,
                    "provider_record_id":
                        record_id,
                    "provider_identity_status":
                        "transport_validated",
                    "parser_status":
                        "parser_failure",
                    "abstract_status":
                        "parser_failure",
                    "title_text":
                        title,
                    "abstract_text":
                        "",
                    "abstract_section_metadata_json":
                        "[]",
                    "error":
                        (
                            "abstract position "
                            "is not an integer"
                        ),
                }


            if position in seen_positions:

                return {
                    "provider_used":
                        "openalex",
                    "source_body_sha256":
                        body_sha256,
                    "provider_record_id":
                        record_id,
                    "provider_identity_status":
                        "transport_validated",
                    "parser_status":
                        "parser_failure",
                    "abstract_status":
                        "parser_failure",
                    "title_text":
                        title,
                    "abstract_text":
                        "",
                    "abstract_section_metadata_json":
                        "[]",
                    "error":
                        "duplicate abstract position",
                }


            seen_positions.add(
                position
            )

            positioned_tokens.append(
                (
                    position,
                    token,
                )
            )


    if not positioned_tokens:

        return {
            "provider_used":
                "openalex",
            "source_body_sha256":
                body_sha256,
            "provider_record_id":
                record_id,
            "provider_identity_status":
                "transport_validated",
            "parser_status":
                "ok",
            "abstract_status":
                "abstract_absent",
            "title_text":
                title,
            "abstract_text":
                "",
            "abstract_section_metadata_json":
                "[]",
            "error":
                "",
        }


    positioned_tokens.sort(
        key=lambda item:
            item[0]
    )


    positions = [
        position
        for position, _
        in positioned_tokens
    ]


    contiguous = (
        positions
        == list(
            range(
                min(
                    positions
                ),
                max(
                    positions
                )
                + 1,
            )
        )
    )


    abstract_text = normalize_whitespace(
        " ".join(
            token
            for _, token
            in positioned_tokens
        )
    )


    return {
        "provider_used":
            "openalex",
        "source_body_sha256":
            body_sha256,
        "provider_record_id":
            record_id,
        "provider_identity_status":
            "transport_validated",
        "parser_status":
            "ok",
        "abstract_status":
            (
                "usable_abstract_openalex"
                if contiguous
                else
                "openalex_position_gap"
            ),
        "title_text":
            title,
        "abstract_text":
            abstract_text,
        "abstract_section_metadata_json":
            "[]",
        "error":
            "",
    }
