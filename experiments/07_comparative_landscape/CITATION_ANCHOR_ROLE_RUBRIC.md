# Experiment 07 direct / near-direct role rubric

Status: FROZEN_PRE_SCREENING

This rubric operationalizes the `direct`, `near_direct`, and
`other_landscape_role` values used during citation-chain anchor screening.

It is frozen before any candidate receives a final identity, eligibility,
role, publication-anchor, or citation-chain decision.

## Purpose

Role assignment describes similarity of a tool's documented analytical output
to the two interpretation questions addressed by BRANCHSNV.

It is separate from:

- general software-landscape eligibility;
- executable benchmark eligibility;
- software availability or maintenance;
- organism specificity;
- statistical model;
- computational performance; and
- whether BRANCHSNV or another method is preferable.

No tool is negatively classified for lacking functionality outside its
documented purpose.

## BRANCHSNV comparison endpoints

Two endpoint families define direct analytical overlap.

### Endpoint D1 — clade-exclusive sequence state

The method directly identifies, classifies, or reports a nucleotide/SNP/allele
state according to its exclusivity or fixation within a phylogenetically
defined clade or lineage.

Examples of qualifying output semantics include:

- clade-specific SNP;
- clade-unique SNP;
- canonical SNP tied to a phylogenetic clade;
- fixed state restricted to a defined clade.

The exact terminology need not match BRANCHSNV.

### Endpoint D2 — branch-associated sequence change

The method directly identifies, reconstructs, maps, or reports a sequence-state
change or substitution on a specified phylogenetic branch/edge, or between its
parent and child nodes.

Examples of qualifying output semantics include:

- mutation assigned to a branch;
- substitution reconstructed along a branch;
- parent-to-child state change;
- branch-specific sequence change.

The method may use parsimony, likelihood, Bayesian inference, or another
documented reconstruction framework. Model choice does not determine role.

## `direct`

Assign `direct` when primary or official evidence establishes that the
software provides D1 and/or D2 as a documented first-class analytical output.

A tool may be `direct` even when important implementation details differ from
BRANCHSNV, including:

- nucleotide versus amino-acid data;
- deterministic versus probabilistic reconstruction;
- treatment of ambiguity or uncertainty;
- organism restrictions; or
- different input formats.

Those differences are recorded separately and may affect benchmark
eligibility.

## `near_direct`

Assign `near_direct` when the software operates in the same analytical
neighbourhood but does not document D1 or D2 as a first-class output.

Examples include software whose documented output primarily consists of:

- reconstructed ancestral node states or sequences from which branch changes
  could subsequently be derived;
- node-associated or tree-associated SNP information that requires additional
  interpretation to obtain a D1 or D2 endpoint; or
- closely related phylogenetic state reconstruction without an explicit
  clade-exclusive or branch-change output.

The possibility that a user could derive D1 or D2 by post-processing does not
by itself make a tool `direct`.

## `other_landscape_role`

Assign `other_landscape_role` when the tool is eligible for the broader
software landscape but its documented outputs do not satisfy the definitions
of either `direct` or `near_direct`.

## `not_established`

Assign `not_established` when the available primary or official evidence is
insufficient to support one of the classifications above.

## Evidence rule

Role is assigned from the documented method/output semantics, not from:

- the seed-registry role;
- tool name;
- search-query match;
- citation count;
- reviewer familiarity; or
- anticipated benchmark performance.

The prespecified seed role remains retained as provenance and may disagree with
the evidence-supported final role.

## Relationship to citation chaining

A tool may seed citation chaining only if the separately frozen anchor
screening criteria are also satisfied:

1. identity confirmed;
2. software-landscape decision `include`;
3. final role `direct` or `near_direct`; and
4. canonical publication anchor established.

This rubric does not itself make an anchor decision.
