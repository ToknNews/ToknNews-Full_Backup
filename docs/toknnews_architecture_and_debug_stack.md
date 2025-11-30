# ToknNews: Architecture and GPT Audio Stack Debug Plan

## System Overview

```
[Ingestion Stack] 
   └── api_fetchers.py, fetch_all.py, ingestion_aggregator.py
       └── Pulls, filters, and ranks headlines
           └── Feeds -> rank_stories.py -> episode_builder.py
               └── timeline_builder.py (GPT-driven sequencing of cast + headlines)
                   ├── Uses: daypart_rules, pd_controller, cast_fatigue, pacing_model
                   └── Outputs: timeline dict -> episode_runner.py
                           └── script_engine_v3.py
                               ├── Calls openai_writer.py for line generation
                               ├── Assembles persona sequences
                               └── Sends to audio pipeline
```

## Audio Rendering Stack

- `tts_renderer.py`: batch generation per character
- `tts_engine.py`: ElevenLabs API
- `mixer.py`: assembles speech + stingers + bed
- `audio_block_renderer.py`: block-level rendering (per scene)
- `processor/audio_utils.py`: applies effects (ducking, normalize)
- Output: `final_mix.wav`

## Known Issues

1. **Timeline Confusion**
   - Redundant logic in `duo_crosstalk`, `pd_controller`, and `timeline_builder`
   - Some legacy `chip_toss` lines may override clean GPT transitions
   - Toss vs. scene intro distinction is not always respected

2. **Line Order Inconsistency**
   - GPT outputs correct ordering, but render step may not sequence Vega → Chip → others as expected
   - `vega` intro must be fixed at top of timeline (with theme_music)

3. **Redundant Files**
   - Stale `.bak` files
   - Multiple entrypoints (e.g., episode_loop.py vs. run_test.py)

## Next Steps

1. **Stabilize source-of-truth branch**
   - We are using `source` for now
   - All refactors and patches should flow through here

2. **Full rewrite of:**
   - `timeline_builder.py`: enforce consistent anchor flow
   - `pd_controller.py`: shrink logic, clean edge cases

3. **Standardize GPT prompts**
   - All anchor/toss/story lines should share conventions
   - Leverage `director_logger` for traceable transitions

4. **Clean audio config**
   - Ensure tts_render uses timeline order
   - Strip out leftover stubs from test_payload

5. **Set new PM2 process**
   - Deploy from `/opt/toknnews`

---

## Deployment Notes

- All files now under `/opt/toknnews` instead of `/var/www`
- PM2 config under `pm2/processes.json`

