/* ------------------------------------------------------
      TOKN GLOBAL AESTHETIC FRAMEWORK — JS
   ------------------------------------------------------ */

document.addEventListener("DOMContentLoaded", () => {

    // ---------------------------------------------
    // GLOBAL PARTICLES (identical to landing page)
    // ---------------------------------------------
    const layer = document.getElementById("particle-layer");

    function spawnParticle() {
        if (!layer) return;

        const p = document.createElement("div");
        p.classList.add("particle");

        const size = Math.random() * 4 + 2;
        const left = Math.random() * 100;
        const duration = Math.random() * 4 + 4;

        p.style.width = `${size}px`;
        p.style.height = `${size}px`;
        p.style.left = `${left}vw`;
        p.style.animationDuration = `${duration}s`;

        layer.appendChild(p);
        setTimeout(() => p.remove(), duration * 1000);
    }

    setInterval(spawnParticle, 160);
});


/* ------------------------------------------------------
   REUSABLE OPEN/CLOSE PANEL HANDLER
------------------------------------------------------ */
function toknBindPanel(openBtnId, panelId, closeBtnId) {
    document.addEventListener("DOMContentLoaded", () => {
        const openBtn = document.getElementById(openBtnId);
        const panel = document.getElementById(panelId);
        const closeBtn = document.getElementById(closeBtnId);

        if (!openBtn || !panel) return;

        openBtn.addEventListener("click", () => panel.classList.add("open"));
        if (closeBtn) closeBtn.addEventListener("click", () => panel.classList.remove("open"));
    });
}

