#!/usr/bin/env python3
"""Pilot analysis modules A/B/C for Project 2.

Modules:
A. Frequency & keyness
B. Collocations
C. Framing dictionary

The analysis is designed for a small pilot corpus and uses a curated phrase bank
aligned with the project blueprint, so it remains informative even when the
corpus is modest in size.
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
FINAL_DATA_PATH = ROOT / "final_balanced_corpus" / "final_balanced_corpus.csv"
DATA_PATH = ROOT / "pilot_corpus" / "pilot_corpus_clean.csv"
OUT_DIR = ROOT / "pilot_analysis_outputs"
OUT_DIR.mkdir(exist_ok=True)

EN_STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "that", "this", "have",
    "will", "been", "were", "their", "there", "about", "through", "which",
    "over", "under", "after", "before", "more", "than", "both", "such", "used",
    "what", "when", "where", "while", "among", "within", "without", "could",
    "should", "would", "must", "may", "also", "not", "other", "same", "these",
    "those", "its", "their", "during", "between", "across", "year", "years",
    "including", "based", "according", "point", "due", "either", "still", "made",
    "many", "some", "part", "about", "related", "country", "countries", "region",
    "regions", "market", "markets", "industry", "industries", "policy", "policies"
}

EN_KEYWORD_LIST = [
    "supply chain", "import dependence", "industrial policy", "import exposure",
    "trade disruption", "supply chain risk", "supply chain resilience",
    "diversification", "critical imports", "source concentration", "strategic dependence",
    "geopolitical risk", "trade tension", "industrial security", "market access",
    "trade cooperation", "supply stability", "dependency", "risk", "security",
    "resilience", "stability", "disruption", "investment", "partnership",
    "reliance on china", "electrical machinery", "electronics manufacturing",
    "semiconductors", "integrated circuits", "industrial equipment", "power equipment",
    "machinery imports", "trade dependence", "supply shortages", "policy intervention",
    "growth opportunity", "investment opportunities", "supply chain resilience"
]

ZH_KEYWORD_LIST = [
    "供应链", "进口依赖", "产业政策", "进口结构", "贸易风险", "供应链风险",
    "供应链韧性", "多元化", "关键进口", "供给集中", "战略依赖", "地缘政治风险",
    "贸易摩擦", "产业安全", "市场准入", "贸易合作", "供应稳定", "风险", "安全",
    "韧性", "稳定", "中断", "投资", "合作", "电气设备", "电子元器件", "半导体",
    "集成电路", "工业设备", "电力设备", "机械设备", "进口依赖", "产业链依赖",
    "政策干预", "增长机会", "投资机会", "供应短缺"
]

FRAME_GROUPS = {
    "risk": {
        "en": ["risk", "security", "resilience", "disruption", "shortages", "vulnerability", "geopolitical risk", "supply shortages", "trade disruption", "trade tension"],
        "zh": ["风险", "安全", "韧性", "中断", "短缺", "脆弱性", "地缘政治风险", "供应短缺", "贸易风险", "贸易摩擦"],
    },
    "policy": {
        "en": ["industrial policy", "policy intervention", "trade cooperation", "market access", "import dependence", "strategic dependence", "diversification"],
        "zh": ["产业政策", "政策干预", "贸易合作", "市场准入", "进口依赖", "战略依赖", "多元化"],
    },
    "supply_chain": {
        "en": ["supply chain", "supply chain risk", "supply chain resilience", "supplier diversification", "source concentration", "critical imports"],
        "zh": ["供应链", "供应链风险", "供应链韧性", "供应商多元化", "供给集中", "关键进口"],
    },
    "cooperation": {
        "en": ["cooperation", "partnership", "investment", "market access", "trade cooperation", "stable trade", "growth opportunity"],
        "zh": ["合作", "伙伴关系", "投资", "市场准入", "贸易合作", "稳定贸易", "增长机会"],
    },
    "technology": {
        "en": ["electrical machinery", "electronics manufacturing", "semiconductors", "integrated circuits", "industrial equipment", "power equipment", "machinery imports"],
        "zh": ["电气设备", "电子制造", "半导体", "集成电路", "工业设备", "电力设备", "机械设备"],
    },
}


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def tokenize_en(text: str):
    text = text.lower()
    tokens = re.findall(r"[a-z]+(?:-[a-z]+)?", text)
    return [t for t in tokens if t not in EN_STOPWORDS and len(t) > 1]


def tokenize_zh(text: str):
    # Chinese tokenizer for this pilot: segment by Chinese character sequences.
    chunks = re.findall(r"[\u4e00-\u9fff]+", text)
    return [chunk for chunk in chunks if len(chunk) > 1]


def count_phrase_occurrences(text: str, phrase: str, language: str):
    normalized = text.lower() if language == "en" else text
    phrase_norm = phrase.lower() if language == "en" else phrase
    return normalized.count(phrase_norm)


def compute_frequency_keyness(df: pd.DataFrame):
    result = []
    for lang in ["en", "zh"]:
        subset = df[df["language"] == lang].copy()
        all_tokens = []
        for text in subset["raw_text"]:
            if lang == "en":
                all_tokens.extend(tokenize_en(text))
            else:
                all_tokens.extend(tokenize_zh(text))

        if not all_tokens:
            continue

        counts = Counter(all_tokens)
        total_tokens = sum(counts.values())
        top_terms = []
        for term, count in counts.most_common(20):
            if count < 2:
                continue
            rf = (count / total_tokens) * 1000
            top_terms.append({
                "language": lang,
                "term": term,
                "count": count,
                "freq_per_1000_tokens": round(rf, 3),
            })
        result.extend(top_terms)

    # Also add dictionary-based phrase counts for aligned with blueprint
    for lang in ["en", "zh"]:
        keyword_list = EN_KEYWORD_LIST if lang == "en" else ZH_KEYWORD_LIST
        subset = df[df["language"] == lang]
        phrase_counts = Counter()
        for text in subset["raw_text"]:
            for phrase in keyword_list:
                count = count_phrase_occurrences(text, phrase, lang)
                phrase_counts[phrase] += count
        for phrase, count in phrase_counts.most_common(20):
            if count <= 0:
                continue
            result.append({
                "language": lang,
                "term": phrase,
                "count": count,
                "freq_per_1000_tokens": round((count / max(1, subset["raw_text"].str.len().sum() / 1000)) * 1, 3),
                "source": "keyword_bank",
            })

    return pd.DataFrame(result)


def compute_collocations(df: pd.DataFrame):
    rows = []
    for lang in ["en", "zh"]:
        phrase_list = EN_KEYWORD_LIST if lang == "en" else ZH_KEYWORD_LIST
        subset = df[df["language"] == lang]
        all_counts = Counter()
        for text in subset["raw_text"]:
            for phrase in phrase_list:
                ph_count = count_phrase_occurrences(text, phrase, lang)
                if ph_count:
                    all_counts[phrase] += ph_count
        for phrase, count in all_counts.most_common(20):
            rows.append({
                "language": lang,
                "collocation": phrase,
                "count": count,
                "relative_strength": round(count / max(1, len(subset)), 3),
            })
    return pd.DataFrame(rows)


def compute_framing_scores(df: pd.DataFrame):
    frames = []
    for lang in ["en", "zh"]:
        subset = df[df["language"] == lang]
        for frame_name, terms in FRAME_GROUPS.items():
            phrase_list = terms[lang]
            total = 0
            for text in subset["raw_text"]:
                for phrase in phrase_list:
                    total += count_phrase_occurrences(text, phrase, lang)
            frames.append({
                "language": lang,
                "frame": frame_name,
                "count": total,
                "per_document": round(total / max(1, len(subset)), 3),
            })
    return pd.DataFrame(frames)


def build_report(df: pd.DataFrame):
    freq_df = compute_frequency_keyness(df)
    coll_df = compute_collocations(df)
    frame_df = compute_framing_scores(df)

    key_points = []
    for lang in ["en", "zh"]:
        top = freq_df[freq_df["language"] == lang].sort_values(["count", "freq_per_1000_tokens"], ascending=False).head(8)
        key_points.append(f"{lang.upper()} top terms: {', '.join(top['term'].tolist()[:5])}")

    top_coll = coll_df.sort_values(["language", "count"], ascending=[True, False])
    key_points.append(f"Highest collocation overall: {top_coll.iloc[0]['collocation']} ({top_coll.iloc[0]['count']} matches)")

    report = "\n".join([
        "Project 2 pilot analysis report",
        "==============================",
        "",
        *key_points,
        "",
        "Module A: top frequency/keyness terms",
        "-----------------------------------",
        str(freq_df.sort_values(["language", "count"], ascending=[True, False]).head(20).to_string(index=False)),
        "",
        "Module B: collocations", 
        "---------------------",
        str(coll_df.sort_values(["language", "count"], ascending=[True, False]).head(20).to_string(index=False)),
        "",
        "Module C: framing dictionary",
        "---------------------------",
        str(frame_df.sort_values(["language", "count"], ascending=[True, False]).to_string(index=False)),
    ])

    report_path = OUT_DIR / "pilot_analysis_report.txt"
    report_path.write_text(report, encoding="utf-8")

    freq_df.to_csv(OUT_DIR / "module_a_frequency_keyness.csv", index=False, encoding="utf-8-sig")
    coll_df.to_csv(OUT_DIR / "module_b_collocations.csv", index=False, encoding="utf-8-sig")
    frame_df.to_csv(OUT_DIR / "module_c_framing_dictionary.csv", index=False, encoding="utf-8-sig")

    print(report_path)
    print(f"Rows in frequency/keyness: {len(freq_df)}")
    print(f"Rows in collocations: {len(coll_df)}")
    print(f"Rows in framing: {len(frame_df)}")


def main():
    data_path = FINAL_DATA_PATH if FINAL_DATA_PATH.exists() else DATA_PATH
    if not data_path.exists():
        raise FileNotFoundError(f"Clean corpus not found: {data_path}")

    df = pd.read_csv(data_path, encoding="utf-8-sig", dtype=str)
    df["raw_text"] = df["raw_text"].fillna("").map(normalize_text)
    df["language"] = df["language"].fillna("").str.lower().str.strip()
    df["language"] = df["language"].replace({"cn": "zh"})
    df = df[df["language"].isin(["en", "zh"])].copy()

    if len(df) < 10:
        print("Pilot corpus is small; continuing with a pilot-level analysis, but results should be treated as indicative rather than final.")
    else:
        print(f"Running full analysis on balanced corpus: {len(df)} rows")

    build_report(df)


if __name__ == "__main__":
    main()
