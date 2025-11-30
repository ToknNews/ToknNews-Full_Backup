#!/usr/bin/env python3
"""
ToknNews LIVE — Unified Compiler (v3 Final Integration)
Connects ingestion → script_engine_v3 → audio → Unreal exporter.
"""

import os, sys, json, time

# Set module root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# --- Imports from v3 engine ----
from script_engine.script_engine_v3 import generate_script
from script_engine.unreal_exporter import export_unreal_package

def compile_scene(headline: str, article_context: str = "", cluster_articles=None):
    if cluster_articles is None:
        cluster_articles = []

    # Generate the full v3 script package
    scene = generate_script(
        headline=headline,
        article_context=article_context,
        cluster_articles=cluster_articles,
        character="chip"
    )

    # Export Unreal metadata
    export_unreal_package(scene)

    return scene

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--headline", required=True)
    parser.add_argument("--context", default="")
    args = parser.parse_args()

    out = compile_scene(args.headline, args.context)
    print("[LIVE Compiler] ✔ Scene compiled:", args.headline)
