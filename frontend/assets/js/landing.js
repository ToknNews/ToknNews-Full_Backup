//
// TOKN LANDING PAGE — Particles + Multi-User Login Modal
//

document.addEventListener("DOMContentLoaded", () => {
    // ============================================================
    // TOKN FLOATING PARTICLE ENGINE (Homepage Variant)
    // ============================================================
    const container = document.getElementById("particle-layer");
    if (!container) return;

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

    setInterval(spawnParticle, 240);
});


//
// ELEMENT REFERENCES
//
const loginModal = document.getElementById("studioLoginModal");
const studioLoginBtn = document.getElementById("studioLoginBtn");
const enterSystemBtn = document.getElementById("enterSystemBtn");

const closeLogin = document.getElementById("closeLogin");

//
// LOGIN INPUTS
//
const loginUserInput = document.getElementById("studioUser");
const loginPasswordInput = document.getElementById("studioPassword");
const loginTotpInput = document.getElementById("studioTotp");
const loginSubmit = document.getElementById("studioLoginSubmit");
const loginError = document.getElementById("studioLoginError");


//
// LOGIN MODAL BEHAVIOR
//
function openLoginModal() {
    loginError.textContent = "";
    loginModal.classList.remove("hidden");
}

function closeLoginModal() {
    loginModal.classList.add("hidden");
}

closeLogin?.addEventListener("click", closeLoginModal);


//
// SECRET LOGIN BUTTON → OPEN MODAL
//
studioLoginBtn?.addEventListener("click", () => {
    openLoginModal();
});


//
// CORRECT "ENTER SYSTEM" BUTTON
//
enterSystemBtn?.addEventListener("click", () => {
    window.location.href = "/system.html";
});


//
// MULTI-USER LOGIN SUBMISSION
//
loginSubmit?.addEventListener("click", async () => {
    loginError.textContent = "";

    const username = loginUserInput.value.trim();
    const pw = loginPasswordInput.value.trim();
    const token = loginTotpInput.value.trim();

    if (!username || !pw || !token) {
        loginError.textContent = "Missing username, password, or code.";
        return;
    }

    try {
        const res = await fetch("/api/studio/login", {
            method: "POST",
            headers: { "Content-Type":"application/json" },
            body: JSON.stringify({
                username,
                password: pw,
                token
            })
        });

        const data = await res.json();

        if (!data.ok) {
            loginError.textContent = data.error?.message || "Login failed.";
            return;
        }

        // SUCCESS → redirect cleanly
        window.location.replace("/studio.html");

    } catch (err) {
        loginError.textContent = "Network error — try again.";
    }
});
