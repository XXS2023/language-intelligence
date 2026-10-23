# Bilingual Language Intelligence: Chinese vs English Market Narratives

This repository contains a corpus-based portfolio project comparing how Chinese and English sources describe the same industrial and trade developments.

## Project focus

- Topic: China-related industrial policy, trade exposure, semiconductors, electronics, and supply-chain resilience
- Method: bilingual corpus collection, cleaning, and comparative linguistic analysis
- Goal: identify cross-lingual framing differences in risk, cooperation, policy, technology, and supply-chain narratives

## Repository structure

- `collect_pilot_corpus.py` - collection script for pilot corpus
- `clean_pilot_corpus.py` - cleaning and normalization pipeline
- `pilot_analysis_modules.py` - analysis modules A/B/C
- `final_balanced_corpus.py` - balanced bilingual corpus build script
- `final_balanced_sources.txt` - curated final source list
- `pilot_corpus/` - raw and cleaned pilot corpus CSV files
- `final_balanced_corpus/` - final balanced corpus output
- `pilot_analysis_outputs/` - frequency/keyness, collocations, framing outputs
- `final_bilingual_comparison_report.md` - polished narrative report

## Main outputs

- Frequency/keyness:
  - `pilot_analysis_outputs/module_a_frequency_keyness.csv`
- Collocations:
  - `pilot_analysis_outputs/module_b_collocations.csv`
- Framing dictionary:
  - `pilot_analysis_outputs/module_c_framing_dictionary.csv`
- Combined analysis summary:
  - `pilot_analysis_outputs/pilot_analysis_report.txt`

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 pilot_analysis_modules.py
```

## Portfolio value

This project demonstrates an end-to-end language-intelligence workflow:
source curation -> corpus construction -> cleaning -> bilingual comparative analysis -> narrative interpretation.

## License

See `LICENSE.txt` (CC BY-NC 4.0).
