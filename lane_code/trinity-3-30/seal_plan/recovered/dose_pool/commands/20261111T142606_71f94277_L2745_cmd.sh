<!-- recovered by seal_plan: transcript=71f94277 line=2745 utc=2026-11-11T14:26:06.034Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd && NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ) && T=$(date -u +%Y%m%dT%H%MZ) && m=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory
cat > dose_pool/inbox/${T}_ORCH_user_ruling_rewrite.md <<EOF
# ORCH ($NOW): the user's ruling on the prose traces, and what it adds to your scoping
The user, 2026-11-11: "Good you read the traces. Feel free to use the Gemini key to rewrite the traces. Or if you could programmatically change [them], that would be nice." So both routes are open; the programmatic one is preferred where its inputs exist.
- Route A (programmatic): the frame-level generator with per-frame ground truth, as in my 14:2xZ note. Your scoping table says how many rows it covers with what exists today.
- Route B (Gemini key): for scenes without per-frame ground truth, Argon and Carbon do the frame-level PERCEPTION only: for each question's named objects, in the 32 sampled frames, which frames show the object and where (box and point), in the Gemini-native format that lane gemini_native measured (/scratch/jjyeung/orch_cd/gemini_native/out/LABEL247_SWITCH.md and its record), with the two models' agreement as the filter (lane label_247's runner is the reference; read-only). The program, not the model, then lifts and computes, and a row is kept only if its computed answer reproduces the ground-truth answer within the type's tolerance and every frame and box it cites exists in the labels. The model never writes the reasoning or the numbers: an earlier rewrite by a language model invented references it had not seen (saved note lesson-vsd-invented-references-20261109.md in /home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/).
- Add to your RESULT: for route B, what geometry the program would use when a scene has scene-level boxes but no per-frame depth or pose (which rows can be computed from the annotated boxes alone once the frames and boxes are cited, and which need tower or sensor depth), and a pilot plan: 200 rows per type, with grounding correctness against ground truth on the scenes where it exists, answer reproduction, the rate of cited frames or boxes that do not exist (must be 0), calls and tokens per row, and the daily throughput at 8 concurrent calls per model. Do not start the pilot until I say; the key is shared with label_247 (80 concurrent calls) and frontier_read. Only the Argon and Carbon buckets, never Gemini 3.1 Pro.
EOF
cat > $m/user-ruling-trace-rewrite-gemini-20261111.md <<'EOF'
---
name: user-ruling-trace-rewrite-gemini-20261111
description: USER 2026-11-11 - prose traces may be rewritten with the Gemini key or converted programmatically; read training traces before training; the orchestrator's rule for how Gemini is used in a rewrite
metadata:
  type: feedback
---

The user, 2026-11-11 ~06:25 PT, after I read a 170K-row data pool's traces and found them to be prose stating the ground-truth value: "Good you read the traces. Feel free to use the Gemini key to rewrite the traces. Or if you could programmatically change [them], that would be nice."

**Why:** the pool's questions and answers were sound but its traces were in the form that loses ([[trace-review-20261107]], [[toolprog-results-20261107]]); the user wants them converted, by program where possible and with the Gemini key otherwise, and values reading the actual training text before a launch ([[experiment-design-lessons-20261108]] rule 7).

**How to apply:**
- Read sample rows of every new training stream myself (or have a lane quote them) before it goes near a GPU; a lane's "rows traced" count says nothing about the trace form.
- Prefer the programmatic frame-level generator where per-frame ground truth exists.
- My rule for the Gemini route (my interpretation, not the user's words): Argon and Carbon supply frame-level perception only (which frames show the object, boxes, points; two-model agreement), the program lifts and computes, and a row is kept only if its answer reproduces ground truth and every cited frame and box exists. The model never writes the reasoning or the numbers ([[lesson-vsd-invented-references-20261109]]). Only the Argon and Carbon buckets ([[gemini-key-main-priority]]).
EOF
echo '- **READ FIRST, USER 11-11:** [Rewrite prose traces: program or Gemini key](user-ruling-trace-rewrite-gemini-20261111.md) read sample rows before any launch; Gemini supplies frame perception only, the program computes' >> $m/MEMORY.md
echo "$NOW orch-home-distill-79: USER ~14:25Z: 'Good you read the traces. Feel free to use the Gemini key to rewrite the traces. Or if you could programmatically change [them], that would be nice.' Memory user-ruling-trace-rewrite-gemini-20261111. Told dose_pool: route A programmatic (preferred), route B Argon+Carbon for frame-level perception only with program-computed answers and a keep rule; add route-B geometry and a 200-rows-per-type pilot plan to its scoping RESULT; no pilot until my go." >> ORCH_HANDOFF.md