/* ============================================================
   TOKNNEWS V2 — ADMIN DASHBOARD LOGIC (PUBLIC API VERSION)
   Controls + Analytics Engine
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

    /* ---------------------------------------------------------
       TAB SWITCHING (Controls <-> Analytics)
    --------------------------------------------------------- */

    const tabControls = document.getElementById("tabControls");
    const tabAnalytics = document.getElementById("tabAnalytics");

    const controlsView = document.getElementById("controlsView");
    const analyticsView = document.getElementById("analyticsView");

    tabControls.addEventListener("click", () => {
        tabControls.classList.add("active");
        tabAnalytics.classList.remove("active");

        controlsView.classList.add("active");
        analyticsView.classList.remove("active");
    });

    tabAnalytics.addEventListener("click", () => {
        tabAnalytics.classList.add("active");
        tabControls.classList.remove("active");

        analyticsView.classList.add("active");
        controlsView.classList.remove("active");

        loadAllAnalytics();  // load charts on demand
    });


    /* ---------------------------------------------------------
       API ROUTING — PUBLIC ACCESS
    --------------------------------------------------------- */

    const API_BASE = "http://5.161.45.99:5599";

    const API = {
        saveMode:        API_BASE + "/api/admin/override_mode",
        saveCap:         API_BASE + "/api/admin/override_cap",
        ingestRun:       API_BASE + "/api/admin/ingest",
        ingestStatus:    API_BASE + "/api/admin/ingest",
        storybank:       API_BASE + "/api/admin/storybank",
        pdstate:         API_BASE + "/api/admin/pd_state",
        generateEpisode: API_BASE + "/api/admin/generate_episode",

        // Analytics
        sentimentHist:   API_BASE + "/api/admin/analytics/sentiment",
        domainHist:      API_BASE + "/api/admin/analytics/domains",
        ingestHist:      API_BASE + "/api/admin/analytics/ingest",
        episodesHist:    API_BASE + "/api/admin/analytics/episodes",
        clusterHist:     API_BASE + "/api/admin/analytics/clusters"
    };


    async function postJSON(url, payload) {
        try {
            const res = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            return await res.json();
        } catch (e) {
            console.error("POST error:", e);
            return { error: true };
        }
    }

    async function getJSON(url) {
        try {
            const res = await fetch(url);
            return await res.json();
        } catch (e) {
            console.error("GET error:", e);
            return { error: true };
        }
    }


    /* ---------------------------------------------------------
       CONTROLS TAB FUNCTIONS
    --------------------------------------------------------- */

    const modeSelect      = document.getElementById("modeSelect");
    const saveModeBtn     = document.getElementById("saveMode");
    const modeStatus      = document.getElementById("modeStatus");

    const storyCapInput   = document.getElementById("storyCapInput");
    const saveCapBtn      = document.getElementById("saveCap");
    const capStatus       = document.getElementById("capStatus");

    const ingestInfo      = document.getElementById("ingestInfo");
    const triggerIngest   = document.getElementById("triggerIngest");

    const storyBankStats  = document.getElementById("storyBankStats");
    const refreshSB       = document.getElementById("refreshStoryBank");

    const pdInspector     = document.getElementById("pdInspector");
    const refreshPD       = document.getElementById("refreshPD");

    const generateEpisode = document.getElementById("generateEpisode");
    const episodeStatus   = document.getElementById("episodeStatus");


    saveModeBtn.addEventListener("click", async () => {
        const mode = modeSelect.value;
        const rsp = await postJSON(API.saveMode, { mode });

        modeStatus.textContent = rsp.error
          ? "Error saving mode override."
          : `Mode override saved: ${mode}`;
    });

    saveCapBtn.addEventListener("click", async () => {
        const cap = parseInt(storyCapInput.value);
        const rsp = await postJSON(API.saveCap, { story_cap: cap });

        capStatus.textContent = rsp.error
          ? "Error saving story cap."
          : `Story cap saved: ${cap}`;
    });


    async function loadIngestStatus() {
        const rsp = await getJSON(API.ingestStatus);
        if (rsp.error) {
            ingestInfo.textContent = "Ingestion error.";
        } else {
            ingestInfo.innerHTML = `
                Last ingest: ${new Date(rsp.last_ingest * 1000).toLocaleString()}<br>
                Total Stories: ${rsp.story_count}<br>
                RSS: ${rsp.rss_count}<br>
                API: ${rsp.api_count}
            `;
        }
    }

    triggerIngest.addEventListener("click", async () => {
        ingestInfo.textContent = "Running ingestion...";
        await postJSON(API.ingestRun, {});
        loadIngestStatus();
    });

    loadIngestStatus();


    async function loadStoryBank() {
        const rsp = await getJSON(API.storybank);
        if (rsp.error) {
            storyBankStats.textContent = "Error loading StoryBank.";
        } else {
            storyBankStats.innerHTML = `
                <strong>Total Stored:</strong> ${rsp.total}<br>
                <strong>Domains:</strong> ${JSON.stringify(rsp.domains)}<br>
                <strong>Sentiment:</strong> ${JSON.stringify(rsp.sentiment)}
            `;
        }
    }
    refreshSB.addEventListener("click", loadStoryBank);
    loadStoryBank();


    async function loadPDState() {
        const rsp = await getJSON(API.pdstate);
        if (rsp.error) {
            pdInspector.innerHTML = "<p>Error loading PD state.</p>";
            return;
        }

        const usage = rsp.anchor_usage || {};
        pdInspector.innerHTML = "";

        Object.entries(usage).forEach(([name, count]) => {
            const card = document.createElement("div");
            card.className = "pd-anchor-card";

            card.innerHTML = `
                <div class="pd-anchor-name">${name.toUpperCase()}</div>
                <div class="pd-anchor-usage">Used: ${count}</div>
                <div class="pd-fatigue-bar">
                    <div class="pd-fatigue-fill" style="width:${Math.min(count * 12, 100)}%"></div>
                </div>
            `;

            pdInspector.appendChild(card);
        });
    }
    refreshPD.addEventListener("click", loadPDState);
    loadPDState();


    generateEpisode.addEventListener("click", async () => {
        episodeStatus.textContent = "Generating episode...";
        const rsp = await postJSON(API.generateEpisode, {});
        episodeStatus.textContent = rsp.error
          ? "Episode generation failed."
          : `Episode Created: ${rsp.episode_id}`;
    });


    /* =========================================================
       ANALYTICS CHART ENGINE
    ========================================================= */

    async function loadAllAnalytics() {
        loadAnchorUsage();
        loadDomainHeat();
        loadSentimentTrend();
        loadClusterRadar();
        loadIngestionVelocity();
        loadEpisodeHistory();
    }


    /* ---------------------------------------------------------
       1. Anchor Usage Bars
    --------------------------------------------------------- */
    async function loadAnchorUsage() {
        const rsp = await getJSON(API.pdstate);
        if (rsp.error) return;

        const canvas = document.getElementById("chartAnchorUsage");
        const ctx = canvas.getContext("2d");

        const usage = rsp.anchor_usage;
        const anchors = Object.keys(usage);
        const counts  = Object.values(usage);

        const barWidth = 40;
        const gap = 30;
        const startX = 20;
        const base = canvas.height - 30;

        ctx.clearRect(0,0,canvas.width,canvas.height);
        ctx.font = "14px Space Grotesk";

        anchors.forEach((a, i) => {
            const h = counts[i] * 8;
            ctx.fillStyle="rgba(50,255,172,0.55)";
            ctx.fillRect(startX + i * (barWidth + gap), base - h, barWidth, h);

            ctx.fillStyle="#fff";
            ctx.fillText(a.toUpperCase(), startX + i * (barWidth + gap), base + 18);
        });
    }


    /* ---------------------------------------------------------
       2. Domain Heat Radial Wheel
    --------------------------------------------------------- */
    async function loadDomainHeat() {
        const rsp = await getJSON(API.domainHist);
        if (rsp.error || rsp.length === 0) return;

        const latest = rsp[rsp.length - 1];
        const canvas = document.getElementById("chartDomainHeat");
        const ctx = canvas.getContext("2d");

        ctx.clearRect(0,0,canvas.width,canvas.height);

        const dom = latest.domains;
        const keys = Object.keys(dom);
        const vals = Object.values(dom);

        let total = vals.reduce((a,b)=>a+b,0);

        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const radius = 80;

        let startAngle = 0;

        keys.forEach((k,i)=>{
            const frac = vals[i]/total;
            const end = startAngle + frac * Math.PI * 2;

            ctx.beginPath();
            ctx.strokeStyle = "rgba(80,140,255,0.9)";
            ctx.lineWidth = 18;
            ctx.arc(cx, cy, radius, startAngle, end);
            ctx.stroke();

            startAngle = end;
        });
    }


    /* ---------------------------------------------------------
       3. Sentiment Sparkline
    --------------------------------------------------------- */
    async function loadSentimentTrend() {
        const rsp = await getJSON(API.sentimentHist);
        if (rsp.error || rsp.length < 2) return;

        const canvas = document.getElementById("chartSentiment");
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0,0,canvas.width,canvas.height);

        const points = rsp.map(r => r.sentiment.Positive - r.sentiment.Negative);
        const max = Math.max(...points);
        const min = Math.min(...points);
        const scale = (canvas.height - 40) / (max - min || 1);

        ctx.beginPath();
        ctx.moveTo(10, canvas.height - 20 - (points[0]-min)*scale);

        points.forEach((p,i)=>{
            const x = 10 + i*(canvas.width/(points.length-1));
            const y = canvas.height - 20 - (p-min)*scale;
            ctx.lineTo(x,y);
        });

        ctx.strokeStyle = "rgba(50,255,172,0.9)";
        ctx.lineWidth = 3;
        ctx.shadowColor = "rgba(50,255,172,0.8)";
        ctx.shadowBlur = 12;
        ctx.stroke();
    }


    /* ---------------------------------------------------------
       4. Narrative Cluster Radar
    --------------------------------------------------------- */
    async function loadClusterRadar() {
        const rsp = await getJSON(API.clusterHist);
        if (rsp.error || Object.keys(rsp).length === 0) return;

        const canvas = document.getElementById("chartClusterRadar");
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0,0,canvas.width,canvas.height);

        const keys = Object.keys(rsp);
        const vals = Object.values(rsp);
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const maxVal = Math.max(...vals);
        const radius = 90;

        ctx.beginPath();
        keys.forEach((k,i)=>{
            const angle = (i/keys.length)*Math.PI*2;
            const r = (vals[i]/maxVal)*radius;

            const x = cx + r*Math.cos(angle);
            const y = cy + r*Math.sin(angle);

            i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
        });
        ctx.closePath();

        ctx.strokeStyle="rgba(80,140,255,0.9)";
        ctx.lineWidth=2;
        ctx.shadowColor="rgba(80,140,255,0.8)";
        ctx.shadowBlur=12;
        ctx.stroke();
    }


    /* ---------------------------------------------------------
       5. Ingestion Velocity
    --------------------------------------------------------- */
    async function loadIngestionVelocity() {
        const rsp = await getJSON(API.ingestHist);
        if (rsp.error || rsp.length < 2) return;

        const canvas = document.getElementById("chartVelocity");
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0,0,canvas.width,canvas.height);

        const totals = rsp.map(r => r.total);
        const max = Math.max(...totals);
        const min = Math.min(...totals);
        const scale = (canvas.height-40)/(max-min || 1);

        ctx.beginPath();
        ctx.moveTo(10, canvas.height - 20 - (totals[0]-min)*scale);

        totals.forEach((t,i)=>{
            const x = 10+i*(canvas.width/(totals.length-1));
            const y = canvas.height - 20 - (t-min)*scale;
            ctx.lineTo(x,y);
        });

        ctx.strokeStyle="rgba(58,99,255,0.9)";
        ctx.lineWidth=3;
        ctx.shadowColor="rgba(58,99,255,0.8)";
        ctx.shadowBlur=14;
        ctx.stroke();
    }


    /* ---------------------------------------------------------
       6. Episode Timeline
    --------------------------------------------------------- */
    async function loadEpisodeHistory() {
        const rsp = await getJSON(API.episodesHist);
        if (rsp.error || rsp.length === 0) return;

        const canvas = document.getElementById("chartEpisodeHistory");
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0,0,canvas.width,canvas.height);

        const episodes = rsp;
        const xSpacing = canvas.width / (episodes.length+1);
        const base = canvas.height - 40;

        episodes.forEach((ep,i)=>{
            const x = (i+1)*xSpacing;
            const y = base - Math.log(ep.runtime || 1)*20;

            ctx.beginPath();
            ctx.arc(x,y,8,0,Math.PI*2);
            ctx.fillStyle="rgba(50,255,172,0.8)";
            ctx.shadowColor="rgba(50,255,172,0.7)";
            ctx.shadowBlur=10;
            ctx.fill();
        });
    }

});
