/* Shared particles */
function spawnParticle() {
    const container = document.getElementById("particle-layer");
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

/* Fetch QR from backend */
fetch("/api/studio/qrcode")
    .then(r => r.json())
    .then(data => {
        document.getElementById("qrImage").src = data.qr;
    })
    .catch(err => {
        console.error("QR load failed:", err);
    });
