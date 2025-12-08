//
// PARTICLES — identical to system page
//
document.addEventListener("DOMContentLoaded", () => {
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
});


//
// ENTER SYSTEM — Works already, leaving unchanged
//
document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("enterSystemBtn");
    btn?.addEventListener("click", () => {
        window.location.href = "/system.html";
    });
});


//
// --- LOGIN MODAL LOGIC (Password + TOTP) ---
//
document.addEventListener("DOMContentLoaded", () => {
    const loginBtn  = document.getElementById("studioLoginBtn");
    const modal     = document.getElementById("studioLoginModal");
    const closeBtn  = document.getElementById("closeLogin");
    const submitBtn = document.getElementById("studioLoginSubmit");
    const errorBox  = document.getElementById("studioLoginError");

    if (!loginBtn || !modal || !closeBtn || !submitBtn) return;

    // OPEN
    loginBtn.addEventListener("click", () => {
        modal.classList.remove("hidden");
        modal.classList.add("open");
        errorBox.textContent = "";
    });

    // CLOSE
    closeBtn.addEventListener("click", () => {
        modal.classList.remove("open");
        modal.classList.add("hidden");
    });

    // SUBMIT LOGIN
    submitBtn.addEventListener("click", async () => {
        const password = document.getElementById("studioPassword").value.trim();
        const token    = document.getElementById("studioTotp").value.trim();

        if (!password || !token) {
            errorBox.textContent = "Enter both password and authentication code.";
            return;
        }

        try {
            const resp = await fetch("/api/studio/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ password, token })
            });

            const data = await resp.json();

            if (data.ok) {
                window.location.href = "/studio.html";
            } else {
                errorBox.textContent = data.error || "Login failed.";
            }
        } catch (err) {
            errorBox.textContent = "Network error — try again.";
        }
    });
});
