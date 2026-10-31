# ScamLens Evaluation Results

> **Important Disclaimer**: This evaluation strictly measures the deterministic URL rules, brand directory matching, and scoring engine on a benchmark of 10 real legitimate retailer URLs and 10 synthetic lookalike domains in `--no-network` mode. It reflects deterministic rule precision on synthetic cases, **not** real-world accuracy across all wild internet domains.

## Executive Summary

- **Total Benchmark Test Cases**: 20 (10 Legitimate + 10 Synthetic Lookalikes)
- **Lookalikes Caught**: 10 / 10 (100.0%)
- **Lookalike High Risk Flag Rate**: 10 / 10 (100.0%)
- **Legitimate Sites Flagged High (False Alarms)**: 0 / 10 (0.0%)
- **Lookalike Floor Enforcement**: Verified. No lookalike domain scored below Medium risk (minimum score >= 45/100).

---

## 1. Legitimate Retailer URLs (Real Domains)

All 10 legitimate brand and retailer URLs are correctly identified through `brands.json` matching. None were flagged as High risk (0 false alarms).

| Brand | Domain / URL | Risk Score | Risk Label | Status |
| :--- | :--- | :---: | :---: | :--- |
| Daraz | `https://www.daraz.pk/products/sony-wh-1000xm5-i123456.html` | 5/100 | **Low** | PASSED (Low Risk) |
| PriceOye | `https://priceoye.pk/audio/wireless-earbuds/soundpeats-engine-4` | 5/100 | **Low** | PASSED (Low Risk) |
| Telemart | `https://telemart.pk/apple-iphone-15-pro-max-256gb.html` | 5/100 | **Low** | PASSED (Low Risk) |
| HomeShopping | `https://homeshopping.pk/products/Samsung-Galaxy-S24-Ultra.html` | 5/100 | **Low** | PASSED (Low Risk) |
| Apple | `https://www.apple.com/shop/buy-iphone/iphone-15-pro` | 5/100 | **Low** | PASSED (Low Risk) |
| Samsung | `https://www.samsung.com/pk/smartphones/galaxy-s24-ultra/` | 5/100 | **Low** | PASSED (Low Risk) |
| Nike | `https://www.nike.com/t/air-jordan-1-low-mens-shoes-0zPcvV` | 5/100 | **Low** | PASSED (Low Risk) |
| Adidas | `https://www.adidas.com/us/ultraboost-light-running-shoes/GY9135.html` | 5/100 | **Low** | PASSED (Low Risk) |
| Easypaisa | `https://easypaisa.com.pk/consumer-products/` | 5/100 | **Low** | PASSED (Low Risk) |
| JazzCash | `https://jazzcash.com.pk/online-payments/` | 5/100 | **Low** | PASSED (Low Risk) |

---

## 2. Synthetic Lookalike Domains (Non-Existent / Impersonations)

All 10 synthetic lookalike domains were successfully intercepted by the lookalike detection engine and suspicious TLD heuristics, triggering strong warning signals.

| Target Brand | Lookalike URL | Risk Score | Risk Label | Signals Triggered |
| :--- | :--- | :---: | :---: | :--- |
| Daraz | `https://daraz-super-deals.xyz/sale` | 83/100 | **High** | Suspicious or Cheap TLD; Multiple Hyphens in Domain; Lookalike Domain Detected (Daraz); Domain Age Unknown via RDAP |
| PriceOye | `https://priceoye-clearance-sale.shop/phones` | 83/100 | **High** | Suspicious or Cheap TLD; Multiple Hyphens in Domain; Lookalike Domain Detected (PriceOye); Domain Age Unknown via RDAP |
| Telemart | `https://telemart-official-discount.top/item` | 83/100 | **High** | Suspicious or Cheap TLD; Multiple Hyphens in Domain; Lookalike Domain Detected (Telemart); Domain Age Unknown via RDAP |
| HomeShopping | `https://homeshopping-pakistan-deals.click/order` | 83/100 | **High** | Suspicious or Cheap TLD; Multiple Hyphens in Domain; Lookalike Domain Detected (HomeShopping); Domain Age Unknown via RDAP |
| Apple | `https://apple-official-store.shop/iphone15` | 83/100 | **High** | Suspicious or Cheap TLD; Multiple Hyphens in Domain; Lookalike Domain Detected (Apple); Domain Age Unknown via RDAP |
| Samsung | `https://samsung-galaxy-sale-pk.site/buy` | 83/100 | **High** | Suspicious or Cheap TLD; Multiple Hyphens in Domain; Lookalike Domain Detected (Samsung); Domain Age Unknown via RDAP |
| Nike | `https://nike-pakistan-shoes-outlet.buzz/airjordan` | 83/100 | **High** | Suspicious or Cheap TLD; Multiple Hyphens in Domain; Lookalike Domain Detected (Nike); Domain Age Unknown via RDAP |
| Adidas | `https://adidas-shoes-official.icu/ultraboost` | 83/100 | **High** | Suspicious or Cheap TLD; Multiple Hyphens in Domain; Lookalike Domain Detected (Adidas); Domain Age Unknown via RDAP |
| Easypaisa | `https://easypaisa-cash-reward.top/claim` | 83/100 | **High** | Suspicious or Cheap TLD; Multiple Hyphens in Domain; Lookalike Domain Detected (Easypaisa); Domain Age Unknown via RDAP |
| JazzCash | `https://jazzcash-bonus-lottery.monster/login` | 83/100 | **High** | Suspicious or Cheap TLD; Multiple Hyphens in Domain; Lookalike Domain Detected (JazzCash); Domain Age Unknown via RDAP |

---

## Key Observations

1. **Brand Directory Precision**:
   Well-known brands (`daraz`, `priceoye`, `telemart`, `homeshopping`, `apple`, `samsung`, `nike`, `adidas`, `easypaisa`, `jazzcash`) are checked against their official domain whitelist. When the brand name appears in an unauthorized domain (e.g. `daraz-super-deals.xyz`), it is immediately assigned a +50 weight signal.
2. **Floor Protection**:
   In `--no-network` mode (simulating offline evaluation or unreachable sites), the score floor rule ensures that any lookalike domain receives at least 45 points, preventing missing network data from falsely lowering risk.
3. **Compound Heuristics**:
   When a lookalike domain combines multiple hyphens and a low-cost TLD (`.xyz`, `.shop`, `.top`, `.click`), the combined score reaches 65-80 (High Risk), matching expectations.
