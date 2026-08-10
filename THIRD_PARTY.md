# Third-party sources and attribution

## SNPPar validation materials

Experiment 03 retrieves published SNP matrices, phylogenies, node-labelled trees and
SNPPar mutation-event outputs from `d-j-e/SNPPar_test`. These upstream files are not
committed here. Their source URLs and required SHA-256 hashes are embedded in the
experiment code and verified before analysis.

- Edwards DJ, Duchêne S, Pope B, Holt KE. *SNPPar: identifying convergent evolution
  and other homoplasies from microbial whole-genome alignments*. Microbial Genomics.
  2021;7:000694. DOI: 10.1099/mgen.0.000694.
- Perrin A et al. *Evolutionary dynamics and genomic features of the Elizabethkingia
  anophelis 2015 to 2016 Wisconsin outbreak strain*. Nature Communications.
  2017;8:15483. DOI: 10.1038/ncomms15483.
- Lieberman TD et al. *Parallel bacterial evolution within multiple patients identifies
  candidate pathogenicity genes*. Nature Genetics. 2011;43:1275–1280.
  DOI: 10.1038/ng.997.

## Published focal-branch comparisons

Experiment 05 compares BRANCHSNV output with published branch-associated SNVs from:

- White RT et al. *20 years later: unravelling the genomic success of New Zealand's
  home-grown AK3 community-associated methicillin-resistant Staphylococcus aureus*.
  Microbial Genomics. 2025;11:001452. DOI: 10.1099/mgen.0.001452.
- White RT et al. *Rapid identification and subsequent contextualization of an outbreak
  of methicillin-resistant Staphylococcus aureus in a neonatal intensive care unit using
  nanopore sequencing*. Microbial Genomics. 2024;10:001273.
  DOI: 10.1099/mgen.0.001273.
- White RT et al. *Integration of blaOXA-48 into a Col156 plasmid drove a
  carbapenem-resistant Escherichia coli ST131 outbreak in New Zealand: Global genomic
  evidence for the gene’s multilayered dissemination*. Drug Resistance Updates.
  2026;84:101327. DOI: 10.1016/j.drup.2025.101327.

The exact author working alignments and trees used by Experiments 05 and 06 are
committed under `inputs/empirical/` with SHA-256 integrity checks. Public sequence-data
accessions and BioProjects are reported in the associated manuscript.
