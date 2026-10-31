# Graph Report - scamlens  (2026-10-31)

## Corpus Check
- 20 files · ~12,201 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .css 1)

## Summary
- 161 nodes · 316 edges · 11 communities (9 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `48adb91c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.py
- analyze_url_signals
- llm_analyzer.py
- test_page_fetcher.py
- calculate_risk_score
- ScamLens: Shop Check
- build_comparison_links
- app.js
- ScamLens Evaluation Results
- check_endpoint

## God Nodes (most connected - your core abstractions)
1. `analyze_url_signals()` - 25 edges
2. `calculate_risk_score()` - 14 edges
3. `build_comparison_links()` - 13 edges
4. `analyze_with_llm()` - 12 edges
5. `check_endpoint()` - 12 edges
6. `fetch_and_parse_page()` - 12 edges
7. `check_domain_age_rdap()` - 12 edges
8. `ScamLens: Shop Check` - 10 edges
9. `extract_json_from_llm()` - 9 edges
10. `check_official_store_claim_mismatch()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `test_clean_query_term()` --calls--> `clean_query_term()`  [EXTRACTED]
  tests/test_alternatives.py → app/alternatives.py
- `test_all_links_from_templates_and_google_site_search()` --calls--> `build_comparison_links()`  [EXTRACTED]
  tests/test_alternatives.py → app/alternatives.py
- `test_query_priority()` --calls--> `build_comparison_links()`  [EXTRACTED]
  tests/test_alternatives.py → app/alternatives.py
- `test_clean_think_blocks()` --calls--> `clean_think_blocks()`  [EXTRACTED]
  tests/test_llm_analyzer.py → app/llm_analyzer.py
- `test_extract_json_from_llm()` --calls--> `extract_json_from_llm()`  [EXTRACTED]
  tests/test_llm_analyzer.py → app/llm_analyzer.py

## Import Cycles
- None detected.

## Communities (11 total, 2 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.12
Nodes (9): AICheckRequest, api_check_ai(), api_check_quick(), api_status(), CheckRequest, execute_quick_check(), get_brands(), health_check() (+1 more)

### Community 1 - "analyze_url_signals"
Cohesion: 0.16
Nodes (17): analyze_url_signals(), extract_domain_parts(), levenshtein_distance(), load_brands(), normalize_url(), Signal, test_excessive_hyphens_and_digits(), test_insecure_http_signal() (+9 more)

### Community 2 - "llm_analyzer.py"
Cohesion: 0.18
Nodes (9): analyze_with_llm(), check_official_store_claim_mismatch(), clean_think_blocks(), extract_json_from_llm(), test_analyze_with_llm_model_offline_fallback(), test_analyze_with_llm_native_success(), test_clean_think_blocks(), test_extract_json_from_llm() (+1 more)

### Community 3 - "test_page_fetcher.py"
Cohesion: 0.21
Nodes (8): fetch_and_parse_page(), check_domain_age_rdap(), test_page_fetch_and_parse_success(), test_page_fetch_js_rendered_fallback(), test_page_fetch_suspicious_payment(), test_rdap_known_domain(), test_rdap_not_found(), test_rdap_recent_domain()

### Community 4 - "calculate_risk_score"
Cohesion: 0.17
Nodes (9): calculate_risk_score(), evaluate_set(), run_evaluation(), write_results_file(), test_disclaimer_present_and_no_probability_word(), test_high_risk_compound_scam(), test_lookalike_floor_never_below_medium(), test_official_brand_scores_low() (+1 more)

### Community 5 - "ScamLens: Shop Check"
Cohesion: 0.12
Nodes (15): 1. What It Is & Who It Helps, 2. How to Run on Windows 11, 3. How It Works (Rules + Open-Weight Model), 4. Real Results from `results.md`, 5. Model & License, 6. Original Work vs. Third-Party Libraries, 7. Honest Limitations, 8. What We Learned (+7 more)

### Community 6 - "build_comparison_links"
Cohesion: 0.31
Nodes (7): build_comparison_links(), clean_query_term(), load_brands(), load_retailers(), test_all_links_from_templates_and_google_site_search(), test_clean_query_term(), test_query_priority()

### Community 8 - "app.js"
Cohesion: 0.48
Nodes (5): renderAlternatives(), renderAuditChecks(), renderQuickResults(), renderSignals(), updateGauge()

### Community 9 - "ScamLens Evaluation Results"
Cohesion: 0.33
Nodes (5): 1. Legitimate Retailer URLs (Real Domains), 2. Synthetic Lookalike Domains (Non-Existent / Impersonations), Executive Summary, Key Observations, ScamLens Evaluation Results

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `analyze_url_signals()` connect `analyze_url_signals` to `main.py`, `check_endpoint`, `test_page_fetcher.py`, `calculate_risk_score`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12318840579710146 - nodes in this community are weakly interconnected._
- **Why does `calculate_risk_score()` connect `calculate_risk_score` to `main.py`, `check_endpoint`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Should `ScamLens: Shop Check` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._
- **Why does `check_endpoint()` connect `check_endpoint` to `main.py`, `analyze_url_signals`, `llm_analyzer.py`, `test_page_fetcher.py`, `calculate_risk_score`, `build_comparison_links`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._