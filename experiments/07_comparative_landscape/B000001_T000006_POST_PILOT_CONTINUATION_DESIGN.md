# Experiment 07 B000001 T000006 post-pilot continuation design

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This freeze defines the first controlled scientific-screening tranche after completion of the B000001 positions 1–11 pilot.

It does not edit the human-review packet, create scientific decisions, create a live authorization, or mutate the production ledger.

Parent completion commit:

`3e0171417b8844045df781a39c0a35e8fbe26364`

## Current production state

- production events: 22
- ledger SHA-256: `85eabc27f89cc215b75b4b48611e6131f8ef1f7e7d5a022b1229d1241bd960ac`
- complete: 11
- awaiting source escalation: 0
- ready: 94,611
- blocked metadata: 484
- positions 1–11: terminal

## T000006 bounded tranche

- batch: `B000001`
- positions: `12–36`
- target count: `25`
- expected event IDs: `E000000023–E000000047`
- expected post-event count: `47`
- initial events only
- superseding events prohibited
- partial execution prohibited
- positions 37–500 remain unauthorized

This 25-record tranche is a bounded scale-up. It does not establish automatic authority for any subsequent tranche.

## Exact target identity

- ordered entity IDs SHA-256: `a169877057cf928be5c945a266405406ae15833271daef89c0179d3d5260b5f2`
- canonical membership rows SHA-256: `0ea1bb77b778a8105389da08336eed90f6163c41f4fd7d8c1eb559a788f3c126`
- canonical baseline rows SHA-256: `1fbad740eb36d57838f46f60a4ff7cf81fe7d448ee7e8e0950fad72638bc5c59`
- canonical target identity SHA-256: `2c558ee5be00441beefffdb8632b1daaee6f427d384879dbdad5e85497316647`

### Target records

- position 12: `publication_component:citation:publication:doi:10.1002/9780470015902.a0022872`; row SHA `0a1276a5ef94e990f3ba0fbd99c8249beb82fd6a8f82ca5345968887bde15ff9`; title `Evolution of Eukaryotic RNA Polymerases`
- position 13: `publication_component:citation:publication:doi:10.1002/9780470015902.a0022889`; row SHA `6425916665d0d410ee6b7fe5b6248e958b4a0d6d4cbe73cb2ab106e6c3a9a1b8`; title `Evolution of Immune Proteins in Insects`
- position 14: `publication_component:citation:publication:doi:10.1002/9780470600122.ch3`; row SHA `52acf9fd06cb4aad4970592c08d2b4493bf92afc30b30f3de7893bc609c5adbb`; title `Sequence‐Based Analysis of Bacterial Population Structures`
- position 15: `publication_component:citation:publication:doi:10.1002/9780470600122.ch5`; row SHA `0d09efab4ea8a37e7908ee40aea387977dfd9c50c875b5d322990eb130bf6df8`; title `Statistical Methods for Detecting the Presence of Natural Selection in Bacterial Populations`
- position 16: `publication_component:citation:publication:doi:10.1002/9780470741894.ch1`; row SHA `193cfd334594367ff93247b7b2f90d43adf62e5ad2df3c0d879a38e31d5e2361`; title `The Basics of Protein Sequence Analysis`
- position 17: `publication_component:citation:publication:doi:10.1002/9780470892107.ch25`; row SHA `896af0e6cf7779fc5e68bb73a4e3172969eaf1472288d3e1f1789a8e9b4f8fc7`; title `Phylogenetic Search Algorithms for Maximum Likelihood`
- position 18: `publication_component:citation:publication:doi:10.1002/9781118860526.ch7`; row SHA `6d311bda6e75fd95ee02d3709352c8b24a5fa5ccd7311d457d7941f11eca84e0`; title `Adaptation of Flower Form: An Evo‐Devo Approach to Study Adaptive Evolution in Flower Morphology`
- position 19: `publication_component:citation:publication:doi:10.1002/9781119053095.ch80`; row SHA `8ed7108e273139e328a7963ed1f618fbcf9ee24134069c860746e9f4caf21d6f`; title `LegumeIP: An Integrative Platform for Comparative Genomics and Transcriptomics of Model Legumes`
- position 20: `publication_component:citation:publication:doi:10.1002/9781119072799.ch16`; row SHA `76c6ac287de1f4ae842a4157b1b4dc9c2cbf8f579da993f2441ba80364340746`; title `COMPARATIVE GENOMICS IN THE ASTERACEAE REVEALS LITTLE EVIDENCE FOR PARALLEL EVOLUTIONARY CHANGE IN INVASIVE TAXA`
- position 21: `publication_component:citation:publication:doi:10.1002/9781119127291.ch26`; row SHA `dc36174b700ee08267b582d698535779f291a85ef77878fe6cf2b1e6a93296a2`; title `Genomic and Epigenetic Aspects of Sex Determination in Half‐Smooth Tongue Sole`
- position 22: `publication_component:citation:publication:doi:10.1002/9781119487845.ch14`; row SHA `d57244f1ee82b29b5afac1c83cf131b5455e6190847971f32408ab6b44d6e2e1`; title `Detecting Natural Selection`
- position 23: `publication_component:citation:publication:doi:10.1002/9781119487845.ch36`; row SHA `6b42f51ede5773b397eb434c961229c990c7c16f9d008ae9480f9ea4d0f142db`; title `Bacterial Population Genomics`
- position 24: `publication_component:citation:publication:doi:10.1002/9781119990475.ch12`; row SHA `debc6bb7d70a6895d4bd991a2e6b6b73a309b7ca7a8cb2ead020761f0438cfae`; title `Evolving Perceptions on the Antiquity of the Modern Avian Tree`
- position 25: `publication_component:citation:publication:doi:10.1002/9781394284252.ch11`; row SHA `50b43bdc7e4ce1a10d74cb2d9577134bd7ccb5d40ac270ce7cc16e66199719c0`; title `Phylodynamics`
- position 26: `publication_component:citation:publication:doi:10.1002/9783527844340.ch18`; row SHA `18c23854ea023e0b86975874d50621f7f32ee4253679a84b35be49ddb3d552df`; title `Recent Trends in Computational Tools for Industrially Important Enzymes`
- position 27: `publication_component:citation:publication:doi:10.1002/adbi.202200002`; row SHA `c7588c4c10eec9b2a4bddd5c0981994615b8797254b264c209b5b90deec7f6a5`; title `3D Bioprinted Neural‐Like Tissue as a Platform to Study Neurotropism of Mouse‐Adapted SARS‐CoV‐2`
- position 28: `publication_component:citation:publication:doi:10.1002/advs.201901672`; row SHA `9160b73b466b42658d25fc12a30017b92262dcb6ac70e6386814e899dea3c2d0`; title `Comparison of Arachis monticola with Diploid and Cultivated Tetraploid Genomes Reveals Asymmetric Subgenome Evolution and Improvement of Peanut`
- position 29: `publication_component:citation:publication:doi:10.1002/advs.201901850`; row SHA `11e8259c9cbe55d44cc91ca0b289d69bac522dd995140ca2a17c439be1f4f367`; title `Mesostigma viride Genome and Transcriptome Provide Insights into the Origin and Evolution of Streptophyta`
- position 30: `publication_component:citation:publication:doi:10.1002/advs.202205445`; row SHA `b1bd19f24480c462286113436b3ea9f2f3b8836919a14eea2d8391557e04e527`; title `Optimization and Deoptimization of Codons in SARS‐CoV‐2 and Related Implications for Vaccine Development`
- position 31: `publication_component:citation:publication:doi:10.1002/advs.202309990`; row SHA `acd97ffb988945214b153d9143385d653bf48d25509c3825f93faf766cf7cd57`; title `Lineage‐Specific CYP80 Expansion and Benzylisoquinoline Alkaloid Diversity in Early‐Diverging Eudicots`
- position 32: `publication_component:citation:publication:doi:10.1002/advs.202402644`; row SHA `c78d42d70e4c451b04e156a4948540d212afefbc1800e70fe4104d27e2a9a15e`; title `De novo Whole‐Genome Assembly of the 10‐Gigabase Fokienia Hodginsii Genome to Reveal Differential Epigenetic Events Between Callus and Xylem`
- position 33: `publication_component:citation:publication:doi:10.1002/advs.202408861`; row SHA `152effe770173e27335077c734f23a9deb92a0d1e96ceb3d9b907392bd184630`; title `Chromatin Topological Domains Associate With the Rapid Formation of Tandem Duplicates in Plants`
- position 34: `publication_component:citation:publication:doi:10.1002/advs.202413023`; row SHA `068553f9cf1ddddbff7124b72fe4ded61cc33f548a50e775e05d5723fe3d541c`; title `Genomic Insights into Post‐Domestication Expansion and Selection of Body Size in Ponies`
- position 35: `publication_component:citation:publication:doi:10.1002/advs.202417054`; row SHA `c09eed1358a38586660b00a52f7ea1cf899409c614708a3d318c67166048eebb`; title `Chromosome‐Level Genome Assembly of the Leafcutter Bee Megachile rotundata Reveals Its Ecological Adaptation and Pollination Biology`
- position 36: `publication_component:citation:publication:doi:10.1002/advs.202503974`; row SHA `266aad7a5753c7d4f5d8463eeef312efab40d410308ce3fdeb5d6796e9c88d71`; title `Subgenome Dominance in Allotetraploid Actinidia valvata Regulates RNA m 6 A Modification for Waterlogging Tolerance`

## Review-packet boundary

Pre-T000006 review-packet SHA-256: `09e08a25873e9a628a2c7900b82f384f7b5838bb166b89d412759fe92a9101d6`

Pre-T000006 bytes: `314642`

At this design freeze, all eight `proposed_` fields remain blank for positions 12–500.

A later controlled review stage may target positions 12–36 only. Positions 37–500 must remain blank.

No software or model preclassification is permitted.

## Scientific review contract

Every target position requires explicit human review.

Permitted initial outcomes remain:

1. terminal `record_decision`;
2. `source_escalation`.

Terminal decisions remain:

- `exclude`;
- `retain_for_method_assessment`.

Frozen exclusion reasons remain:

- `application_only_no_reusable_method`
- `unrelated_variant_or_data_type`
- `duplicate_record_same_method_no_distinct_capability`
- `unsupported_by_primary_or_stable_authoritative_source`

Terminal decisions require substantive evidence and a non-empty source locator. Insufficient evidence remains explicit through `source_escalation` rather than forced classification.

## Authority separation

This post-pilot workflow separates human review work from live production-event authority.

The intended sequence is:

1. freeze this exact tranche;
2. implement and validate a post-pilot tranche guard without mutation;
3. conduct controlled human review/evidence work for positions 12–36;
4. freeze the resulting exact proposal/scientific decisions;
5. create a separately tracked one-use T000006 live authorization;
6. pin a fixed transaction timestamp and exact projected post-ledger SHA;
7. atomically append the authorized transaction;
8. create and validate the exact three-file checkpoint;
9. freeze T000006 completion/reconciliation before any further tranche.

The live authorization must not precede the frozen scientific proposal.

## Checkpoint

Reserved checkpoint:

`results/07_comparative_landscape/baseline_scientific_screening_event_receipts/T000006`

Exact final files:

1. `authorization.json`
2. `proposal.tsv`
3. `receipt.json`

Append-success/checkpoint-failure remains a recovery-required state. The accepted ledger must not be rolled back or replayed.

## Projected state invariants

If exactly 25 authorized initial events are accepted:

- event count: `22 -> 47`
- ready: `94,611 -> 94,586`
- blocked metadata remains `484`
- new terminal + awaiting-source-escalation states = `25`
- complete + awaiting-source-escalation after T000006 = `36`

The exact split between complete and awaiting-source-escalation cannot be preselected; it depends on human scientific review.

## No authority by this design

This freeze does not:

- modify `review_packet.tsv`;
- classify any target record;
- create a proposal;
- create T000006 authorization;
- call `allow_production=True`;
- append an event;
- create the T000006 checkpoint;
- authorize positions 37–500.

## Next gate

`IMPLEMENT_GENERIC_POST_PILOT_TRANCHE_GUARD_WITHOUT_EVENTS_OR_REVIEW_MUTATION`
