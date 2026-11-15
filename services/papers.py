"""Scholarly search with source attribution and reciprocal-rank fusion."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from urllib.parse import quote, urlsplit
import re

import requests
from bs4 import BeautifulSoup
from defusedxml import ElementTree

HEADERS = {"User-Agent": "SophiaNet/1.0 (educational paper discovery)"}


def plain(value):
    return BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)


def safe_url(value):
    if not value:
        return None
    parts = urlsplit(value)
    return value if parts.scheme in {"https", "http"} and parts.hostname and not parts.username and not parts.password else None


def crossref(query, since):
    params = {"query.bibliographic": query, "rows": 20, "sort": "relevance"}
    if since:
        params["filter"] = f"from-pub-date:{since}-01-01"
    response = requests.get("https://api.crossref.org/works", params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()
    papers = []
    for item in response.json()["message"]["items"]:
        if item.get("type") not in {"journal-article", "proceedings-article", "posted-content"}:
            continue
        title = plain((item.get("title") or [""])[0])
        doi = item.get("DOI", "").strip().lower()
        if not title or not doi:
            continue
        years = item.get("published", item.get("issued", {})).get("date-parts", [[]])
        papers.append({"title": title, "doi": doi, "year": years[0][0] if years and years[0] else None,
                       "authors": [" ".join(filter(None, [a.get("given"), a.get("family")])) for a in item.get("author", [])][:20],
                       "abstract": plain(item.get("abstract"))[:5000], "url": "https://doi.org/" + quote(doi, safe="/"),
                       "pdf_url": None, "venue": plain((item.get("container-title") or [""])[0])})
    return papers


def arxiv(query, since):
    # Quote the whole user query so API search operators cannot replace our filters.
    terms = 'all:"' + query.replace('"', ' ') + '"'
    if since:
        terms += f" AND submittedDate:[{since}01010000 TO {date.today().year}12312359]"
    response = requests.get("https://export.arxiv.org/api/query", params={"search_query": terms, "max_results": 20, "sortBy": "relevance"}, headers=HEADERS, timeout=15)
    response.raise_for_status()
    root = ElementTree.fromstring(response.content)
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    papers = []
    for entry in root.findall("a:entry", ns):
        url = safe_url(entry.findtext("a:id", "", ns))
        title = " ".join(entry.findtext("a:title", "", ns).split())
        if not url or not title:
            continue
        if 'arxiv.org/api/errors' in url:
            raise ValueError("arXiv query rejected")
        published = entry.findtext("a:published", "", ns)
        pdf = next((safe_url(link.get("href")) for link in entry.findall("a:link", ns) if link.get("title") == "pdf"), None)
        papers.append({"title": title, "doi": entry.findtext("arxiv:doi", "", ns).strip().lower() or None,
                       "authors": [a.findtext("a:name", "", ns) for a in entry.findall("a:author", ns)][:20],
                       "year": int(published[:4]) if published[:4].isdigit() else None,
                       "abstract": " ".join(entry.findtext("a:summary", "", ns).split())[:5000],
                       "url": url.replace('http://', 'https://', 1), "pdf_url": pdf.replace('http://', 'https://', 1) if pdf else None,
                       "venue": entry.findtext("arxiv:journal_ref", "arXiv preprint", ns)})
    return papers


def search_papers(query, since=None, limit=10):
    results, warnings = {}, []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(provider, query, since): name for name, provider in (("Crossref", crossref), ("arXiv", arxiv))}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception:
                warnings.append(f"{name} is unavailable. Results may be incomplete.")
    if not results:
        raise RuntimeError("All scholarly sources are unavailable")
    merged, identities = [], {}
    # Fixed provider order makes ties deterministic, regardless of request completion order.
    for source in ("Crossref", "arXiv"):
        seen = set()
        for rank, paper in enumerate(results.get(source, []), 1):
            if since and (not paper["year"] or paper["year"] < since):
                continue
            keys = ["title:" + re.sub(r"\W+", "", paper["title"].casefold())]
            if paper["doi"]:
                keys.insert(0, "doi:" + paper["doi"].lower())
            index = next((identities[key] for key in keys if key in identities), None)
            if index is None:
                index = len(merged)
                merged.append({**paper, "sources": [], "score": 0.0})
            item = merged[index]
            for key in keys:
                identities[key] = index
            if index in seen:
                continue
            seen.add(index)
            item["score"] += 1 / (60 + rank)
            item["sources"].append(source)
            for key in ("abstract", "pdf_url", "doi"):
                if not item[key] and paper[key]:
                    item[key] = paper[key]
    papers = sorted(merged, key=lambda item: -item["score"])[:limit]
    for rank, paper in enumerate(papers, 1):
        paper["rank"] = rank
        del paper["score"]
    return {"query": query, "papers": papers, "warnings": sorted(warnings), "sources_searched": sorted(results),
            "ranking": "Reciprocal-rank fusion of up to 20 results per source; ranking is not a quality or correctness score."}
