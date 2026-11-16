<!-- recovered by seal_plan: transcript=71f94277 line=28407 utc=2026-11-14T04:06:28.601Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_RULING_hold_trinity_recovery_and_orchard_routed_feasibility.md <<'EOF'
# ORCH ruling on BLOCKER 0404Z: hold the Trinity recovery; report on running the routed read on Orchard instead

Right to stop. Two facts decide it: every card on trinity-0-28 is busy (main's r3123 among them, and main has priority), and filling that disk further for a read that has no card would only take space from main.

## 1. Trinity path: hold, with a light watch

- Start nothing on trinity-0-28: no export, no depth files, no guard.
- Once every 30 minutes, inside your normal session cadence and through your existing session (no new node, no retry of 0-3), read on trinity-0-28 the free space and the eight cards. If a 48 GB card reads empty at two consecutive checks and free space is at least 151 GB, post a QUESTION with the reading; I then tell main and give the go. Do not start on your own.
- The ssh record you gave (two completed calls and one failed attempt in five minutes) is well inside the cluster's login limits; noted for the user.

## 2. The question that matters more: can the routed read run on Orchard?

Trinity cards will stay contested while main's evaluations run, and every later checkpoint (step 400, the final export, any continuation) needs a routed read too. Orchard has what the direct reads use, the production trainer's own runtime (so parity with training is natural), the base model, the depth initializer and the model manifest as staged parts, the dev-S1 frames, and H100 cards; our four-GPU `advanced` cap frees when the leg ends at about 15:00Z (one job at a time there).

Post one RESULT, at most 40 lines, CPU only, no build:
1. What the routed reader needs at run time, item by item: code (`M/native/out2/read_runtime.py`, `nomdg.py` and what they import), runtime, the export, base, depth initializer, manifest, the 636-item cohort's RGB, masks and geometry. For each: is it already on Orchard (path and evidence), or only on Trinity (path, bytes), and how it would get there (the approved route is Trinity to GCS to Orchard; state bytes and time at 8 MB/s).
2. What your accepted Orchard launcher would need: a new job family beside the direct ones, its staging, its result return (size), and what must be confirmed. Reuse the accepted staging and return code unchanged wherever possible, and say which lines would differ.
3. The parity gate (P1 to P3) on Orchard: what it compares and whether the production runtime removes the runtime-admission question.
4. Expected GPU time for the 636 items on one H100 (from any measured per-item time you hold; otherwise say it is unmeasured and how the first minutes of the job would measure it), and whether the camera cohort (450 items) is part of it.
5. Build time, review needs, and the earliest hour it could be submitted.

I decide between the two paths when I have this. The queued direct reads and the IF-P0 submissions are unaffected.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: evalx(19) BLOCKER 0404Z: trinity-0-28 at 151.66 GB free (0.34 GB under my 152 GB start gate) and GPU 6 now occupied (VLLM worker 44.6 GB; all eight cards busy; main's r3123 running there); nothing started. Its ssh record before the 0-3 drop: two completed calls + the failed one in five minutes (well inside the login limits; cause of the drop unknown). RULING ($N): Trinity recovery ON HOLD (no bytes; a 30-minute light watch of 0-28; QUESTION if a card is empty at two consecutive checks and >= 151 GB free); feasibility RESULT requested for running the routed read on ORCHARD (production runtime, staged inputs, H100; what is missing and how it gets there; launcher family; parity; GPU time; build and review). Re-armed evwait (bvbwh4b6p)." >> $C/ORCH_HANDOFF.md; echo $N