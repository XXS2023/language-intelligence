#!/usr/bin/env python3
"""Clean and normalize the Project 2 pilot corpus.

This script reads the raw pilot CSV, removes unusable records, normalizes
metadata, standardizes language labels, and writes a cleaned version ready for
bilingual analysis.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "pilot_corpus" / "pilot_corpus_raw.csv"
OUT_PATH = ROOT / "pilot_corpus" / "pilot_corpus_clean.csv"

REQUIRED_COLUMNS = [
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


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_language(value) -> str:
    if pd.isna(value):
        return ""
    value = str(value).strip().lower()
    mapping = {
        "cn": "zh",
        "zh": "zh",
        "zh-cn": "zh",
        "chi": "zh",
        "chinese": "zh",
        "en": "en",
        "eng": "en",
        "english": "en",
    }
    return mapping.get(value, value)


def read_raw_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "cp1252"):
        try:
            return pd.read_csv(path, encoding=encoding, dtype=str, keep_default_na=False)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="utf-8", dtype=str, keep_default_na=False, engine="python")


def normalize_date(value) -> str:
    value = normalize_text(value)
    if not value:
        return ""
    return value


def dedup_key(row: pd.Series) -> str:
    url = normalize_text(row.get("url", ""))
    title = normalize_text(row.get("title", ""))
    text_prefix = normalize_text(row.get("raw_text", ""))[:150]
    if url:
        return f"url::{url}"
    if title or text_prefix:
        return f"title::{title}|{text_prefix}"
    return ""


def is_sector_relevant(row: pd.Series) -> bool:
    title = normalize_text(row.get("title", "")).lower()
    query = normalize_text(row.get("query", "")).lower()
    text = normalize_text(row.get("raw_text", "")).lower()
    combined = f"{title} {query} {text}"

    en_terms = [
        "electrical machinery", "electrical", "electronics", "machinery imports",
        "supply chain", "industrial equipment", "semiconductor", "integrated circuits",
        "components", "manufacturing", "import dependence", "trade dependence",
        "supply chain risk", "industrial policy", "critical imports", "export permit"
    ]
    zh_terms = [
        "电气设备", "电子元器件", "机械设备", "供应链", "工业设备", "半导体",
        "集成电路", "组件", "制造业", "进口依赖", "贸易风险", "产业政策",
        "关键进口", "出口许可", "汽车出口", "摩托车"
    ]
    return any(term in combined for term in en_terms + zh_terms)


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw corpus not found: {RAW_PATH}")

    df = read_raw_csv(RAW_PATH)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    clean_df = df.copy()
    clean_df["language"] = clean_df["language"].apply(normalize_language)
    clean_df["source_name"] = clean_df["source_name"].apply(normalize_text)
    clean_df["source_type"] = clean_df["source_type"].apply(normalize_text)
    clean_df["sector_tag"] = clean_df["sector_tag"].apply(normalize_text)
    clean_df["country_focus"] = clean_df["country_focus"].apply(normalize_text)
    clean_df["publish_date"] = clean_df["publish_date"].apply(normalize_date)
    clean_df["title"] = clean_df["title"].apply(normalize_text)
    clean_df["url"] = clean_df["url"].apply(normalize_text)
    clean_df["query"] = clean_df["query"].apply(normalize_text)
    clean_df["raw_text"] = clean_df["raw_text"].apply(normalize_text)
    clean_df["collection_date"] = clean_df["collection_date"].apply(normalize_date)

    # Keep high-quality records only.
    clean_df = clean_df[clean_df["language"].isin(["en", "zh"])].copy()
    clean_df = clean_df[clean_df["title"].str.len() > 4].copy()
    clean_df = clean_df[clean_df["raw_text"].str.len() >= 200].copy()
    clean_df = clean_df[clean_df.apply(is_sector_relevant, axis=1)].copy()

    clean_df["dup_key"] = clean_df.apply(dedup_key, axis=1)
    clean_df = clean_df.drop_duplicates(subset="dup_key", keep="first").copy()
    clean_df = clean_df.drop(columns=["dup_key"])

    # Rebuild doc_id in stable sequential format.
    clean_df = clean_df.reset_index(drop=True)
    clean_df["doc_id"] = [f"p2_{idx:04d}" for idx in range(1, len(clean_df) + 1)]

    # Keep output columns in a predictable order.
    output_columns = REQUIRED_COLUMNS
    clean_df = clean_df[output_columns]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Raw rows: {len(df)}")
    print(f"Clean rows: {len(clean_df)}")
    print(f"Saved to: {OUT_PATH}")
    print(clean_df["language"].value_counts().to_dict())


if __name__ == "__main__":
    main()
