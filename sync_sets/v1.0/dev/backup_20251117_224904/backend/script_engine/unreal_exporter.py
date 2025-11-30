#!/usr/bin/env python3
"""
TOKNNews — Unreal Export Bridge (Module C-9)
Creates a standardized export JSON for Unreal Engine.
"""

import os, json, time

EXPORT_PATH = "/var/www/toknnews/data/unreal_export.json"

def export_unreal_package(scene_dict):
    """
    scene_dict = output from script_engine_v3.generate_script()
    Writes Unreal-ready JSON to EXPORT_PATH.
    """
    try:
        package = {
            "generated_at": time.time(),
            "scene_id": scene_dict.get("unreal", {}).get("scene_id"),
            "headline": scene_dict.get("headline"),
            "segment_type": scene_dict.get("segment_type"),
            "camera_plan": scene_dict.get("unreal", {}).get("camera_plan"),
            "shot_plan": scene_dict.get("unreal", {}).get("shot_plan", []),
            "characters": scene_dict.get("unreal", {}).get("characters", []),
            "duration_seconds": scene_dict.get("unreal", {}).get("duration_seconds"),
            "audio_tracks": scene_dict.get("unreal", {}).get("audio_tracks", []),
            "timeline": scene_dict.get("timeline", []),
            "audio_file": scene_dict.get("audio_file")

        }

        tmp = EXPORT_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(package, f, indent=2)
        os.replace(tmp, EXPORT_PATH)

        print(f"[UnrealExport] ✔ Exported → {EXPORT_PATH}")
    except Exception as e:
        print(f"[UnrealExport] ❌ Error: {e}")
