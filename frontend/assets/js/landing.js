document.addEventListener("DOMContentLoaded", () => {

    // PARTICLE ENGINE (same as before)
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

    // MAIN CTA → system console
    const systemBtn = document.getElementById("enterSystemBtn");
    systemBtn.addEventListener("click", () => {
        window.location.href = "/system.html";
    });

    // CONTROL STUDIO LOGIN (TOTP)
    const loginBtn   = document.getElementById("studioLoginBtn");
    const modal      = document.getElementById("studioLoginModal");
    const closeBtn   = document.querySelector(".studio-close");
    const codeInput  = document.getElementById("studioKey");
    const submitBtn  = document.getElementById("studioSubmit");

    function openModal() {
        modal.classList.remove("hidden");
        codeInput.value = "";
        codeInput.focus();
    }

    function closeModal() {
        modal.classList.add("hidden");
    }

    loginBtn.addEventListener("click", openModal);
    closeBtn.addEventListener("click", closeModal);

    submitBtn.addEventListener("click", async () => {
        const code = codeInput.value.trim();
        if (!code) {
            alert("Enter your 6-digit code.");
            return;
        }

        try {
            const res = await fetch("/api/studio/totp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code })
            });

            if (!res.ok) {
                alert("Invalid or expired code.");
                return;
            }

            const data = await res.json();
            if (data.ok) {
                // TODO: change to your real studio URL
                window.location.href = "/control-studio.html";
            } else {
                alert("Invalid or expired code.");
            }
        } catch (e) {
            console.error("TOTP error", e);
            alert("Error verifying code.");
        }
    });
});
