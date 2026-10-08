# Experiment 07 search-completeness validation plan

Status: FROZEN_PRE_CITATION_CHAINING

## Purpose

This plan specifies how the performance of the already-completed database
search will be evaluated after citation chaining and final direct/near-direct
landscape screening are complete.

No metric in this plan permits modification of the primary formal or
high-recall search corpus.

## 1. Primary validation population

The primary validation population will be the final set of
evidence-supported `direct` and `near_direct` software methods established
after all protocol-defined discovery and screening stages are complete.

Call the number of final direct/near-direct methods `N_final`.

This final set is not known at the time this validation plan is frozen.

## 2. Relative recall, not absolute recall

Because there is no independently enumerable universe of all relevant software,
the endpoint is **relative recall against the final discovered eligible set**,
not absolute sensitivity.

For a discovery route `R`:

`relative_recall_R = methods in final set recovered by R / N_final`

The denominator and numerator will both be reported as counts as well as
percentages.

No claim of 100% absolute completeness will be made even if relative recall is
100%.

## 3. Database-search relative recall

For every final direct/near-direct method, method-level linkage back to the
frozen search corpus will be performed using source-backed identity evidence.

The following will be calculated:

### Formal search relative recall

Number and proportion of final direct/near-direct methods represented by at
least one record in the original formal-search stage.

### High-recall-stage relative recall

Number and proportion represented by at least one record in the high-recall
stage.

### Combined database-search relative recall

Number and proportion represented by either formal or high-recall database
search.

### Citation-only yield

Number and proportion of final direct/near-direct methods discovered through
citation chaining that have no corresponding record in the frozen merged
database-search universe.

## 4. Search-source contribution

Coverage of the final direct/near-direct set will be reported separately for:

- PubMed;
- OpenAlex; and
- bio.tools.

Source intersections will also be retained so that overlapping recovery is not
double-counted.

These results describe observed coverage and do not rank databases.

## 5. Query-family contribution

Using frozen query provenance, coverage of the final direct/near-direct set
will be calculated for each formal and high-recall query family.

For each family report:

- final methods recovered;
- final methods uniquely recovered by that family, if any; and
- overlap with other families.

This analysis uses already-retrieved records and does not rerun or alter any
query.

## 6. Individual-query contribution

For Q01–Q18 and HR01–HR05, report the number of final direct/near-direct methods
with at least one attributable record.

A descriptive leave-one-query and leave-one-family calculation may also be
performed from the frozen provenance table:

- remove that query/family's provenance computationally;
- determine how many final methods would still have been represented by the
  remaining frozen search results.

This is a provenance ablation, not a new bibliographic search.

It will not be used to retrospectively optimize the primary search.

## 7. Non-seed generalization check

Because the pre-search seed registry contributed to vocabulary development,
seed recovery is not an independent validation set.

Any final direct/near-direct methods that were **not** present in the original
31-tool seed registry will therefore be reported separately.

For this non-seed subset, calculate:

- representation in the formal search;
- representation in the high-recall search;
- representation in the combined database search; and
- citation-only discovery.

This provides a stronger check on whether the generic vocabulary generalized
beyond the methods known during query development.

If no non-seed direct/near-direct methods exist in the final set, this endpoint
will be reported as `not_estimable` rather than interpreted.

## 8. Miss analysis

Every final direct/near-direct method absent from the merged database-search
universe will undergo a structured miss analysis.

The analysis will determine, where evidence allows, whether absence is
consistent with:

- relevant terminology absent from title/abstract;
- terminology not represented by the frozen query vocabulary;
- publication not indexed by one or more searched bibliographic sources;
- software described primarily in documentation/repository material;
- method identity hidden behind a different title/name;
- metadata/indexing limitations; or
- another documented reason.

This analysis is descriptive.

Terms observed during miss analysis will not be added to the primary search.

## 9. Seed-recovery diagnostic reporting

The seed diagnostic will be retained as a separate development-set sensitivity
check.

Report:

- original formal seed-name recovery;
- high-recall seed-name recovery;
- merged seed-name recovery; and
- direct/near-direct seed recovery.

These results must be labelled as non-independent because seed knowledge
contributed to vocabulary development.

Candidate-name recovery must not be equated with confirmed method recovery.

## 10. Citation-chaining contribution

Citation chaining will be reported separately from database retrieval.

For each chaining wave, later protocol stages will retain:

- anchors searched;
- backward records retrieved;
- forward records retrieved;
- unique records after deduplication;
- candidate software methods identified;
- newly eligible landscape methods;
- newly eligible direct/near-direct methods; and
- methods promoted to next-wave anchors.

The citation-chaining stopping criterion will be frozen separately before
citation retrieval begins.

## 11. Interpretation

The completed analysis will answer three distinct questions:

1. **Was the original exact-phrase search sufficient by itself?**
2. **How much additional recovery was provided by the generic high-recall
   expansion?**
3. **How much relevant method discovery remained dependent on citation
   chaining?**

The results will be reported whether favourable or unfavourable.

A low relative recall for the database search will not trigger retrospective
query modification.

## 12. Reproducibility

All validation calculations will operate on frozen:

- search candidate records;
- source/query provenance;
- deduplication identities;
- final screening decisions; and
- citation-chain provenance.

The implementation will be committed before the final validation result is
calculated.
