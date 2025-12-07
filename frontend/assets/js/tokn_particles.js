/* ===========================================================
   Tokn Universal Particle Engine
   Used on: landing, system console, episodes
   Author: Tokn Autonomous Broadcast Core
=========================================================== */

export function initToknParticles(layerId = "particle-layer") {
    const layer = document.getElementById(layerId);
    if (!layer) return;

    const spawnInterval = 110; // ms

    function spawnParticle() {
        const p = document.createElement("div");
        p.classList.add("tokn-particle");

        // Random size + opacity + drift layer
        const size = Math.random() * 4 + 2;
        const opacity = Math.random() * 0.55 + 0.25;
        const left = Math.random() * 100;

        // Depth simulation (background particles move slower)
        const depth = Math.random(); // 0 = far, 1 = near
        const driftSpeed = 14 + depth * 10; // slower for far particles

        p.style.width = `${size}px`;
        p.style.height = `${size}px`;
        p.style.left = `${left}vw`;
        p.style.opacity = opacity;
        p.style.filter = `drop-shadow(0 0 ${4 + depth * 10}px rgba(0,150,255,0.8))`;

        layer.appendChild(p);

        const startY = 120;  // off bottom
        const endY = -40;    // float past top

        p.animate(
            [
                { transform: `translateY(${startY}vh) translateX(0px)` },
                {
                    transform: `translateY(${endY}vh) translateX(${Math.random() * 30 - 15}px)`
                }
            ],
            {
                duration: driftSpeed * 1000,
                easing: "ease-out",
                fill: "forwards"
            }
        );

        setTimeout(() => p.remove(), driftSpeed * 1000);
    }

    setInterval(spawnParticle, spawnInterval);
}
