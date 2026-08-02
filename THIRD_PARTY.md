# Third-party sources and attribution

## SNPPar validation materials

Experiment 03 retrieves published SNP matrices, phylogenies, node-labelled trees and
SNPPar mutation-event outputs from:

- Repository: `d-j-e/SNPPar_test`
- Repository licence: GNU General Public License v3.0
- SNPPar publication: Edwards DJ, Duchêne S, Pope B, Holt KE. *SNPPar: identifying
  convergent evolution and other homoplasies from microbial whole-genome
  alignments*. Microbial Genomics. 2021;7:000694.
  DOI: 10.1099/mgen.0.000694.

The third-party source files are not committed here. The download manifest in
`experiments/03_published_datasets/run.py` records the source URL and expected
SHA-256 checksum for every file. The downloader accepts a file only when its checksum
matches.

The underlying published datasets should also be cited:

- Perrin A et al. *Evolutionary dynamics and genomic features of the
  Elizabethkingia anophelis 2015 to 2016 Wisconsin outbreak strain*. Nature
  Communications. 2017;8:15483. DOI: 10.1038/ncomms15483.
- Lieberman TD et al. *Parallel bacterial evolution within multiple patients
  identifies candidate pathogenicity genes*. Nature Genetics. 2011;43:1275–1280.
  DOI: 10.1038/ng.997.

## AK3 comparison

The published branch tables used in Experiment 03 are from:

- White RT et al. *20 years later: unravelling the genomic success of New Zealand's
  home-grown AK3 community-associated methicillin-resistant Staphylococcus aureus*.
  Microbial Genomics. 2025;11:001452. DOI: 10.1099/mgen.0.001452.

The exact AK3 alignment and tree are not included in this repository snapshot. Their
required SHA-256 checksums are recorded in the Experiment 03 documentation and code.
