# ToknNews Addon Modules

Each script in this folder is an isolated enhancement for the main ToknNews dashboard.

## Usage
All addons are loaded via `<script src="/modules/js/addons/*.js" defer></script>` tags
added at the bottom of `/var/www/toknnews/dashboard.html`.

They must **never** modify the dashboard layout or core JavaScript.
Only read data (JSON files) or append new DOM sections below existing content.

## Naming Convention
- `*_index.js`  → Data aggregation / analytics hooks  
- `*_pulse.js`  → Visual effects or live status indicators  
- `*_overlay.js` → Investor demo overlays or metrics  

## Versioning
Each time you add or change an addon:
git add modules/js/addons/
git commit -m "Addon: <name> updated"
git push origin dev
