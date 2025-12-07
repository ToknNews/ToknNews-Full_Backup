/* =========================================================
   TOKNNEWS V2 - FRONTEND APP.JS
   Controls:
    - Command Orb Menu
    - Slide-In Navigation Drawer
    - Docs Pop-Up
    - Episode Loading
    - Headline Loading
    - Live Data Placeholders
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    /* -----------------------------------------------------
       SLIDE-IN MENU (LEFT PANEL)
    ----------------------------------------------------- */
    const cmdOrb = document.getElementById("cmd-orb");
    const navPanel = createNavPanel();
    document.body.appendChild(navPanel);

    let navOpen = false;

    cmdOrb.addEventListener("click", () => {
        navOpen = !navOpen;
        toggleNavPanel(navOpen);
    });

    function toggleNavPanel(open) {
        if (open) {
            navPanel.classList.add("nav-open");
        } else {
            navPanel.classList.remove("nav-open");
        }
    }

    function createNavPanel() {
        const panel = document.createElement("div");
        panel.id = "nav-panel";
        panel.className = "nav-panel glass-card";

        panel.innerHTML = `
            <div class="nav-header">
                <h2>ToknNews</h2>
            </div>

            <ul class="nav-list">
                <li><a href="index.html">Home</a></li>
                <li><a href="episodes.html">Episodes</a></li>
                <li><a id="navDocs" href="#">Technical Overview</a></li>
                <li><a href="docs.html" target="_blank">Docs (New Tab)</a></li>
                <li><a href="/admin/index.html">Admin Login</a></li>
            </ul>
        `;
        return panel;
    }


    /* -----------------------------------------------------
       DOCS POP-UP PANEL
    ----------------------------------------------------- */

    const openDocsBtn = document.getElementById("openDocs") || document.getElementById("navDocs");
    const docsPanel = document.getElementById("docsPanel");
    const closeDocsBtn = document.getElementById("closeDocs");

    if (openDocsBtn) {
        openDocsBtn.addEventListener("click", () => {
            docsPanel.classList.remove("hidden");
            toggleNavPanel(false);
        });
    }

    if (closeDocsBtn) {
        closeDocsBtn.addEventListener("click", () => {
            docsPanel.classList.add("hidden");
        });
    }


    /* -----------------------------------------------------
       LIVE DATA PLACEHOLDERS (READY FOR BACKEND ENDPOINTS)
    ----------------------------------------------------- */

    // Ingestion Pulse
    const ingestStatus = document.getElementById("ingestStatus");

    function updateIngestStatus() {
        // Placeholder for your backend endpoint
        ingestStatus.textContent = "Last ingest: just now";
    }
    updateIngestStatus();


    // Enrichment Status
    const enrichStatus = document.getElementById("enrichStatus");

    function updateEnrichStatus() {
        enrichStatus.textContent = "Meta-enriched: 15 / Total Stories: 93";
    }
    updateEnrichStatus();


    // Domain Heatmap Placeholder
    const heatCanvas = document.getElementById("domainHeat");
    if (heatCanvas) {
        const ctx = heatCanvas.getContext("2d");
        ctx.fillStyle = "#3A63FF";
        ctx.strokeStyle = "#32FFAC";
        ctx.lineWidth = 4;

        ctx.beginPath();
        ctx.arc(100, 100, 40, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillText("Markets", 70, 160);
    }


    /* -----------------------------------------------------
       HEADLINE LOADER (STATIC SAMPLE UNTIL API IS READY)
    ----------------------------------------------------- */

    const headlineCards = document.getElementById("headlineCards");

    function loadHeadlines() {
        if (!headlineCards) return;

        const sample = [
            "Market sentiment shifts as liquidity rotates into new sectors.",
            "Retail positioning cools while institutional flows increase.",
            "Volatility resurfaces across digital assets as volume rises."
        ];

        sample.forEach(headline => {
            const card = document.createElement("div");
            card.className = "headline-card glass-card";
            card.textContent = headline;
            headlineCards.appendChild(card);
        });
    }
    loadHeadlines();


    /* -----------------------------------------------------
       EPISODE CARD LOADER
       (Pulls from http://5.161.45.99:8999/ )
    ----------------------------------------------------- */

    const episodeGrid = document.getElementById("episodeGrid");
    const EPISODE_FEED = "http://5.161.45.99:8999/";

    async function loadEpisodes() {
        if (!episodeGrid) return;

        try {
            // Placeholder fetch — adjust when your API is ready
            // const res = await fetch(EPISODE_FEED);
            // const episodes = await res.json();

            // TEMP SAMPLE DATA
            const episodes = [
                { title: "ToknNews — Market Pulse", runtime: "2:14" },
                { title: "ToknNews — Crypto Rundown", runtime: "1:57" },
                { title: "ToknNews — Evening Brief", runtime: "2:32" }
            ];

            episodes.forEach(ep => {
                const card = document.createElement("div");
                card.className = "episode-card";

                card.innerHTML = `
                    <img src="assets/img/YT_Banner_Tokn.jpg" class="episode-thumb" />
                    <div class="episode-info">
                        <h3>${ep.title}</h3>
                        <p>${ep.runtime}</p>
                    </div>
                `;

                episodeGrid.appendChild(card);
            });

        } catch (e) {
            console.error("Error loading episodes:", e);
        }
    }

    loadEpisodes();


});
