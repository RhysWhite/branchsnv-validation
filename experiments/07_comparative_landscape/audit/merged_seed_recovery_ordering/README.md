# Merged seed-recovery ordering audit

The production merged-universe seed-recovery diagnostic initially failed an
auxiliary byte-for-byte comparison of the formal-stage candidate-match
projection against the earlier formal-search output.

A differential audit established that this was an ordering-only validation
issue.

Both projections contain exactly 29 candidate evidence rows, with zero missing
and zero extra row occurrences. Only two positional rows differ. They are the
two OpenAlex records for SNPPar recovered by Q11:

- W3041660225
- W4225492844

These rows have the same seed tool, source, title, and query ID. Those are all
fields used by the original checker's output sort key. Python's stable sort
therefore preserves their prior input ordering. The merged search universe had
already imposed its own deterministic candidate ordering, causing these two
otherwise tied rows to appear in the reverse order.

After deterministic full-row canonicalization, the formal-stage outputs are
identical, with SHA-256:

7b00244753bbdc8b19637dfcc2bab96ba77633ea649a887a2b9203462fc20c14

No matching rule, alias, normalization rule, phrase-match rule, evidence row,
seed-recovery status, search expression, screening decision, eligibility
decision, or capability classification was changed.

The already-generated production seed-recovery output is retained unchanged.
Subsequent validation treats exact row-multiset equality plus deterministic
canonicalized equality as the appropriate reproduction criterion when the
original stable-sort key contains ties.
