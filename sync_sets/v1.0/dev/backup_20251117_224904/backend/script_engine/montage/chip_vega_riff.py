# chip_vega_riff.py

def build_chip_vega_riff():
    """
    Quick conversational riff between Chip and Vega after a reset.
    Light banter: weekend plans, vibe checks, quick humor.
    """
    return [
        {
            "speaker": "Chip Blue",
            "role": "lead_anchor",
            "type": "reset_riff_chip",
            "line": "Vega, that reset took the wind out of my sails — how’s the vibe on your end?"
        },
        {
            "speaker": "Vega Watt",
            "role": "vibe_booth",
            "type": "reset_riff_vega",
            "line": "Vibe’s solid, Chip. Been a wild week though — you get into anything good over the weekend?"
        },
        {
            "speaker": "Chip Blue",
            "role": "lead_anchor",
            "type": "reset_riff_chip_reply",
            "line": "Mostly charts and too much coffee. You know how it goes."
        }
    ]
