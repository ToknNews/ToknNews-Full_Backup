# TOKNNEWS TRANSFER BRAIN — FULL PROJECT SPEC (v1.0)

This file is the canonical, unified system description for ToknNews.
It overrides all previous instructions and governs all development activity.

---

## 0. PURPOSE

This document captures EVERYTHING required to develop ToknNews:

- Full architecture  
- Module responsibilities  
- Ingestion → enrichment → PD → grok_writer → timeline → episode  
- Anchor cast + persona rules  
- Cleanup plan  
- Future roadmap  
- Development rules  
- Canonical directories  
- Canonical GitHub branch (toknnews-episode-overhaul)  

This is the single source of truth for the system.

---

## 1. TOP-LEVEL PROJECT GOAL

ToknNews is an end-to-end autonomous crypto broadcast engine that:

1. Ingests news from RSS, APIs, social signals, and on-chain data  
2. Normalizes and enriches each item (domain, sentiment, summary, anchors)  
3. Scores and ranks stories  
4. Selects anchors using PD Engine v3  
5. Produces a multi-anchor conversation using grok_writer  
6. Assembles the episode via timeline_builder_v3  
7. Emits production-ready JSON blocks (optional audio render)

Output types:

- Short episode  
- Full multi-story rundown  
- Deep dive  
- Breaking news  
- Linear JSON blocks compatible with Unreal pipeline  

---

## 2. CANONICAL CODEBASE

Only the following directories contain real code:

```
/opt/toknnews
├── backend/
│   ├── rest/routes/ingest_v2/
│   ├── script_engine/
│   │   ├── persona/
│   │   ├── knowledge/
│   │   ├── episode_runner.py
│   │   ├── grok_writer.py
│   │   └── timeline_builder.py
│   └── runtime/
├── dev/
├── config/
├── docs/
├── frontend/
└── README.md
```

Everything else (logs, data, episodes, assets, temp, backup) is **not** source code.

---

## 3. INGESTION PIPELINE — INTENDED DESIGN

### Location
`backend/rest/routes/ingest_v2/`

### Flow

RAW SOURCES →  
normalize →  
enrich_item (GPT summary + domain + sentiment + anchors) →  
enrich_stage3 (optional signals) →  
aggregate_ingestion (dedupe + merge + ranking memory window) →  
`rolling_stories.json` (final output)

### Raw Sources

RSS:
- Cointelegraph  
- CoinDesk  
- The Block  
- Decrypt  
- CryptoPanic RSS extension  

APIs:
- MarketAux  
- NewsData  
- CryptoPanic JSON  
- Birdeye Solana token movers  
- Moralis whale & price  
- DexScreener trending  
- CoinGecko trending  
- Pump.fun trending  
- ETH RPC signals  

Desired (future):
- Reddit  
- X/Twitter  
- Coindesk paid API  
- Market Intel  
- Dune  

---

## 4. ENRICHMENT PIPELINE — INTENDED DESIGN

### Location
`backend/rest/routes/ingest_v2/enrich_v2.py`

### Output schema

```
{
  "headline": "...",
  "summary": "<GPT one-sentence neutral>",
  "domain": "macro/markets/defi/onchain/ai/culture/general",
  "sentiment": "Positive/Negative/Neutral",
  "importance": 5,
  "anchors": ["cash","bond"],
  "source": "RSS/API",
  "timestamp": <epoch>
}
```

### Domain Mapping

| domain     | anchor(s)       |
|------------|-----------------|
| macro      | bond            |
| markets    | cash, bond      |
| defi       | reef            |
| onchain    | ledger          |
| ai         | neura           |
| culture    | bitsy           |
| regulation | lawson          |
| general    | chip            |

### Notes
- Summary uses GPT-4o-mini  
- Sentiment uses regex  
- Domain uses dictionary  
- Importance boosted by volatility signals  

---

## 5. RANKING ENGINE

### Location
`backend/script_engine/knowledge/rank_stories.py`

### Ranking factors

- Domain weight  
- Sentiment weight  
- Recency decay  
- `importance * 2`  
- Breaking boost (<2h)  

Sorted descending.

---

## 6. PD ENGINE v3

Inputs:

- enriched stories  
- rank scores  
- anchor mapping  
- cast fatigue  
- breaking flags  
- story order  

Output per story:

```
{
  "primary_anchor": "...",
  "secondary_anchor": "... or None",
  "flags": {
     "breaking": true|false,
     "hot": true|false,
     "cold_start": true|false
  }
}
```

Rules:

- Primary comes from domain  
- Secondary from PD Engine  
- Secondary omitted for very hot stories  
- Cast fatigue rotates speakers  

---

## 7. TIMELINE BUILDER v3

### Location
`backend/script_engine/persona/timeline_builder.py`

### Output structure

- Chip intro  
- Rundown  
- For each story:
  - grok_writer conversation  
- Outro  

### Calls:
`write_block_conversation()` in grok_writer.py

### Block schema

```
{
  "speaker": "chip",
  "tag": "chip_intro",
  "text": "...",
  "timestamp": <ts>,
  "voice_id": "teAyVV..."
}
```

---

## 8. GROK_WRITER — LINGUISTIC ENGINE

### Location
`backend/script_engine/grok_writer.py`

Responsibilities:

- Multi-anchor conversation generation  
- Style overlays + mood engine  
- Conversational memory  
- Seed persona prompts  
- 4–6 line output per story  

Flow:

Chip → primary → secondary (optional) → Chip moderates.

---

## 9. EPISODE RUNNER

### Location
`backend/script_engine/episode_runner.py`

Steps:

1. Load rolling_stories.json  
2. PD Engine  
3. Timeline builder  
4. grok_writer conversations  
5. Export blocks JSON  
6. Save episode metadata  
7. (Optional) audio render  

---

## 10. KNOWN ISSUES

### Ingestion

- MarketAux missing  
- CryptoPanic JSON broken  
- NewsData throttled  
- Moralis deprecated endpoint  
- DexScreener TLS timeouts  
- RSS dominates API data  
- aggregator not consistently used  
- enrich_stage3 blocks on slow APIs  

### Conversation

- Chip-only bug appears intermittently  
- Secondary anchors missing  
- Anchor selection fallback too aggressive  
- Story Slices errors from feedparser  

### PD

- PD v3 not wired everywhere  
- Secondary assignment sometimes drops  
- Cast fatigue not consistent  
- Breaking logic not fully active  
- Domain misclassification  

---

## 11. CLEANUP PLAN

Delete:

### Directories:

```
backend/live/
backend/ai_export/
backend/sandbox/
backend/rest/routes/ingest/
backend/script_engine/persona/timeline_builder_old_bak.py
```

### Logs + episodes:

```
logs/*
data/episodes/*
data/blocks/*
data/logs/*
```

### Runtime DBs:

```
data/*.db
data/pd_state.json
```

### Backup files:

```
*~
*.bak
*.save
```

### Deprecated modules:

```
backend/live/*.py
backend/live/toknnews_coindesk_api.py
backend/live/multi_article_synthesizer.py
backend/live/hybrid_ingestor.py
```

---

## 12. FUTURE ROADMAP

### A. Ingestion

- Reddit  
- X/Twitter  
- Moralis v3  
- Dune  
- Coindesk premium  

### B. PD Engine v4

- Full cast balancing  
- Fatigue system  
- Dynamic episode formats  
- Sponsored ads  
- Hijinx/chaos mode  

### C. Episode formats

- Morning Brief  
- Breaking  
- Deep Dive  
- Chaos Friday  

### D. Dashboard

- Flag stories  
- Override anchors  
- Trigger modes  
- Sponsored insertion  

---

## 13. ANCHOR CAST — CANONICAL

| Name   | Role        | Voice ID |
|--------|-------------|----------|
| chip   | host        | teAyVV… |
| lawson | legal       | Wz0W8i… |
| reef   | defi        | 7pLXps… |
| bond   | macro       | ckPPrw… |
| cash   | markets     | b2zP5W… |
| ledger | onchain     | NZN55a… |
| neura  | ai          | U21zT7… |
| bitsy  | culture     | VOkhRo… |
| penny  | retail      | 7WqwVs… |
| rex    | memes       | 5Rbobt… |
| cap    | venture     | eeFsfJ… |
| vega   | booth       | Ax1HxH… |

Rules:

- Vega = booth only  
- Chip intros + outros always  
- Primary by domain  
- Secondary via PD unless domain heat is high  

---

## 14. DEVELOPMENT RULES

DO:

- Always use full-file replacements (cat)  
- Always show `cd`  
- Ensure PYTHONPATH includes `/opt/toknnews`  
- Regenerate block schemas  
- Test ingestion + script generation separately  

NEVER:

- Reference GitHub main  
- Re-introduce deprecated ingestion  
- Mix old ingestion logic  
- Modify without full replacement  
- Reinstate fallback writers  

---

## 15. CANONICAL BRANCH

**`toknnews-episode-overhaul`**  
ONLY branch.  
Everything else is obsolete.

---

## 16. TRANSFER BRAIN COMMANDMENT

Before modifying ANY file:

1. Check Transfer Brain  
2. Check GitHub branch version  
3. Check server file via cat  
4. Synthesize both  
5. Produce corrected file (full replacement)

If contradiction occurs:

- **Transfer Brain > GitHub**  
- **Server > GitHub**  

This document is binding.

---

✔ TRANSFER BRAIN v1.0 — END OF FILE ✔
