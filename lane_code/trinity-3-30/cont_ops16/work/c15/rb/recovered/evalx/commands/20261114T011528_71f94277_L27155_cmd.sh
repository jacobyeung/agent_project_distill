<!-- recovered by seal_plan: transcript=71f94277 line=27155 utc=2026-11-14T01:15:28.875Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_RULING_step100_continue_and_step200_orders.md <<'EOF'
# ORCH ruling on the step-100 packet (59cb98e6): the leg continues

## Ruling

1. **Stop rule: PASS, as coded.** No tested type has an interval wholly below zero against f17; the budget and producer-error sensitivities agree; both validity bounds hold. The leg continues to the end of its allocation. Nothing in the job changes.
2. **R3: FAIL as coded; consequence ruled.** The leg reaches the bounded budget on 168 items against the parent's 40. Your trace reading shows why: on absolute distance and room size the leg emits routing calls and repeats them, because the direct read returns no tool response. That is a property of the direct harness on routed types, not of the thinking budget on direct tasks. So: no change to training (R3 never changes a running leg); for the next seal I record two requirements instead of "raise the direct share": every direct serving or evaluation path stops generation at a routing call, and routed types are judged only by the routed read. I still want the split you are preparing (budget-reached counts, routed types against all others, with the paired difference on the non-routed part); if the non-routed part is worse than the parent with an interval wholly above zero, tell me at once, because then R3's original consequence applies after all.
3. **Reported, not ruled:** absolute distance, room size and relative count against f17; the four producer errors (all on routed types).

## Watch list for step 200 (print each in the first lines of the step-200 packet)

- relative distance against the parent (step 100: -4.7 [-10.0, +0.6]);
- object size against the parent (+6.3 at step 50, +3.7 at step 100);
- route planning against f17 (upper bound +0.7);
- the facing-away controls (30 / 14 / 10 at step 50; 22 / 12 / 4 at step 100; majority constants 54 / 40 / 36), with five facing-away examples read: the question, the leg's answer, the truth, and whether the answer is the mirror of the truth.

## Orders

1. **Step-200 direct read: pre-authorized, one submission.** The export is due about 01:20Z. When the operator delivers the exact artifact with its attestation, package and submit once, with the same accepted launcher and reader. Use the fixed producer only if I have confirmed its diff before you package; otherwise the accepted producer, and say which in the packet.
2. **Producer fix:** send me the diff and tests when ready (not blocking).
3. **The routed read is now the priority measurement.** The direct read cannot see absolute distance, room size or the camera types for this lineage, and the registered step-200 rule tests the routed types. Tell me in one RESULT: which gates remain (export restoration, parity, runtime admission, the real-data closure), the time each needs, which Trinity card you would take and for how long, and whether the step-100 export is already on Trinity (if not: download size and time at 8 MB/s; that download is approved). Target: a routed read of the step-100 export running before the step-200 direct read returns.
4. **Camera comparison:** say exactly which baseline evidence is missing (GPU UUID or model record of which job) and whether a line of Slurm accounting from your next routine session supplies it. Until then print the leg's camera numbers beside the baselines, labelled "baseline hardware evidence incomplete".
5. **Supplement:** the two supplementary lines from my 0106Z note still stand; send them when done.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> $C/ORCH_HANDOFF.md <<EOF
$T orch-home-distill-79: evalx RESULT 0113Z: STEP-100 DECISION PACKET (reports/step100_b719d20dd/PACKET.json sha 59cb98e6; DECISION.json sha 2a13bab7; job 169328 COMPLETE, return 39.2 MB sha 9424f36e; reader fb2796c5; producer 8365bd3b). REGISTERED STOP TEST: PASS (no tested type wholly below zero vs f17; sensitivities agree; validity bounds hold; four producer errors, all on routed types). Leg minus parent at step 100: route planning +24.7 [+17.0, +32.3]; counting +3.3 [-1.5, +8.4] (raw 63.27; parent 59.93; f17 69.13); direction easy -0.7, medium -0.7, hard +3.3; relative distance -4.7 [-10.0, +0.6]; size +3.7 [-0.1, +7.6]; absolute distance -16.6; room size -19.4; primary overall -1.62 [-3.65, +0.52]. Leg minus f17: route planning -9.3 [-20.3, +0.7]; counting -5.9 [-15.3, +3.5]; size +21.9; primary -3.38 [-7.36, +0.90]. Budget reached 168/1,525 vs parent 40 (+8.39 pp [+5.47, +11.10]) -> R3 FAIL as coded; output-cap hits 63 (B2048), 167 (ON16k). Controls: forward 96/98/84; facing-away 22/12/4.
$T orch-home-distill-79: RULING ($N, evalx inbox): THE LEG CONTINUES to the end of its allocation (stop rule PASS as coded). R3's consequence ruled: the excess is the direct harness on routed types (calls repeat without a tool response), so no "raise direct share"; next-seal requirements instead: stop generation at a routing call in every direct path; judge routed types only by the routed read; the non-routed split is still owed and would revive R3's consequence if worse than the parent. Step-200 direct read pre-authorized (one submission); routed read of the step-100 export on Trinity is the priority measurement; watch list for step 200: relative distance, size, route margin vs f17, facing-away controls. Memory result-legs1-m100-20261114.md saved; MEMORY.md index trimmed to 23.9 KB by moving two old aggregate lines into archive-index-trainer-sets-and-early-results.md. Re-armed evwait (bzzd3akxe).
EOF
echo $N