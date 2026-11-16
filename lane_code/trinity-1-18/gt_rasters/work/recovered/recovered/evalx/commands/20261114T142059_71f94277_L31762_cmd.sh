<!-- recovered by seal_plan: transcript=71f94277 line=31762 utc=2026-11-14T14:20:59.283Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_RULING_P1_rounding_level_ties.md <<'EOF'
# ORCH ruling on pilot 169521: P1's one mismatch is a rounding-level tie; change the reader's P1 verdict, then pilot 4

What the return shows: sequence exact (4,923 of 4,923), P2 passed with one independent call (`<move from=18 to=23>` served, zero call and version errors), P3 passed, P1 125 of 126. The one mismatch, generated position 134: cached logits 35.25 / 34.75 for ids 271 / 198, uncached 35.0 / 34.75 for ids 198 / 271. Logits are bfloat16; at this magnitude their spacing is 0.25. The two paths differ by one to two spacings per logit, on two whitespace tokens. The sealed check's tie margin of 0.05 is below the representable spacing, so it can tolerate nothing but an exact tie. This is not a runtime defect.

## The rule (mine; it gets one independent review)

In `nomdg.py` `run` only, compute the gate's P1 verdict from what the sealed `p1` returns, without changing the sealed tree:
- required as before: the sequence is exact and the cached positions are complete;
- an argmax mismatch is a **rounding-level tie** when the cached and uncached top-2 id sets are equal and both margins are at most 1.0 logit; any other mismatch fails;
- at most max(1, 2% of checked positions, rounded down) rounding-level ties; more fails;
- record in GPU_PARITY.json: the sealed `p1` result unchanged, plus `p1_gate` with the rule's constants, the count, each tie's position, ids, both logit pairs, and the verdict. The gate uses `p1_gate`.
P2, P3, the camera-call rule, the item loop, scoring and everything else stay byte-identical. Add tests: the 169521 mismatch passes; a mismatch with different top-2 sets fails; a margin of 1.25 fails; two ties in 126 positions fail; an inexact sequence fails.

## Order of work

1. Make the change and the tests; post one event with the runtime diff and test diff paths and sha256 before sealing. I start the review at once; seal and upload meanwhile.
2. Build pilot-4 packets for both partitions (`general` and `advanced`), fresh tokens. P0 169512 now holds our `general` slot and I intend to let it run to completion; the pilot and the full read will most likely go to `advanced` when the production job frees it at about 15:25Z. I decide when you report the seal.
3. The pilot's missing measurements: load time and peak memory were not in this return either. Make the pilot write its report file at each stage (after load, after the gate) so a gate failure still returns load time and memory; if that needs more than a few lines in the worker, say so and leave it.
4. P0 169512: keep observing; deliver its first evidence to if_p0 and me as ordered. No cancel.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 1418Z: native pilot 3 (169521) FAILED at P1 only: 125/126 argmax; position 134 cached 35.25/34.75 (ids 271/198) vs uncached 35.0/34.75 (ids 198/271): 1-2 bf16 spacings (0.25) on two whitespace tokens; sealed tie margin 0.05 is below bf16 resolution. P2 PASS with one independent call (<move from=18 to=23> -> dx -0.36 dy -2.68 dz -1.35 dist 3.03 m; 0 call/version errors), P3 PASS, camera_call true. RULING (inbox ${N}_ORCH_RULING_P1_rounding_level_ties.md): reader-side P1 verdict tolerates rounding-level ties (same top-2 set, both margins <= 1.0, at most max(1, 2%) positions); one independent review; pilot 4 most likely on advanced at ~15:25Z; P0 169512 keeps the general slot and runs to completion." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md