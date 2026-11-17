# Research Paper Studio

Open **Research Papers** in the chatbot sidebar (`/chatbot/t/research-studio`). Enter a research topic, optionally select the earliest publication year, then search. Cards show source-supplied titles, authors (up to 20), year, venue, DOI, abstracts when available, original paper links and arXiv PDF links. Export the reading list as Markdown before leaving the page; search results are not stored in the database.

## LLM-guided research

The Studio now uses NVIDIA through a bounded LangGraph workflow: **plan → retrieve → select**. The planner interprets the original question into a concise scholarly search phrase and focus. Retrieval uses the Crossref/arXiv service described below. The selector reviews up to 20 deduplicated candidates using titles, years, venue and abstracts (up to 1,600 characters each), and returns ordered candidate IDs with short relevance explanations. Empty selections are allowed when nothing fits.

Pydantic validates model output. Duplicate IDs, out-of-range IDs and selections exceeding the requested limit are rejected. Final metadata and URLs are copied from retrieved records, never constructed by the LLM. The card's “Why this paper” section is an AI assessment of metadata, not a full-text review or a verified statement of research findings. Abstracts and source attribution remain visible separately.

The planner and selector require `NVIDIA_API_KEY`; model calls consume provider usage and add latency. The underlying scholarly retrieval itself still uses public sources. No silent retrieval-only fallback is used if LLM output is invalid. The web proxy allows up to four minutes for the workflow. The standalone research/debate lookup tool continues to use deterministic retrieval, avoiding recursive LLM orchestration.

Verification for this change: 43 backend tests pass; TypeScript and targeted lint pass. A live HTTP research question returned five source-linked papers with AI explanations. A browser search using the live Python API on an isolated test port checked the search brief, relevance cards, export and mobile width; that browser check forwarded the request directly to Python instead of exercising the web proxy transport. The Notes Tool's original upload layout was restored. Google OAuth and full-text factual verification were not exercised.

## Retrieval behavior

The authenticated web endpoint `POST /api/papers` proxies to Python `POST /search-papers`. Both validate a 2–500-character topic, an optional year between 1900 and the current year, and a result limit of 1–20 (default 10).

Python searches the public Crossref and arXiv endpoints concurrently, with a 15-second timeout per request. The retrieval helper itself requires no new dependency or API key; the Studio additionally uses the LLM workflow above. Public scholarly services can impose rate limits or availability restrictions. The shared research/debate `search_papers` tool now reuses this same service.

Crossref candidates are restricted to journal and proceedings articles; books, chapters and generic posted content are excluded. arXiv provides preprints, which may not have undergone peer review. Abstracts and PDFs are included only when returned by a source; no claims are inferred from titles and no paywall is bypassed. Missing abstracts are labelled in the UI.

The search retrieves up to 20 candidates from each source. Duplicate DOI or normalized-title matches are merged, combining attribution, abstracts and PDF availability. Retrieval candidate ordering uses reciprocal-rank fusion (`1 / (60 + source_rank)`) of source ordering, with deterministic ties. Rankings are neither quality scores nor calibrated relevance probabilities. Local filtering and a bounded candidate pool can omit papers: this is a discovery tool, not an exhaustive literature review or a guarantee of the globally most relevant research.

A failed source produces an explicit warning while the other source can still supply results. Successful empty searches show a helpful empty state. If both sources fail, the API returns a safe HTTP 502 and the UI offers retry. HTML/JATS metadata is converted to plain text; link schemes are constrained to HTTP(S). Links open in a separate tab; the service does not fetch arbitrary URLs or download paper bodies.

## Verification

- The retrieval unit tests cover, including duplicate merging/enrichment, source outages, year filtering, provider parsing, metadata cleanup, URL schemes, request validation and safe API errors.
- TypeScript and targeted lint for the new frontend/API pass.
- Live searches for retrieval-augmented generation and CRISPR returned real results from both sources. These checks validate retrieval and contracts, not an expert relevance benchmark.
- Browser checks used a temporary signed test session, the actual web server, Python and live source results. Search, year filter, abstracts, reading-list export and mobile layout passed. The temporary session was cleared after testing; Google OAuth itself was not exercised.
- Empty results, partial-source warnings and unavailable-search UI states were checked using mocked browser responses. Backend outage handling is also covered with unit tests.
- Anonymous web requests return 401; authenticated invalid requests return 400; invalid Python requests return 422.

Run backend tests from `microservice`:

```bash
conda run --no-capture-output -n sophianet-venv python -m unittest discover -s tests -q
```

With the Python API running on port 8000, run the opt-in live retrieval check from `microservice`:

```bash
conda run --no-capture-output -n sophianet-venv python scripts/check_papers.py
```

`TEST_API_URL` can override the API address. This check makes real requests to scholarly services and fails if neither source returns usable matches. A partial-source outage is printed as a warning.

Primary API references: [Crossref REST API](https://github.com/CrossRef/rest-api-doc), [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html).
