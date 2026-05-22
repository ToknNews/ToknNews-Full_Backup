# ToknNews-Full_Backup

This repository contains the **complete operational codebase** for the **ToknNews** autonomous AI-driven crypto broadcast system.

## 📁 Repository Overview

### Core Systems
- **`backend/`** — Main application logic, ingestion, and services
- **`script_engine/`** — Editorial synthesis, persona director (PD), timeline builder, and dialogue generation
- **`runtime/`** — Grok client, API wrappers, and core utilities
- **`editorial/`** — Content processing and synthesis modules
- **`signal_engine/`** — Trading intelligence and signal generation (integrated from ToknClaw)

### Key Features
- Autonomous news ingestion (RSS, Marketaux, on-chain, X sentiment)
- Multi-persona broadcast engine (Chip, Ledger, Bond, Reef, Lawson, Bitsy, etc.)
- TTS-safe promo and segment generation
- Trading signal engine with strategy families and explainability
- Grok + OpenAI hybrid chaining
- Modular pipeline architecture

## Tech Stack
- Python 3
- Grok API (xAI)
- OpenAI (for refinement)
- Moralis / Chainstack (on-chain)
- Marketaux, RSS feeds
- SQLite + JSON persistence

## Purpose of This Repo
- Full disaster recovery backup
- Version control and auditing
- Development reference
- Server migration / rebuild capability

---

**Last Updated:** $(date '+%Y-%m-%d %H:%M UTC')

**Note:** This is a backup repository. Do not commit real `.env` files or secrets.

