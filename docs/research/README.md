# SophiaNet research collection

This folder contains **ten primary research papers** selected to explain SophiaNet's component choices and identify evaluation gaps. Read the [literature review](../literature_review.md) for findings, limitations, implementation comparisons, and a proposed evaluation plan. These papers are a focused engineering corpus; they are not an exhaustive survey or evidence that SophiaNet reproduces their results.

All PDFs were retrieved from public author, publisher, or arXiv sources on **October 30, 2026**. Each local file passed PDF-signature, readable-text, page-count, and SHA-256 checks using `pypdf` in the `sophianet-venv` Conda environment. The [catalogue](papers.json) records authors, first publication/preprint year, venue, version where identifiable, source/download URLs, byte size, page count, checksum, and access date.

## The ten papers

The year column uses the initial preprint/publication year; conference publication and the downloaded revision are shown separately.

| ID | Paper and authors | Year / venue / local revision | Relevance | Sources and local copy |
| --- | --- | --- | --- | --- |
| 01 | **Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks** — Patrick Lewis et al. | 2020; NeurIPS 2020; arXiv v4 revised 2021-04-12; 19 pages | Retrieval-grounded generation foundation | [Primary record](https://arxiv.org/abs/2005.11401) · [PDF](01_rag_knowledge_intensive_nlp.pdf) |
| 02 | **ReAct: Synergizing Reasoning and Acting in Language Models** — Shunyu Yao et al. | 2022; ICLR 2023; v3 revised 2023-03-10; 33 pages | Model/action feedback loops | [Primary record](https://arxiv.org/abs/2210.03629) · [PDF](02_react_reasoning_and_acting.pdf) |
| 03 | **Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks** — Nils Reimers and Iryna Gurevych | 2019; EMNLP-IJCNLP 2019; v1 dated 2019-08-27; 11 pages | Efficient sentence representation and similarity | [Publisher](https://aclanthology.org/D19-1410/) · [PDF](03_sentence_bert.pdf) |
| 04 | **Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection** — Akari Asai et al. | 2023; later ICLR 2024; local v1 dated 2023-10-17; 30 pages | Learned retrieval and evidence critique as an unimplemented comparison | [Primary record](https://arxiv.org/abs/2310.11511) · [PDF](04_self_rag.pdf) |
| 05 | **Tutor CoPilot: A Human-AI Approach for Scaling Real-Time Expertise** — Rose E. Wang et al. | 2024 initial preprint; local v3 revised 2026-10-10; no venue asserted; 53 pages | Educational-outcome study design | [Primary record](https://arxiv.org/abs/2410.03017) · [PDF](05_tutor_copilot.pdf) |
| 06 | **Learning Transferable Visual Models From Natural Language Supervision** — Alec Radford et al. | 2021; ICML 2021; local arXiv v1 header dated 2021-02-26; 48 pages | CLIP image/text alignment | [Publisher](https://proceedings.mlr.press/v139/radford21a.html) · [PDF](06_clip.pdf) |
| 07 | **BLIP: Bootstrapping Language-Image Pre-training for Unified Vision-Language Understanding and Generation** — Junnan Li et al. | 2022; ICML 2022; local v2 header dated 2022-02-15; 12 pages | Image-to-text captioning foundation | [Publisher](https://proceedings.mlr.press/v162/li22n.html) · [PDF](07_blip.pdf) |
| 08 | **High-Resolution Image Synthesis with Latent Diffusion Models** — Robin Rombach et al. | 2021 preprint; CVPR 2022; local v2 header dated 2022-04-13; 45 pages | Foundational conditioned image synthesis | [Primary record](https://arxiv.org/abs/2112.10752) · [PDF](08_latent_diffusion.pdf) |
| 09 | **An Overview of the Tesseract OCR Engine** — Ray Smith | 2007; ICDAR 2007, pp. 629–633; author-hosted PDF without an arXiv version; 5 pages | Historical OCR architecture | [Author's publication record](https://research.google/pubs/an-overview-of-the-tesseract-ocr-engine/) · [PDF](09_tesseract_ocr.pdf) |
| 10 | **Nemotron 3 Nano: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning** — NVIDIA report; Aaron Blakeman and collaborators in the arXiv record | 2025 technical report; v1 header dated 2025-12-23, cover dated 2025-12-25; 40 pages | Related Nemotron-family architecture and agentic post-training | [Primary record](https://arxiv.org/abs/2512.20848) · [PDF](10_nemotron_3_nano.pdf) |

## Version and implementation boundaries

Tutor CoPilot's local v3 and its landing-page abstract have different sample counts. Use the versioned PDF for numerical claims rather than combining versions. The Self-RAG local copy is its initial preprint, not the later conference PDF. Several arXiv downloads use an unversioned URL; the catalogue records the version found in the downloaded PDF header, and its checksum identifies that exact copy.

The original Sentence-BERT paper is not the exact training report for SophiaNet's MiniLM checkpoint. The latent-diffusion paper is not an exact model report for the configured Flux or Stable Diffusion 3.5 models. The Nano report is not the report for the application's active **Nemotron 3.5 Lightning** endpoint. Paper benchmark results and hardware throughput numbers must not be described as SophiaNet results. See the [model inventory](../models_and_ai_infrastructure.md), [architecture](../system_architecture.md), and [evaluation limits](../evaluation_and_limitations.md).

## Provenance and reuse

The PDFs are unmodified source copies; the application did not generate them. Original authors and rights holders retain their rights, and each source's publication or distribution terms continue to apply. A public download or inclusion in this local research collection does not grant a new right to relicense or republish a paper. Cite the primary record and the appropriate version when using its findings.

[Research notes](notes/SophiaNet%20research%20foundations) record inspected sections, evidence, and code-grounded inferences. The original [retrieval/education manifest](notes/SophiaNet%20research%20foundations/rag_manifest.json) and [vision/OCR manifest](notes/SophiaNet%20research%20foundations/vision_pdf_manifest.json) are retained alongside the combined [papers.json](papers.json). Empty PDF title metadata is not treated as a corrupt file: signature, page parsing, text extraction, source identity, and hash checks identify the copies.

The collection supports review and citation. It does not contain reproduced experiments, newly trained models, or a systematic-review screening database.
