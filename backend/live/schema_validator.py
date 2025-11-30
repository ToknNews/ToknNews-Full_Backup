#!/usr/bin/env python3
"""
TOKNNews Schema Validator
Ensures scene_block_schema.json exists and is structurally valid.
If missing or invalid, rebuilds it automatically.
"""

import os, json

SCHEMA_PATH = "/var/www/toknnews/data/scene_block_schema.json"

FALLBACK_SCHEMA = {
    "schema_version": "1.0",
    "block_structure": {
        "framing": {
            "duration": 0.01,
            "description": "Studio framing: medium-wide shot of Chip behind the ToknNews desk. Camera steady, broadcast lighting."
        },
        "dialogue": {
            "duration": 14.9,
            "description": "Main scene dialogue lines. 3–5 sentences with dynamic verbs, gestures, and tone variation."
        },
        "segue": {
            "duration": 10.0,
            "description": "Scene wrap-up with emotional handoff, gesture, and contextual segue to next story."
        }
    }
}

REQUIRED_KEYS = ["schema_version", "block_structure"]

def validate_schema() -> dict:
    """Checks schema integrity; rebuilds if missing or malformed."""
    if not os.path.exists(SCHEMA_PATH):
        print("[Schema] Missing schema file — rebuilding from fallback.")
        with open(SCHEMA_PATH, "w") as f:
            json.dump(FALLBACK_SCHEMA, f, indent=2)
        return FALLBACK_SCHEMA

    try:
        with open(SCHEMA_PATH, "r") as f:
            schema = json.load(f)
        if not all(k in schema for k in REQUIRED_KEYS):
            raise ValueError("Missing top-level keys")
        bs = schema.get("block_structure", {})
        for block in ["framing", "dialogue", "segue"]:
            if block not in bs:
                raise ValueError(f"Missing block: {block}")
        print("[Schema] ✅ Schema validated.")
        return schema
    except Exception as e:
        print(f"[Schema] Invalid or corrupt file: {e} — rebuilding fallback.")
        with open(SCHEMA_PATH, "w") as f:
            json.dump(FALLBACK_SCHEMA, f, indent=2)
        return FALLBACK_SCHEMA

if __name__ == "__main__":
    validate_schema()
