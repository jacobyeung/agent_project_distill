# Off-AWS re-plan: what trains and reads next on Trinity and Orchard (lane offaws_replan, 2026-11-09)

Status: PLAN, 2026-11-09 ~21:45Z (13:45 PT). Scope (USER 11-09 ~13:03 PT): Trinity and Orchard only. Mind is storage and a copy relay. Every model weight and needed input leaves AWS, and the copy order only decides what goes first. Claude Opus subagents do kit ports and debugging.
Tags: **M** = measured (source given); **E** = estimate. Times are UTC, with PT (UTC-8) in brackets. The Orchard cluster clock is taken to be US Eastern (UTC-5): its running jobs list end times that only make sense at UTC-5 or UTC-6, so Orchard-derived times carry ±1 h.

## Question
With no AWS compute, what do we train and read next, where, and when? Which runs belong on Orchard H100s, and which fit Trinity's 49 GB cards? In what order must the AWS copy-off deliver inputs?

## Answer
- **The 9B full fine-tuning line (CP2, with CP1-R as fallback) moves to Orchard's advanced 4-GPU H100 slot at world 4.** Trinity cannot host it.
  - 0-13 has 7 cards, while the trainer recipe validates world 8, 16 or 32 (ELEVEN_DAY_AWS_PLAN, Orchard portability).
  - No other allowed node shows 8 free 49 GB cards.
  - 64-frame rows do not fit on 49 GB cards.
  - Its ~0.3-0.5 TB of inputs (E) would need 1-2 days through Trinity's governor at ~3 MB/s.
- **Trinity 0-13 runs two things:** the frozen-backbone grounding test (MDG-A, GPUs 0-4) and the inference reads (evalx, GPUs 5-6). The small vnice cards have no decision-changing job tonight.
- **Inputs take two routes.**
  - **Orchard:** AWS -> GCS (session URIs minted on 2-18, ~65-80 MB/s M) -> login-node `gcloud storage cat` -> /project/community cache (780 GB free at 21:09Z, M) -> node /tmp.
  - **Trinity:** Mind -> 2-18 through the governor, as one serial stream.
- **Orchard's queue binds, not the kit.** The earliest 4-GPU start is Tue 15:00-18:00Z (07:00-10:00 PT), E. The first CP2 read comes ~3.5 h later, inside the allocation (E).

### Ranked queue
| # | Item | Host, GPUs | Earliest launch | First read | Decision it changes |
|---|---|---|---|---|---|
| 1 | **MDG-A**: 39M mask decoder on frozen T0 m800 (MASK_DECODER_GROUNDING_DESIGN) | 0-13 GPUs 0-4, normal priority | Mon ~23:00Z (15:00 PT), mdg_build E | fail-fast ~23:40Z; read Tue ~06:00Z (Mon 22:00 PT) | GO: MDG becomes the grounding path at the next T-line change. NO-GO: choose among GH1, a SAM 3 tower with a presence gate, and pt-track |
| 2 | **ReVSI dev cap71** (452 q, ReVSI's own 32 frames): T0 m800 first (no extra copy), then CP1 m200 | 0-13 GPUs 5-6 (evalx, vLLM 0.32) | T0 m800 Tue ~00:30Z (Mon 16:30 PT); CP1 m200 ~03:00Z (19:00 PT), E | ~01:30Z (17:30 PT) / ~04:00Z (20:00 PT) | A gap to SOTA of <=~3 puts grounding and routed types first; a gap of >=~6 puts VQA dose and frames first in CP2/CP3 |
| 3 | **MDG follow-up.** GO: P1-MDG routing table plus the MDG eval pass (~7 H100 GPU-h in the record). NO-GO: grounding fallback | 0-13 GPUs 0-4 | Tue ~06:30Z (Mon 22:30 PT) | Tue ~10:00Z (02:00 PT), E | which VSI object types route in CP2/CP3 |
| 4 | **CP2**, warm-started from CP1 m200 at world 4. Contents: 64 nested VQA frames, ARKit sensor-depth rows, v3.11 routed rows with the tool-mode flag, k1208 traces, route 3x and room rows, pointing negatives, frozen GXC connector | Orchard advanced, 4 x H100 | Tue 15:00-18:00Z (07:00-10:00 PT), E; needs the slot, the closure in GCS and the port | m50 at +~3.5 h, read in-allocation (~30 min): Tue ~19:00-22:00Z (11:00-14:00 PT), E | CP2 becomes the lineage base and the final recipe, or a failing component is unbundled at the next change point |
| 4b | **CP1-R**, only if CP2 is not READY when the slot opens: CP1 m200 init, route 3x, room 5x, pose weight 1.5 | same | same | m50 at +~2.5 h, E | carries the line if CP2 slips |
| 5 | CP2 prep (~1-5 min, M from orchard_kit) | Orchard general, 1 GPU (main has priority) | when general frees | minutes | none; it is a gate |

