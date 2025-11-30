# backend/script_engine/timeline_blocks/vega_pad_block.py

def build_vega_pad_block(hijinx_line: str) -> dict:
    """
    Returns a timeline block for a Vega vibe segment.
    This gets inserted whenever PD emits 'vega_pad'.
    """

    return {
        "type": "vega_pad",
        "speaker": "Vega Watt",
        "style": "energetic",
        "content": hijinx_line,
        "audio_role": "booth",
        "camera": "studio-wide",
        "duration_estimate": 4
    }
