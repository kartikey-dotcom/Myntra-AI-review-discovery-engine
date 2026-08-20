document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    loadVerifiedFindings();
    loadCorpusStats();
    loadRejectedLog();

    // Event Listeners
    document.getElementById("btn-scan")?.addEventListener("click", handleSyntheticScan);
    document.getElementById("btn-fetch-seller")?.addEventListener("click", handleSellerReport);
    document.getElementById("btn-batch-analyze")?.addEventListener("click", handleBatchAnalysis);
    document.getElementById("close-modal")?.addEventListener("click", closeModal);
});

function initNavigation() {
    const tabs = [
        { btn: "tab-btn-findings", view: "view-verified" },
        { btn: "tab-btn-stats", view: "view-stats" },
        { btn: "tab-btn-rejected", view: "view-rejected" },
        { btn: "tab-btn-appendix", view: "view-appendix" }
    ];

    tabs.forEach(t => {
        document.getElementById(t.btn)?.addEventListener("click", () => {
            tabs.forEach(x => {
                document.getElementById(x.btn)?.classList.remove("active");
                document.getElementById(x.view)?.classList.remove("active");
            });
            document.getElementById(t.btn)?.classList.add("active");
            document.getElementById(t.view)?.classList.add("active");
        });
    });
}

// 1. Load Verified Findings (View 1)
async function loadVerifiedFindings() {
    const container = document.getElementById("findings-container");
    if (!container) return;

    try {
        const resp = await fetch("/api/v1/corpus/verified-findings");
        const data = await resp.json();
        const list = data.verified_findings || [];

        if (list.length === 0) {
            container.innerHTML = `<p style="color: var(--text-sub);">No verified claims in database yet.</p>`;
            return;
        }

        container.innerHTML = list.map(item => `
            <div class="finding-card">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <span class="finding-category-pill">${item.category.replace(/_/g, ' ')}</span>
                        <span class="finding-category-pill" style="background:rgba(255,255,255,0.1); color:#ffffff; font-size:0.75rem;">${item.source_platform || 'Play Store'}</span>
                    </div>
                    <div class="finding-claim">"${item.claim_text}"</div>
                    <div class="quote-box">"${item.quote}"</div>
                </div>
                <div class="finding-footer">
                    <div>
                        <span>SKU: ${item.sku_id}</span>
                        ${item.height_cm ? ` • ${item.height_cm}cm` : ''}
                        ${item.weight_kg ? ` / ${item.weight_kg}kg` : ''}
                    </div>
                    <button class="trace-btn" onclick="openRecordModal('${item.review_id}')">Trace Record ${item.review_id}</button>
                </div>
            </div>
        `).join("");
    } catch (e) {
        console.error("Failed to load verified findings", e);
    }
}

// 2. Load Corpus Stats (View 2)
async function loadCorpusStats() {
    try {
        const resp = await fetch("/api/v1/corpus/analytics");
        const data = await resp.json();

        document.getElementById("stat-total-reviews").innerText = (data.total_corpus_reviews || 0).toLocaleString();
        document.getElementById("stat-total-claims").innerText = (data.total_claims_evaluated || 0).toLocaleString();
        document.getElementById("stat-pass-rate").innerText = `${data.verification_pass_rate_pct || 0}%`;
        document.getElementById("stat-rejected-count").innerText = (data.rejected_claims_count || 0).toLocaleString();

        const sourceData = data.source_breakdown || {};
        if (document.getElementById("stat-playstore-count")) {
            document.getElementById("stat-playstore-count").innerText = (sourceData["Play Store"] || 0).toLocaleString();
            document.getElementById("stat-appstore-count").innerText = (sourceData["App Store"] || 0).toLocaleString();
            document.getElementById("stat-reddit-count").innerText = (sourceData["Reddit"] || 0).toLocaleString();
        }

        const catContainer = document.getElementById("category-bars-container");
        if (!catContainer) return;

        const breakdown = data.category_breakdown || {};
        catContainer.innerHTML = Object.keys(breakdown).map(cat => {
            const item = breakdown[cat];
            const readableName = cat.replace(/_/g, ' ').toUpperCase();
            return `
                <div class="cat-bar-item">
                    <div class="cat-bar-header">
                        <span>${readableName}</span>
                        <span>${item.count} mentions (${item.percentage}%)</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill" style="width: ${item.percentage}%"></div>
                    </div>
                </div>
            `;
        }).join("");
    } catch (e) {
        console.error("Failed to load corpus stats", e);
    }
}

// 3. Load Rejected Log (View 3)
async function loadRejectedLog() {
    const tableBody = document.getElementById("rejected-table-body");
    if (!tableBody) return;

    try {
        const resp = await fetch("/api/v1/corpus/rejected-log");
        const data = await resp.json();
        const list = data.rejected_log || [];

        if (list.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-sub);">No rejected claims logged.</td></tr>`;
            return;
        }

        tableBody.innerHTML = list.map(item => `
            <tr>
                <td><strong>#${item.claim_id}</strong></td>
                <td><span class="finding-category-pill">${item.category.replace(/_/g, ' ')}</span></td>
                <td>${item.claim_text}</td>
                <td style="font-style:italic;">"${item.quote}"</td>
                <td class="rejection-badge">${item.rejection_reason || 'Failed Stage 3 Verification'}</td>
                <td><button class="trace-btn" onclick="openRecordModal('${item.review_id}')">${item.review_id}</button></td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Failed to load rejected log", e);
    }
}

// Modal Click-Traceability Handler
async function openRecordModal(reviewId) {
    const modal = document.getElementById("record-modal");
    const body = document.getElementById("modal-body-content");
    modal.classList.remove("hidden");

    try {
        const resp = await fetch(`/api/v1/corpus/records/${reviewId}`);
        const rec = await resp.json();

        body.innerHTML = `
            <div style="display:flex; justify-content:space-between; margin-bottom:1rem;">
                <span class="user-badge">${rec.user_id}</span>
                <span style="color:var(--primary); font-weight:700;">Record ID: ${rec.review_id}</span>
            </div>
            <p style="margin-bottom:0.8rem;"><strong>SKU:</strong> ${rec.sku_id} (${rec.sku_title || 'Apparel Item'})</p>
            <div class="body-pill" style="margin-bottom:1rem;">
                Height: ${rec.height_cm ? rec.height_cm + 'cm' : 'N/A'} | 
                Weight: ${rec.weight_kg ? rec.weight_kg + 'kg' : 'N/A'} | 
                Size: ${rec.size_worn || 'N/A'} | 
                Build: ${rec.body_build || 'N/A'}
            </div>
            <h4>Raw Customer Review Text:</h4>
            <div class="quote-box" style="margin-top:0.5rem; font-style:normal;">
                "${rec.sanitized_text || rec.raw_text}"
            </div>
            <p style="font-size:0.8rem; color:var(--text-sub); margin-top:1rem;">Ingested: ${rec.created_at}</p>
        `;
    } catch (e) {
        body.innerHTML = `<p style="color:var(--danger)">Failed to load record details.</p>`;
    }
}

function closeModal() {
    document.getElementById("record-modal")?.classList.add("hidden");
}

async function handleBatchAnalysis() {
    const skuId = document.getElementById("batch-sku").value || "MYN-CONVERSION-BATCH";
    const rawInput = document.getElementById("batch-input").value;
    const outputDiv = document.getElementById("batch-results");

    const lines = rawInput.split("\n").filter(l => l.trim());
    if (lines.length === 0) return;

    const reviews = lines.map((text, idx) => ({
        user_id: `USER-EXT-${idx+1:03d}`,
        rating: 4,
        review_text: text
    }));

    try {
        const resp = await fetch("/api/v1/reviews/bulk-analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sku_id: skuId, brand: "Myntra Brand", reviews: reviews })
        });
        const data = await resp.json();
        outputDiv.classList.remove("hidden");
        outputDiv.innerHTML = `<p style="color:var(--success)">✓ Ingested ${data.processed_count} reviews into conversion pipeline!</p>`;

        loadVerifiedFindings();
        loadCorpusStats();
        loadRejectedLog();
    } catch (e) {
        console.error("Batch error", e);
    }
}

async function handleSyntheticScan() {
    const text = document.getElementById("synthetic-input").value;
    const outputDiv = document.getElementById("scan-results");

    try {
        const resp = await fetch("/api/v1/trust/synthetic-scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });
        const data = await resp.json();
        outputDiv.classList.remove("hidden");
        outputDiv.innerHTML = `<p>Synthetic Score: ${(data.synthetic_confidence_score * 100).toFixed(1)}%</p>`;
    } catch (e) {
        console.error("Scan error", e);
    }
}

async function handleSellerReport() {
    const brand = document.getElementById("seller-brand").value;
    const outputDiv = document.getElementById("seller-report");

    try {
        const resp = await fetch(`/api/v1/seller/dashboard/${brand}`);
        const data = await resp.json();
        outputDiv.innerHTML = `<p>Brand: ${data.brand} | Calibration: ${data.size_calibration_recommendation}</p>`;
    } catch (e) {
        console.error("Seller report error", e);
    }
}
