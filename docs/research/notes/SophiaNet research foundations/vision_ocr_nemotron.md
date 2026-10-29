# Vision, OCR and Nemotron research foundations

Accessed 2026-10-30. PDF validation used `pypdf` in `sophianet-venv`; files were downloaded unchanged from public primary/author-hosted sources. Local hashes identify copies, not publisher endorsements.

## [06] Learning Transferable Visual Models From Natural Language Supervision

### Takeaway
Contrastive image/text pretraining enables zero-shot transfer through natural-language class descriptions. The paper discusses specialized-task and distribution limitations. [Primary source](https://proceedings.mlr.press/v139/radford21a.html).

### Cited findings
- **Authors / publication:** Alec Radford, Jong Wook Kim, Chris Hallacy, Aditya Ramesh, Gabriel Goh, Sandhini Agarwal, Girish Sastry, Amanda Askell, Pamela Mishkin, Jack Clark, Gretchen Krueger, Ilya Sutskever. 2021; ICML 2021 / PMLR 139:8748–8763. [Publication record](https://proceedings.mlr.press/v139/radford21a.html).
- **Source PDF:** [Download](https://arxiv.org/pdf/2103.00020); resolved to `https://arxiv.org/pdf/2103.00020`.
- **Local copy:** [../../06_clip.pdf](../../06_clip.pdf) — 48 pages, 6813639 bytes.
- **SHA-256:** `6478b6e571a7d6fcd846d8ef77bfd60c285f1986abb8f475eedc43de403074f5`.
- **Inspected:** Abstract; §2 training objective and temperature; §6 limitations; PDF pp. 1, 4, 18–19.
- **Additional primary record:** [Source](https://arxiv.org/abs/2103.00020).

### Inferences
SophiaNet reuses CLIP for an image/prompt diagnostic, not a newly trained joint retrieval system. [Implementation](../../../../microservice/services/clip.py).

### Gaps
The code divides a learned-temperature-scaled logit by 100 and clamps it; this does not establish a calibrated probability or verified educational-image quality. [Implementation](../../../../microservice/services/clip.py).

## [07] BLIP: Bootstrapping Language-Image Pre-training for Unified Vision-Language Understanding and Generation

### Takeaway
BLIP combines understanding and generation with caption bootstrapping and filtering of noisy image/text data, reporting gains on retrieval, captioning and VQA benchmarks. [Primary source](https://proceedings.mlr.press/v162/li22n.html).

### Cited findings
- **Authors / publication:** Junnan Li, Dongxu Li, Caiming Xiong, Steven Hoi. 2022; ICML 2022 / PMLR 162:12888–12900. [Publication record](https://proceedings.mlr.press/v162/li22n.html).
- **Source PDF:** [Download](https://arxiv.org/pdf/2201.12086); resolved to `https://arxiv.org/pdf/2201.12086`.
- **Local copy:** [../../07_blip.pdf](../../07_blip.pdf) — 12 pages, 1303121 bytes.
- **SHA-256:** `63e0335cdd57c3d92b907b89c93d10befdd29b8aeed108091bbde90c121ed97a`.
- **Inspected:** Abstract; introduction; CapFilt framework; §7 conclusion; PDF pp. 1–4, 9.
- **Additional primary record:** [Source](https://arxiv.org/abs/2201.12086).

### Inferences
SophiaNet uses an existing BLIP caption checkpoint to convert attachments into text for RAG. [Implementation](../../../../microservice/utils/files.py).

### Gaps
That application is not BLIP training or full multimodal reasoning. The custom blur/contrast/edge/grayscale preprocessing needs an ablation; no accuracy benefit is established. [Implementation](../../../../microservice/services/image_captioning.py).

## [08] High-Resolution Image Synthesis with Latent Diffusion Models

### Takeaway
Denoising in an autoencoder latent space reduces computational cost relative to pixel-space diffusion; cross-attention supports conditioning. Sequential sampling and precision loss remain limitations. [Primary source](https://arxiv.org/abs/2112.10752).

### Cited findings
- **Authors / publication:** Robin Rombach, Andreas Blattmann, Dominik Lorenz, Patrick Esser, Björn Ommer. Preprint 2021-12-20; revised 2022-04-13; CVPR 2022. [Publication record](https://arxiv.org/abs/2112.10752).
- **Source PDF:** [Download](https://arxiv.org/pdf/2112.10752); resolved to `https://arxiv.org/pdf/2112.10752`.
- **Local copy:** [../../08_latent_diffusion.pdf](../../08_latent_diffusion.pdf) — 45 pages, 40842586 bytes.
- **SHA-256:** `46ede043a8dc07ca1f0f445620523fe1ad8b2436bd83856a3835612a47e9f79e`.
- **Inspected:** Abstract; latent representation/conditioning methodology; §5 limitations and societal impact; PDF pp. 1–4, 9.
- **Additional primary record:** [Source](https://arxiv.org/abs/2112.10752v2).

### Inferences
SophiaNet composes hosted image generation and fallback with learning workflows. [Implementation](../../../../microservice/services/images.py).

### Gaps
This foundational paper is not the exact architecture report for configured Flux.1-dev or Stable Diffusion 3.5 Large. Attractive generated pictures do not establish factual or pedagogical correctness. [Configured models](../../../../microservice/config/models.py).

## [09] An Overview of the Tesseract OCR Engine

### Takeaway
The paper describes line and word processing, character recognition and adaptive classification in the historical Tesseract engine, with evaluation on scanned document sets. [Primary source](https://research.google/pubs/an-overview-of-the-tesseract-ocr-engine/).

### Cited findings
- **Authors / publication:** Ray Smith. 2007; Ninth International Conference on Document Analysis and Recognition (ICDAR), pp. 629–633; DOI 10.1109/ICDAR.2007.4376991. [Publication record](https://research.google/pubs/an-overview-of-the-tesseract-ocr-engine/).
- **Source PDF:** [Download](https://research.google.com/pubs/archive/33418.pdf); resolved to `https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/33418.pdf`.
- **Local copy:** [../../09_tesseract_ocr.pdf](../../09_tesseract_ocr.pdf) — 5 pages, 168158 bytes.
- **SHA-256:** `a95ae92b905eddf961d0444ef88082b7d4b0597b4a6b4239bf94f8af50a73328`.
- **Inspected:** Complete five-page paper, particularly §2 architecture, recognition/adaptation, and §8 results.

### Inferences
SophiaNet wraps Tesseract through pytesseract to extract uploaded image text. [Implementation](../../../../microservice/utils/ocr.py).

### Gaps
A 2007 engine description is not validation of the currently installed OCR binary, arbitrary handwriting, formulas, or multilingual class notes; evaluate contemporary application inputs with CER/WER. [Implementation scope](../../../../microservice/utils/ocr.py).

## [10] Nemotron 3 Nano: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning

### Takeaway
The report presents a sparse hybrid Mamba/Transformer model with supervised and reinforcement-learning post-training for reasoning, chat and agentic tasks. Throughput comparisons use specified H200 workloads. [Primary source](https://arxiv.org/abs/2512.20848).

### Cited findings
- **Authors / publication:** NVIDIA (collective technical-report author; arXiv lists Aaron Blakeman and collaborators). 2025 technical report; arXiv submitted 2025-12-23, v1; downloaded PDF cover dated 2025-12-25. [Publication record](https://arxiv.org/abs/2512.20848).
- **Source PDF:** [Download](https://arxiv.org/pdf/2512.20848); resolved to `https://arxiv.org/pdf/2512.20848`.
- **Local copy:** [../../10_nemotron_3_nano.pdf](../../10_nemotron_3_nano.pdf) — 40 pages, 1035079 bytes.
- **SHA-256:** `91d0a294db6e42f00e7fcee50df5dcbf19a5264a11443d117a199b1065eb71f4`.
- **Inspected:** Abstract; §1 and Figure 1 benchmark/throughput setup; §2.1 architecture; post-training discussion; PDF pp. 1–4, 9.
- **Additional primary record:** [Source](https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Nano-Technical-Report.pdf).

### Inferences
It motivates a tool-capable Nemotron-family backend; SophiaNet contributes application orchestration rather than model training. [Implementation](../../../../microservice/services/assistant.py).

### Gaps
The active model is Nemotron 3.5 Lightning, not this Nano checkpoint. Nano benchmark, throughput and context claims cannot be assigned to SophiaNet or its cloud deployment. [Configured backend](../../../../microservice/config/models.py).

