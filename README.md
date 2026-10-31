# ScamLens: Shop Check

> An intelligent, open-weight e-commerce safety evaluator. Analyzes online shop URLs, checks brand impersonation, inspects storefront policies, and suggests verified retailer alternatives.

---

## 1. What It Is & Who It Helps

Online shoppers frequently encounter sponsored ads or social media links promoting heavily discounted electronics, branded shoes, and luxury items. Many of these storefronts are fly-by-night lookalikes that collect upfront payments via bank transfers or cards without delivering goods.

**ScamLens: Shop Check** helps consumers verify online product links **before** sharing payments, OTPs, or card details. Users paste a link (and optional product name or image) to instantly receive:
- A **Risk Score (0–100)** and label (**Low**, **Medium**, or **High Risk**)
- Transparent **evidence for every warning signal** detected
- A clear **"What we could and couldn't check"** audit box
- Direct links to **trusted, verified retailers** (Daraz.pk, PriceOye.pk, Telemart.pk, HomeShopping.pk, and official brand domains) to compare real pricing and availability

> **Disclaimer**: ScamLens provides warning signs, not proof or guarantees. Never share bank OTPs or card details on unverified platforms.

---

## 2. How to Run on Windows 11

### Prerequisites
- Windows 11 (CPU-only, 16GB RAM supported)
- Python 3.10+ installed
- [Ollama](https://ollama.com/) (optional for local AI text extraction, runs at `http://localhost:11434`)
- **Network Note**: Page fetching and RDAP domain-age queries require active internet connectivity. Only the AI model (`qwen3.5:2b`) runs on-device locally via Ollama.

### Setup & Launch

1. **Clone or Navigate to the Project**:
   ```powershell
   cd c:\Users\Elitebook\Desktop\scamlens
   ```

2. **Install Runtime Dependencies**:
   ```powershell
   python -m pip install -r requirements.txt
   ```
   *(Optional dev tools like Graphify can be installed via `pip install -r requirements-dev.txt`)*

3. **Start Ollama LLM**:
   Install Ollama from [ollama.com](https://ollama.com) and pull the open-weight model:
   ```powershell
   ollama pull qwen3.5:2b
   ```
   *Tip: You can optionally set `$env:OLLAMA_CONTEXT_LENGTH = "4096"` in PowerShell for faster CPU memory allocation.*
   *Note: If Ollama is offline or uninstalled, ScamLens automatically falls back to full rule-based evaluation without crashing, updating the UI badge to "AI: unavailable".*

4. **Run the Application**:
   ```powershell
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

5. **Open in Browser**:
   Visit [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Run Automated Tests & Benchmark
```powershell
# Run full pytest suite (35 unit and integration tests)
python -m pytest -v

# Run benchmark evaluation
python eval.py
```

---

## 3. How It Works (Rules + Open-Weight Model)

ScamLens employs a layered defense architecture combining fast deterministic rules with local language model extraction:

```
[ User Link ]
      │
      ├── 1. URL Analysis (Deterministic Heuristics)
      │      ├── HTTPS vs HTTP check
      │      ├── IP address hostname detection
      │      ├── Punycode / IDN homograph checks
      │      ├── URL shortener detection (bit.ly, tinyurl, etc.)
      │      ├── Low-cost / suspicious TLD checks (.xyz, .top, .shop, etc.)
      │      ├── Excessive hyphen and digit counts
      │      ├── Whitelisted brand directory matching (brands.json)
      │      └── Social media shop identification (Instagram, FB, WhatsApp)
      │
      ├── 2. Domain Age via RDAP (rdap.org)
      │      ├── Registered < 90 days ago = High Risk (+35 pts)
      │      ├── Registered < 365 days ago = Medium (+15 pts)
      │      └── Unknown = Minor weight (+3 pts)
      │
      ├── 3. Live Page Fetcher (Server HTML, No JS Execution)
      │      ├── 8s timeout, max 5 redirects, max 1MB limit
      │      ├── Contact extraction (phone, email, physical address)
      │      ├── Policy detection (return/refund/exchange policy)
      │      └── Payment flags (Cash on Delivery vs Bank Transfer Only / Crypto / Gift Cards)
      │
      ├── 4. Open-Weight LLM Extraction (Ollama @ localhost:11434)
      │      ├── Model: qwen3.5:2b (temperature 0, max 250 tokens, thinking disabled)
      │      ├── Strips <think> reasoning blocks, enforces 25s timeout
      │      ├── Extracts claims: product name, claimed brand, official store claims
      │      └── Cross-checks claims against registered domain
      │
      ├── 5. Scoring Engine
      │      ├── Weighted sum capped at 100
      │      ├── 0-33 Low | 34-66 Medium | 67-100 High
      │      └── Lookalike floor: Lookalikes never drop below Medium (min 45 pts)
      │
      └── 6. Comparison Engine (retailers.json)
             └── Deterministic Google site-search templates (Never LLM-generated URLs)
```

---

## 4. Real Results from `results.md`

We evaluated the deterministic rules on a benchmark of 10 real legitimate retailer URLs and 10 synthetic lookalike domains:

- **Benchmark Total**: 20 test cases
- **Legitimate Retailers Flagged High (False Alarms)**: **0 / 10 (0.0%)** (all 10 scored Low Risk, 5/100)
- **Synthetic Lookalikes Intercepted**: **10 / 10 (100.0%)** (all 10 scored High Risk, 83/100)
- **Score Floor Enforcement**: Verified. No lookalike domain scored below Medium risk.

> **Important**: This evaluation uses 10 synthetic lookalike domains crafted by the team and 10 real retailer URLs to measure deterministic URL rule accuracy. It does not reflect an exhaustive in-the-wild internet sampling.

---

## 5. Model & License

- **Default Model**: `qwen3.5:2b` via Ollama at `http://localhost:11434` (configurable via `MODEL` and `BASE_URL`).
- **Model License**: Qwen series open-weight license — see the [Ollama model page](https://ollama.com/library/qwen3.5) for terms.
- **Privacy & Execution**: The model runs on-device locally via Ollama. Page fetching and RDAP require network access to inspect the target storefront.

---

## 6. How We Used Graphify

We integrated **Graphify** (`graphifyy` 0.9.99, an open-source knowledge graph tool for codebases) as a developer inspection tool. It is kept exclusively in `requirements-dev.txt` to keep the runtime lightweight.

### Commands Executed:
```powershell
# 1. Register tool capabilities
graphify install

# 2. Extract code knowledge graph (AST-only, no LLM required)
graphify update .

# 3. Query module relationships & call graphs
graphify explain "app/main.py"
graphify explain "app/scoring.py"
graphify explain "app/url_signals.py"
graphify path "app/main.py" "app/scoring.py"
```

### Real Findings & Code Improvements:
1. **Module Architecture Mapping**: Graphify confirmed that `app/main.py` is the central God Node / hub connecting all 6 core submodules (`url_signals`, `rdap_client`, `page_fetcher`, `llm_analyzer`, `scoring`, `alternatives`).
2. **Blast Radius Analysis**: Tracing dependencies of `app/scoring.py` and `app/url_signals.py` showed that changing scoring weights or lookalike detection impacts `app/main.py`, `eval.py`, `app/llm_analyzer.py`, and test suites.
3. **Dead Code Cleanup**: Graphify flagged `app/config.py` as having zero exported symbols. Inspection revealed an unused import (`from pydantic import BaseModel`). This dead import was cleanly removed while keeping all 35 tests green.
4. **Graph Artifacts**: The generated interactive graph view and report are saved under `graphify-out/`:
   - [Interactive Graph View](graphify-out/graph.html) (155 KB)
   - [Graph Summary Report](graphify-out/GRAPH_REPORT.md)

---

## 7. Original Work vs. Third-Party Libraries

### Third-Party Libraries & Runtimes:
- **FastAPI** & **Starlette**: HTTP routing, static file hosting, and ASGI framework
- **Uvicorn**: ASGI web server
- **HTTPX**: Async HTTP client for RDAP queries and web scraping
- **BeautifulSoup4**: HTML parsing and text extraction
- **OpenAI Python SDK**: Client interface for local Ollama OpenAI-compatible endpoint
- **Ollama**: Local open-weight LLM execution engine
- **Graphifyy**: Code knowledge graph analysis (developer dependency)
- **Pytest**: Unit testing framework

### Original Components Built from Scratch:
- **Lookalike & Typosquatting Detection Engine** (`app/url_signals.py`): Levenshtein distance matching against brand directories with whitelist domain resolution.
- **Deterministic URL Signal Suite** (`app/url_signals.py`): Heuristic checks for Punycode, suspicious TLDs, IP hosts, and social seller classification.
- **Domain Age Evaluator** (`app/rdap_client.py`): ISO-8601 registration parsing and age-tier weighting.
- **Safe HTML Page Analyzer** (`app/page_fetcher.py`): Regex-based contact extraction, payment risk categorizer, and JS-rendering detector.
- **LLM Extraction & Think-Block Stripper** (`app/llm_analyzer.py`): Structured JSON extraction with Ollama native `think:false` mode and official store claim mismatch detection.
- **Scoring Engine with Floor Guarantees** (`app/scoring.py`): Multi-signal weighted aggregator with lookalike floor protection.
- **Safe Comparison Link Generator** (`app/alternatives.py`): Whitelisted retailer site-search template builder.
- **Progressive Frontend Interface** (`static/`): Dark-mode responsive UI with SVG circular gauge, live audit checklist, on-page error handling, and asynchronous two-phase loading.

---

## 8. Honest Limitations

1. **Warning Signs, Not Proof**: Heuristic scores highlight risk factors (e.g. recent domain, lack of address). A legitimate startup may have a new domain, while a sophisticated fraudster could hijack an older domain.
2. **Client-Side Rendered (SPA) Storefronts**: ScamLens fetches raw server HTML without running a headless browser (for CPU speed and security). React/Vue client-only storefronts will yield "page unreadable", falling back to URL and RDAP signals without unfair penalty.
3. **RDAP Missing on National ccTLDs**: National registries like `.pk` do not publish public RDAP query endpoints; domain age for `.pk` is labeled "unknown" with minimal weight penalty.
4. **Small Model Language Limitations**: The 2B parameter model is optimized for CPU inference, but can be inconsistent and less nuanced on complex Urdu / Roman Urdu text compared to larger models.

---

## 9. License

This project is licensed under the [MIT License](LICENSE).
