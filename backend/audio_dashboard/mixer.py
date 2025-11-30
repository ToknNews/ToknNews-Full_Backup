from pydub import AudioSegment
import os

def mix_scene(scene_id, block_paths):
    """
    Concatenates all rendered audio files (block_paths) into one final MP3.
    Returns the final mixed file path.
    """

    if not block_paths:
        print("[Mixer] ERROR: No block_paths provided to mixer.")
        return None

    try:
        final = AudioSegment.empty()

        for path in block_paths:
            if not os.path.exists(path):
                print(f"[Mixer] WARNING: Missing audio block: {path}")
                continue

            segment = AudioSegment.from_file(path)
            final += segment

        # Output filename
        out_dir = "mixed_scenes"
        os.makedirs(out_dir, exist_ok=True)

        out_path = os.path.join(out_dir, f"scene_{scene_id}_final.mp3")
        final.export(out_path, format="mp3")

        return out_path

    except Exception as e:
        print(f"[Mixer] ERROR mixing scene: {e}")
        return None
