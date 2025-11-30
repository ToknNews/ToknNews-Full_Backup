# backend/script_engine/timeline_blocks/bitsy_meta_block.py

def build_bitsy_meta_block(line: str) -> dict:
    """
    Returns a Bitsy meta-moment block for the timeline.
    Light, observational, not full comedy.
    """

    return {
        "type": "bitsy_meta",
        "speaker": "Bitsy Gold",
        "style": "meta",
        "content": line,
        "camera": "cutaway",
        "audio_role": "commentary",
        "duration_estimate": 3
    }
