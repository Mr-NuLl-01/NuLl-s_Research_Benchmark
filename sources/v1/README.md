# V1 offline source materials

These are real, publicly available source papers and figures, archived so the candidate can complete each research question without a network connection. They are supplied as source evidence, not as benchmark answers. The numerical sensor and replication fixtures are benchmark-created synthetic data and are not measurements from these papers.

## Exact licenses and supplied scope

| ID | Paper | Article-specific license | Supplied readable scope |
| --- | --- | --- | --- |
| P1 | Weissgerber TL, Milic NM, Winham SJ, Garovic VD (2015). *Beyond Bar and Line Graphs: Time for a New Data Presentation Paradigm*. PLOS Biology 13(4), e1002128. DOI: [10.1371/journal.pbio.1002128](https://doi.org/10.1371/journal.pbio.1002128) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), explicitly linked in this article's XML permissions | Complete main article text and bibliography, all three main figures, and complete S1 Text supplemental methods/results as readable extracted text. Other supplementary files are not supplied. |
| P2 | Rougier NP, Droettboom M, Bourne PE (2014). *Ten Simple Rules for Better Figures*. PLOS Computational Biology 10(9), e1003833. DOI: [10.1371/journal.pcbi.1003833](https://doi.org/10.1371/journal.pcbi.1003833) | [CC0 1.0 public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/), as explicitly stated by this article. Do not substitute the publisher's usual CC BY license. | Complete main article text and bibliography, all eight main figures. Linked GitHub figure scripts and external references are not supplied. |
| P3 | Crameri F, Shephard GE, Heron PJ (2020). *The misuse of colour in science communication*. Nature Communications 11, 5444. DOI: [10.1038/s41467-020-19160-7](https://doi.org/10.1038/s41467-020-19160-7) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), from this article's Rights and permissions statement, including its third-party material caveat | Complete main Abstract, Introduction (including boxes and all six figures), Methods, Data availability and References. Supplementary Notes and supplementary figures are not supplied and cannot be treated as read. |

The article-specific permissions statements are retained verbatim in `manifest.json`. No credit line in these supplied main figures declares an exclusion from the article license. P2 Figure 1 is the authors' remake of a newspaper figure; the original caption explaining that transformation is retained. P3 Figure 1 credits the historical Marie Skłodowska-Curie photograph to Henri Manuel; this attribution is retained. The archive does not purport to license publisher website chrome or independently cited third-party papers. Their external bibliographic links are references, not supplied readings.

Retrieved 2026-10-17 UTC. The UTC clock was checked when preparing the manifest. `download-urls.json` records the original figure and supplement URLs. `manifest.json` records URL (for downloaded original bytes), SHA-256, size, role, exact license evidence and supplied reading scope. The original XML/HTML/DOCX files are retained. Original high-resolution figure retrieval URLs, byte sizes and SHA-256 records are preserved in `retrieved-original-images.json`; the high-resolution duplicates are omitted from this compact archive. Faithful offline display derivatives are retained for all 17 figures, and are sufficient to regenerate every candidate packet. Cryptographic hashes establish byte identity; they do not establish the scientific truth of the papers.

## Transformation and offline use

`article-packets.json` contains reformatted, readable article text and base64-embedded display figures. The candidate HTMLs embed this content inside visible expandable reading sections. They do not need to open a source directory, load a remote image or fetch a paper. A digest or synopsis is not substituted for the paper text. The paper bibliographies retain their original local numbering, while P1/P2/P3 are benchmark source IDs.

The original figures have display derivatives in `offline-figures/`. These are downsampled to a maximum 1100 pixels per side and quantized to 128 colours to keep each self-contained candidate file below 3 MB. Figure content and complete captions are retained. Candidates are instructed not to treat downsampled image pixels as quantitative source data. Source formulae, definitions and typographical errors are preserved as published. P1 S1 tables are provided as sequential source-cell text extracted from DOCX; the DOCX original is also archived here. The tasks ask for transparent handling of source ambiguities, without injecting evaluator conclusions into the reading material.

Rebuild the readable source packet and byte manifest locally with:

```bash
python sources/v1/prepare_sources.py
```

This preparation script requires `lxml` and `Pillow` (the image derivatives are checked in). Benchmark task generation and integrity tests use the Python standard library. No network is used by the rebuild script. If source assets are intentionally replaced, review the exact new license and reading scope before rebuilding; regenerating hashes alone is not a license review.

## Synthetic figure

`synthetic/make_figure.py`, `paired.csv` and `transient.csv` generate the actual two-panel input figure embedded in R04. This source is original benchmark material. It is a figure to interpret, not a candidate answer. The paired experiment and transient experiment use different devices. The caption defines the independent units, batch colours, input timing and the across-device sample SD shading. No p-values, mechanism experiments or long-term observations are supplied. Regeneration requires local `numpy` and `matplotlib`:

```bash
MPLCONFIGDIR=/tmp/nrb-mpl python sources/v1/synthetic/make_figure.py
```

R01's actual style references (P1 Figure 2, P2 Figure 7, P3 Figure 3) and R04's actual input figure were visually opened and inspected during construction. This inspection checked the supplied content and display readability; it is not a certification of the papers' scientific claims. Original figure style references are shown with full source captions and license credit in the candidate task.
