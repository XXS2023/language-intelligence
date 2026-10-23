#!/usr/bin/env python3
"""Build the final balanced bilingual corpus for Project 2.

This stage is deliberately more realistic and balanced than the pilot:
- curated sources from Chinese and English official / policy / business pages
- no dependency on blocked media scraping
a- targets a more even Chinese/English distribution
- writes a corpus ready for final bilingual analysis
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "final_balanced_sources.txt"
OUT_DIR = ROOT / "final_balanced_corpus"
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / "final_balanced_corpus.csv"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}


def normalize_space(text: str) -> str:
    return " ".join((text or "").split())


def today_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def load_sources(path: Path) -> list[str]:
    if not path.exists():
        return []
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                items.append(line)
    return items


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    raw = response.content
    for encoding in ("utf-8", "utf-8-sig", "gbk", "gb2312", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return response.text


def extract_title(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if title:
        return title
    return url


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    candidates = []
    for selector in [
        "article", "main", "div.article", "div.article-body", "div.news-content",
        "div.content", "div.page_content", "div.detail", "section", "div.text",
        "div[id*='content']", "div[class*='content']", "div[class*='body']"
    ]:
        for node in soup.select(selector):
            text = normalize_space(node.get_text(" ", strip=True))
            if len(text) > 120:
                candidates.append(text)
    if candidates:
        combined = "\n".join(candidates[:10])
        if len(combined) > 200:
            return combined

    paragraphs = []
    for p in soup.find_all("p"):
        text = normalize_space(p.get_text(" ", strip=True))
        if len(text) > 40:
            paragraphs.append(text)
    if paragraphs:
        return "\n".join(paragraphs[:25])

    body = normalize_space(soup.get_text(" ", strip=True))
    return body[:20000]


def parse_source_entry(entry: str):
    parts = [p.strip() for p in entry.split("|")]
    if len(parts) >= 5:
        return {
            "language": parts[0],
            "source_name": parts[1],
            "source_type": parts[2],
            "query": parts[3],
            "url": parts[4],
        }
    return None


def write_csv(rows: list[dict], out_path: Path):
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

    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, row in enumerate(rows, 1):
            writer.writerow(
                {
                    "doc_id": f"final_{idx:04d}",
                    "language": row["language"],
                    "source_name": row["source_name"],
                    "source_type": row["source_type"],
                    "sector_tag": row["sector_tag"],
                    "country_focus": row["country_focus"],
                    "publish_date": row["publish_date"],
                    "title": row["title"],
                    "url": row["url"],
                    "query": row["query"],
                    "raw_text": row["raw_text"],
                    "collection_date": row["collection_date"],
                }
            )


def main() -> None:
    entries = [parse_source_entry(e) for e in load_sources(SOURCE_PATH)]
    entries = [e for e in entries if e]
    if not entries:
        raise SystemExit(f"No source entries found in {SOURCE_PATH}")

    rows = []
    seen_urls = set()
    for entry in entries:
        url = entry["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        try:
            html = fetch_html(url)
            title = extract_title(html, url)
            text = extract_text(html)
            if len(text) < 200:
                print(f"Skipping low-text page: {url}")
                continue
            rows.append(
                {
                    "language": entry["language"],
                    "source_name": entry["source_name"],
                    "source_type": entry["source_type"],
                    "sector_tag": "HS85",
                    "country_focus": "China/EU/Poland",
                    "publish_date": "",
                    "title": title,
                    "url": url,
                    "query": entry["query"],
                    "raw_text": text,
                    "collection_date": today_iso(),
                }
            )
            print(f"Collected: {entry['source_name']} ({entry['language']})")
        except Exception as exc:
            print(f"Failed to fetch {url}: {exc}")

    write_csv(rows, OUT_PATH)
    print(f"Saved {len(rows)} final balanced-corpus rows to {OUT_PATH}")
    print(f"English rows: {sum(1 for r in rows if r['language'] == 'en')}")
    print(f"Chinese rows: {sum(1 for r in rows if r['language'] == 'cn')}")


if __name__ == "__main__":
    main()
