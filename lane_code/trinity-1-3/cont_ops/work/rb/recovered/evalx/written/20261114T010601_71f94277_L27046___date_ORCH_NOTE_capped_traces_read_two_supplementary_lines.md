<!-- recovered by seal_plan: transcript=71f94277 line=27046 utc=2026-11-14T01:06:01.365Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_NOTE_capped_traces_read_two_supplementary_lines.md heredoc_quoted -->
# ORCH note on RESULT 0104Z: read and understood; two supplementary lines for the step-100 packet

**What the traces say.** On absolute distance and room size the leg now emits routing calls (`<gap a=... b=... rule=...>`) and then repeats them, because the direct read gives it no tool response: median thinking 2,048 on both types, against 47 and 51 for the parent. The leg has no direct rows for these two types (they are trained only as routing), so its direct scores on them measure the harness, not the model. On route planning the leg answers at once (median one thinking token, parent 98), which is where the +22.7 comes from.

**Consequences for the step-100 packet (reporting only; the decision fork and the registered rules stay exactly as confirmed):**
1. Add a supplementary table, produced by a separate small script that imports the confirmed primitives and is labelled SUPPLEMENTARY, NOT A RULE: primary overall with the two routed types removed from both arms (leg minus parent, leg minus f17, with intervals), and the budget-reached counts split into routed types (absolute distance, room size) and all other types, leg against parent, with the paired difference on the non-routed part.
2. In the packet's first lines, state that the direct read cannot score the two routed types for this lineage and that their numbers wait for the routed read.

Do this only if it costs under about 20 minutes; the decision packet itself must not wait for it. If it would, send the packet first and the supplement after.

**Priority after the packet:** the routed read of the step-100 export on Trinity is now the only way to see absolute distance, room size and the camera types for this lineage. Continue its gates (export restoration, parity, runtime admission, the real-data closure) and post one RESULT when a routed read can start, naming the card and the expected duration; ask me before taking a card for more than the probe.