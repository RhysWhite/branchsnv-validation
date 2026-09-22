# OpenAlex credential static-check audit

Status: RESOLVED_PRE_PRODUCTION

## Context

After the OpenAlex API key was moved from URL query parameters to the HTTP
`Authorization` header, an auxiliary static source-text check searched for the
literal substring:

`api_key=`

The check reported a failure.

No production citation retrieval had occurred.

## Cause

The literal substring check was over-broad.

It matched ordinary Python keyword-argument syntax in the internal function
call:

`api_key=api_key`

This passes the environment-derived credential from `main()` to
`retrieve_openalex()`.

It is not URL construction.

## Follow-up validation

A read-only audit performed after the failure established that:

1. neither `openalex_single_url()` nor `openalex_forward_url()` accepts an
   `api_key` argument;
2. no `build_url()` parameter dictionary contains an `api_key` key;
3. the OpenAlex retrieval calls contain `Authorization` headers;
4. generated OpenAlex anchor-resolution URLs contain no `api_key` parameter;
5. generated OpenAlex forward-citation URLs contain no `api_key` parameter;
6. the URL constructors cannot receive the API key under their current
   signatures;
7. the complete offline retrieval regression suite still passes; and
8. no production citation retrieval had occurred.

## Interpretation

The failed literal-substring test was therefore a false positive in the audit
test, not evidence of credential exposure.

The underlying credential-hardening implementation remains unchanged.

This audit changes no scientific protocol, citation source, anchor, retrieval
operation, count validation, screening rule, or stopping rule.
