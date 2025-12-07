document.addEventListener("DOMContentLoaded", () => {
    const particleLayer = document.getElementById("particle-layer");

    // --- Floating particles ---
    function spawnParticle() {
        const p = document.createElement("div");
        p.classList.add("particle");

        const size = Math.random() * 4 + 2;
        p.style.width = `${size}px`;
        p.style.height = `${size}px`;
        p.style.left = `${Math.random() * 100}vw`;
        p.style.animationDuration = `${4 + Math.random() * 4}s`;

        particleLayer.appendChild(p);
        setTimeout(() => p.remove(), 8000);
    }
    setInterval(spawnParticle, 160);

    // --- Login Modal ---
    const loginBtn = document.getElementById("loginBtn");
    const modal = document.getElementById("studioLoginModal");
    const closeBtn = document.getElementById("closeLogin");
    const submitBtn = document.getElementById("studioLoginSubmit");

    loginBtn.addEventListener("click", () => {
        modal.classList.add("open");
    });

    closeBtn.addEventListener("click", () => {
        modal.classList.remove("open");
    });

    submitBtn.addEventListener("click", async () => {
        const pw = document.getElementById("studioPassword").value;
        const code = document.getElementById("studioTOTP").value;

        const res = await fetch("/api/studio/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password: pw, token: code })
        });

        const data = await res.json();

        if (!data.ok) {
            alert("Login failed: " + data.error);
            return;
        }

        alert("Access granted!");
        modal.classList.remove("open");
        window.location.href = "/system.html";
    });
});
