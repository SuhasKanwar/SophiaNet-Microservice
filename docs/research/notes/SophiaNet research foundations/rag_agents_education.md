# Retrieval, agents and educational evidence

Access date: 2026-10-30. PDFs below are unmodified, freely accessible author preprints downloaded directly from arXiv. Each passed PDF-signature, parser, page-count and nonempty-text checks with `pypdf` in `sophianet-venv`. Checksums identify the exact local copies; they do not establish copyright permission for republication. No experiments were reproduced.

## 01 — Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

### Takeaway

Combining learned retrieval and generation improves knowledge-intensive benchmarks; SophiaNet implements a simpler inference-time retrieval pipeline. [Primary source](https://arxiv.org/abs/2005.11401v4)

### Cited Findings

- Authors: Patrick Lewis; Ethan Perez; Aleksandra Piktus; Fabio Petroni; Vladimir Karpukhin; Naman Goyal; Heinrich Küttler; Mike Lewis; Wen-tau Yih; Tim Rocktäschel; Sebastian Riedel; Douwe Kiela. First preprint 2020; accepted at NeurIPS 2020; downloaded revision v4 (2021). [Metadata](https://arxiv.org/abs/2005.11401)
- Method: jointly trained DPR/BART, passage marginalization and a Wikipedia index; evaluation covers QA, generation and fact verification. [Sections 2–4](https://arxiv.org/pdf/2005.11401v4)
- File: `01_rag_knowledge_intensive_nlp.pdf`; 19 pages; SHA256 `23e3249e9a1e75418d82efecab0ea8c4d033b89c93742f63208d47ce01f21233`. [Downloaded PDF](https://arxiv.org/pdf/2005.11401v4)
- Examined: abstract, methods pp. 2–4, results pp. 5–8, discussion p. 9. [PDF](https://arxiv.org/pdf/2005.11401v4)

### Inferences

- SophiaNet's request-local FAISS attachments, frozen MiniLM and hosted Nemotron do not reproduce this training method. [Implementation](../../../../microservice/services/rag.py)

### Gaps

- This paper does not validate SophiaNet's educational effectiveness or retrieval quality. [Scope](https://arxiv.org/abs/2005.11401v4)

## 02 — ReAct: Synergizing Reasoning and Acting in Language Models

### Takeaway

Interleaving model decisions with external actions supports evidence gathering and task completion. [Primary source](https://arxiv.org/abs/2210.03629v3)

### Cited Findings

- Authors: Shunyu Yao; Jeffrey Zhao; Dian Yu; Nan Du; Izhak Shafran; Karthik Narasimhan; Yuan Cao. First preprint October 2022; ICLR 2023; downloaded camera-ready v3 (March 2023). [Metadata](https://arxiv.org/abs/2210.03629)
- Evaluated on HotpotQA, FEVER, ALFWorld and WebShop; retrieval can still mislead agents and action failures remain. [Sections 3–4](https://arxiv.org/pdf/2210.03629v3)
- File: `02_react_reasoning_and_acting.pdf`; 33 pages; SHA256 `f285b0971ae4a790e402fb93966bed3adde2cf0a04977d08b2b40d6ab0cace69`. [Downloaded PDF](https://arxiv.org/pdf/2210.03629v3)
- Examined: abstract, method p. 3, reasoning/action evaluations pp. 4–8 and conclusion p. 9. [PDF](https://arxiv.org/pdf/2210.03629v3)

### Inferences

- SophiaNet uses a related tool-feedback loop, not the paper's exposed reasoning trajectories or benchmarks. [Implementation](../../../../microservice/agents/graph.py)

### Gaps

- A working graph does not establish factual correctness or ReAct-level benchmark performance. [Scope](https://arxiv.org/abs/2210.03629v3)

## 03 — Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks

### Takeaway

Independent sentence embeddings permit efficient semantic comparison instead of repeatedly encoding every sentence pair. [Primary source](https://arxiv.org/abs/1908.10084v1)

### Cited Findings

- Authors: Nils Reimers; Iryna Gurevych. Preprint August 2019; EMNLP-IJCNLP 2019; ACL pages 3982–3992; DOI `10.18653/v1/D19-1410`. [Publisher metadata](https://aclanthology.org/D19-1410/)
- Siamese/triplet training is assessed on semantic similarity, transfer tasks and computational efficiency. [Sections 3–8](https://arxiv.org/pdf/1908.10084v1)
- File: `03_sentence_bert.pdf`; 11 pages; SHA256 `92366d22fc0521350d6cbe0ad72bcee754f90e88181d7b4a8e2adb1e7e594fec`. [Downloaded PDF](https://arxiv.org/pdf/1908.10084v1)
- Examined: abstract, model p. 3, evaluations pp. 4–7 and efficiency/conclusion p. 8. [PDF](https://arxiv.org/pdf/1908.10084v1)

### Inferences

- SophiaNet applies the sentence-transformer ecosystem through MiniLM; this paper is not the exact MiniLM checkpoint's training report. [Configuration](../../../../microservice/config/models.py)

### Gaps

- Similarity benchmarks do not establish course-document retrieval accuracy or student learning gains. [Scope](https://arxiv.org/abs/1908.10084v1)

## 04 — Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection

### Takeaway

Retrieval decisions and evidence/answer critiques can be learned rather than applying fixed retrieval indiscriminately. [Primary source](https://arxiv.org/abs/2310.11511v1)

### Cited Findings

- Authors: Akari Asai; Zeqiu Wu; Yizhong Wang; Avirup Sil; Hannaneh Hajishirzi. Preprint October 2023; later ICLR 2024. Local copy is the 2023 preprint, not the conference PDF. [Preprint metadata](https://arxiv.org/abs/2310.11511); [conference proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/file/25f7be9694d7b32d5cc670927b8091e1-Paper-Conference.pdf)
- Trained reflection tokens control retrieval and assess relevance/support; experiments assess factuality and attribution. [Sections 3–5](https://arxiv.org/pdf/2310.11511v1)
- File: `04_self_rag.pdf`; 30 pages; SHA256 `d9eaa1398abac0df67a9d0933a5bf8b6d9d83d2e72da2a486073cd842dd52978`. [Downloaded PDF](https://arxiv.org/pdf/2310.11511v1)
- Examined: abstract, method pp. 3–5, evaluation/results pp. 6–10 and conclusion p. 10. [PDF](https://arxiv.org/pdf/2310.11511v1)

### Inferences

- SophiaNet has neither learned reflection tokens nor an explicit evidence-grading stage. [Implementation](../../../../microservice/services/assistant.py)

### Gaps

- Adding tool execution alone cannot substantiate a Self-RAG implementation or its accuracy claims. [Method](https://arxiv.org/abs/2310.11511v1)

## 05 — Tutor CoPilot: A Human-AI Approach for Scaling Real-Time Expertise

### Takeaway

An evaluated human-tutor assistant provides a stronger educational evidence model than application-level demonstrations. [Primary source](https://arxiv.org/pdf/2410.03017v3)

### Cited Findings

- Authors: Rose E. Wang; Ana T. Ribeiro; Carly D. Robinson; Susanna Loeb; Dora Demszky. First preprint October 2024; local v3 revised October 2026. Treat as an arXiv preprint here; no venue is asserted. [Metadata](https://arxiv.org/abs/2410.03017)
- Randomized live-tutoring evaluation reports a four-percentage-point mathematics mastery increase. Limited exposure, context generalization and grade-appropriate suggestions remain concerns. [Results and limitations](https://arxiv.org/pdf/2410.03017v3)
- File: `05_tutor_copilot.pdf`; 53 pages; SHA256 `90274f5c23ea01d4c3c4921b4abb6b369665a1d23deabb0dd4fb255cd09bfa7f`. [Downloaded PDF](https://arxiv.org/pdf/2410.03017v3)
- Examined: abstract p. 1, methods pp. 4–8, results pp. 8–14, discussion/limitations pp. 15–17. [PDF](https://arxiv.org/pdf/2410.03017v3)
- Version warning: the landing-page abstract's sample counts differ from the current PDF. Use the versioned PDF for numerical claims; do not mix versions. [Landing page](https://arxiv.org/abs/2410.03017); [v3](https://arxiv.org/pdf/2410.03017v3)

### Inferences

- SophiaNet's learner-facing multimodal workflows differ from tutor decision support, without demonstrated superiority. [Implemented agents](../../../../microservice/services/assistant.py)

### Gaps

- SophiaNet has no comparable learner-outcome trial; Tutor CoPilot's effect size cannot transfer to it. [Study scope](https://arxiv.org/pdf/2410.03017v3)
