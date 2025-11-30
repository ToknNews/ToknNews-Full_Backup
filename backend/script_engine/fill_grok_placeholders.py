#!/usr/bin/env python3
import json
import sys
from loguru import logger
from script_engine.grok_client import grok_complete

def load_blocks(path):
    with open(path) as f:
        return json.load(f)

def save_blocks(path, blocks):
    with open(path, "w") as f:
        json.dump(blocks, f, indent=2, ensure_ascii=False)
    logger.success(f"Filled blocks saved → {path}")

def fill_block(block):
    text = block["text"]
    if "Grok would have said this" not in text and "punchy" not in text.lower():
        return text  # nothing to fill

    prompt = (
        "You are writing a sharp, professional crypto news broadcast line for Token News.\n"
        "Style: confident, concise, institutional tone. No hype. 12–22 words max.\n"
        "Never mention Grok, AI, or that you're filling a placeholder.\n\n"
        f"Original instruction: {text}\n"
        "Write exactly one broadcast line:"
    )
    
    response = grok_complete([{"role": "user", "content": prompt}], temperature=0.6)
    cleaned = response.strip().strip('"\'')
    logger.info(f"Grok fill: {text[:50]}... → {cleaned}")
    return cleaned

def main(path):
    blocks = load_blocks(path)
    changed = False
    for b in blocks:
        if "text" in b:
            old = b["text"]
            new = fill_block(b)
            if new != old:
                b["text"] = new
                changed = True
    
    if changed:
        save_blocks(path, blocks)
    else:
        logger.info("No placeholders found — nothing to fill")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: fill_grok_placeholders.py <blocks.json>")
        sys.exit(1)
    main(sys.argv[1])
