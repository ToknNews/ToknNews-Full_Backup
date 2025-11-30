/* ToknNews — scenes_index.js
   Provides a helper to compute daily scene counts from an array of scenes.
   Safe: no DOM writes, no network writes, just a pure function.
*/
function computeDailyCounts(scenes) {
  if (!Array.isArray(scenes)) return [];
  const map = {};

  for (const s of scenes) {
    if (!s || !s.time) continue;

    let day;
    const t = String(s.time);

    // Handle formats like "2025-10-27T12:06:00Z" or "10/27 12:06"
    if (t.includes('T')) {
      day = t.split('T')[0]; // → 2025-10-27
    } else if (t.includes(' ')) {
      day = t.split(' ')[0]; // → 10/27
    } else {
      day = t; // fallback
    }

    map[day] = (map[day] || 0) + 1;
  }

  // return sorted by date ascending
  return Object.keys(map)
    .sort((a, b) => new Date(a) - new Date(b))
    .map(d => ({ date: d, count: map[d] }));
}
