TRANSFER_BRAIN_V2.md

ToknNews — System Transfer, Canon, and Forward Roadmap

Last updated: Dec 2025

0. Purpose of This Document (Read This First)

This document exists so that:

A new ChatGPT chat can immediately understand ToknNews

No modules are re-invented or broken accidentally

Deprecated work is not revived

Future development can proceed without re-explaining the system

This document is split into two halves:

CURRENT SYSTEM (FACTUAL, LIVE)

FUTURE ROADMAP (PLANNED, NOT YET LIVE)

Do not mix these mentally.

PART I — CURRENT SYSTEM (LIVE & CANONICAL)
1. Server & Runtime Environment

OS: Ubuntu Linux

Python: 3.10.12

Project Root:

/opt/toknnews


Environment Variables:

/opt/toknnews/.env


Secrets Loader:

backend/runtime/vault_loader.py

2. High-Level System Flow (What Actually Runs)
External Sources
→ Story Lake (raw, normalized)
→ Semantic Extraction
→ Semantic + GPT Clustering
→ Narrative Briefs
→ Dialogue Generation
→ Timeline Assembly
→ TTS / Render


Every arrow corresponds to a file written to disk.

3. Canonical Data Artifacts (Disk Contracts)

These files define module boundaries.

3.1 Story Lake (Raw Truth)
/opt/toknnews/data/stories/story_lake.json


One entry per story

Fields:

headline

summary

domain

source

semantic_keys (if extracted)

❌ No clustering

❌ No dedupe

✅ This is the input universe

3.2 Story Clusters (Event Grouping)
/opt/toknnews/data/stories/story_clusters.json
/opt/toknnews/data/stories/story_refined_clusters.json


Each cluster = one real-world event

Single-story clusters are valid

GPT is used only to confirm same-event, not theme similarity

3.3 Narrative Briefs (Editorial Layer)
/opt/toknnews/data/stories/narrative_briefs.json


Each brief contains:

narrative_id

domain

anchors

thesis

context (what / why / what’s missing)

conflict_points

memory_hooks

recommended_runtime_sec

source_count

This is the handoff point to dialogue.

3.4 Dialogue Blocks (Conversational Units)
/opt/toknnews/data/stories/dialogue_blocks.json


Turn-by-turn anchor dialogue

Chip appears in every block

Other anchors are domain-based

Runtime is estimated here

3.5 Episode Timeline (Final Show)
/opt/toknnews/data/episodes/episode_timeline.json


Fully ordered show

Includes:

Vega opening

Chip intro

Transitions

Dialogue segments

Outro

Runtime capped (currently 10 minutes)

4. Ingestion System (LIVE)
4.1 Ingestion Entry Point
backend/rest/routes/ingest_v2/ingest_controller.py


This is the only supported ingestion entry.

Responsibilities:

Calls RSS + API fetchers

Normalizes stories

Enriches (domain, sentiment, metadata)

Writes to story_lake.json

4.2 RSS Sources (Primary, Stable)
backend/rest/routes/ingest_v2/sources_rss.py


Includes:

CoinDesk

CoinTelegraph

CryptoSlate

CryptoPanic RSS (free tier)

RSS is favored for stability and cost control.

4.3 API Sources (Modular, Optional)
backend/rest/routes/ingest_v2/api_fetchers.py
backend/rest/routes/ingest_v2/sources_api.py


Includes:

CryptoPanic API

MarketAux

NewsData.io

CoinGecko (trending only)

Moralis (on-chain signals)

Etherscan (v2)

Solscan (limited)

Each source:

Can fail independently

Must never crash ingestion

5. Semantic Extraction (LIVE)
backend/script_engine/editorial/semantic_extractor.py


Produces semantic_keys:

domain

assets

event_type

actors

time_scope

confidence

Runs before clustering.

6. Clustering System (LIVE)
6.1 Clustering Engine
backend/script_engine/editorial/clustering_engine.py


Two-pass strategy:

Semantic / TF-IDF similarity

GPT same-event confirmation

❗ GPT does not collapse themes — only identical events.

6.2 Clustering Runner
backend/script_engine/editorial/run_semantic_clustering.py


Input:

story_lake.json


Output:

story_refined_clusters.json

7. Narrative Synthesis (LIVE)
backend/script_engine/editorial/narrative_synthesizer.py


Consumes:

story_refined_clusters.json


Produces:

narrative_briefs.json


This is where editorial intelligence lives.

8. Dialogue Generation (LIVE)
backend/script_engine/editorial/dialogue_generator.py


Consumes:

narrative_briefs.json


Produces:

dialogue_blocks.json


Rules:

Chip participates in every segment

Turn count scales by importance

Anchors reference each other by name

Persona tone is enforced here

9. Timeline Assembly (LIVE)
backend/script_engine/editorial/timeline_builder_v6.py


Responsibilities:

Domain quotas

Runtime cap (10 minutes)

Vega opening (booth voice only)

Chip transitions

TTS sanitization

10. CANONICAL ANCHOR SYSTEM (SOURCE OF TRUTH)
10.1 Where Anchors Are Defined

Canonical source (do not duplicate):

backend/script_engine/persona/


Key files:

persona_router.py

pd_engine_v45.py

pd_rules_v4.py

voice_map.json

Any new chat should inspect these files first.

10.2 Full Canonical Anchor List (As of Now)
PRIMARY / ACTIVE

Chip

Role: Lead anchor, show control

Appears in every segment

Handles transitions, framing, callbacks

Bond

Role: Macro, rates, regulation

Reef

Role: DeFi, protocols, on-chain activity

SECONDARY / LIMITED

Bitsy

Role: Culture, memes, humor, community

Used sparingly to avoid tonal dilution

Vega

Role: Booth / splash voice ONLY

Opens show with:

“Welcome to Token News.”

❌ Never analyzes news

❌ Never breaks stories

FUTURE / PARKED (Not Active)

Cash

Ledger

Neura

Ivy

Penny

These exist in persona memory but are not currently in rotation.

PART II — FUTURE ROADMAP (PLANNED)
11. GPT-Native Ingestion (Planned)

Goal:

Reduce dependence on paid APIs

Use GPT to:

Discover fresh headlines

Generate synthetic multi-source coverage

Feed results into Story Lake

This will coexist with RSS, not replace it initially.

12. Transfer Brain (Next Phase)

Create:

/opt/toknnews/docs/TRANSFER_BRAIN_V3.md


Purpose:

Allow stateless AI handoff

Encode editorial rules, non-goals, persona constraints

13. Memory & Continuity (Planned)

SQLite + vector memory

Questions answered:

“Have we covered this before?”

“Is this a sequel or contradiction?”

Memory hooks already exist in briefs

14. Phrase Variation Engine (Planned)

Goal:

Eliminate repetition (“Exactly, Chip”)

Introduce controlled linguistic diversity

Applied post-dialogue, pre-timeline

15. Show-Flow Intelligence (Planned)

Chip previews upcoming segments

Callbacks to earlier discussions

Dynamic pacing based on runtime pressure

16. Long-Term Scale Plan

Two-tier GPT usage:

Cheap models for clustering / scoring

Premium models for narrative synthesis

Importance-based token allocation

Event-level caching

17. How to Resume in a New Chat

Paste this document

Say:

“We are continuing from TRANSFER_BRAIN_V2.”

Specify:

Module name

File path

Desired change

No re-architecture required.

END OF TRANSFER_BRAIN_V2
