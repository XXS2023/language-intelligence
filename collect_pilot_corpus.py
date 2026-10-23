#!/usr/bin/env python3
"""Project 2 pilot corpus collector.

This version is intentionally conservative and realistic.
It does not rely on DuckDuckGo search result scraping, because many target sites
block automated access. Instead, it works with a small hand-curated list of
verified, accessible URLs from official and policy sources in Chinese and English.

This is the right approach for a pilot corpus because it ensures that the first
sample is real, readable, and usable for analysis.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Sequence

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "pilot_corpus"
OUTPUT_DIR.mkdir(exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}


def today_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def normalize_space(text: str) -> str:
    return " ".join((text or "").split())


def load_manual_urls(path: str | Path) -> List[str]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    urls = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def load_url_files(paths: Sequence[str | Path]) -> List[str]:
    combined = []
    for path in paths:
        combined.extend(load_manual_urls(path))
    return combined


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    # Some Chinese government pages declare UTF-8 in the HTML but do not set the
    # HTTP charset header consistently. requests may therefore decode them as
    # Latin-1/CP1252, which creates the mojibake seen in the CSV.
    raw = response.content
    for encoding in ("utf-8", "utf-8-sig", "gbk", "gb2312", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return response.text


def get_title_from_html(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if title:
        return title
    return url


def extract_text_from_html(html: str, language: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    # Prefer content-heavy article containers when available.
    candidate_blocks = []
    for selector in [
        "article",
        "main",
        "div.article",
        "div.article-body",
        "div.news-content",
        "div.content",
        "div.news",
        "div.text",
        "div.page_content",
        "div.detail",
        "div[id*='content']",
        "div[class*='content']",
    ]:
        for node in soup.select(selector):
            text = normalize_space(node.get_text(" ", strip=True))
            if len(text) > 120:
                candidate_blocks.append(text)

    if candidate_blocks:
        text = "\n".join(candidate_blocks[:8])
        if len(text) > 200:
            return text

    paragraphs = []
    for p in soup.find_all("p"):
        txt = normalize_space(p.get_text(" ", strip=True))
        if len(txt) > 40:
            paragraphs.append(txt)

    if paragraphs:
        return "\n".join(paragraphs[:25])

    text = normalize_space(soup.get_text(" ", strip=True))
    return text[:15000]


def build_record(url: str, language: str, source_name: str, source_type: str, query: str, sector_tag: str = "HS85") -> dict:
    html = fetch_html(url)
    title = get_title_from_html(html, url)
    text = extract_text_from_html(html, language)
    return {
        "doc_id": "",
        "language": language,
        "source_name": source_name,
        "source_type": source_type,
        "sector_tag": sector_tag,
        "country_focus": "China/EU/Poland",
        "publish_date": "",
        "title": title,
        "url": url,
        "query": query,
        "raw_text": text,
        "collection_date": today_iso(),
    }


def write_records(records: Sequence[dict], out_path: Path) -> None:
    fieldnames = [
        "doc_id",
        "language",
        "source_name",
        "source_type",
        "sector_tag",
        "country_focus",
        "publish_date",
        "title",
        "url",
        "query",
        "raw_text",
        "collection_date",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, rec in enumerate(records, 1):
            writer.writerow(
                {
                    "doc_id": f"p2_{idx:04d}",
                    "language": rec["language"],
                    "source_name": rec["source_name"],
                    "source_type": rec["source_type"],
                    "sector_tag": rec["sector_tag"],
                    "country_focus": rec["country_focus"],
                    "publish_date": rec["publish_date"],
                    "title": rec["title"],
                    "url": rec["url"],
                    "query": rec["query"],
                    "raw_text": rec["raw_text"],
                    "collection_date": rec["collection_date"],
                }
            )


def main() -> None:
    url_files = [
        ROOT / "manual_urls.txt",
        ROOT / "sector_expansion_urls.txt",
        ROOT / "phase3_targeted_urls.txt",
    ]
    manual_urls = load_url_files(url_files)
    if not manual_urls:
        raise SystemExit("No manual URLs were found. Add verified URLs to manual_urls.txt or sector_expansion_urls.txt first.")

    records: List[dict] = []
    used_urls = set()

    for url in manual_urls:
        if url in used_urls:
            continue

        # source metadata is encoded in the URL list entries as a prefix
        # Example format: language|source_name|source_type|query|url
        parts = [p.strip() for p in url.split("|")]
        if len(parts) >= 5:
            language = parts[0]
            source_name = parts[1]
            source_type = parts[2]
            query = parts[3]
            actual_url = parts[4]
        else:
            actual_url = url
            language = "en"
            source_name = "manual_source"
            source_type = "manual"
            query = "manual_url"

        try:
            record = build_record(actual_url, language, source_name, source_type, query)
            if len(record["raw_text"]) > 200:
                records.append(record)
                used_urls.add(url)
                print(f"Collected: {source_name} ({language})")
            else:
                print(f"Skipped low-text page: {actual_url}")
        except Exception as exc:
            print(f"Failed to fetch {actual_url}: {exc}")

    out_path = OUTPUT_DIR / "pilot_corpus_raw.csv"
    write_records(records, out_path)
    print(f"Saved {len(records)} records to {out_path}")


if __name__ == "__main__":
    main()
