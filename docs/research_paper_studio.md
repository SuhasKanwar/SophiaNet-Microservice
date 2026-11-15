# Research Paper Studio

Open **Research Papers** in the chatbot sidebar (`/chatbot/t/research-studio`). Enter a research topic, optionally select the earliest publication year, then search. Cards show source-supplied titles, authors (up to 20), year, venue, DOI, abstracts when available, original paper links and arXiv PDF links. Export the reading list as Markdown before leaving the page; search results are not stored in the database.

## Search behavior

The authenticated web endpoint `POST /api/papers` proxies to Python `POST /search-papers`. Both validate a 2–500-character topic, an optional year between 1900 and the current year, and a result limit of 1–20 (default 10).

Python searches the public Crossref and arXiv endpoints concurrently, with a 15-second timeout per request. No new dependency, API key, paid inference or LLM generation is required. Public scholarly services can impose rate limits or availability restrictions. The shared research/debate `search_papers` tool now reuses this same service.

Crossref candidates are restricted to journal and proceedings articles; books, chapters and generic posted content are excluded. arXiv provides preprints, which may not have undergone peer review. Abstracts and PDFs are included only when returned by a source; no claims are inferred from titles and no paywall is bypassed. Missing abstracts are labelled in the UI.

The search retrieves up to 20 candidates from each source. Duplicate DOI or normalized-title matches are merged, combining attribution, abstracts and PDF availability. Relevance is reciprocal-rank fusion (`1 / (60 + source_rank)`) of source ordering, with deterministic ties. Rankings are neither quality scores nor calibrated relevance probabilities. Local filtering and a bounded candidate pool can omit papers: this is a discovery tool, not an exhaustive literature review or a guarantee of the globally most relevant research.

A failed source produces an explicit warning while the other source can still supply results. Successful empty searches show a helpful empty state. If both sources fail, the API returns a safe HTTP 502 and the UI offers retry. HTML/JATS metadata is converted to plain text; link schemes are constrained to HTTP(S). Links open in a separate tab; the service does not fetch arbitrary URLs or download paper bodies.

## Verification

- 39 backend tests pass, including duplicate merging/enrichment, source outages, year filtering, provider parsing, metadata cleanup, URL schemes, request validation and safe API errors.
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
