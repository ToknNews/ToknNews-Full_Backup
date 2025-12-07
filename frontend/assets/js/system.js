//
// TOKN System Console – Stable Baseline
//

document.addEventListener("DOMContentLoaded", () => {
    // ============================================
    // TOKN GLOBAL PARTICLE ENGINE (Landing-style)
    // ============================================
    const container = document.getElementById("particle-layer");

    function spawnParticle() {
        if (!container) return;

        const p = document.createElement("div");
        p.classList.add("particle");

        const size = Math.random() * 4 + 2;
        const left = Math.random() * 100;
        const duration = Math.random() * 4 + 4; // 4–8s

        p.style.width = `${size}px`;
        p.style.height = `${size}px`;
        p.style.left = `${left}vw`;
        p.style.animationDuration = `${duration}s`;

        container.appendChild(p);
        setTimeout(() => p.remove(), duration * 1000);
    }

    setInterval(spawnParticle, 160);

    // ============================================
    // ARCHITECTURE PANEL
    // ============================================
    const panel = document.getElementById("archPanel");
    const openBtn = document.getElementById("openArchitecture");
    const closeBtn = document.getElementById("archClose");

    if (openBtn && panel) {
        openBtn.addEventListener("click", () => panel.classList.add("open"));
    }
    if (closeBtn && panel) {
        closeBtn.addEventListener("click", () => panel.classList.remove("open"));
    }

    // ============================================
    // ANALYTICS POLLING (safe baseline)
    // ============================================
    startAnalyticsPolling();
});

// ---------------------------
// Analytics Polling
// ---------------------------
let pollTimer = null;

function startAnalyticsPolling() {
    fetchAndRender();
    pollTimer = setInterval(fetchAndRender, 5000);
}

function fetchAndRender() {
    fetch("/api/admin/analytics/dashboard")
        .then(r => r.json())
        .then(renderDashboard)
        .catch(err => console.error("Analytics error:", err));
}

// ---------------------------
// Rendering Logic
// ---------------------------
let ingestCtx, domainsCtx, sentimentCtx;

function renderDashboard(data) {
    renderIngestChart(data.ingest_history || []);
    renderDomainChart(data.domains.domains || {});
    renderSentimentChart(data.sentiment.sentiment || {});
    renderClusters(data.clusters);
    renderOnchain(data.onchain);
    renderEpisodes(data.episodes);
}

// ---------------------------
// Micro Charts – Canvas
// ---------------------------
function renderIngestChart(history) {
    const canvas = document.getElementById("ingestChart");
    if (!canvas) return;
    if (!ingestCtx) ingestCtx = canvas.getContext("2d");

    const values = history.slice(-20).map(h => h.total);
    drawMiniBarChart(ingestCtx, values, "#00aaff");
}

function renderDomainChart(domains) {
    const canvas = document.getElementById("domainsChart");
    if (!canvas) return;
    if (!domainsCtx) domainsCtx = canvas.getContext("2d");

    const keys = Object.keys(domains);
    const values = keys.map(k => domains[k]);
    drawMiniPieChart(domainsCtx, keys, values);
}

function renderSentimentChart(sentiment) {
    const canvas = document.getElementById("sentimentChart");
    if (!canvas) return;
    if (!sentimentCtx) sentimentCtx = canvas.getContext("2d");

    drawMiniBarChart(
        sentimentCtx,
        [sentiment.Positive || 0, sentiment.Neutral || 0, sentiment.Negative || 0],
        "#66ccff"
    );
}

// ---------------------------
// Chart Helpers
// ---------------------------
function drawMiniBarChart(ctx, values, color) {
    const w = ctx.canvas.width;
    const h = ctx.canvas.height;
    ctx.clearRect(0, 0, w, h);

    const max = Math.max(...values, 1);
    const barW = w / (values.length || 1);

    values.forEach((v, i) => {
        const barH = (v / max) * (h - 10);
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.7;
        ctx.fillRect(i * barW, h - barH, barW * 0.8, barH);
    });
}

function drawMiniPieChart(ctx, labels, values) {
    const total = values.reduce((s, v) => s + v, 0);
    if (total === 0) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        return;
    }

    const cx = ctx.canvas.width / 2;
    const cy = ctx.canvas.height / 2;
    const r = Math.min(cx, cy) - 4;

    let start = 0;
    values.forEach((v, i) => {
        const angle = (v / total) * Math.PI * 2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, r, start, start + angle);
        ctx.fillStyle = `hsl(${(i * 60) % 360}, 80%, 60%)`;
        ctx.fill();
        start += angle;
    });
}

// ---------------------------
// Cluster Panel
// ---------------------------
function renderClusters(clusterObj) {
    const panel = document.getElementById("clusterList");
    if (!panel) return;

    if (!clusterObj || !clusterObj.clusters) {
        panel.innerHTML = "No clusters available.";
        return;
    }

    panel.innerHTML = clusterObj.clusters
        .map(c => `
            <div class="cluster-item">
                <h4>${c.name}</h4>
                <p>${c.summary}</p>
            </div>
        `)
        .join("");
}

// ---------------------------
// On-chain panel
// ---------------------------
function renderOnchain(on) {
    const el = document.getElementById("onchainPanel");
    if (!el || !on) return;

    el.innerHTML = `
        <div>Volatility: ${on.volatility}</div>
        <div>Whale Volume: ${on.whale_volume}</div>
        <div>Largest Tx: ${on.largest_tx}</div>
    `;
}

// ---------------------------
// Recent episodes
// ---------------------------
function renderEpisodes(episodes) {
    const el = document.getElementById("episodesPanel");
    if (!el || !episodes) return;

    el.innerHTML = episodes
        .slice(-5)
        .map(ep => `<div>Episode ${ep.id}</div>`)
        .join("");
}
