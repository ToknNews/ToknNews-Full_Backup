/* ============================================================
   ToknNews V2 — ADMIN DASHBOARD LOGIC
   Controls:
    • Show Mode Override
    • Story Cap Override
    • Ingestion Trigger
    • StoryBank Stats Loader
    • PDv4 Casting Inspector
    • Episode Generation
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

    /* ---------------------------------------------------------
       ELEMENT HOOKS
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

    /* ---------------------------------------------------------
       API ROUTES (modify when backend is ready)
    --------------------------------------------------------- */
    const API = {
        saveMode:        "/api/admin/override_mode",
        saveCap:         "/api/admin/override_cap",
        ingest:          "/api/admin/ingest",
        storybank:       "/api/admin/storybank",
        pdstate:         "/api/admin/pd_state",
        generateEpisode: "/api/admin/generate_episode"
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
            return { error: true, message: e.toString() };
        }
    }

    async function getJSON(url) {
        try {
            const res = await fetch(url);
            return await res.json();
        } catch (e) {
            console.error("GET error:", e);
            return { error: true, message: e.toString() };
        }
    }

    /* =========================================================
       SHOW MODE OVERRIDE
    ========================================================= */
    saveModeBtn.addEventListener("click", async () => {
        const mode = modeSelect.value;

        const rsp = await postJSON(API.saveMode, { mode });
        if (rsp.error) {
            modeStatus.textContent = "Error saving mode override.";
        } else {
            modeStatus.textContent = `Mode override saved: ${mode}`;
        }
    });

    /* =========================================================
       STORY CAP OVERRIDE
    ========================================================= */
    saveCapBtn.addEventListener("click", async () => {
        const cap = parseInt(storyCapInput.value);

        const rsp = await postJSON(API.saveCap, { story_cap: cap });
        if (rsp.error) {
            capStatus.textContent = "Error saving story cap.";
        } else {
            capStatus.textContent = `Story cap saved: ${cap}`;
        }
    });

    /* =========================================================
       INGESTION MONITOR + TRIGGER
    ========================================================= */
    async function loadIngestionStatus() {
        const rsp = await getJSON(API.ingest);
        if (rsp.error) {
            ingestInfo.textContent = "Ingestion error.";
        } else {
            ingestInfo.textContent = `
                Last ingest: ${rsp.last_ingest || 'N/A'}
                • Total Stories: ${rsp.story_count || 0}
                • RSS: ${rsp.rss_count || 0}
                • API: ${rsp.api_count || 0}
            `;
        }
    }

    triggerIngest.addEventListener("click", async () => {
        ingestInfo.textContent = "Running ingestion...";
        const rsp = await postJSON(API.ingest, {});
        if (rsp.error) {
            ingestInfo.textContent = "Ingestion failed.";
        } else {
            ingestInfo.textContent = "Ingestion complete.";
            loadIngestionStatus();
        }
    });

    loadIngestionStatus();

    /* =========================================================
       STORYBANK MEMORY
    ========================================================= */
    async function loadStoryBank() {
        const rsp = await getJSON(API.storybank);
        if (rsp.error) {
            storyBankStats.textContent = "Error loading StoryBank.";
            return;
        }

        storyBankStats.innerHTML = `
            <strong>Total Stored:</strong> ${rsp.total || 0}<br>
            <strong>Domains:</strong> ${JSON.stringify(rsp.domains)}<br>
            <strong>Sentiment:</strong> ${JSON.stringify(rsp.sentiment)}
        `;
    }

    refreshSB.addEventListener("click", loadStoryBank);
    loadStoryBank();

    /* =========================================================
       PDv4 CASTING INSPECTOR
    ========================================================= */
    async function loadPDState() {
        const rsp = await getJSON(API.pdstate);
        if (rsp.error) {
            pdInspector.innerHTML = "<p>Error loading PD state.</p>";
            return;
        }

        const usage = rsp.anchor_usage || {};
        pdInspector.innerHTML = "";

        Object.entries(usage).forEach(([anchor, count]) => {
            const card = document.createElement("div");
            card.className = "pd-anchor-card";

            card.innerHTML = `
                <div class="pd-anchor-name">${anchor.toUpperCase()}</div>
                <div class="pd-anchor-usage">Used: ${count}</div>

                <div class="pd-fatigue-bar">
                    <div class="pd-fatigue-fill" style="width: ${Math.min(count * 12, 100)}%;"></div>
                </div>
            `;

            pdInspector.appendChild(card);
        });
    }

    refreshPD.addEventListener("click", loadPDState);
    loadPDState();

    /* =========================================================
       GENERATE EPISODE
    ========================================================= */
    generateEpisode.addEventListener("click", async () => {
        episodeStatus.textContent = "Generating episode...";
        const rsp = await postJSON(API.generateEpisode, {});
        if (rsp.error) {
            episodeStatus.textContent = "Episode generation failed.";
        } else {
            episodeStatus.textContent = `Episode Complete: ${rsp.episode_id}`;
        }
    });

});
