document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("checkForm");
  const urlInput = document.getElementById("urlInput");
  const productNameInput = document.getElementById("productNameInput");
  const imageInput = document.getElementById("imageInput");
  const submitBtn = document.getElementById("submitBtn");
  const btnText = submitBtn.querySelector(".btn-text");

  // Image preview elements
  const imagePreviewContainer = document.getElementById("imagePreviewContainer");
  const imagePreviewImg = document.getElementById("imagePreviewImg");
  const imageFileName = document.getElementById("imageFileName");
  const removeImageBtn = document.getElementById("removeImageBtn");

  // Results elements
  const resultsSection = document.getElementById("resultsSection");
  const displayDomain = document.getElementById("displayDomain");
  const scoreNumber = document.getElementById("scoreNumber");
  const gaugeBar = document.getElementById("gaugeBar");
  const riskBadge = document.getElementById("riskBadge");
  const disclaimerLine = document.getElementById("disclaimerLine");
  const aiSummaryText = document.getElementById("aiSummaryText");
  const aiStatusBadge = document.getElementById("aiStatusBadge");
  const aiBullets = document.getElementById("aiBullets");
  const auditGrid = document.getElementById("auditGrid");
  const signalsList = document.getElementById("signalsList");
  const signalCount = document.getElementById("signalCount");
  const displayQuery = document.getElementById("displayQuery");
  const compareGrid = document.getElementById("compareGrid");
  const copySummaryBtn = document.getElementById("copySummaryBtn");
  const toast = document.getElementById("toast");

  let currentResultData = null;

  // Handle image upload preview
  imageInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        imagePreviewImg.src = event.target.result;
        imageFileName.textContent = file.name;
        imagePreviewContainer.classList.remove("hidden");
      };
      reader.readAsDataURL(file);
    }
  });

  removeImageBtn.addEventListener("click", () => {
    imageInput.value = "";
    imagePreviewImg.src = "";
    imageFileName.textContent = "";
    imagePreviewContainer.classList.add("hidden");
  });

  // Handle sample buttons
  document.querySelectorAll(".btn-sample").forEach((btn) => {
    btn.addEventListener("click", () => {
      urlInput.value = btn.dataset.url || "";
      productNameInput.value = btn.dataset.name || "";
      form.dispatchEvent(new Event("submit"));
    });
  });

  // Toast notification
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.remove("hidden");
    setTimeout(() => {
      toast.classList.add("hidden");
    }, 3000);
  }

  // Update circular gauge
  function updateGauge(score, color) {
    const circumference = 2 * Math.PI * 68; // ~427
    const offset = circumference - (score / 100) * circumference;
    gaugeBar.style.strokeDashoffset = offset;
    gaugeBar.style.stroke = color;
    scoreNumber.textContent = score;
    scoreNumber.style.color = color;
  }

  // Render quick results
  function renderQuickResults(data) {
    currentResultData = data;
    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

    const scoreData = data.score_data;
    displayDomain.textContent = data.hostname || "Storefront";

    // Gauge & Score
    updateGauge(scoreData.score, scoreData.color);

    // Risk Badge
    riskBadge.textContent = scoreData.label_text;
    riskBadge.className = `risk-badge ${scoreData.label.toLowerCase()}`;

    // Disclaimer
    disclaimerLine.textContent = scoreData.disclaimer || "Warning signs, not proof. Never share OTPs or card details.";

    // Render Audit Checklist
    renderAuditChecks(scoreData.audit_checks || []);

    // Render Signals
    renderSignals(scoreData.signals || []);

    // Render Alternatives
    renderAlternatives(data.alternatives);

    // Initial AI status
    aiStatusBadge.textContent = "Analyzing...";
    aiSummaryText.textContent = "Extracting page claims and checking seller reputation with AI model...";
    aiBullets.innerHTML = "";
  }

  function renderAuditChecks(checks) {
    auditGrid.innerHTML = "";
    checks.forEach((item) => {
      const el = document.createElement("div");
      el.className = "audit-item";
      const iconClass = item.checked ? (item.success ? "success" : "fail") : "info";
      const iconSym = item.checked ? (item.success ? "✓" : "!") : "—";
      el.innerHTML = `
        <div class="audit-item-header">
          <span class="audit-icon ${iconClass}">${iconSym}</span>
          <span class="audit-name">${item.name}</span>
        </div>
        <div class="audit-desc">${item.status}</div>
      `;
      auditGrid.appendChild(el);
    });
  }

  function renderSignals(signals) {
    signalsList.innerHTML = "";
    signalCount.textContent = `${signals.length} signal${signals.length === 1 ? "" : "s"}`;

    signals.forEach((sig) => {
      const el = document.createElement("div");
      const sev = (sig.severity || "info").toLowerCase();
      el.className = `signal-item severity-${sev}`;

      const weight = sig.score_weight || 0;
      let weightText = "";
      let weightClass = "";
      if (sig.is_risk && weight > 0) {
        weightText = `+${weight} pts`;
        weightClass = "risk";
      } else if (!sig.is_risk && weight < 0) {
        weightText = `${weight} pts`;
        weightClass = "trust";
      }

      el.innerHTML = `
        <div class="signal-content">
          <div class="signal-title-row">
            <span class="signal-title">${sig.title}</span>
            <span class="signal-badge ${sev}">${sig.severity || 'info'}</span>
          </div>
          <div class="signal-evidence">${sig.evidence}</div>
        </div>
        ${weightText ? `<span class="signal-points ${weightClass}">${weightText}</span>` : ""}
      `;
      signalsList.appendChild(el);
    });
  }

  function renderAlternatives(alternatives) {
    if (!alternatives) return;
    displayQuery.textContent = alternatives.search_query || "product";
    compareGrid.innerHTML = "";

    const links = alternatives.links || [];
    links.forEach((link) => {
      const a = document.createElement("a");
      a.href = link.search_url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.className = `compare-btn ${link.is_brand_official ? "official-brand" : ""}`;

      a.innerHTML = `
        <div class="compare-retailer-name">
          <span>${link.retailer}</span>
          <span class="compare-retailer-dom">${link.domain}</span>
        </div>
        <svg class="compare-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
          <polyline points="15 3 21 3 21 9"/>
          <line x1="10" y1="14" x2="21" y2="3"/>
        </svg>
      `;
      compareGrid.appendChild(a);
    });
  }

  // Handle Form Submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = urlInput.value.trim();
    if (!url) return;

    const productName = productNameInput.value.trim();

    // Loading state
    submitBtn.disabled = true;
    btnText.textContent = "Checking URL & Page...";

    try {
      // Step 1: Immediate quick check (Rules + RDAP + Page Fetch)
      const quickResp = await fetch("/api/check-quick", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url, product_name: productName })
      });

      if (!quickResp.ok) {
        const err = await quickResp.json();
        alert(err.detail || "Failed to analyze link");
        submitBtn.disabled = false;
        btnText.textContent = "Check Store Safety";
        return;
      }

      const quickData = await quickResp.json();
      renderQuickResults(quickData);

      // Restore submit button immediately so user isn't stuck
      submitBtn.disabled = false;
      btnText.textContent = "Check Another Store";

      // Step 2: Background AI analysis via Ollama
      fetch("/api/check-ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: quickData.url,
          hostname: quickData.hostname,
          title: quickData.page_analysis.title || "",
          visible_text: quickData.page_analysis.visible_text || "",
          product_name: quickData.product_name,
          brand_key: quickData.url_analysis.matched_brand
        })
      })
      .then((res) => res.json())
      .then((aiData) => {
        const llm = aiData.llm_analysis;
        if (llm.ai_available) {
          aiStatusBadge.textContent = llm.elapsed_seconds ? `Complete (${llm.elapsed_seconds}s)` : "Complete";
          aiStatusBadge.style.background = "rgba(16, 185, 129, 0.2)";
          aiStatusBadge.style.color = "#10b981";
          aiSummaryText.textContent = llm.summary || "AI analysis completed.";

          // Append red flags and missing info bullets
          aiBullets.innerHTML = "";
          const flags = llm.red_flags || [];
          const missing = llm.missing_trust_info || [];

          flags.forEach((f) => {
            const li = document.createElement("li");
            li.textContent = `🚩 ${f}`;
            aiBullets.appendChild(li);
          });
          missing.forEach((m) => {
            const li = document.createElement("li");
            li.textContent = `⚠️ ${m}`;
            aiBullets.appendChild(li);
          });

          // If official store claim mismatch detected
          if (aiData.mismatch_signal) {
            quickData.score_data.signals.push(aiData.mismatch_signal);
            renderSignals(quickData.score_data.signals);
            // Re-evaluate score if mismatch added
            let newScore = Math.min(100, quickData.score_data.score + (aiData.mismatch_signal.score_weight || 30));
            quickData.score_data.score = newScore;
            updateGauge(newScore, "#ef4444");
            riskBadge.textContent = "High Risk";
            riskBadge.className = "risk-badge high";
          }

          // Update alternatives if AI found better product name
          if (aiData.alternatives) {
            renderAlternatives(aiData.alternatives);
          }

          // Update audit checklist AI box
          const auditItems = document.querySelectorAll(".audit-item");
          if (auditItems.length >= 4) {
            auditItems[3].querySelector(".audit-icon").className = "audit-icon success";
            auditItems[3].querySelector(".audit-icon").textContent = "✓";
            auditItems[3].querySelector(".audit-desc").textContent = "Ollama model verified claims and text";
          }
        } else {
          aiStatusBadge.textContent = "Unavailable";
          aiStatusBadge.style.background = "rgba(148, 163, 184, 0.2)";
          aiStatusBadge.style.color = "#94a3b8";
          aiSummaryText.textContent = llm.ai_error || "AI model offline or busy. Full score evaluated using deterministic security rules.";
        }
      })
      .catch((err) => {
        aiStatusBadge.textContent = "Unavailable";
        aiSummaryText.textContent = "AI model offline. Store safety evaluated via deterministic rules.";
      });

    } catch (err) {
      console.error(err);
      alert("Error checking URL: " + err.message);
      submitBtn.disabled = false;
      btnText.textContent = "Check Store Safety";
    }
  });

  // Copy Summary to clipboard
  copySummaryBtn.addEventListener("click", () => {
    if (!currentResultData) return;
    const scoreData = currentResultData.score_data;
    const hostname = currentResultData.hostname;
    const score = scoreData.score;
    const label = scoreData.label_text;
    const disclaimer = scoreData.disclaimer;

    const signals = scoreData.signals || [];
    const signalsSummary = signals
      .filter((s) => s.is_risk)
      .map((s) => `- ${s.title}: ${s.evidence}`)
      .join("\n");

    const text = [
      `🔍 ScamLens: Shop Check Report`,
      `Target: ${hostname}`,
      `Risk Score: ${score}/100 (${label})`,
      ``,
      `Detected Warning Signs:`,
      signalsSummary || "- None flagged by URL and page rules.",
      ``,
      `Disclaimer: ${disclaimer}`,
      `Generated by ScamLens Shop Check`
    ].join("\n");

    navigator.clipboard.writeText(text).then(() => {
      showToast("Summary copied to clipboard!");
    }).catch(() => {
      showToast("Unable to copy to clipboard.");
    });
  });
});

