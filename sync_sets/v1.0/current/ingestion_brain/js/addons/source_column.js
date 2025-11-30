// =============================
// TOKNNews Dashboard Addon v0.5
// Adds Source column, newest-first sort, and max 50-row limit
// =============================

document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.getElementById("scene-tbody");
  if (!tableBody) {
    console.warn("[Dashboard] scene-tbody not found.");
    return;
  }

  // Fetch the existing scenes.json data
  fetch("/data/scenes.json")
    .then(res => res.json())
    .then(data => {
      let scenes = data.scenes || [];

      // Sort by timestamp (newest first)
      scenes.sort((a, b) => new Date(b.time || b.timestamp) - new Date(a.time || a.timestamp));

      // Cap to 100 latest scenes
      scenes = scenes.slice(0, 100);

      // Inject the new Source column header dynamically if not already there
      const headerRow = document.querySelector("table thead tr");
      if (headerRow && !headerRow.querySelector("th.source-col")) {
        const sourceHeader = document.createElement("th");
        sourceHeader.textContent = "Source";
        sourceHeader.classList.add("source-col");
        headerRow.appendChild(sourceHeader);
      }

      // Clear existing table body
      tableBody.innerHTML = "";

      // Populate the rows (tight, no links)
      tableBody.innerHTML = "";
      scenes.forEach(scene => {
        const row = document.createElement("tr");

        const time = scene.local_time || scene.time || scene.timestamp || "—";
        const char = scene.character || "Chip";
        const topic = scene.topic || scene.headline || "-";
        const runtime = scene.runtime || scene.runtime_s || "—";
        const source = scene.source || "—";

        row.innerHTML = `
          <td>${time}</td>
          <td>${char}</td>
          <td>${topic}</td>
          <td>${runtime}</td>
          <td>${source}</td>
        `;

        tableBody.appendChild(row);
      });

      console.log(`[Dashboard] ✅ Loaded ${scenes.length} scenes (newest first).`);
    })
    .catch(err => console.error("[Dashboard] ❌ Failed to load scenes.json", err));
});
