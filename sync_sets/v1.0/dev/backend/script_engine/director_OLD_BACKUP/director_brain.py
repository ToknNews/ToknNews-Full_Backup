# backend/script_engine/director/director_brain.py

from .director_logger import log_event
from .director_state import DirectorState
from .daypart_rules import get_daypart
from .pacing_model import compute_energy_level


class ProgrammingDirector:
    """
    Minimal version of the Programming Director.
    Later patches will add segment routing, breaking logic,
    ad engine, hijinx rules, memory engine, etc.
    """

    def __init__(self):
        self.state = DirectorState()

    def evaluate(self, story_queue, last_segment_result=None) -> str:
        """
        Stage 4:
        - breaking news check
        - ad opportunity
        - router logic
        """

        from .segment_router import route_next_segment
        from .ad_logic import should_run_ad
        from .breaking_logic import check_breaking_interrupt

        daypart = get_daypart()
        energy = compute_energy_level(self.state)

        # --- Compute Escalation Level ---
        from .breaking_logic import compute_escalation_level
        escalation = compute_escalation_level(
            story_queue=story_queue,
            state=self.state,
            daypart=daypart,
            energy=energy
        )

        # Suppress escalation temporarily after a reset
        if self.state.reset_suppression_cycles > 0:
            escalation = 0

        self.state.escalation_level = escalation

        # --- Breaking News always overrides ---
        breaking_story = check_breaking_interrupt(self.state)
        if breaking_story:
            log_event(
                event_type="breaking_interrupt",
                message="Breaking news detected — overriding segment flow",
                data={"headline": breaking_story.get("headline")},
                tone="breaking"
            )
            return "breaking"

        # --- Reset Check (should_reset_show + reset_allowed) ---
        from .breaking_logic import should_reset_show, reset_allowed
        from datetime import datetime

        # Track recent segment history
        if last_segment_result:
            self.state.segment_history.append(last_segment_result)

        # Initialize intro_time if missing
        if not hasattr(self.state, "last_intro_time"):
            self.state.last_intro_time = datetime.utcnow()

        # Combined reset condition
        if should_reset_show(self.state, story_queue) and reset_allowed(self.state):
            log_event(
                event_type="chip_reset_triggered",
                message="Chip Reset triggered by PD (timing + escalation + queue).",
                data={
                    "escalation": self.state.escalation_level,
                    "stories": len(story_queue),
                    "segment_history": self.state.segment_history[-5:],
                },
                tone=daypart
            )
            self.state.last_reset_time = datetime.utcnow()
            self.state.last_segment = "chip_reset"
            self.state.reset_suppression_cycles = 2   # suppress escalation for next 2 cycles
            return {"type": "chip_reset", "stories": story_queue}

        # --- Reset Trigger (requires escalation + cooldown) ---
        from datetime import datetime
        if reset_allowed(self.state):
            log_event(
                event_type="chip_reset_triggered",
                message="Escalation triggered a Chip Reset cycle.",
                data={"escalation": self.state.escalation_level},
                tone=daypart
            )
            self.state.last_reset_time = datetime.utcnow()
            return {"type": "chip_reset", "stories": story_queue}

        # --- Suppression counter (skip reset for next N cycles) ---
        if getattr(self.state, "reset_suppression_cycles", 0) > 0:
            self.state.reset_suppression_cycles -= 1
            # Prevent reset while suppression active
            if self.state.reset_suppression_cycles > 0:
                # Escalation should be ignored during suppression
                self.state.escalation_level = 0

        # --- Hijinx + Cast Fatigue (always compute unless breaking) ---
        from .hijinx_rules import determine_hijinx_level
        from .cast_fatigue import compute_cast_fatigue

        fatigue = compute_cast_fatigue(self.state.cast_usage)
        hijinx = determine_hijinx_level(daypart, sentiment=None, importance=None)

        log_event(
            event_type="behavior_modifiers",
            message=f"Hijinx={hijinx}, fatigue={fatigue}",
            data={"fatigue": fatigue, "hijinx": hijinx},
            tone=daypart
        )

        # --- Hijinx Probability ---
        from .hijinx_frequency import hijinx_probability
        hijinx_prob = hijinx_probability(daypart, sentiment=None, importance=None)

        log_event(
            event_type="hijinx_probability",
            message=f"Hijinx probability={hijinx_prob}",
            data={"probability": hijinx_prob},
            tone=daypart
        )

        # --- Decide whether to execute hijinx ---
        import random

        if random.random() < hijinx_prob:
            from .hijinx_engine import choose_hijinx_action

            hijinx_line = choose_hijinx_action(hijinx)

            if hijinx_line:
                log_event(
                    event_type="hijinx_triggered",
                    message=f"Hijinx executed: {hijinx_line}",
                    data={"line": hijinx_line},
                    tone=daypart
                )

                # --- Bitsy Meta Hijinx (Tier 2) ---
                if hijinx_line.startswith("Bitsy:"):
                    self.state.last_segment = "bitsy_meta"
                    return {
                        "type": "bitsy_meta",
                        "line": hijinx_line
                    }

                # --- Vega Pad Hijinx (Tier 1) ---
                self.state.last_segment = "vega_pad"
                self.state.hijinx_line = hijinx_line
                return {
                    "type": "vega_pad",
                    "hijinx_line": hijinx_line
                }

        # Mark last intro if needed (rundown counts as intro)
        if getattr(self.state, "last_segment", None) == "intro_rundown":
            from datetime import datetime
            self.state.last_intro_time = datetime.utcnow()

        # --- Reset Routing (Chip Reset) ---
        from .breaking_logic import should_reset_show, reset_allowed

        if should_reset_show(self.state, story_queue) and reset_allowed(self.state):
            log_event(
                event_type="chip_reset_triggered",
                message="Programming Director routing → chip_reset",
                data={"daypart": daypart, "energy": energy},
                tone="reset"
            )
            self.state.last_reset_time = datetime.utcnow()
            self.state.last_segment = "chip_reset"
            return "chip_reset"

        # --- Ad logic ---
        import script_engine.director.ad_logic as ad

        if ad.should_run_ad(self.state, daypart):
            self.state.last_promo_time = datetime.utcnow()
            log_event(
                event_type="ad_opportunity",
                message="Promo/Ad break allowed (timing + daypart)",
                data={"daypart": daypart, "energy": energy},
                tone=daypart
            )
            return "ad_break"

        # --- Normal routing ---
        next_segment = route_next_segment(
            state=self.state,
            story_queue=story_queue,
            energy=energy,
            daypart=daypart
        )

        log_event(
            event_type="segment_selected",
            message=f"Director routed to: {next_segment}",
            data={"daypart": daypart, "energy": energy},
            tone=daypart
        )

        self.state.last_segment = next_segment

        return next_segment
