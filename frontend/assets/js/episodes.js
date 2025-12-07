/* Floating particles */
function spawnParticle() {
    const layer = document.getElementById("particle-layer");
    const p = document.createElement("div");
    p.classList.add("particle");

    const size = Math.random() * 3 + 2;
    const left = Math.random() * 100;

    p.style.width = `${size}px`;
    p.style.height = `${size}px`;
    p.style.left = `${left}vw`;
    p.style.opacity = Math.random() * 0.8 + 0.2;

    layer.appendChild(p);

    const floatTime = Math.random() * 6 + 6;

    p.animate(
        [
            { transform: "translateY(40vh)" },
            { transform: "translateY(-60vh)" }
        ],
        {
            duration: floatTime * 1000,
            easing: "ease-out",
        }
    );

    setTimeout(() => p.remove(), floatTime * 1000);
}

setInterval(spawnParticle, 140);

/* Load Episodes */
document.addEventListener("DOMContentLoaded", () => {
    const grid = document.getElementById("episodesGrid");

    fetch("/api/admin/episodes")
        .then(r => r.json())
        .then(data => {
            grid.innerHTML = "";

            if (!Array.isArray(data) || data.length === 0) {
                grid.innerHTML = "<p>No episodes generated yet.</p>";
                return;
            }

            data.reverse().forEach(ep => {
                const card = document.createElement("div");
                card.className = "episode-card";

                const videoUrl = `/episodes/${ep.episode_id}.mp4`; // Adjust if needed

                card.innerHTML = `
                    <video controls>
                        <source src="${videoUrl}" type="video/mp4">
                    </video>

                    <div class="episode-title">Episode ${ep.episode_id}</div>
                    <div class="episode-meta">
                        ${ep.story_count} stories • Runtime: ${Math.round(ep.runtime)}s
                    </div>
                `;

                grid.appendChild(card);
            });
        })
        .catch(err => {
            grid.innerHTML = "<p>Error loading episodes.</p>";
            console.error(err);
        });
});
