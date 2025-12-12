/* ============================================================================
   TOKN Control Studio — Unified JS (Episode Console + Clusters Ready)
   ============================================================================ */

document.addEventListener("DOMContentLoaded", () => {

    /* ============================================================
       PARTICLE ENGINE (shared aesthetic)
    ============================================================ */
    const container = document.getElementById("particle-layer");
    function spawnParticle() {
        const p = document.createElement("div");
        p.classList.add("particle");
        const size = Math.random() * 4 + 2;
        const left = Math.random() * 100;
        const duration = Math.random() * 4 + 4;
        p.style.width = `${size}px`;
        p.style.height = `${size}px`;
        p.style.left = `${left}vw`;
        p.style.animationDuration = `${duration}s`;
        container.appendChild(p);
        setTimeout(() => p.remove(), duration * 1000);
    }
    setInterval(spawnParticle, 160);


    /* ============================================================
       SIDEBAR NAVIGATION
    ============================================================ */
    const sideItems = document.querySelectorAll(".side-item");
    const panels    = document.querySelectorAll(".studio-panel");

    function activatePanel(id) {
        panels.forEach(p => p.classList.remove("active"));
        document.getElementById("panel-" + id)?.classList.add("active");

        sideItems.forEach(b => b.classList.remove("active"));
        document.querySelector(`[data-panel="${id}"]`)?.classList.add("active");

        // Load per-panel backend endpoints
        if (id === "episodes") {
            loadEpisodeHistory();
            loadAutonomousStatus();
        }
        if (id === "clusters") {
            loadClusters();
        }
    }

    sideItems.forEach(btn =>
        btn.addEventListener("click", () => activatePanel(btn.dataset.panel))
    );

    activatePanel("dashboard");



    /* ========================================================================
       SECTION 1 — LLM SEGMENT GEN
       ======================================================================== */
    const segConcept = document.getElementById("segmentConcept");
    const segPersona = document.getElementById("segmentPersona");
    const segModel   = document.getElementById("segmentModel");
    const segLN      = document.getElementById("segmentLateNight");
    const segOut     = document.getElementById("segmentOutput");
    const segBtn     = document.getElementById("segmentGenerateBtn");
    const segActions = document.getElementById("segmentActions");

    let lastSegmentScript = "";

    segBtn.addEventListener("click", async () => {
        segOut.style.display = "none";
        segActions.classList.remove("active");

        const payload = {
            concept: segConcept.value.trim(),
            persona: segPersona.value.trim(),
            model: segModel.value.trim(),
            latenight: segLN.checked
        };

        const r = await fetch("/api/studio/llm/generate_segment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await r.json();
        segOut.textContent = JSON.stringify(data, null, 2);
        segOut.style.display = "block";

        if (data.ok) {
            lastSegmentScript = data.script;
            segActions.classList.add("active");
        }
    });



    /* ========================================================================
       SECTION 2 — FEED QUERY
       ======================================================================== */
    const fqQuery = document.getElementById("feedQueryInput");
    const fqPersona = document.getElementById("feedPersona");
    const fqModel = document.getElementById("feedModel");
    const fqLN = document.getElementById("feedLateNight");
    const fqOut = document.getElementById("feedOutput");
    const fqActions = document.getElementById("feedActions");
    const fqBtn = document.getElementById("feedGenerateBtn");

    fqBtn.addEventListener("click", async () => {
        fqOut.style.display = "none";
        fqActions.classList.remove("active");

        const payload = {
            query: fqQuery.value.trim(),
            persona: fqPersona.value.trim(),
            model: fqModel.value.trim(),
            latenight: fqLN.checked
        };

        const r = await fetch("/api/studio/llm/query_feeds", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await r.json();
        fqOut.textContent = JSON.stringify(data, null, 2);
        fqOut.style.display = "block";

        if (data.ok) fqActions.classList.add("active");
    });

    /* ========================================================================
       SECTION 3 — CLUSTERS VIEWER (FINAL DROP-IN)
       ======================================================================== */

    const clusterGrid        = document.getElementById("clusterGrid");
    const clusterModeLabel   = document.getElementById("clusterMode");
    const clusterUpdatedLabel = document.getElementById("clusterUpdated");
    const clusterRefreshBtn  = document.getElementById("clusterRefreshBtn");

    async function loadClusters() {
        if (!clusterGrid) return;

        clusterGrid.innerHTML = "Loading clusters…";

        try {
            const r = await fetch("/api/admin/analytics/clusters");
            const data = await r.json();

            if (!data || !Array.isArray(data.clusters) || !data.clusters.length) {
                clusterGrid.innerHTML = "No cluster data available.";
                return;
            }

            // Header metadata
            if (clusterModeLabel) {
                clusterModeLabel.textContent = `Clustering: ${data.source || "unknown"}`;
            }
            if (clusterUpdatedLabel && data.ts) {
                clusterUpdatedLabel.textContent =
                    `Updated: ${new Date(data.ts * 1000).toLocaleTimeString()}`;
            }

            clusterGrid.innerHTML = data.clusters.map(cluster => {
                const stories = cluster.stories || [];

                const anchors = [...new Set(
                    stories.flatMap(s => s.anchors || [])
                )];

                const avgImportance = stories.length
                    ? (
                        stories.reduce((a, s) => a + (s.importance || 0), 0)
                        / stories.length
                      ).toFixed(1)
                    : "–";

                return `
                    <div class="cluster-card">
                        <h3>${cluster.domain.toUpperCase()} (${stories.length})</h3>

                        <div class="cluster-meta">
                            <div><strong>Anchors:</strong> ${anchors.join(", ") || "—"}</div>
                            <div><strong>Avg Importance:</strong> ${avgImportance}</div>
                        </div>

                        <ul class="cluster-stories">
                            ${stories.slice(0, 4).map(s => `
                                <li>
                                    <strong>${s.headline}</strong>
                                    <div class="cluster-story-meta">
                                        Importance: ${s.importance ?? "—"} |
                                        ${s.sentiment ?? "Neutral"}
                                    </div>
                                </li>
                            `).join("")}
                        </ul>

                        ${stories.length > 4 ? `
                            <div class="cluster-more">
                                + ${stories.length - 4} more stories
                            </div>
                        ` : ""}
                    </div>
                `;
            }).join("");

        } catch (err) {
            console.error("[Clusters] Failed to load", err);
            clusterGrid.innerHTML = "Failed to load clusters.";
        }
    }

    /* Manual recompute */
    clusterRefreshBtn?.addEventListener("click", () => {
        clusterGrid.innerHTML = "Recomputing clusters…";
        loadClusters();
    });


    /* ========================================================================
       SECTION 4 — EPISODE CONSOLE
       ======================================================================== */
    const epPreview = document.getElementById("episodePreview");
    const epEditor  = document.getElementById("episodeEditor");
    const epActions = document.getElementById("episodeActions");
    const epMeta    = document.getElementById("episodeMeta");
    const epBtn     = document.getElementById("episodeGenerateBtn");
    const epIngest  = document.getElementById("episodeNewIngestBtn");
    const epAutoBtn = document.getElementById("episodeAutoToggle");

    let currentEpisode = null;

    epIngest?.addEventListener("click", async () => {
        epPreview.textContent = "Refreshing stories…";
        const r = await fetch("/api/studio/episode/breaking", { method: "POST" });
        const data = await r.json();
        alert(data.ok ? "Ingest refreshed. Now click Generate Script." : "Ingest failed.");
    });

    epBtn.addEventListener("click", async () => {
        epPreview.style.display = "none";
        epEditor.classList.remove("active");
        epActions.classList.remove("active");
        epMeta.classList.remove("active");

        const r = await fetch("/api/studio/episode/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({})
        });

        const data = await r.json();
        if (!data.ok) {
            epPreview.textContent = "ERROR: " + data.error;
            epPreview.style.display = "block";
            return;
        }

        currentEpisode = data;

        epPreview.textContent = JSON.stringify(data.blocks, null, 2);
        epPreview.style.display = "block";

        epEditor.innerHTML = data.blocks
            .map((b, i) => `
                <div class="edit-block">
                    <label><strong>${b.speaker}</strong> (${b.tag})</label>
                    <textarea class="edit-text" data-idx="${i}">${b.text}</textarea>
                </div>
            `)
            .join("");

        epEditor.classList.add("active");
        epActions.classList.add("active");

        epMeta.innerHTML = `
            <div><strong>Episode ID:</strong> ${data.episode_id}</div>
            <div><strong>Mode:</strong> ${data.mode}</div>
        `;
        epMeta.classList.add("active");
    });

    document.getElementById("episodeApproveBtn")?.addEventListener("click", async () => {
        if (!currentEpisode) return;

        const edits = [...document.querySelectorAll(".edit-text")].map(el => el.value);

        const r = await fetch("/api/studio/episode/approve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                episode_id: currentEpisode.episode_id,
                audio_blocks: currentEpisode.audio_blocks,
                edits
            })
        });

        const data = await r.json();
        alert(data.ok ? "Render Started." : "Approval Failed.");
        loadEpisodeHistory();
    });

    async function loadEpisodeHistory() {
        const panel = document.getElementById("episodeHistory");
        if (!panel) return;

        const r = await fetch("/api/studio/episodes/history");
        const data = await r.json();

        if (!data.ok) {
            panel.innerHTML = "Failed to load history.";
            return;
        }

        panel.innerHTML = data.episodes
            .map(ep => `
                <div class="history-item">
                    <strong>${ep.episode_id}</strong>
                    <div>${new Date(ep.timestamp * 1000).toLocaleString()}</div>
                    <div>${ep.mode}</div>
                </div>
            `)
            .join("");
    }

    async function loadAutonomousStatus() {
        const r = await fetch("/api/studio/autonomous/status");
        const data = await r.json();
        epAutoBtn.checked = data.autonomous;
    }

    epAutoBtn?.addEventListener("change", async () => {
        await fetch("/api/studio/autonomous/set", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ enabled: epAutoBtn.checked })
        });
        alert("Autonomous mode updated.");
    });

});

/* ------------------------------------------------------------
   SYSTEM LOG VIEWER (PM2 logs)
------------------------------------------------------------ */
async function loadLogs() {
    const box = document.getElementById("logsContent");
    if (!box) return;

    try {
        const r = await fetch("/api/admin/logs");
        const data = await r.json();

        if (!data.ok) {
            box.textContent = "Failed to load logs.";
            return;
        }

        box.textContent = data.text || "(empty)";
    } catch {
        box.textContent = "Error loading logs.";
    }
}

document.getElementById("logsRefreshBtn")?.addEventListener("click", loadLogs);
