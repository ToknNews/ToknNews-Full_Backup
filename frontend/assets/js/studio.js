/* ============================================================
   TOKN Control Studio — CLEAN VERSION (NO OLD EPISODE QUEUE)
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

    /* ============================================================
       PARTICLE ENGINE
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

    function activatePanel(panelId) {
        panels.forEach(p => p.classList.remove("active"));
        const panel = document.getElementById("panel-" + panelId);
        if (panel) panel.classList.add("active");

        sideItems.forEach(b => b.classList.remove("active"));
        const btn = document.querySelector(`[data-panel="${panelId}"]`);
        if (btn) btn.classList.add("active");
    }

    sideItems.forEach(btn => {
        btn.addEventListener("click", () => activatePanel(btn.dataset.panel));
    });

    activatePanel("dashboard");



    /* ============================================================
       SECTION 1 — LLM SEGMENT GENERATOR
    ============================================================ */

    const segConcept   = document.getElementById("segmentConcept");
    const segPersona   = document.getElementById("segmentPersona");
    const segModel     = document.getElementById("segmentModel");
    const segLN        = document.getElementById("segmentLateNight");
    const segOut       = document.getElementById("segmentOutput");
    const segBtn       = document.getElementById("segmentGenerateBtn");
    const segActions   = document.getElementById("segmentActions");

    let lastSegmentScript = "";
    let lastSegmentDomain = "";

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
            lastSegmentDomain = data.recommended_persona || "";
            segActions.classList.add("active");
        }
    });

    document.getElementById("queueSegmentBtn").addEventListener("click", async () => {
        await fetch("/api/studio/llm/queue_segment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                persona: segPersona.value.trim(),
                script: lastSegmentScript,
                domain: lastSegmentDomain
            })
        });
        alert("Segment queued.");
    });

    document.getElementById("saveSegmentBtn").addEventListener("click", async () => {
        await fetch("/api/studio/llm/save_to_storybank", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                persona: segPersona.value.trim(),
                script: lastSegmentScript,
                domain: lastSegmentDomain,
                tags: ["segment"]
            })
        });
        alert("Saved to StoryBank.");
    });



    /* ============================================================
       SECTION 2 — FEED QUERY
    ============================================================ */

    const fqQuery   = document.getElementById("feedQueryInput");
    const fqPersona = document.getElementById("feedPersona");
    const fqModel   = document.getElementById("feedModel");
    const fqLN      = document.getElementById("feedLateNight");
    const fqBtn     = document.getElementById("feedGenerateBtn");
    const fqOut     = document.getElementById("feedOutput");
    const fqActions = document.getElementById("feedActions");
    const fqMeta    = document.getElementById("feedMeta");

    let lastFeedScript = "";
    let lastFeedDomain = "";

    fqBtn.addEventListener("click", async () => {
        fqOut.style.display = "none";
        fqActions.classList.remove("active");
        fqMeta.classList.remove("active");

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

        if (data.ok) {
            lastFeedScript = data.script;
            lastFeedDomain = data.recommended_persona || "";

            fqMeta.innerHTML = `
                <div><strong>Cluster:</strong> ${data.cluster}</div>
                <div><strong>Summary:</strong> ${data.cluster_summary}</div>
                <div><strong>Signals:</strong></div>
                <ul>${data.signals_used.map(s => `<li>${s}</li>`).join("")}</ul>
            `;
            fqMeta.classList.add("active");
            fqActions.classList.add("active");
        }
    });

    document.getElementById("queueFeedBtn").addEventListener("click", async () => {
        await fetch("/api/studio/llm/queue_segment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                persona: fqPersona.value.trim(),
                script: lastFeedScript,
                domain: lastFeedDomain
            })
        });
        alert("Feed segment queued.");
    });

    document.getElementById("saveFeedBtn").addEventListener("click", async () => {
        await fetch("/api/studio/llm/save_to_storybank", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                persona: fqPersona.value.trim(),
                script: lastFeedScript,
                domain: lastFeedDomain,
                tags: ["feed_query"]
            })
        });
        alert("Feed saved.");
    });



    /* ============================================================
       SECTION 3 — AD MANAGER (unchanged)
    ============================================================ */

    // ... YOUR AD MANAGER CODE STAYS AS-IS ...



    /* ============================================================
       SECTION 4 — EPISODE CONSOLE (NEW SYSTEM ONLY)
    ============================================================ */

    const epMode = document.getElementById("episodeMode");
    const epCap  = document.getElementById("episodeCap");
    const epSkip = document.getElementById("episodeSkipIngest");

    const epBtn     = document.getElementById("episodeGenerateBtn");
    const epPreview = document.getElementById("episodePreview");
    const epEditor  = document.getElementById("episodeEditor");
    const epActions = document.getElementById("episodeActions");
    const epMeta    = document.getElementById("episodeMeta");

    let lastEpisode = null;

    epBtn.addEventListener("click", async () => {
        epPreview.style.display = "none";
        epEditor.classList.remove("active");
        epActions.classList.remove("active");
        epMeta.classList.remove("active");

        const payload = {
            mode: epMode.value,
            cap: Number(epCap.value),
            skip_ingest: epSkip.checked
        };

        const r = await fetch("/api/studio/episode/preview", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await r.json();
        lastEpisode = data;

        if (!data.ok) {
            epPreview.textContent = "ERROR: " + (data.error || "Unknown error");
            epPreview.style.display = "block";
            return;
        }

        epPreview.textContent = JSON.stringify(data.blocks, null, 2);
        epPreview.style.display = "block";

        epEditor.innerHTML = data.blocks
            .map((b, i) => `
                <div class="edit-block">
                    <label><strong>${b.speaker}</strong> (${b.tag})</label>
                    <textarea data-idx="${i}" class="edit-text">${b.text}</textarea>
                </div>
            `)
            .join("");

        epEditor.classList.add("active");
        epActions.classList.add("active");

        epMeta.innerHTML = `
            <div><strong>Episode ID:</strong> ${data.episode_id}</div>
            <div><strong>Mode:</strong> ${data.mode}</div>
            <div><strong>Estimated Runtime:</strong> ${(data.estimated_runtime_sec/60).toFixed(2)} min</div>
        `;
        epMeta.classList.add("active");
    });

    document.getElementById("episodeApproveBtn")
        .addEventListener("click", async () => {
            if (!lastEpisode) return;

            const edits = [...document.querySelectorAll(".edit-text")]
                .map(el => el.value);

            const r = await fetch("/api/studio/episode/approve", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    episode_id: lastEpisode.episode_id,
                    edits
                })
            });

            const data = await r.json();
            alert(data.ok ? "Approved." : "Failed.");
        });

    document.getElementById("episodeRenderBtn")
        .addEventListener("click", async () => {
            if (!lastEpisode) return;

            const r = await fetch("/api/studio/episode/render", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ episode_id: lastEpisode.episode_id })
            });

            const data = await r.json();
            alert(data.ok ? "Render started." : "Render failed.");
        });

});
