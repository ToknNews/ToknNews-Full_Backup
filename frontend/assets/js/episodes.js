/* ============================================================
   TOKN EPISODES — REAL DATA + SLIDE-UP PLAYER (NO AUDIO YET)
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

    const grid   = document.getElementById("episodesGrid");
    const player = document.getElementById("epPlayer");
    const closeBtn = document.getElementById("epClose");

    const title = document.getElementById("epPlayerTitle");
    const info  = document.getElementById("epPlayerInfo");
    const art   = document.getElementById("epPlayerArt");

    /* ------------------------------------------------------------
       LOAD EPISODES (REAL DATA)
       ------------------------------------------------------------ */
    async function loadEpisodes() {
        grid.innerHTML = "Loading episodes…";

        try {
            const r = await fetch("/api/studio/episodes/history");
            const data = await r.json();

            if (!data.ok) {
                grid.innerHTML = "Failed to load episodes.";
                return;
            }

            // 🔑 Reverse chronological (newest first)
            const episodes = data.episodes
                .sort((a, b) => b.timestamp - a.timestamp);

            grid.innerHTML = episodes.map(ep => `
                <div class="episode-card"
                     data-id="${ep.episode_id}"
                     data-runtime="${ep.runtime_sec}"
                     data-mode="${ep.mode}"
                     data-ts="${ep.timestamp}">

                    <img
                        src="/frontend/assets/img/YT_Banner_Tokn.jpg"
                        class="episode-thumb"
                    />

                    <div class="episode-meta">
                        <h3 class="episode-title">${ep.episode_id}</h3>
                        <div class="episode-info">
                            ${new Date(ep.timestamp * 1000).toLocaleString()}
                            • ${ep.mode}
                        </div>
                    </div>
                </div>
            `).join("");

        } catch (err) {
            grid.innerHTML = "Error loading episodes.";
            console.error(err);
        }
    }

    /* ------------------------------------------------------------
       OPEN SLIDE-UP PLAYER (UI ONLY)
       ------------------------------------------------------------ */
    grid.addEventListener("click", e => {
        const card = e.target.closest(".episode-card");
        if (!card) return;

        const epId = card.dataset.id;
        const mode = card.dataset.mode;
        const runtime = Math.round(card.dataset.runtime);

        title.textContent = epId;
        info.textContent  = `${mode} • ${runtime}s • Audio playback coming soon`;
        art.src = "/frontend/assets/img/YT_Banner_Tokn.jpg";

        player.classList.remove("hidden");
    });

    /* ------------------------------------------------------------
       CLOSE PLAYER
       ------------------------------------------------------------ */
    closeBtn.addEventListener("click", () => {
        player.classList.add("hidden");
    });

    /* ------------------------------------------------------------
       INIT
       ------------------------------------------------------------ */
    loadEpisodes();

});
